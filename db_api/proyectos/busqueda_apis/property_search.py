import json
import aioboto3
from adrf.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from proyectos.models import Property
from proyectos.serializers import PropertySerializer
from proyectos.busqueda_apis import helpers
from django.db.models import Q
from django.core.cache import cache
from asgiref.sync import sync_to_async
import os

@api_view(['POST'])
async def search_properties_by_similarity(request):
    """
    Search properties using cosine similarity (ASYNC)
    Body: {"query": "texto de búsqueda", "limit": 10}
    """
    query_text = request.data.get('query')
    limit = request.data.get('limit', 10)

    # Enforce maximum limit of 15
    limit = min(limit, 15)

    if not query_text:
        return Response(
            {"error": "El campo 'query' es requerido"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate embedding for the query (async)
    query_embedding = await helpers.generate_query_embedding_async(query_text)

    if not query_embedding:
        return Response(
            {"error": "Error al generar el embedding de búsqueda"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Perform cosine similarity search using pgvector (sync to async)
    @sync_to_async
    def get_similar_properties():
        properties = Property.objects.raw(
            '''
            SELECT *, 1 - (busqueda <=> %s::vector) as similarity
            FROM properties
            WHERE busqueda IS NOT NULL
            ORDER BY busqueda <=> %s::vector
            LIMIT %s
            ''',
            [query_embedding, query_embedding, limit]
        )

        # Serialize results and add similarity score
        results = []
        for prop in properties:
            serializer = PropertySerializer(prop)
            property_data = serializer.data
            property_data['similarity'] = prop.similarity
            results.append(property_data)

        return results

    results = await get_similar_properties()
    return Response(results)


@api_view(['GET'])
def filter_properties(request):
    """
    Filter properties by various criteria (SYNC - no AWS calls)
    Query params:
    - type: property type
    - min_price: minimum pricing
    - max_price: maximum pricing
    - view_type: type of view
    - project_id: filter by project
    - num_bedrooms: number of bedrooms (via typology)
    - num_bathrooms: number of bathrooms (via typology)
    - search: text search in title/description
    """
    properties = Property.objects.select_related('typology_id', 'project_id').all()

    # Filter by type
    prop_type = request.query_params.get('type')
    if prop_type:
        properties = properties.filter(type__icontains=prop_type)

    # Filter by price range
    min_price = request.query_params.get('min_price')
    if min_price:
        properties = properties.filter(pricing__gte=int(min_price))

    max_price = request.query_params.get('max_price')
    if max_price:
        properties = properties.filter(pricing__lte=int(max_price))

    # Filter by view type
    view_type = request.query_params.get('view_type')
    if view_type:
        properties = properties.filter(view_type__icontains=view_type)

    # Filter by project
    project_id = request.query_params.get('project_id')
    if project_id:
        properties = properties.filter(project_id=project_id)

    # Filter by number of bedrooms (via typology)
    num_bedrooms = request.query_params.get('num_bedrooms')
    if num_bedrooms:
        properties = properties.filter(typology_id__num_bedrooms=int(num_bedrooms))

    # Filter by number of bathrooms (via typology)
    num_bathrooms = request.query_params.get('num_bathrooms')
    if num_bathrooms:
        properties = properties.filter(typology_id__num_bathrooms=int(num_bathrooms))

    # Filter by area range (via typology)
    min_area = request.query_params.get('min_area')
    if min_area:
        properties = properties.filter(typology_id__area_m2__gte=min_area)

    max_area = request.query_params.get('max_area')
    if max_area:
        properties = properties.filter(typology_id__area_m2__lte=max_area)

    # Text search in title/description
    search = request.query_params.get('search')
    if search:
        properties = properties.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

    # Limit to maximum 15 results
    properties = properties[:15]

    serializer = PropertySerializer(properties, many=True)
    return Response(serializer.data)
