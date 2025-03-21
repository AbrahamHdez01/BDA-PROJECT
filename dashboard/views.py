from django.shortcuts import render
from django.views.generic import TemplateView, DetailView, ListView
from django.db.models import Count, Avg, Sum, Q, F
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone

from .models import (
    Location, Demographics, Person, MedicalHistory,
    EnvironmentalFactor, Disease, HealthcareResource, HealthRecord
)

import pandas as pd
import numpy as np
import json
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta

class DashboardView(TemplateView):
    template_name = 'dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Basic statistics for the dashboard summary
        context['total_records'] = HealthRecord.objects.count()
        context['distinct_people'] = Person.objects.count()
        context['distinct_locations'] = Location.objects.count()
        
        # Get recent health records for the main dashboard table
        context['recent_records'] = HealthRecord.objects.select_related(
            'person', 'disease', 'environmental_factor'
        ).order_by('-date_of_data_collection')[:10]
        
        # Get disease severity distribution
        severity_counts = HealthRecord.objects.values(
            'disease_severity'
        ).annotate(count=Count('id')).order_by('disease_severity')
        context['severity_data'] = {
            'labels': [item['disease_severity'] for item in severity_counts],
            'data': [item['count'] for item in severity_counts]
        }
        
        # Get risk level distribution
        risk_counts = HealthRecord.objects.values(
            'infection_risk_level'
        ).annotate(count=Count('id')).order_by('infection_risk_level')
        context['risk_data'] = {
            'labels': [item['infection_risk_level'] for item in risk_counts],
            'data': [item['count'] for item in risk_counts]
        }
        
        # Get outbreak status distribution
        outbreak_counts = HealthRecord.objects.values(
            'outbreak_status'
        ).annotate(count=Count('id')).order_by('outbreak_status')
        context['outbreak_data'] = {
            'labels': [item['outbreak_status'] for item in outbreak_counts],
            'data': [item['count'] for item in outbreak_counts]
        }
        
        return context

class DiseasePredictionView(TemplateView):
    template_name = 'dashboard/prediction.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Example of a simple disease prediction model based on available data
        # In a real application, you'd have more sophisticated models
        
        # Fetch relevant data for prediction
        latest_records = HealthRecord.objects.select_related(
            'person', 'environmental_factor', 'healthcare_resource'
        ).order_by('-date_of_data_collection')[:1000]
        
        if latest_records:
            # Get time series for predictions
            dates = HealthRecord.objects.values('date_of_data_collection').annotate(
                count=Count('id')
            ).order_by('date_of_data_collection')
            
            # Convert to lists for plotting
            date_list = [item['date_of_data_collection'].strftime('%Y-%m-%d') for item in dates]
            count_list = [item['count'] for item in dates]
            
            # Store in context for visualization
            context['time_series'] = {
                'dates': date_list,
                'counts': count_list,
                'prediction_dates': self._get_future_dates(date_list, 30),
                'prediction_counts': self._predict_future_counts(date_list, count_list, 30)
            }
            
            # Get AQI vs Disease Severity correlation
            aqi_data = []
            severity_mapping = {'None': 0, 'Mild': 1, 'Moderate': 2, 'Severe': 3}
            
            for record in latest_records:
                if record.environmental_factor and record.disease_severity:
                    aqi_data.append({
                        'aqi': record.environmental_factor.air_quality_index,
                        'severity': severity_mapping.get(record.disease_severity, 0)
                    })
            
            if aqi_data:
                # Prepare data for scatter plot
                scatter_data = []
                for item in aqi_data:
                    scatter_data.append({"x": item["aqi"], "y": item["severity"]})
                
                context['aqi_severity'] = scatter_data
                
                # Linear regression for AQI prediction
                X = np.array([item['aqi'] for item in aqi_data]).reshape(-1, 1)
                y = np.array([item['severity'] for item in aqi_data])
                
                if len(X) > 1:  # Need at least 2 points for regression
                    model = LinearRegression()
                    model.fit(X, y)
                    
                    # Generate prediction line
                    aqi_range = list(range(min(X[:, 0].astype(int)), max(X[:, 0].astype(int)) + 10, 5))
                    aqi_pred = np.array(aqi_range).reshape(-1, 1)
                    severity_pred = model.predict(aqi_pred).tolist()
                    
                    context['aqi_prediction'] = {
                        'aqi_range': aqi_range,
                        'severity_pred': severity_pred
                    }
        
        # Sample locations for Risk Assessment table
        context['locations'] = [
            {
                'name': 'Downtown',
                'current_risk': 'High Risk',
                'predicted_risk': 'Medium Risk',
                'risk_change': -15
            },
            {
                'name': 'Westside',
                'current_risk': 'Medium Risk',
                'predicted_risk': 'Low Risk',
                'risk_change': -25
            },
            {
                'name': 'Northside',
                'current_risk': 'Low Risk',
                'predicted_risk': 'Medium Risk',
                'risk_change': 20
            }
        ]
        
        return context
    
    def _get_future_dates(self, date_strings, days_to_predict):
        """Generate future dates for prediction"""
        if not date_strings:
            return []
            
        last_date = datetime.strptime(date_strings[-1], '%Y-%m-%d')
        future_dates = [
            (last_date + timedelta(days=i+1)).strftime('%Y-%m-%d') 
            for i in range(days_to_predict)
        ]
        return future_dates
    
    def _predict_future_counts(self, date_strings, counts, days_to_predict):
        """Simple prediction model for future disease counts"""
        if not date_strings or len(date_strings) < 2:
            return [counts[-1]] * days_to_predict if counts else [0] * days_to_predict
            
        # Convert dates to numerical values for regression
        date_nums = list(range(len(date_strings)))
        
        # Build a simple model (Random Forest Regressor works well for time series)
        X = np.array(date_nums).reshape(-1, 1)
        y = np.array(counts)
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Predict future values
        future_X = np.array(range(len(date_strings), len(date_strings) + days_to_predict)).reshape(-1, 1)
        predictions = model.predict(future_X)
        
        # Ensure predictions are positive
        return [max(0, int(p)) for p in predictions]

