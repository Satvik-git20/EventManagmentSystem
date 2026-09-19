from rest_framework import permissions


class IsOrganizer(permissions.BasePermission):
    """
    Custom permission to only allow organizers to create/edit events.
    """
    message = 'Only organizers can perform this action.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'userprofile') and request.user.userprofile.is_organizer


class IsEventOrganizer(permissions.BasePermission):
    """
    Custom permission to only allow the event organizer to edit/delete their event.
    """
    message = 'Only the event organizer can perform this action.'

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        return obj.organizer == request.user


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow organizers to create events, but anyone to read.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'userprofile') and
            request.user.userprofile.is_organizer
        )