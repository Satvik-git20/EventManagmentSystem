from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Event, Registration
from .serializers import EventSerializer, RegistrationSerializer


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class RegisterEventView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer

    def perform_create(self, serializer):
        event_id = self.kwargs['event_id']
        event = Event.objects.get(id=event_id)
        user = self.request.user
        if Registration.objects.filter(user=user, event=event).exists():
            return Response(
                {'error': 'You are already registered for this event.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Registration.objects.filter(event=event).count() >= event.capacity:
            return Response(
                {'error': 'Event is at full capacity.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save(user=user, event=event)


class UserRegistrationsView(generics.ListAPIView):
    serializer_class = RegistrationSerializer

    def get_queryset(self):
        user = self.request.user
        return Registration.objects.filter(user=user)


class CancelRegistrationView(generics.DestroyAPIView):
    serializer_class = RegistrationSerializer

    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user)