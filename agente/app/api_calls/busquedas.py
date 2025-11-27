import os, json

from app.models import api_models
from app.auxiliares import print_info_api_call, retry_on_failure
from dotenv import load_dotenv
from httpx import AsyncClient, Response, Timeout
from fastapi import HTTPException

load_dotenv()

timeout = Timeout(20.0)

API_DB = os.getenv('API_DB')
SETUP = os.getenv('SETUP')


@retry_on_failure()
async def buscar_proyectos_semantica(query: str, limit: int = 3):
    """
    Búsqueda semántica de proyectos usando embeddings
    """
    async with AsyncClient(timeout=timeout) as client:
        payload = {
            "query": query,
            "limit": limit
        }
        response = await client.post(f"{API_DB}/proyectos/search/projects", json=payload)
        print_info_api_call(response)
        return response.json(), response.status_code


@retry_on_failure()
async def buscar_propiedades_semantica(query: str, limit: int = 3):
    """
    Búsqueda semántica de propiedades usando embeddings
    """
    async with AsyncClient(timeout=timeout) as client:
        payload = {
            "query": query,
            "limit": limit
        }
        response = await client.post(f"{API_DB}/proyectos/search/properties", json=payload)
        print_info_api_call(response)
        return response.json(), response.status_code


@retry_on_failure()
async def filtrar_propiedades(filters: dict):
    """
    Filtra propiedades por criterios específicos
    filters: {min_price, max_price, num_bedrooms, num_bathrooms, type, etc}
    """
    async with AsyncClient(timeout=timeout) as client:
        # Build query params from filters
        params = "&".join([f"{k}={v}" for k, v in filters.items() if v is not None])
        response = await client.get(f"{API_DB}/proyectos/filter/properties?{params}")
        print_info_api_call(response)
        return response.json(), response.status_code


@retry_on_failure()
async def filtrar_proyectos(filters: dict):
    """
    Filtra proyectos por criterios específicos
    filters: {district, has_showroom, includes_parking, search, etc}
    """
    async with AsyncClient(timeout=timeout) as client:
        params = "&".join([f"{k}={v}" for k, v in filters.items() if v is not None])
        response = await client.get(f"{API_DB}/proyectos/filter/projects?{params}")
        print_info_api_call(response)
        return response.json(), response.status_code


@retry_on_failure()
async def obtener_propiedades_por_proyecto(project_id: str):
    """
    Obtiene todas las propiedades de un proyecto específico.

    Args:
        project_id: UUID del proyecto

    Returns:
        tuple: (lista_propiedades, status_code)
    """
    async with AsyncClient(timeout=timeout) as client:
        response = await client.get(f"{API_DB}/proyectos/properties/project/{project_id}")
        print_info_api_call(response)
        return response.json(), response.status_code