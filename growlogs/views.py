from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import GrowLog, GrowLogEntry

def growlog_list(request):
    """Display list of grow logs."""
    growlogs = GrowLog.objects.filter(is_public=True).select_related('grower', 'strain')
    if request.user.is_authenticated:
        # Add user's private logs
        private_logs = GrowLog.objects.filter(grower=request.user, is_public=False)
        growlogs = growlogs | private_logs
    return render(request, "growlogs/list.html", {"growlogs": growlogs})

def growlog_detail(request, pk):
    """Display grow log details."""
    growlog = get_object_or_404(GrowLog, pk=pk)
    if not growlog.is_public and growlog.grower != request.user:
        messages.error(request, _("You don't have permission to view this grow log."))
        return redirect("growlogs:list")
    entries = growlog.entries.all().order_by('day')
    return render(request, "growlogs/detail.html", {
        "growlog": growlog,
        "entries": entries
    })

@login_required
def growlog_create(request):
    """Create new grow log."""
    # Placeholder for form handling
    return render(request, "growlogs/create.html")
