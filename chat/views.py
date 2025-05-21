from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ChatMessage

# Create your views here.

@login_required
def chat_room(request):
    """Display chat room."""
    messages = ChatMessage.objects.all().select_related('author').order_by('-created_at')[:50]
    return render(request, "chat/room.html", {"messages": messages})
