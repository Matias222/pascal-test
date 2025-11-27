FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

#CMD ["gunicorn", "--bind", "0.0.0.0:8001", "db_api.wsgi:application"]
CMD ["uvicorn", "api.asgi:application", "--host" ,"0.0.0.0" ,"--port" ,"8000"]
