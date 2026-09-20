from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .agent import get_ai_response
from .models import ChatMessage
from .serializers import ChatMessageSerializer, ChatRequestSerializer

HISTORY_WINDOW = 10


class ChatView(APIView):
    def get(self, request):
        messages = ChatMessage.objects.filter(user=request.user).order_by('created_at')[:200]
        return Response({'success': True, 'results': ChatMessageSerializer(messages, many=True).data})

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data['message']

        history = list(
            ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:HISTORY_WINDOW]
        )[::-1]
        history_payload = [{'role': m.role, 'content': m.content} for m in history]

        user_message = ChatMessage.objects.create(user=request.user, role=ChatMessage.Role.USER, content=message)

        try:
            answer = get_ai_response(request.user, message, history=history_payload)
        except RuntimeError as exc:
            user_message.delete()
            return Response(
                {'success': False, 'message': str(exc), 'errors': {}}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception:
            user_message.delete()
            return Response(
                {
                    'success': False,
                    'message': 'The AI assistant is temporarily unavailable. Please try again shortly.',
                    'errors': {},
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        assistant_message = ChatMessage.objects.create(user=request.user, role=ChatMessage.Role.ASSISTANT, content=answer)

        return Response(
            {
                'success': True,
                'user_message': ChatMessageSerializer(user_message).data,
                'assistant_message': ChatMessageSerializer(assistant_message).data,
            },
            status=status.HTTP_201_CREATED,
        )
