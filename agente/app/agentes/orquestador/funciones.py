from app.models import api_models, agent_models
from app import auxiliares, agents_main

import json

tools = [
    {
        "name": "cambiar_flujo_agente",
        "description": """Cambia el flujo de conversación a un agente especializado.

Usa esta herramienta cuando determines que el usuario necesita un tipo específico de asistencia:

- BUSCADOR: Cuando el usuario quiere buscar propiedades inmobiliarias, departamentos, casas, o pregunta sobre características específicas (habitaciones, precio, ubicación, distrito, etc.)
  Ejemplos: "Busco un depa de 2 habitaciones", "Quiero algo en Miraflores", "Departamentos baratos"

- AGENDADOR: Cuando el usuario quiere agendar, programar o solicitar una visita, cita o reunión.
  Ejemplos: "Quiero agendar una visita", "Puedo ir el sábado?", "Quisiera visitarlos"

- ORQUESTADOR: Mantén este flujo para saludos simples, preguntas generales sobre qué puedes hacer, o conversación casual sin intención específica.
  Ejemplos: "Hola", "Qué puedes hacer?", "Buenas tardes"

IMPORTANTE: Si un saludo viene acompañado de una intención clara (ej: "Hola, busco un depa de 3 habitaciones"), debes cambiar directamente al agente correspondiente (BUSCADOR en este caso), no quedarte en ORQUESTADOR.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "nuevo_estado": {
                    "type": "string",
                    "enum": [estado.value for estado in api_models.TipoEstado],
                    "description": "El tipo de agente al que se debe cambiar el flujo"
                },
                "razonamiento": {
                    "type": "string",
                    "description": "Breve explicación de por qué se está cambiando a este agente (para debugging y tracking)"
                }
            },
            "required": ["nuevo_estado", "razonamiento"]
        }
    }
]


async def ejecucion(api_state:api_models.ApiState,agente:agent_models.Agente,function_args:dict,tool_name:str):

    response=None

    if(tool_name=="cambiar_flujo_agente"):

        api_state.lead.estado_agentico=function_args["nuevo_estado"]

        agents_main.asignacion(api_state,agente)

        response = json.dumps({
                "status": "success",
                "mensaje": f"Cambio exitoso a {api_state.lead.estado_agentico}, continua con el proceso"
            })
        
        agente.funciones=[] #Cuando cambiamos de agente se reinicia el tool trace

    else:

        raise Exception("La IA se equivoco con el nombre de la funcion a llamar")

    return response