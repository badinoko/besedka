from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Strain, StockItem

def catalog(request):
    """Display the store catalog."""
    strains = Strain.objects.all().select_related('breeder')
    return render(request, "store/catalog.html", {"strains": strains})

def strain_detail(request, pk):
    """Display strain details."""
    strain = get_object_or_404(Strain, pk=pk)
    stock_items = strain.stock_items.filter(in_stock=True)
    return render(request, "store/strain_detail.html", {
        "strain": strain,
        "stock_items": stock_items
    })
