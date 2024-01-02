# Dockerfile, Image, Container

FROM python:3.8.5
WORKDIR /app
COPY requirements.txt .
COPY ./app ./app
RUN pip install -r requirements.txt

CMD ["python", "./app/main.py"]