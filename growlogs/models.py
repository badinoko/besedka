from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import PublicModel, TimeStampedModel
from django.conf import settings
from magicbeans_store.models import Strain

class GrowLog(PublicModel):
    """
    Represents a grow diary/log.
    """
    title = models.CharField(_("Title"), max_length=255)
    grower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='growlogs')
    strain = models.ForeignKey(Strain, on_delete=models.SET_NULL, null=True, related_name='growlogs')
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"), null=True, blank=True)
    setup_description = models.TextField(_("Setup Description"))
    
    class Meta:
        verbose_name = _("Grow Log")
        verbose_name_plural = _("Grow Logs")
        ordering = ['-start_date']
        
    def __str__(self):
        return f"{self.title} by {self.grower.username}"

class GrowLogEntry(TimeStampedModel):
    """
    Represents a single entry in a grow log.
    """
    growlog = models.ForeignKey(GrowLog, on_delete=models.CASCADE, related_name='entries')
    day = models.PositiveIntegerField(_("Day"))
    description = models.TextField(_("Description"))
    temperature = models.DecimalField(_("Temperature"), max_digits=4, decimal_places=1, null=True, blank=True)
    humidity = models.DecimalField(_("Humidity %"), max_digits=4, decimal_places=1, null=True, blank=True)
    ph = models.DecimalField(_("pH"), max_digits=3, decimal_places=1, null=True, blank=True)
    
    class Meta:
        verbose_name = _("Grow Log Entry")
        verbose_name_plural = _("Grow Log Entries")
        ordering = ['day']
        unique_together = ['growlog', 'day']
        
    def __str__(self):
        return f"{self.growlog.title} - Day {self.day}"
