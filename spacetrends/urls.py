from django.urls import include, path
from rest_framework import routers

from .views import IndexPageView, LaunchViewSet, LaunchSummaryViewSet, VehicleViewSet, OrbitViewSet, SiteViewSet


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()

router.register(r'vehicles', VehicleViewSet)
router.register(r'launches', LaunchViewSet)
router.register(r'launch_summary', LaunchSummaryViewSet, basename='launch_summary')
router.register(r'sites', SiteViewSet)
router.register(r'orbits', OrbitViewSet)

urlpatterns = [
    path('', IndexPageView.as_view(), name="index.html"),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]