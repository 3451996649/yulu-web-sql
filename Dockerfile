# 使用官方 Python 运行时作为父镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将当前目录内容复制到容器的 /app 目录中
COPY requirements.txt .
COPY yulu_server_sql.py .

# 安装依赖包
RUN pip install --no-cache-dir -r requirements.txt

# 创建数据目录用于持久化数据库
RUN mkdir -p /data

# 使端口 6673 可供此容器外的环境使用
EXPOSE 6673

# 定义环境变量
ENV FLASK_ENV=production
ENV DB_FILE=/data/quotes.db

# 创建非root用户运行应用（安全最佳实践）
RUN groupadd -r yulu && useradd -r -g yulu yulu
RUN chown -R yulu:yulu /app /data
USER yulu

# 在容器启动时运行服务器
CMD ["gunicorn", "--bind", "0.0.0.0:6673", "--workers", "4", "yulu_server_sql:app"]
