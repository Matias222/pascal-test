from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import Lead
from ..serializers import LeadSerializer

@api_view(['GET'])
def get_all_leads(request):
    leads = Lead.objects.all()
    serializer = LeadSerializer(leads, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def create_lead(request):
    serializer = LeadSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def update_lead(request, pk):
    try:
        lead = Lead.objects.get(pk=pk)
    except Lead.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = LeadSerializer(lead, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def read_lead(request, pk):
    try:
        lead = Lead.objects.get(pk=pk)
    except Lead.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data="No existe lead")

    serializer = LeadSerializer(lead)
    return Response(serializer.data)

@api_view(['GET'])
def read_lead_by_phone(request, phone):
    try:
        lead = Lead.objects.get(phone=phone)
    except Lead.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data="No existe lead con ese teléfono")

    serializer = LeadSerializer(lead)
    return Response(serializer.data)

@api_view(['DELETE'])
def delete_lead(request, pk):
    try:
        lead = Lead.objects.get(pk=pk)
    except Lead.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data="No existe")

    lead.delete()
    return Response(status=status.HTTP_202_ACCEPTED, data="Eliminado correctamente")
