from django.db import models
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Event, Registration
from .permissions import IsEventOrganizer, IsOrganizerOrReadOnly
from .serializers import EventSerializer, RegistrationSerializer


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.select_related('organizer').annotate(
        confirmed_count=Count('registrations', filter=models.Q(registrations__status='confirmed'))
    ).all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsOrganizerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['date', 'location', 'organizer']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date', 'created_at', 'capacity']
    ordering = ['-date']

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsEventOrganizer()]
        return super().get_permissions()


class RegisterEventView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        event_id = self.kwargs['event_id']
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response(
                {'error': 'Event not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user

        if Registration.objects.filter(user=user, event=event).exists():
            return Response(
                {'error': 'You are already registered for this event.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if event.is_full:
            return Response(
                {'error': 'Event is at full capacity.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user, event=event)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserRegistrationsView(generics.ListAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['registered_at', 'status']
    ordering = ['-registered_at']

    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user).select_related('event')


class CancelRegistrationView(generics.DestroyAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'registration_id'

    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user, status='confirmed')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = 'cancelled'
        instance.save()
        return Response({'message': 'Registration cancelled successfully.'}, status=status.HTTP_200_OK)
