# README

Este readme es 100% hecho a mano (los individuales de cada repo tienen una gran parte de IA)

Hemos dividido el task en 2

db_api -> Repositorio en Django  
agente -> Repositorio en FastAPI para el sistema multi agente

De esta forma queda mas modular.

La arquitectura especifica de cada uno esta en sus respectivos readme

Los componentes se encuentran correctamente levantados en un APPRunner de AWS  
La base de datos en un RDS  
Y el proveedor de whatsapp es kap.so

## Cosas que se agregaron a la propuesta original:
- Lead tiene un atributo nuevo llamado estado_agentico
- Conversations tiene un atributo nuevo llamado funciones, donde se almacenan las tools utilizan por el agente actual (estos rags requieren contrastar informacion el modelo necesita saber que cosas ha llamado)
- No existe un prompt routeador lo considere innecesario, el agente onboarding es el que hace el small talk pero tambien esta en capacidad de interactuar

## Propuesta de interaccion:
Lo he diseñado de tal manera que el agente te deje hacer preguntas libremente sin pedir ninguna informacion antes. Solo te pide el nombre y correo al momento de agendar la cita.  
Siento que cuando fatigas mucho al usuario antes de que vea el valor lo quemas.

## Propuesta de cache:
- No se implemento Redis.
- No lo considere necesario. La BD una vez calienta jalando la informacion de lead (que si o si debemos jalar), las demas queries corren abajo de 200ms, no vi necesaria incorporar redis para el buffer de data.
- Se implemento cache de 24h en Django para las busquedas vectoriales

## Propuesta agentica:
- Son 3 agentes que tienen permitido navegar entre ellos, el mas "poderoso" es busqueda que cuenta con rags ademas de opciones de filtrado tradicional.
- Los detalles del RAG estan especificados en el readme de la bd

## Cosas que faltaron:
- Mejor manejo del contexto (Las tool generan mucha info esto requiere rag squared pero no me dio el tiempo)
- Mejor manejo multimodelo (tranquilamente haiku puede hacer de onboarding y de agendador pero Anthropic aun no incorpora structured outputs a su api, se pudo hacer con xml como siempre lo he trabajado pero por falta de tiempo se dejo asi)
- Handling de audio e imagenes
- Algunos RC raros que pueden llegar a ocurrir
- Mejor handling de queries complejas (no se puede depender del modelo en hacer los joins hay que hacerlo uno mismo)

## Probar:
- Prueben -> +1 (202) 998-5713