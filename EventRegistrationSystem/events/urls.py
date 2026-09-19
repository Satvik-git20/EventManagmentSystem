from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'events', views.EventViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('events/<int:event_id>/register/', views.RegisterEventView.as_view(), name='register-event'),
    path('me/registrations/', views.UserRegistrationsView.as_view(), name='user-registrations'),
    path('me/registrations/<int:registration_id>/cancel/', views.CancelRegistrationView.as_view(), name='cancel-registration'),
]