class LocationAnalysisView(TemplateView):
    template_name = 'dashboard/location_analysis.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all locations
        locations = Location.objects.all()
        context['locations'] = locations
        
        # Prepare data structures for storing location statistics
        location_data = []
        location_names = []
        env_factors_by_location = {
            'aqi': [],
            'temperature': [],
            'humidity': []
        }
        resource_data_by_location = {
            'hospital_capacity': [],
            'personnel': [],
            'resource_util': []
        }
        
        # Generate sample location data for demo purposes
        # In a real app, this would be fetched from the database
        sample_location_data = [
            {"name": "Downtown", "type": "Urban", "records": 3245, "high_risk": 35, "env_quality": "Moderate"},
            {"name": "Westside", "type": "Suburban", "records": 2178, "high_risk": 18, "env_quality": "Good"},
            {"name": "Northside", "type": "Urban", "records": 4125, "high_risk": 42, "env_quality": "Poor"},
            {"name": "Eastside", "type": "Suburban", "records": 1872, "high_risk": 12, "env_quality": "Good"},
            {"name": "Southside", "type": "Rural", "records": 928, "high_risk": 8, "env_quality": "Good"}
        ]
        
        # Location coordinates for map (demonstration data)
        location_coords = []
        
        # Process location data
        for location_info in sample_location_data:
            name = location_info["name"]
            location_type = location_info["type"]
            record_count = location_info["records"]
            high_risk_percentage = location_info["high_risk"]
            env_quality = location_info["env_quality"]
            
            # Calculate other metrics for demonstration
            medium_risk_count = int(record_count * 0.25)
            low_risk_count = record_count - high_risk_percentage - medium_risk_count
            severe_cases = int(high_risk_percentage * 0.7)
            
            # Add location name for charts
            location_names.append(name)
            
            # Add environmental factors data (demo values)
            if env_quality == "Good":
                aqi = 60
            elif env_quality == "Moderate":
                aqi = 120
            else:
                aqi = 180
                
            env_factors_by_location['aqi'].append(aqi)
            env_factors_by_location['temperature'].append(25 + (5 * (location_type == "Urban")))
            env_factors_by_location['humidity'].append(50 + (10 * (location_type == "Rural")))
            
            # Add healthcare resource data (demo values)
            resource_data_by_location['hospital_capacity'].append(85 if location_type == "Urban" else (65 if location_type == "Suburban" else 40))
            resource_data_by_location['personnel'].append(90 if location_type == "Urban" else (70 if location_type == "Suburban" else 45))
            resource_data_by_location['resource_util'].append(75 if location_type == "Urban" else (60 if location_type == "Suburban" else 50))
            
            # Add map coordinates (demo values with random offsets)
            import random
            base_lat = 40.7 # Example: New York City area
            base_lon = -74.0
            
            # Assign risk level
            risk_level = "high" if high_risk_percentage > 30 else "medium" if high_risk_percentage > 15 else "low"
            
            location_coords.append({
                'name': name,
                'lat': base_lat + random.uniform(-0.1, 0.1),
                'lon': base_lon + random.uniform(-0.1, 0.1),
                'risk_level': risk_level,
                'case_count': record_count
            })
            
            # Add to location data for table display
            location_data.append({
                'name': name,
                'type': location_type,
                'record_count': record_count,
                'high_risk_percentage': high_risk_percentage,
                'severe_cases': severe_cases,
                'env_quality': env_quality,
                # Risk levels for context
                'high_risk': high_risk_percentage,
                'medium_risk': medium_risk_count,
                'low_risk': low_risk_count
            })
        
        # Add location data to context
        context['location_data'] = location_data
        
        # Add data for environmental factors chart
        context['environment_data'] = {
            'labels': location_names,
            'aqi': env_factors_by_location['aqi'],
            'temperature': env_factors_by_location['temperature'],
            'humidity': env_factors_by_location['humidity']
        }
        
        # Add data for healthcare resource chart
        context['resource_data'] = {
            'labels': location_names,
            'hospital_capacity': resource_data_by_location['hospital_capacity'],
            'personnel': resource_data_by_location['personnel'],
            'resource_util': resource_data_by_location['resource_util']
        }
        
        # Add map data
        context['map_data'] = json.dumps(location_coords)
        
        # Add risk summary for charts
        risk_summary = {}
        for loc in location_data:
            risk_summary[loc['name']] = {
                'High Risk': loc['high_risk'],
                'Medium Risk': loc['medium_risk'],
                'Low Risk': loc['low_risk']
            }
        
        context['risk_summary'] = risk_summary
        
        return context

