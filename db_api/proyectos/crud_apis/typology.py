from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import Typology
from ..serializers import TypologySerializer

@api_view(['GET'])
def get_all_typologies(request):
    typologies = Typology.objects.all()
    serializer = TypologySerializer(typologies, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def create_typology(request):
    serializer = TypologySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def update_typology(request, pk):
    try:
        typology = Typology.objects.get(pk=pk)
    except Typology.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = TypologySerializer(typology, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def read_typology(request, pk):
    try:
        typology = Typology.objects.get(pk=pk)
    except Typology.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data="No existe typology")

    serializer = TypologySerializer(typology)
    return Response(serializer.data)

@api_view(['DELETE'])
def delete_typology(request, pk):
    try:
        typology = Typology.objects.get(pk=pk)
    except Typology.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data="No existe")

    typology.delete()
    return Response(status=status.HTTP_202_ACCEPTED, data="Eliminado correctamente")
