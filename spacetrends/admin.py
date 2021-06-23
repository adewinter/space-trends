from django.contrib import admin
from spacetrends.models import Launch, Orbit


class LaunchAdmin(admin.ModelAdmin):
	date_hierarchy = 'launch_date'
	list_display = ('launch_date', 'vehicle', 'orbit', 'payload')

admin.site.register(Launch, LaunchAdmin)

class OrbitAdmin(admin.ModelAdmin):
	list_display = ('name', 'code')

admin.site.register(Orbit, OrbitAdmin)
