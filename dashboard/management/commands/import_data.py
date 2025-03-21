import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from django.db import transaction
from dashboard.models import (
    Location, Demographics, Person, MedicalHistory,
    EnvironmentalFactor, Disease, HealthcareResource, HealthRecord
)
from datetime import datetime

class Command(BaseCommand):
    help = 'Import health surveillance data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')
        parser.add_argument(
            '--batch-size', 
            type=int, 
            default=1000,
            help='Number of records to process in each batch'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        batch_size = options['batch_size']
        
        self.stdout.write(self.style.SUCCESS(f'Starting import from {csv_file}'))
        
        # Read the CSV file in chunks to handle large datasets
        for chunk_number, chunk in enumerate(pd.read_csv(csv_file, chunksize=batch_size)):
            self.stdout.write(f'Processing batch {chunk_number + 1}')
            self._process_chunk(chunk)
            
        self.stdout.write(self.style.SUCCESS('Data import completed successfully'))
    
    @transaction.atomic
    def _process_chunk(self, chunk):
        """Process a chunk of data within a transaction"""
        for _, row in chunk.iterrows():
            self._process_record(row)
    
    def _process_record(self, row):
        """Process a single CSV record"""
        # Create or get Location
        location, _ = Location.objects.get_or_create(
            name=row['Location'],
            defaults={
                'type': row.get('Location_Type', 'Unknown'),
                'latitude': float(row.get('Latitude', 0.0)),
                'longitude': float(row.get('Longitude', 0.0)),
                'population': int(row.get('Population', 0))
            }
        )
        
        # Create Demographics
        demographics = Demographics.objects.create(
            age=int(row.get('Age', 0)),
            gender=row.get('Gender', 'Unknown'),
            occupation=row.get('Occupation', 'Unknown'),
            socioeconomic_status=row.get('SES', 'Unknown')
        )
        
        # Create Person
        person = Person.objects.create(
            demographics=demographics,
            location=location,
            vaccination_status=row.get('Vaccination_Status') == 'Yes'
        )
        
        # Create MedicalHistory
        medical_history = MedicalHistory.objects.create(
            person=person,
            chronic_conditions=row.get('Chronic_Conditions', 'None'),
            allergies=row.get('Allergies', 'None'),
            blood_type=row.get('Blood_Type', 'Unknown')
        )
        
        # Parse dates
        collection_date = self._parse_date(row.get('Date_of_Data_Collection'))
        onset_date = self._parse_date(row.get('Date_of_Onset'))
        
        # Create EnvironmentalFactor
        env_factor = EnvironmentalFactor.objects.create(
            date=collection_date or datetime.now().date(),
            location=location,
            air_quality_index=int(row.get('AQI', 0)),
            temperature=float(row.get('Temperature', 0.0)),
            humidity=float(row.get('Humidity', 0.0)),
            precipitation=float(row.get('Precipitation', 0.0)),
            wind_speed=float(row.get('Wind_Speed', 0.0))
        )
        
        # Create Disease
        disease_name = row.get('Diagnosis', 'Unknown')
        disease = Disease.objects.create(
            name=disease_name,
            type=row.get('Disease_Type', 'Unknown'),
            contagion_rate=float(row.get('Transmission_Rate', 0.0)),
            symptoms=row.get('Reported_Symptoms', 'Unknown'),
            incubation_period=int(row.get('Incubation_Period', 0))
        )
        
        # Create HealthcareResource
        healthcare = HealthcareResource.objects.create(
            location=location,
            update_date=collection_date or datetime.now().date(),
            hospital_beds=int(row.get('Hospital_Capacity', 0)),
            available_doctors=int(row.get('Healthcare_Personnel_Availability', 0)),
            ventilators=int(row.get('Ventilators', 0)),
            icu_capacity=int(row.get('ICU_Capacity', 0)),
            occupancy_rate=float(row.get('Resource_Utilization', 0.0))
        )
        
        # Create HealthRecord
        HealthRecord.objects.create(
            person=person,
            disease=disease,
            environmental_factor=env_factor,
            healthcare_resource=healthcare,
            date_of_data_collection=collection_date or datetime.now(),
            disease_severity=row.get('Disease_Severity', 'None'),
            infection_risk_level=row.get('Infection_Risk_Level', 'Low'),
            outbreak_status=row.get('Outbreak_Status', 'None'),
            recovery_time_days=int(row.get('Recovery_Time', 0)),
            hospitalization_required=row.get('Hospitalization_Requirement') == 'Yes',
            close_contacts=int(row.get('Close_Contacts', 0))
        )
    
    def _parse_date(self, date_str):
        """Parse date string or return None if invalid"""
        if pd.isna(date_str) or not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None
