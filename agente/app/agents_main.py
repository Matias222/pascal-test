import json, asyncio

from app.models import api_models, agent_models
from app.agentes.orquestador import todo as orquestador
from app.agentes.buscador import todo as buscador
from app.agentes.agendador import todo as agendador
from app.auxiliares import retry_on_failure

from dotenv import load_dotenv
from anthropic import AsyncAnthropic, transform_schema

client = AsyncAnthropic()

load_dotenv()

client = AsyncAnthropic()

@retry_on_failure()
async def call_claude(agente:agent_models.Agente,modelo:str):


  response_claude = await asyncio.wait_for(
      client.beta.messages.create(
          model=modelo,
          system=agente.sistema,
          messages=agente.messages,
          betas=["structured-outputs-2025-11-13"],
          tools=agente.tools,
          tool_choice={"type": agente.tipo_funciones, "disable_parallel_tool_use": True},
          temperature=agente.temperatura,
          max_tokens=18000,
          output_format={
            "type": "json_schema",
            "schema": transform_schema(agent_models.Response),
        }
      ),
      timeout=agente.timeout_seconds
  )

  return response_claude

def asignacion(api_state:api_models.ApiState,agente:agent_models.Agente):

    if(api_state.lead.estado_agentico==api_models.TipoEstado.ORQUESTADOR): agente_usar=orquestador
    elif(api_state.lead.estado_agentico==api_models.TipoEstado.BUSCADOR): agente_usar=buscador
    elif(api_state.lead.estado_agentico==api_models.TipoEstado.AGENDADOR): agente_usar=agendador
    else: agente_usar=orquestador

    agente.messages = [{}]

    usuario_prompt,dinamico_prompt=agente_usar.usuario_prompt(api_state)
    
    agente.messages[0]={"role": "user", "content": [{"type":"text","text":usuario_prompt,"cache_control": {"type": "ephemeral"}}]}
    agente.messages.append({"role": "user", "content": dinamico_prompt})

    agente.tools=agente_usar.tools
    agente.sistema=agente_usar.sistema_prompt()
    agente.modelo_principal=agente_usar.modelo_principal
    agente.modelo_backup=agente_usar.modelo_backup
    agente.ejecucion=agente_usar.ejecucion

async def carla(api_state:api_models.ApiState):

    agente=agent_models.Agente()

    asignacion(api_state,agente)

    for i in range(7):
        
        print("8"*50)
        print("Agente")
        print(agente.messages)
        print("8"*50)
        
        try:
            agente.timeout_seconds=45
            respuesta_modelo=await call_claude(agente,agente.modelo_principal)
        except:
            agente.timeout_seconds=60
            respuesta_modelo=await call_claude(agente,agente.modelo_backup)

        if(respuesta_modelo.stop_reason == "tool_use"): 

            try:
                tool_use=next(block for block in respuesta_modelo.content if block.type == "tool_use")
            except:
                print("Error en tool_use pero sin content")
                agente.tipo_funciones="any" #forzar tool
                continue

            print("Function call ->", tool_use)

            tool_name = tool_use.name
            function_args = tool_use.input

            response_tool=await agente.ejecucion(api_state,agente,function_args,tool_name)
            
            agente.messages.append({"role": "assistant", "content": respuesta_modelo.content})
            agente.messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": response_tool,
                        }
                    ],
                }
            )

            agente.funciones.append({
                "input": str(function_args),
                "name": tool_name,
                "output": str(response_tool)
            })

        else:

            if(respuesta_modelo.content==[]): #Casos raros que suceden

                    agente.messages.append({"role": "user", "content": f"Ya tienes la informacion de la ultima tool. Dale forma y da una respuesta que englobe a todo esto"})

                    continue
                
            respuesta_json = json.loads(respuesta_modelo.content[0].text)

            api_state.lead.buffer.append(api_models.Chat(tipo=api_models.TipoChat.AI,blob=api_models.AIResponse(respuesta_al_lead=respuesta_json["respuesta_final_usuario"],razonamiento=respuesta_json["razonamiento"])))
            api_state.conversa.funciones=agente.funciones

            print(respuesta_json)
            
            break
    


        


    #usuario_prompt,dinamico_prompt=prompts_usar.usuario_prompt(api_state)
    #messages[0]={"role": "user", "content": [{"type":"text","text":usuario_prompt,"cache_control": {"type": "ephemeral"}}]}
    #messages.append({"role": "user", "content": dinamico_prompt})
    #respuesta=await recursion_arbol(tools,messages,funciones,api_state,1,sistema,temperatura,tipo_funciones)
    #respuesta["herramientas_usadas"]=funciones
    #api_state.ejecucion.claude_respuestas[-1]=respuesta
