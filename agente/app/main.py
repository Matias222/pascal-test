from app import desacople
from fastapi import Depends, FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.models import api_models, external_models

load_dotenv()

SETUP = os.getenv("SETUP")

app = FastAPI(title="Hook API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def hola():
    return "Hola a todos"

@app.post("/hook")
async def whatsapp_webhook(request: external_models.WebhookPayload, background_tasks: BackgroundTasks):

    # En prod devolver respuesta inmediata, liberar la api!

    mensaje = ""
    user_phone = None

    for i in request.data:

        if i.message.type == "text":

            if user_phone is None:
                user_phone = i.message.from_
            mensaje += i.message.text.body + "\n"

        else:

            # Avisar a usuario que fue imagen/audio o usar whisper
            pass

    print(f"Usuario: {user_phone}")
    print(f"Mensaje: {mensaje}")

    background_tasks.add_task(desacople.principal, user_phone, mensaje)
    return

    if SETUP == "LOCAL":
        return await desacople.principal(user_phone, mensaje)
    else:
        background_tasks.add_task(desacople.principal, user_phone, mensaje)

