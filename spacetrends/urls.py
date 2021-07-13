from django.urls import include, path
from .views import IndexPageView

from .models import Launch, Vehicle

from rest_framework import routers, serializers, viewsets

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()

class VehicleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['name', 'notes', 'logged_launches']

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Launch.objects.all()
    serializer_class = VehicleSerializer

# Serializers define the API representation.
class LaunchSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Launch
        fields = ['launch_date', 'launch_id', 'vehicle', 'payload', 'mass']

# ViewSets define the view behavior.
class LaunchViewSet(viewsets.ModelViewSet):
    queryset = Launch.objects.all()
    serializer_class = LaunchSerializer

router.register(r'vehicles', VehicleViewSet)
router.register(r'launches', LaunchViewSet)

urlpatterns = [
    path('', IndexPageView.as_view(), name="index.html"),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]