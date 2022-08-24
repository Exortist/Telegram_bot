FROM python:3.10.6-slim-buster

WORKDIR /app




COPY . /app



RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3.10", "src/main.py"]