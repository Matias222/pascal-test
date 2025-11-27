from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import Property
from ..serializers import PropertySerializer

@api_view(['GET'])
def get_all_properties(request):
    properties = Property.objects.all()
    serializer = PropertySerializer(properties, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def create_property(request):
    serializer = PropertySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def update_property(request, pk):
    try:
        property_obj = Property.objects.get(pk=pk)
    except Property.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = PropertySerializer(property_obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def read_property(request, pk):
    try:
        property_obj = Property.objects.get(pk=pk)
    except Property.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data="No existe property")

    serializer = PropertySerializer(property_obj)
    return Response(serializer.data)

@api_view(['DELETE'])
def delete_property(request, pk):
    try:
        property_obj = Property.objects.get(pk=pk)
    except Property.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data="No existe")

    property_obj.delete()
    return Response(status=status.HTTP_202_ACCEPTED, data="Eliminado correctamente")

@api_view(['GET'])
def get_properties_by_project(request, project_id):
    """
    Get all properties that belong to a specific project
    """
    properties = Property.objects.filter(project_id=project_id)

    if not properties.exists():
        return Response(
            {"error": "No se encontraron propiedades para este proyecto"},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = PropertySerializer(properties, many=True)
    return Response(serializer.data)
