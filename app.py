import json
import logging
import os
import threading
import time

# 确保导入 render_template 和 send_from_directory
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = Flask(__name__)
# 允许所有来源的CORS请求，用于开发阶段。生产环境应限制为特定来源。
app.config['CORS_HEADERS'] = 'Content-Type'
# 允许从任何来源进行WebSocket连接
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading') # 指定async_mode

# 用于存储Lucky STUN规则的IP和端口信息
# 使用字典来存储，键是rule_name
LUCKY_IP_DATA_FILE = 'lucky_ip_data.json'
lucky_ip_data = {}
data_lock = threading.Lock() # 用于线程安全访问数据


def load_lucky_ip_data():
	"""从文件中加载Lucky IP数据"""
	global lucky_ip_data
	if os.path.exists(LUCKY_IP_DATA_FILE):
		with open(LUCKY_IP_DATA_FILE, 'r') as f:
			try:
				lucky_ip_data = json.load(f)
				logging.info(f"Loaded existing data: {lucky_ip_data}")
			except json.JSONDecodeError:
				logging.warning(f"Error decoding {LUCKY_IP_DATA_FILE}, starting with empty data.")
				lucky_ip_data = {}
	else:
		logging.info(f"{LUCKY_IP_DATA_FILE} not found, starting with empty data.")

def save_lucky_ip_data():
	"""
	将Lucky IP数据保存到文件。
	注意：此函数不应自行获取data_lock，因为它预期在调用它的函数中（如update_lucky_ip）已经获取了锁。
	"""
	with open(LUCKY_IP_DATA_FILE, 'w') as f:
		json.dump(lucky_ip_data, f, indent=4)
	logging.info("Lucky IP data saved.")

# 新增的路由，用于在访问根路径时渲染前端页面
@app.route('/')
def index():
	"""渲染Lucky Dashboard的前端页面"""
	# Flask 会自动在 'templates' 文件夹中寻找 'index.html'
	return render_template('index.html')


@app.route('/update_lucky_ip', methods=['POST'])
def update_lucky_ip():
	"""
	接收来自Lucky STUN的Webhook通知，更新IP和端口。
	Lucky STUN Webhook 配置示例:
	URL: http://your_dashboard_ip:5001/update_lucky_ip
	Method: POST
	Headers: Content-Type: application/json
	Body (JSON): {"ip": "#{ip}", "port": "#{port}", "rule_name": "#{name}", "timestamp": "#{time}"}
	"""
	data = request.get_json()
	if not data:
		return jsonify({"status": "error", "message": "Invalid JSON"}), 400

	ip = data.get('ip')
	port = data.get('port')
	rule_name = data.get('rule_name')
	# 接收 timestamp
	timestamp = data.get('timestamp') 

	logging.info(f"Received raw webhook data: {data}")

	if not all([ip, port, rule_name]):
		return jsonify({"status": "error", "message": "Missing ip, port, or rule_name"}), 400

	with data_lock: # 在这里获取锁，保护 lucky_ip_data 的读写
		# 更新数据，确保包含 timestamp
		lucky_ip_data[rule_name] = {
			'ip': ip,
			'port': port,
			'timestamp': timestamp # 存储接收到的时间戳
		}
		save_lucky_ip_data() # 在锁内部调用保存函数

	logging.info(f"Lucky STUN [{rule_name}] IP/Port updated: {ip}:{port} at {timestamp}")

	# 使用 Socket.IO 发送更新到所有连接的客户端
	socketio.emit('all_rules_updated', lucky_ip_data)
	logging.info("Emitted 'all_rules_updated' event to clients.")
	
	return jsonify({"status": "success", "message": "IP and port updated"}), 200

@app.route('/get_lucky_ip', methods=['GET'])
def get_lucky_ip():
	"""提供当前存储的所有Lucky IP数据给前端"""
	with data_lock:
		return jsonify(lucky_ip_data)

@socketio.on('connect')
def handle_connect():
	logging.info("Client connected to WebSocket.")
	# 客户端连接后立即发送所有当前规则数据
	with data_lock:
		emit('all_rules_updated', lucky_ip_data)

@socketio.on('disconnect')
def handle_disconnect():
	logging.info("Client disconnected from WebSocket.")

if __name__ == '__main__':
	load_lucky_ip_data()
	logging.info("Starting Lucky Dashboard Backend...")
	# 运行Flask应用，使用SocketIO的run方法而不是app.run
	# host='0.0.0.0' 允许从外部访问
	# port=5000 是容器内部的端口，Docker Compose 会将其映射到外部的5001
	socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True) # 修复：添加 allow_unsafe_werkzeug=True
