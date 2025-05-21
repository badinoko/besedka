import re
from django.conf import settings
from django.urls import resolve
from django.db.models import signals
from django.utils.deprecation import MiddlewareMixin
from .utils import log_view
from magicbeans_store.models import Strain, StockItem
from growlogs.models import GrowLog
from gallery.models import Photo

class ActionLogMiddleware:
    """
    Middleware to log user views of certain objects.
    This middleware logs views of detail pages for Strains, GrowLogs, and Photos.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Patterns for URLs that should log views
        self.patterns = [
            (r'^/store/strain/(?P<pk>\d+)/$', Strain),
            (r'^/growlogs/(?P<pk>\d+)/$', GrowLog),
            (r'^/gallery/(?P<pk>\d+)/$', Photo),
        ]
    
    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated and request.method == 'GET':
            self._log_view_if_matching(request)
            
        return response
    
    def _log_view_if_matching(self, request):
        """Check if the current URL matches any of our patterns and log if so."""
        path = request.path
        
        for pattern, model_class in self.patterns:
            match = re.match(pattern, path)
            if match:
                try:
                    pk = match.group('pk')
                    obj = model_class.objects.get(pk=pk)
                    log_view(request.user, obj)
                except (model_class.DoesNotExist, ValueError):
                    # Object not found or invalid ID, no logging
                    pass

class RequestUserMiddleware(MiddlewareMixin):
    """
    Middleware for making request.user available to model signal handlers.
    This allows our signal handlers to know which user is causing a model change.
    
    Based on django-crum but simplified for our needs.
    """
    
    thread_local = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import here to avoid circular import
        import threading
        self.__class__.thread_local = threading.local()
    
    def process_request(self, request):
        """Add the current request user to thread local storage."""
        # Skip for anonymous users
        if not request.user.is_authenticated:
            return
        
        self.__class__.thread_local.user = request.user
    
    def process_response(self, request, response):
        """Clear the thread local storage."""
        if hasattr(self.__class__.thread_local, 'user'):
            del self.__class__.thread_local.user
        return response
    
    @classmethod
    def get_current_user(cls):
        """Get the current user from thread local storage."""
        if not cls.thread_local or not hasattr(cls.thread_local, 'user'):
            return None
        return cls.thread_local.user


# This is the actual signal handler that sets the _change_user on model instances
# before they are saved or deleted. This connects to pre_save and pre_delete signals.

def connect_signals():
    """Connect pre_save and pre_delete signals to set _change_user on model instances."""
    signals.pre_save.connect(set_change_user)
    signals.pre_delete.connect(set_change_user)

def set_change_user(sender, instance, **kwargs):
    """
    Set the _change_user on a model instance before it is saved or deleted.
    This allows the instance to know which user is making the change.
    """
    # Skip if the instance already has a _change_user attribute or
    # if the sender is not a model class we care about
    if getattr(instance, '_change_user', None) is not None:
        return
    
    # Get the current user from thread local storage
    current_user = RequestUserMiddleware.get_current_user()
    if current_user:
        instance._change_user = current_user


# Connect the signals when the app is loaded
connect_signals() 