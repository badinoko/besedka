from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Photo, PhotoComment

def photo_list(request):
    """Display list of photos."""
    photos = Photo.objects.filter(is_public=True).select_related('author')
    return render(request, "gallery/list.html", {"photos": photos})

def photo_detail(request, pk):
    """Display photo details."""
    photo = get_object_or_404(Photo, pk=pk)
    if not photo.is_public and photo.author != request.user:
        messages.error(request, _("You don't have permission to view this photo."))
        return redirect("gallery:list")
    comments = photo.comments.all().select_related('author')
    return render(request, "gallery/detail.html", {
        "photo": photo,
        "comments": comments
    })

@login_required
def photo_upload(request):
    """Upload new photo."""
    # Placeholder for form handling
    return render(request, "gallery/upload.html")
