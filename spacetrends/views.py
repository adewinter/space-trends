from django.views.generic.base import TemplateView
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models.functions import TruncYear
from django.db.models import Count

from rest_framework import viewsets, permissions
from rest_framework.response import Response

from .serializers import LaunchSerializer, VehicleSerializer, OrbitSerializer, SiteSerializer
from .models import Launch, Vehicle, Orbit, Site

class IndexPageView(TemplateView):
    template_name = 'index.html'    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['launches'] = Launch.objects.all()[:5]
        return context


class VehicleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]



# ViewSets define the view behavior.
class LaunchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Launch.objects.all()
    serializer_class = LaunchSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # filterset_fields = [f.name for f in Launch._meta.get_fields(include_parents=False)]
    filterset_fields = {
        'mass': ['exact', 'lt', 'gte'],
        'launch_date': ['year', 'year__gte', 'year__lt']
    }

class LaunchSummaryViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def list(self, request, format=None):
        summary = Launch.objects.annotate(year=TruncYear('launch_date')) \
                        .values('year') \
                        .annotate(launch_count=Count('id')) \
                        .values('launch_count', 'year')

        return Response(summary)


class OrbitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Orbit.objects.all()
    serializer_class = OrbitSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class SiteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
