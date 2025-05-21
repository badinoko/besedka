from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import User

# Create your views here.

@login_required
def profile(request):
    """User profile view."""
    return render(request, "users/profile.html", {"user": request.user})

@require_POST
def telegram_login(request):
    """Handle Telegram login callback."""
    # This is a placeholder for Telegram login callback
    # The actual implementation will verify the data from Telegram
    telegram_data = request.POST
    
    try:
        # Find or create user based on Telegram ID
        user, created = User.objects.get_or_create(
            telegram_id=telegram_data.get("id"),
            defaults={
                "username": telegram_data.get("username", ""),
                "first_name": telegram_data.get("first_name", ""),
                "last_name": telegram_data.get("last_name", ""),
            }
        )
        
        if created:
            messages.success(request, _("Account created successfully!"))
        
        login(request, user)
        return redirect("home")
        
    except Exception as e:
        messages.error(request, _("Authentication failed. Please try again."))
        return redirect("home")
