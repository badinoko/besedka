from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

def index(request):
    return render(request, "chat/index.html")

def room(request, room_name):
    return render(request, "chat/chat_room_fullscreen.html", {"room_name": room_name})





