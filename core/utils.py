from .models import ActionLog
from django.contrib.auth.models import AnonymousUser

def log_action(user, action_type, model_name, object_id=None, object_repr="", details=""):
    """
    Log a user action in the system.

    Args:
        user: The user who performed the action (can be AnonymousUser)
        action_type: One of ActionLog.ACTION_* constants
        model_name: Name of the model being acted upon
        object_id: ID of the object being acted upon (optional)
        object_repr: String representation of the object (optional)
        details: Additional details about the action (optional)

    Returns:
        The created ActionLog instance
    """
    user_to_log = user if user and user.is_authenticated else None

    return ActionLog.objects.create(
        user=user_to_log,
        action_type=action_type,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        details=details,
    )

def log_login(user):
    """Log a user login."""
    return log_action(
        user=user,
        action_type=ActionLog.ACTION_LOGIN,
        model_name="User",
        object_id=user.id,
        object_repr=str(user),
    )

def log_logout(user):
    """Log a user logout."""
    return log_action(
        user=user,
        action_type=ActionLog.ACTION_LOGOUT,
        model_name="User",
        object_id=user.id,
        object_repr=str(user),
    )

def log_add(user, obj, details=""):
    """Log the addition of an object."""
    return log_action(
        user=user,
        action_type=ActionLog.ACTION_ADD,
        model_name=obj.__class__.__name__,
        object_id=obj.pk,
        object_repr=str(obj),
        details=details,
    )

def log_edit(user, obj, details=""):
    """Log the editing of an object."""
    return log_action(
        user=user,
        action_type=ActionLog.ACTION_EDIT,
        model_name=obj.__class__.__name__,
        object_id=obj.pk,
        object_repr=str(obj),
        details=details,
    )

def log_delete(user, obj_class, obj_id, obj_repr, details=""):
    """Log the deletion of an object."""
    return log_action(
        user=user,
        action_type=ActionLog.ACTION_DELETE,
        model_name=obj_class.__name__,
        object_id=obj_id,
        object_repr=obj_repr,
        details=details,
    )

def log_view(user, obj, details=""):
    """Log the viewing of an object."""
    return log_action(
        user=user,
        action_type=ActionLog.ACTION_VIEW,
        model_name=obj.__class__.__name__,
        object_id=obj.pk,
        object_repr=str(obj),
        details=details,
    )
