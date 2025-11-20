# 1. 使用官方 Python 基础镜像
FROM python:3.11-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 复制应用代码和 FAISS 索引
# 关键: faiss_index 文件夹必须预先在本地通过 ingest.py 生成
# 此步骤会将 app.py 和 faiss_index/ 文件夹都复制到镜像中
COPY app.py .
COPY faiss_index/ ./faiss_index/
COPY data.txt .

# 4.5 构建 FAISS 索引 (如果还不存在)
# RUN python ingest.py

# 5. 暴露端口
EXPOSE 8080

# 6. 启动命令
# 用 uvicorn 运行 FastAPI 应用
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]