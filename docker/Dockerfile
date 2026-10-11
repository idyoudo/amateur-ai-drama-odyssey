# AADO 控制面/worker 镜像（Python 3.12-slim，代码兼容 3.9）
FROM python:3.12-slim

WORKDIR /app

# 依赖：后端（SQLAlchemy/FastAPI/uvicorn）+ 媒体核心（numpy/Pillow）
COPY requirements.txt ./
COPY demo/requirements.txt ./demo-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r demo-requirements.txt

# 代码
COPY film/ ./film/
COPY apps/ ./apps/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# 默认起 API；worker 服务用 command 覆盖
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "4000"]
