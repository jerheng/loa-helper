# Dockerfile, Image, Container

FROM python:3.8.18-slim
WORKDIR /app
COPY requirements.txt .
COPY ./app ./app
RUN pip install -r requirements.txt

CMD ["python", "-u", "./app/main.py"]
