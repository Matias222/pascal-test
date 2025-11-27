import json, asyncio, os
from dotenv import load_dotenv
from app.auxiliares import print_info_api_call, retry_on_failure
from app.models import api_models, agent_models
from httpx import AsyncClient, Response, Timeout

load_dotenv()

timeout = Timeout(7)

KAPSO = os.getenv('KAPSO')
NUMERO = os.getenv('NUMERO')

@retry_on_failure()
async def enviar_mensaje(api_models: api_models.ApiState):

    payload={
        "messaging_product": "whatsapp",
        "to": api_models.lead.phone,
        "type": "text",
        "text": {
            "body": api_models.lead.buffer[-1].blob.respuesta_al_lead
        }
    }

    headers={
        "X-API-Key":KAPSO,
        "Content-Type": "application/json"
    }

    async with AsyncClient(timeout=timeout) as client:
        
        response = await client.post(f"https://api.kapso.ai/meta/whatsapp/v21.0/{NUMERO}/messages", json=payload, headers=headers)
        
        print_info_api_call(response)
        
        return response.json(), response.status_code