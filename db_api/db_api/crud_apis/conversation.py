from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import Conversation
from ..serializers import ConversationSerializer

@api_view(['GET'])
def get_all_conversations(request):
    conversations = Conversation.objects.all()
    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def create_conversation(request):
    serializer = ConversationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def update_conversation(request, pk):
    try:
        conversation = Conversation.objects.get(pk=pk)
    except Conversation.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = ConversationSerializer(conversation, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def read_conversation(request, pk):
    try:
        conversation = Conversation.objects.get(pk=pk)
    except Conversation.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data="No existe conversation")

    serializer = ConversationSerializer(conversation)
    return Response(serializer.data)

@api_view(['DELETE'])
def delete_conversation(request, pk):
    try:
        conversation = Conversation.objects.get(pk=pk)
    except Conversation.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data="No existe")

    conversation.delete()
    return Response(status=status.HTTP_202_ACCEPTED, data="Eliminado correctamente")

@api_view(['GET'])
def get_latest_conversation_by_lead(request, lead_id):
    """
    Get the most recent conversation for a lead (by last_message_at)
    """
    try:
        conversation = Conversation.objects.filter(lead_id=lead_id).order_by('-last_message_at').first()

        if not conversation:
            return Response(
                {"error": "No se encontraron conversaciones para este lead"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
