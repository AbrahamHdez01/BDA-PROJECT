import csv
import os
import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from dashboard.models import (
    Location, Demographics, Person, MedicalHistory, 
    EnvironmentalFactor, Disease, HealthcareResource, HealthRecord
)

class Command(BaseCommand):
    help = 'Import sample data from CSV file into the database'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting data import...'))
        
        # Clear existing data
        self.stdout.write('Clearing existing data...')
        Location.objects.all().delete()
        Demographics.objects.all().delete()
        Person.objects.all().delete()
        MedicalHistory.objects.all().delete()
        EnvironmentalFactor.objects.all().delete()
        Disease.objects.all().delete()
        HealthcareResource.objects.all().delete()
        HealthRecord.objects.all().delete()
        
        # Create locations
        self.stdout.write('Creating locations...')
        locations = {
            'Downtown': self.create_location('Downtown', 'Urban', 40.71, -74.01),
            'Westside': self.create_location('Westside', 'Suburban', 40.75, -74.05),
            'Eastside': self.create_location('Eastside', 'Suburban', 40.72, -73.96),
            'Northside': self.create_location('Northside', 'Urban', 40.78, -73.97),
            'Southside': self.create_location('Southside', 'Rural', 40.65, -74.02),
        }
        
        # Create diseases
        self.stdout.write('Creating diseases...')
        diseases = {
            'COVID-19': self.create_disease('COVID-19', 'Viral', 0.7, ['Fever', 'Cough', 'Fatigue']),
            'Influenza': self.create_disease('Influenza', 'Viral', 0.4, ['Fever', 'Cough', 'Body aches']),
            'E.Coli': self.create_disease('E.Coli', 'Bacterial', 0.3, ['Diarrhea', 'Abdominal pain']),
            'Malaria': self.create_disease('Malaria', 'Parasitic', 0.5, ['Fever', 'Chills', 'Headache']),
            'Tuberculosis': self.create_disease('Tuberculosis', 'Bacterial', 0.6, ['Cough', 'Chest pain', 'Weight loss']),
        }
        
        # Process CSV file if available
        csv_file_path = 'public_health_surveillance_dataset.csv'
        records_created = 0
        
        if os.path.exists(csv_file_path):
            self.stdout.write(f'Processing data from {csv_file_path}...')
            
            with open(csv_file_path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Use data from CSV to create records
                    try:
                        location_name = row.get('location', random.choice(list(locations.keys())))
                        location = locations.get(location_name) or random.choice(list(locations.values()))
                        
                        disease_name = row.get('disease', random.choice(list(diseases.keys())))
                        disease = diseases.get(disease_name) or random.choice(list(diseases.values()))
                        
                        # Create person
                        person = self.create_person(
                            row.get('age', random.randint(1, 90)),
                            row.get('gender', random.choice(['Male', 'Female', 'Other'])),
                            location
                        )
                        
                        # Create environmental factor
                        env_factor = self.create_environmental_factor(
                            location,
                            row.get('air_quality_index', random.randint(30, 200)),
                            row.get('temperature', random.uniform(15, 35)),
                            row.get('humidity', random.uniform(40, 80))
                        )
                        
                        # Create healthcare resource
                        resource = self.create_healthcare_resource(
                            location,
                            row.get('hospital_beds', random.randint(50, 500)),
                            row.get('doctors', random.randint(10, 100)),
                            row.get('ventilators', random.randint(5, 50))
                        )
                        
                        # Create health record
                        record = self.create_health_record(
                            person, 
                            disease,
                            env_factor,
                            resource,
                            row.get('disease_severity', random.choice(['None', 'Mild', 'Moderate', 'Severe'])),
                            row.get('infection_risk_level', random.choice(['Low', 'Medium', 'High'])),
                            row.get('outbreak_status', random.choice(['None', 'Potential', 'Confirmed']))
                        )
                        
                        records_created += 1
                        if records_created % 100 == 0:
                            self.stdout.write(f'Created {records_created} records so far...')
                    
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error processing row: {str(e)}'))
        else:
            self.stdout.write(f'CSV file not found at {csv_file_path}, generating random data...')
            # Generate some random data if CSV doesn't exist
            self.generate_random_data(locations, diseases, 500)
            records_created = 500
        
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {records_created} records'))
    
    def create_location(self, name, location_type, latitude, longitude):
        """Create and save a Location object"""
        location = Location(
            name=name,
            type=location_type,
            latitude=latitude,
            longitude=longitude,
            population=random.randint(5000, 200000)
        )
        location.save()
        return location
    
    def create_disease(self, name, disease_type, contagion_rate, symptoms):
        """Create and save a Disease object"""
        disease = Disease(
            name=name,
            type=disease_type,
            contagion_rate=contagion_rate,
            symptoms=','.join(symptoms),
            incubation_period=random.randint(2, 14)
        )
        disease.save()
        return disease
    
    def create_person(self, age, gender, location):
        """Create and save Person and Demographics objects"""
        # Create demographics
        demographics = Demographics(
            age=int(age) if isinstance(age, (int, float, str)) else random.randint(1, 90),
            gender=gender,
            occupation=random.choice(['Student', 'Teacher', 'Healthcare', 'Office', 'Service', 'Retired']),
            socioeconomic_status=random.choice(['Low', 'Medium', 'High'])
        )
        demographics.save()
        
        # Create person
        person = Person(
            demographics=demographics,
            location=location,
            vaccination_status=random.choice([True, False])
        )
        person.save()
        
        # Create medical history
        history = MedicalHistory(
            person=person,
            chronic_conditions=random.choice(['None', 'Diabetes', 'Hypertension', 'Asthma', 'Heart Disease']),
            allergies=random.choice(['None', 'Pollen', 'Medication', 'Food']),
            blood_type=random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'])
        )
        history.save()
        
        return person
    
    def create_environmental_factor(self, location, aqi, temperature, humidity):
        """Create and save an EnvironmentalFactor object"""
        env_factor = EnvironmentalFactor(
            location=location,
            date=timezone.now() - timedelta(days=random.randint(0, 30)),
            air_quality_index=int(aqi) if isinstance(aqi, (int, float, str)) else random.randint(30, 200),
            temperature=float(temperature) if isinstance(temperature, (int, float, str)) else random.uniform(15, 35),
            humidity=float(humidity) if isinstance(humidity, (int, float, str)) else random.uniform(40, 80),
            precipitation=random.uniform(0, 50),
            wind_speed=random.uniform(0, 30)
        )
        env_factor.save()
        return env_factor
    
    def create_healthcare_resource(self, location, beds, doctors, ventilators):
        """Create and save a HealthcareResource object"""
        resource = HealthcareResource(
            location=location,
            update_date=timezone.now() - timedelta(days=random.randint(0, 14)),
            hospital_beds=int(beds) if isinstance(beds, (int, float, str)) else random.randint(50, 500),
            available_doctors=int(doctors) if isinstance(doctors, (int, float, str)) else random.randint(10, 100),
            ventilators=int(ventilators) if isinstance(ventilators, (int, float, str)) else random.randint(5, 50),
            icu_capacity=random.randint(10, 100),
            occupancy_rate=random.uniform(0.3, 0.9)
        )
        resource.save()
        return resource
    
    def create_health_record(self, person, disease, env_factor, resource, severity, risk_level, outbreak):
        """Create and save a HealthRecord object"""
        record = HealthRecord(
            person=person,
            disease=disease,
            environmental_factor=env_factor,
            healthcare_resource=resource,
            date_of_data_collection=timezone.now() - timedelta(days=random.randint(0, 60)),
            disease_severity=severity,
            infection_risk_level=risk_level,
            outbreak_status=outbreak,
            recovery_time_days=random.randint(5, 30),
            hospitalization_required=random.choice([True, False]),
            close_contacts=random.randint(0, 20)
        )
        record.save()
        return record
    
    def generate_random_data(self, locations, diseases, num_records):
        """Generate random data records"""
        self.stdout.write(f'Generating {num_records} random records...')
        
        for i in range(num_records):
            # Select a random location and disease
            location = random.choice(list(locations.values()))
            disease = random.choice(list(diseases.values()))
            
            # Create person
            person = self.create_person(
                random.randint(1, 90),
                random.choice(['Male', 'Female', 'Other']),
                location
            )
            
            # Create environmental factor
            env_factor = self.create_environmental_factor(
                location,
                random.randint(30, 200),
                random.uniform(15, 35),
                random.uniform(40, 80)
            )
            
            # Create healthcare resource
            resource = self.create_healthcare_resource(
                location,
                random.randint(50, 500),
                random.randint(10, 100),
                random.randint(5, 50)
            )
            
            # Create health record
            record = self.create_health_record(
                person, 
                disease,
                env_factor,
                resource,
                random.choice(['None', 'Mild', 'Moderate', 'Severe']),
                random.choice(['Low', 'Medium', 'High']),
                random.choice(['None', 'Potential', 'Confirmed'])
            )
            
            if (i + 1) % 100 == 0:
                self.stdout.write(f'Generated {i + 1} records so far...')
