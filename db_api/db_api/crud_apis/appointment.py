from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import Appointment
from ..serializers import AppointmentSerializer

@api_view(['GET'])
def get_all_appointments(request):
    appointments = Appointment.objects.all()
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def create_appointment(request):
    serializer = AppointmentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def update_appointment(request, pk):
    try:
        appointment = Appointment.objects.get(pk=pk)
    except Appointment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = AppointmentSerializer(appointment, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def read_appointment(request, pk):
    try:
        appointment = Appointment.objects.get(pk=pk)
    except Appointment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data="No existe appointment")

    serializer = AppointmentSerializer(appointment)
    return Response(serializer.data)

@api_view(['DELETE'])
def delete_appointment(request, pk):
    try:
        appointment = Appointment.objects.get(pk=pk)
    except Appointment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data="No existe")

    appointment.delete()
    return Response(status=status.HTTP_202_ACCEPTED, data="Eliminado correctamente")

@api_view(['GET'])
def get_latest_appointment_by_lead(request, lead_id):
    """
    Get the most recent appointment for a lead (by scheduled_for)
    """
    try:
        conversation = Appointment.objects.filter(lead_id=lead_id).order_by('-scheduled_for').first()

        if not conversation:
            return Response(
                {"error": "No se encontraron appointments para este lead"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AppointmentSerializer(conversation)
        return Response(serializer.data)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
