from django.db import models

class Orbit(models.Model):
    name = models.CharField(max_length=255, blank=True)
    code = models.CharField(max_length=255)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class Site(models.Model):
    name = models.CharField(max_length=255, blank=True)
    code = models.CharField(max_length=255)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class SiteSummary(models.Model):
    '''
        Gives a launch site's stats for a given year
    '''
    year = models.IntegerField()
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    launch_attempts = models.IntegerField(default=0)
    launch_fails = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.site.name} Site Summary ({self.year})"


class Vehicle(models.Model):
    '''
        Launch Vehicle
    '''
    name = models.CharField(max_length=255)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name}"

class VehiclePerformance(models.Model):
    '''
        Gives vehicle performance/reliability stats from first ever attempt up to and including published or end year
    '''
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)

    inital_year = models.IntegerField()
    end_year = models.IntegerField(blank=True)
    published_year = models.IntegerField()

    launch_attempts = models.IntegerField()
    launch_successes = models.IntegerField(default=0)
    launch_consecutive_successes = models.IntegerField(default=0)

    last_failure = models.DateField(blank=True)

    reliability_estimate_lewis_point = models.FloatField(default=0.00)
    reliability_estimate_adjusted_wald_ci_start = models.FloatField(default=0.00)
    reliability_estimate_adjusted_wald_ci_end = models.FloatField(default=0.00)

    def __str__(self):
        return f"{self.vehicle.name} - Performance Statistics {self.initial_year} - {self.end_year} (published: {self.published_year})"


class VehicleFlightSummary(models.Model):
    '''
        Gives the vehicle flight summary over the course of a given year
    '''
    year = models.IntegerField()
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)

    launch_attempts = models.IntegerField(default=0)
    launch_fails = models.IntegerField(default=0)

    leo_attempts = models.IntegerField(default=0)
    leo_fails = models.IntegerField(default=0)

    beyond_leo_attempts = models.IntegerField(default=0)
    beyond_leo_fails = models.IntegerField(default=0)

    deep_space_attempts = models.IntegerField(default=0)
    deep_space_fails = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.vehicle.name} - Attempts / Fails: {self.launch_attempts} / {self.launch_fails}"


# DATE     VEHICLE           ID      PAYLOAD                 MASS(t) SITE*     ORBIT** NOTE 

# Create your models here.
class Launch(models.Model):
    launch_date = models.DateField()
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    launch_id = models.CharField(max_length=255)
    payload = models.CharField(max_length=255)
    mass = models.FloatField(default=0, help_text="Mass in tons")
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    site_pad_code = models.CharField(blank=True, help_text="Optional launch site pad code", max_length=255)
    orbit = models.ForeignKey(Orbit, on_delete=models.CASCADE)
    orbit_uncertain = models.BooleanField(default=False, help_text="True when it is unclear whether specified orbit data is accurate.")

    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Launch [{self.launch_date}] - {self.vehicle.name} - {self.orbit.code}"
