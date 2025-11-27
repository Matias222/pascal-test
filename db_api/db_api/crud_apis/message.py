from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import Message, Conversation
from ..serializers import MessageSerializer

@api_view(['GET'])
def get_all_messages(request):
    messages = Message.objects.all()
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_messages_by_lead(request, lead_id):
    """
    Get last k messages for a specific lead across all their conversations
    Query params: limit (default: 50)
    """
    limit = request.query_params.get('limit', 50)

    try:
        limit = int(limit)
    except ValueError:
        return Response(
            {"error": "El parámetro 'limit' debe ser un número entero"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get all conversations for this lead
    conversations = Conversation.objects.filter(lead_id=lead_id)

    if not conversations.exists():
        return Response(
            {"error": "No se encontraron mensajes para este lead"},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get messages from all conversations for this lead, ordered by created_at desc
    messages = Message.objects.filter(
        conversation_id__in=conversations
    ).order_by('-created_at')[:limit]

    serializer = MessageSerializer(messages, many=True)

    return Response({
        "lead_id": lead_id,
        "total_messages": len(messages),
        "limit": limit,
        "messages": serializer.data
    })

@api_view(['POST'])
def create_message(request):
    serializer = MessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def update_message(request, pk):
    try:
        message = Message.objects.get(pk=pk)
    except Message.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = MessageSerializer(message, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def read_message(request, pk):
    try:
        message = Message.objects.get(pk=pk)
    except Message.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data="No existe message")

    serializer = MessageSerializer(message)
    return Response(serializer.data)

@api_view(['DELETE'])
def delete_message(request, pk):
    try:
        message = Message.objects.get(pk=pk)
    except Message.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data="No existe")

    message.delete()
    return Response(status=status.HTTP_202_ACCEPTED, data="Eliminado correctamente")
