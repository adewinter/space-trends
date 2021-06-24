from django.contrib import admin
from spacetrends.models import Launch, Orbit, Site, Vehicle


class LaunchAdmin(admin.ModelAdmin):
	date_hierarchy = 'launch_date'
	list_display = ('launch_date', 'vehicle', 'orbit', 'payload')

admin.site.register(Launch, LaunchAdmin)


class OrbitAdmin(admin.ModelAdmin):
	list_display = ('name', 'code')

admin.site.register(Orbit, OrbitAdmin)

class SiteAdmin(admin.ModelAdmin):
	list_display = ('name', 'code', 'launches_from_this_location')

admin.site.register(Site, SiteAdmin)

class VehicleAdmin(admin.ModelAdmin):
	list_display = ('name', 'logged_launches')

admin.site.register(Vehicle, VehicleAdmin)