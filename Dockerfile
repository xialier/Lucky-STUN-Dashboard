# 使用官方 Python 运行时作为父镜像
FROM python:3.9-slim-buster

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app.py .

# 复制 templates 文件夹及其所有内容到容器内部的 /app/templates
COPY templates /app/templates

# 暴露 Flask 应用监听的端口 (容器内部)
EXPOSE 5000

# 启动 Flask 应用
CMD ["python", "app.py"]
