from django.db import models
from django.utils import timezone

class Location(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)  # Urban, Suburban, Rural
    latitude = models.FloatField()
    longitude = models.FloatField()
    population = models.IntegerField()
    
    def __str__(self):
        return self.name

class Demographics(models.Model):
    age = models.IntegerField()
    gender = models.CharField(max_length=20)
    occupation = models.CharField(max_length=50)
    socioeconomic_status = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.gender}, {self.age} - {self.occupation}"

class Person(models.Model):
    demographics = models.OneToOneField(Demographics, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    vaccination_status = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Person {self.id} - {self.demographics}"

class MedicalHistory(models.Model):
    person = models.OneToOneField(Person, on_delete=models.CASCADE)
    chronic_conditions = models.CharField(max_length=255)
    allergies = models.CharField(max_length=255)
    blood_type = models.CharField(max_length=5)
    
    def __str__(self):
        return f"Medical History for Person {self.person.id}"

class Disease(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)  # Viral, Bacterial, Fungal, Parasitic
    contagion_rate = models.FloatField()
    symptoms = models.TextField()
    incubation_period = models.IntegerField()  # days
    
    def __str__(self):
        return self.name

class EnvironmentalFactor(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    date = models.DateField()
    air_quality_index = models.IntegerField()
    temperature = models.FloatField()  # Celsius
    humidity = models.FloatField()  # Percentage
    precipitation = models.FloatField()  # mm
    wind_speed = models.FloatField()  # km/h
    
    def __str__(self):
        return f"Environmental data for {self.location.name} on {self.date}"

class HealthcareResource(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    update_date = models.DateField()
    hospital_beds = models.IntegerField()
    available_doctors = models.IntegerField()
    ventilators = models.IntegerField()
    icu_capacity = models.IntegerField()
    occupancy_rate = models.FloatField()  # Percentage
    
    def __str__(self):
        return f"Healthcare resources for {self.location.name} as of {self.update_date}"

class HealthRecord(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE)
    environmental_factor = models.ForeignKey(EnvironmentalFactor, on_delete=models.CASCADE, null=True, blank=True)
    healthcare_resource = models.ForeignKey(HealthcareResource, on_delete=models.CASCADE, null=True, blank=True)
    date_of_data_collection = models.DateTimeField(default=timezone.now)
    disease_severity = models.CharField(max_length=50)  # None, Mild, Moderate, Severe
    infection_risk_level = models.CharField(max_length=20)  # Low, Medium, High
    outbreak_status = models.CharField(max_length=20)  # None, Potential, Confirmed
    recovery_time_days = models.IntegerField(null=True, blank=True)
    hospitalization_required = models.BooleanField(default=False)
    close_contacts = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.disease.name} record for Person {self.person.id} on {self.date_of_data_collection.date()}"
