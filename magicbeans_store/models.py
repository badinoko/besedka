from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import TimeStampedModel
from django.conf import settings

class SeedBank(TimeStampedModel):
    """
    Represents a seed bank or breeder.
    """
    name = models.CharField(_("Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    website = models.URLField(_("Website"), blank=True)
    logo = models.ImageField(_("Logo"), upload_to='seedbanks/', null=True, blank=True)
    
    class Meta:
        verbose_name = _("Seed Bank")
        verbose_name_plural = _("Seed Banks")
        
    def __str__(self):
        return self.name

class Strain(TimeStampedModel):
    """
    Represents a cannabis strain.
    """
    name = models.CharField(_("Name"), max_length=255)
    breeder = models.ForeignKey(SeedBank, on_delete=models.CASCADE, related_name='strains')
    description = models.TextField(_("Description"))
    genetics = models.CharField(_("Genetics"), max_length=255)
    flowering_time = models.PositiveIntegerField(_("Flowering Time (weeks)"))
    thc_content = models.CharField(_("THC Content"), max_length=50, blank=True)
    cbd_content = models.CharField(_("CBD Content"), max_length=50, blank=True)
    effect = models.CharField(_("Effect"), max_length=255, blank=True)
    flavor = models.CharField(_("Flavor"), max_length=255, blank=True)
    
    class Meta:
        verbose_name = _("Strain")
        verbose_name_plural = _("Strains")
        
    def __str__(self):
        return f"{self.name} ({self.breeder.name})"

class StockItem(TimeStampedModel):
    """
    Represents a specific seed package in stock.
    """
    strain = models.ForeignKey(Strain, on_delete=models.CASCADE, related_name='stock_items')
    seeds_count = models.PositiveIntegerField(_("Seeds Count"))
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    in_stock = models.BooleanField(_("In Stock"), default=True)
    discount = models.DecimalField(_("Discount %"), max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = _("Stock Item")
        verbose_name_plural = _("Stock Items")
        
    def __str__(self):
        return f"{self.strain.name} ({self.seeds_count} seeds)"

    @property
    def final_price(self):
        if self.discount:
            return self.price * (1 - self.discount / 100)
        return self.price
