from django.db import models

class Orbit(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    notes = models.TextField()

class Site(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    notes = models.TextField()


class Vehicle(models.Model):
    '''
    Vehicle            Overall           By Orbit Type
                   Launches      Earth-Orbit Earth-Escape
                  (Failures)      LEO   >LEO  Deep Space
    '''
    name = models.CharField(max_length=255)

    notes = models.TextField()

class VehiclePerformanceData(models.Model):
    '''
        Gives vehicle performance/reliability stats from first ever attempt up to and including published or end year
                                   Lewis 
                Successes  Point AdjWald   Consc. Last    Dates 
Vehicle         /Attempts  Est*  95%CI*    Succes Fail 
    '''
    inital_year = models.IntegerField()
    end_year = models.IntegerField()
    published_year = models.IntegerField()

    launch_attempts = models.IntegerField()
    launch_successes = models.IntegerField()
    launch_consecutive_successes = models.IntegerField()

    last_failure = models.DateField()
    

    reliability_estimate_lewis_point = 


class VehicleFlightSummary(models.Model):
    '''
        Gives the vehicle flight summary over the course of a given year
    '''
    year = models.IntegerField()
    vehicle = models.ForeignKey(Vehicle)

    launch_attempts = models.IntegerField()
    launch_fails = models.IntegerField()

    leo_attempts = models.IntegerField()
    leo_fails = models.IntegerField()

    beyond_leo_attempts = models.IntegerField()
    beyond_leo_fails = models.IntegerField()

    deep_space_attempts = models.IntegerField()
    deep_space_fails = models.IntegerField()


# DATE     VEHICLE           ID      PAYLOAD                 MASS(t) SITE*     ORBIT** NOTE 

# Create your models here.
class Launch(models.Model):
    launch_date = models.DateField()
    vehicle = 
    name = models.CharField(max_length=255)
    primary_language = models.CharField(max_length=255)
    notes = models.TextField()

class Cheers(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    raw = models.CharField(max_length=255)
    pronunciation = models.CharField(max_length=255)

