from django.contrib import admin
from .models import (
    Location, Demographics, Person, MedicalHistory, 
    EnvironmentalFactor, Disease, HealthcareResource, HealthRecord
)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'population', 'latitude', 'longitude']
    list_filter = ['type']
    search_fields = ['name']

@admin.register(Demographics)
class DemographicsAdmin(admin.ModelAdmin):
    list_display = ['id', 'age', 'gender', 'occupation', 'socioeconomic_status']
    list_filter = ['gender', 'occupation', 'socioeconomic_status']
    search_fields = ['occupation']

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_age', 'get_gender', 'get_location', 'vaccination_status']
    list_filter = ['vaccination_status', 'location']
    search_fields = ['demographics__occupation']
    
    def get_age(self, obj):
        return obj.demographics.age
    get_age.short_description = 'Age'
    
    def get_gender(self, obj):
        return obj.demographics.gender
    get_gender.short_description = 'Gender'
    
    def get_location(self, obj):
        return obj.location.name
    get_location.short_description = 'Location'

@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'person', 'chronic_conditions', 'allergies', 'blood_type']
    list_filter = ['chronic_conditions', 'blood_type']
    search_fields = ['chronic_conditions', 'allergies']

@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'contagion_rate', 'incubation_period']
    list_filter = ['type']
    search_fields = ['name', 'symptoms']

@admin.register(EnvironmentalFactor)
class EnvironmentalFactorAdmin(admin.ModelAdmin):
    list_display = ['location', 'date', 'air_quality_index', 'temperature', 'humidity']
    list_filter = ['location']
    date_hierarchy = 'date'
    search_fields = ['location__name']

@admin.register(HealthcareResource)
class HealthcareResourceAdmin(admin.ModelAdmin):
    list_display = ['location', 'update_date', 'hospital_beds', 'available_doctors', 'occupancy_rate']
    list_filter = ['location']
    date_hierarchy = 'update_date'
    search_fields = ['location__name']

@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'person', 'disease', 'date_of_data_collection', 'disease_severity', 'infection_risk_level']
    list_filter = ['disease_severity', 'infection_risk_level', 'outbreak_status', 'hospitalization_required']
    date_hierarchy = 'date_of_data_collection'
    search_fields = ['person__demographics__occupation', 'disease__name']
