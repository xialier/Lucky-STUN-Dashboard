### **项目结构**

首先，请确保您的项目目录结构如下所示：

```
lucky_dashboard/
├── app.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── templates/
	└── index.html
### **部署和使用说明**

#### **Lucky STUN Dashboard**

这是一个简单的 Dockerized 应用程序，用于显示 Lucky STUN 端口转发规则的最新状态。它包括一个 Flask 后端（处理 Lucky STUN 的 Webhook 和提供数据）和一个响应式前端页面。

#### **特点**

  * 通过 Lucky STUN 的 Webhook 实时更新公网 IP/端口信息。
  * 使用 Socket.IO 实现前端实时更新，无需刷新页面。
  * 前端页面美观，具备 Sun-Panel 风格。
  * 支持手机和 PC 客户端自适应布局。
  * 前端页面包含一个简单的预设密码认证。
  * 数据持久化存储在 `lucky_ip_data.json` 文件中。

#### **前提条件**

  * 已安装 Docker 和 Docker Compose。
  * 一个正在运行的 Lucky STUN 客户端，并配置了 Webhook 功能。

#### **快速开始**

1.  **克隆仓库：**

	```bash
	git clone https://github.com/xialier/Lucky-STUN-Dashboard.git
	cd lucky_dashboard
	```


2.  **配置密码和域名：**
	打开 `templates/index.html` 文件，找到以下两行并进行修改：

	```javascript
	const CORRECT_PASSWORD = "123321"; // <-- 将此处的 "123321" 替换为您自己的密码
	const fixedDomain = "xialier.*****.net"; // <-- 将此处的域名替换为您实际的域名
	```

	**注意：** 前端密码保护安全性较低，不适用于敏感信息。

3.  **构建和运行 Docker 服务：**
	在 `lucky_dashboard` 目录中，执行以下命令构建 Docker 镜像并启动服务。`--no-cache` 选项确保每次都使用最新的文件进行构建。

	```bash
	docker compose build --no-cache backend
	docker compose up -d
	```

	此命令会启动一个名为 `lucky_backend` 的 Docker 容器，并将其内部的 `5000` 端口映射到宿主机的 `5001` 端口。

4.  **配置 Lucky STUN Webhook：**
	打开您的 Lucky STUN 客户端设置，找到 Webhook 或通知相关的配置项，添加一个新的 Webhook。

	  * **URL:** `http://<您的NAS局域网IP>:5001/update_lucky_ip`
		例如：`http://192.168.2.8:5001/update_lucky_ip`
	  * **Method:** `POST`
	  * **Headers:** `Content-Type: application/json`
	  * **Body (JSON):**
		```json
		{
		  "ip": "#{ip}",
		  "port": "#{port}",
		  "rule_name": "#{name}",
		  "timestamp": "#{time}"
		}
		```

	保存配置并触发一次更新（例如，重启 Lucky STUN 客户端或等待其定时更新）。

5.  **访问 Dashboard：**
	在浏览器中访问 `http://<您的NAS局域网IP>:5001`。
	例如：`http://192.168.2.8:5001`
	您将看到密码输入框，输入您在 `index.html` 中设置的密码后即可访问 Dashboard。

#### **持久化数据**

数据会存储在 `lucky_ip_data.json` 文件中。为了确保数据在容器重启后不丢失，`docker-compose.yml` 已经包含了卷挂载配置：

```yaml
	volumes:
	  - ./lucky_ip_data.json:/app/lucky_ip_data.json # 将数据文件挂载到主机
```

这将把容器内部的 `/app/lucky_ip_data.json` 文件映射到您 `lucky_dashboard` 项目目录下的 `lucky_ip_data.json` 文件，实现数据持久化。

#### **停止和清理**

要停止并移除 Docker 服务：

```bash
docker compose down
```

要停止、移除服务并删除 Docker 镜像和数据卷：

```bash
docker compose down -v --rmi all
```
