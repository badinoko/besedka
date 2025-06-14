from core.context_processors.navigation import navigation_context as _core_navigation_context

# Deprecated shim.  Any legacy imports of "users.context_processors.navigation_context"
# will now transparently call the unified context processor implemented in
# core.context_processors.navigation.  Remove this file once all templates and
# settings have been fully updated.

def navigation_context(request):
    """Proxy to unified navigation context (temporary compatibility layer)."""
    return _core_navigation_context(request)
