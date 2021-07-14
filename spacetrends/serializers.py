from .models import Launch, Vehicle, Orbit, Site
from rest_framework import serializers

# Serializers define the API representation.
class LaunchSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Launch
        fields = '__all__'

class VehicleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class OrbitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Orbit
        fields = ['name', 'code', 'notes', 'launches_to_this_orbit']

class SiteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Site
        fields = ['name', 'code', 'notes', 'launches_from_this_location']