class RiskComputationView(TemplateView):
    template_name = 'dashboard/risk_computation.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # This is a static page with information about risk calculation methodology
        # So we don't need to add any special context data here
        return context

def index(request):
    """Dashboard index view"""
    view = DashboardView.as_view()
    return view(request)

def disease_prediction(request):
    """Disease prediction view"""
    view = DiseasePredictionView.as_view()
    return view(request)

def location_analysis(request):
    """Location analysis view"""
    view = LocationAnalysisView.as_view()
    return view(request)

def risk_computation(request):
    """Risk computation methodology view"""
    view = RiskComputationView.as_view()
    return view(request)

def api_disease_trends(request):
    """API endpoint to get disease trends over time"""
    # Get date range from request parameters or use defaults
    try:
        # Parse start and end dates from request
        if 'start' in request.GET and 'end' in request.GET:
            start_date = datetime.fromisoformat(request.GET.get('start').split('T')[0])
            end_date = datetime.fromisoformat(request.GET.get('end').split('T')[0])
        else:
            # Default: last 30 days if not specified
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
    except (ValueError, TypeError) as e:
        # Handle invalid date format
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        print(f"Error parsing dates: {e}")
    
    # Query daily case counts
    daily_data = HealthRecord.objects.filter(
        date_of_data_collection__gte=start_date,
        date_of_data_collection__lte=end_date
    ).values('date_of_data_collection').annotate(
        count=Count('id')
    ).order_by('date_of_data_collection')
    
    # Format for Chart.js
    dates = [item['date_of_data_collection'].strftime('%Y-%m-%d') for item in daily_data]
    counts = [item['count'] for item in daily_data]
    
    # Also get severity breakdown by day
    severity_data = {}
    for severity in ['None', 'Mild', 'Moderate', 'Severe']:
        severity_counts = HealthRecord.objects.filter(
            date_of_data_collection__gte=start_date,
            date_of_data_collection__lte=end_date,
            disease_severity=severity
        ).values('date_of_data_collection').annotate(
            count=Count('id')
        ).order_by('date_of_data_collection')
        
        # Create a dict mapping date to count for this severity
        severity_dict = {
            item['date_of_data_collection'].strftime('%Y-%m-%d'): item['count'] 
            for item in severity_counts
        }
        
        # Ensure all dates have a value (0 if no data)
        severity_data[severity] = [severity_dict.get(date, 0) for date in dates]
    
    return JsonResponse({
        'dates': dates,
        'total_counts': counts,
        'severity_data': severity_data
    })

def api_environmental_impact(request):
    """API endpoint to analyze environmental factors impact on disease metrics"""
    # Fetch data joining environmental factors with health records
    records = HealthRecord.objects.select_related('environmental_factor').filter(
        environmental_factor__isnull=False
    )[:1000]  # Limit to 1000 records for performance
    
    # Extract data for analysis
    data = []
    for record in records:
        env = record.environmental_factor
        if env and env.air_quality_index and env.temperature and env.humidity:
            # Map severity to numerical value
            severity_mapping = {'None': 0, 'Mild': 1, 'Moderate': 2, 'Severe': 3}
            severity = severity_mapping.get(record.disease_severity, 0)
            
            data.append({
                'aqi': env.air_quality_index,
                'temperature': env.temperature,
                'humidity': env.humidity,
                'severity': severity,
                'date': record.date_of_data_collection.strftime('%Y-%m-%d')
            })
    
    return JsonResponse({
        'environmental_data': data
    })

def api_location_risk_data(request):
    """API endpoint to get risk data by location"""
    # Sample location data for demo
    sample_data = [
        {
            'id': 1,
            'name': 'Downtown',
            'type': 'Urban',
            'total_records': 3245,
            'risk_distribution': {
                'high': 35,
                'medium': 120,
                'low': 3090
            },
            'environmental_factors': {
                'aqi': 120,
                'temperature': 30,
                'humidity': 50
            }
        },
        {
            'id': 2,
            'name': 'Westside',
            'type': 'Suburban',
            'total_records': 2178,
            'risk_distribution': {
                'high': 18,
                'medium': 87,
                'low': 2073
            },
            'environmental_factors': {
                'aqi': 60,
                'temperature': 25,
                'humidity': 55
            }
        }
    ]
    
    return JsonResponse({
        'locations': sample_data
    })
