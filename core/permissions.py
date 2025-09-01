# core/permissions.py
from rest_framework import permissions

class IsCartOwner(permissions.BasePermission):
    """Check if user owns the cart"""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsOrderOwner(permissions.BasePermission):
    """Check if user owns the order"""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class CanCancelOrder(permissions.BasePermission):
    """Check if order can be canceled (only pending orders)"""
    def has_object_permission(self, request, view, obj):
        return obj.status == 'pending' and obj.user == request.user