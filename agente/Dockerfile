FROM python:3.11

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app/ /app

COPY .env .env

EXPOSE 8003

CMD ["fastapi","run","app/main.py","--port","8003"]   
