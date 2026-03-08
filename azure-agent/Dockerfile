FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "streamlit run app_cloud.py --server.address 0.0.0.0 --server.port ${PORT:-8000} --server.headless true"]
