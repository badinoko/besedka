from django.contrib import admin
from .models import ActionLog

@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action_type', 'model_name', 'object_repr')
    search_fields = ('user__username', 'object_repr', 'details')
    list_filter = ('action_type', 'timestamp', 'model_name')
    date_hierarchy = 'timestamp'
    readonly_fields = (
        'user', 'action_type', 'timestamp', 'model_name',
        'object_id', 'object_repr', 'details',
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete logs
        return request.user.is_superuser
