from django.shortcuts import render
from django.views.generic import TemplateView, DetailView, ListView
from django.db.models import Count, Avg, Sum, Q, F, CharField
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

        # Generate sample location data for demo purposes with global coverage
        # In a real app, this would be fetched from the database
        sample_location_data = [
            # North America
            {"name": "New York", "type": "Urban", "records": 3245, "high_risk": 35, "env_quality": "Moderate", "lat": 40.7128, "lon": -74.0060},
            {"name": "Los Angeles", "type": "Urban", "records": 2890, "high_risk": 28, "env_quality": "Poor", "lat": 34.0522, "lon": -118.2437},
            {"name": "Chicago", "type": "Urban", "records": 2178, "high_risk": 18, "env_quality": "Good", "lat": 41.8781, "lon": -87.6298},
            {"name": "Toronto", "type": "Urban", "records": 1872, "high_risk": 12, "env_quality": "Good", "lat": 43.6532, "lon": -79.3832},
            {"name": "Mexico City", "type": "Urban", "records": 4125, "high_risk": 42, "env_quality": "Poor", "lat": 19.4326, "lon": -99.1332},

            # Europe
            {"name": "London", "type": "Urban", "records": 2950, "high_risk": 22, "env_quality": "Moderate", "lat": 51.5074, "lon": -0.1278},
            {"name": "Paris", "type": "Urban", "records": 2780, "high_risk": 25, "env_quality": "Moderate", "lat": 48.8566, "lon": 2.3522},
            {"name": "Berlin", "type": "Urban", "records": 2150, "high_risk": 15, "env_quality": "Good", "lat": 52.5200, "lon": 13.4050},
            {"name": "Rome", "type": "Urban", "records": 1950, "high_risk": 20, "env_quality": "Moderate", "lat": 41.9028, "lon": 12.4964},
            {"name": "Madrid", "type": "Urban", "records": 1850, "high_risk": 18, "env_quality": "Moderate", "lat": 40.4168, "lon": -3.7038},

            # Asia
            {"name": "Tokyo", "type": "Urban", "records": 4500, "high_risk": 30, "env_quality": "Moderate", "lat": 35.6762, "lon": 139.6503},
            {"name": "Beijing", "type": "Urban", "records": 4200, "high_risk": 45, "env_quality": "Poor", "lat": 39.9042, "lon": 116.4074},
            {"name": "Mumbai", "type": "Urban", "records": 5100, "high_risk": 48, "env_quality": "Poor", "lat": 19.0760, "lon": 72.8777},
            {"name": "Seoul", "type": "Urban", "records": 3200, "high_risk": 25, "env_quality": "Moderate", "lat": 37.5665, "lon": 126.9780},
            {"name": "Singapore", "type": "Urban", "records": 1800, "high_risk": 10, "env_quality": "Good", "lat": 1.3521, "lon": 103.8198},

            # Africa
            {"name": "Cairo", "type": "Urban", "records": 3800, "high_risk": 40, "env_quality": "Poor", "lat": 30.0444, "lon": 31.2357},
            {"name": "Lagos", "type": "Urban", "records": 4100, "high_risk": 45, "env_quality": "Poor", "lat": 6.5244, "lon": 3.3792},
            {"name": "Johannesburg", "type": "Urban", "records": 2600, "high_risk": 30, "env_quality": "Moderate", "lat": -26.2041, "lon": 28.0473},
            {"name": "Nairobi", "type": "Urban", "records": 2200, "high_risk": 28, "env_quality": "Moderate", "lat": -1.2921, "lon": 36.8219},
            {"name": "Casablanca", "type": "Urban", "records": 1900, "high_risk": 22, "env_quality": "Moderate", "lat": 33.5731, "lon": -7.5898},

            # South America
            {"name": "São Paulo", "type": "Urban", "records": 4300, "high_risk": 38, "env_quality": "Poor", "lat": -23.5505, "lon": -46.6333},
            {"name": "Buenos Aires", "type": "Urban", "records": 3100, "high_risk": 25, "env_quality": "Moderate", "lat": -34.6037, "lon": -58.3816},
            {"name": "Lima", "type": "Urban", "records": 2800, "high_risk": 30, "env_quality": "Poor", "lat": -12.0464, "lon": -77.0428},
            {"name": "Bogotá", "type": "Urban", "records": 2500, "high_risk": 28, "env_quality": "Moderate", "lat": 4.7110, "lon": -74.0721},
            {"name": "Santiago", "type": "Urban", "records": 2200, "high_risk": 20, "env_quality": "Moderate", "lat": -33.4489, "lon": -70.6693},

            # Oceania
            {"name": "Sydney", "type": "Urban", "records": 1950, "high_risk": 15, "env_quality": "Good", "lat": -33.8688, "lon": 151.2093},
            {"name": "Melbourne", "type": "Urban", "records": 1800, "high_risk": 12, "env_quality": "Good", "lat": -37.8136, "lon": 144.9631},
            {"name": "Auckland", "type": "Urban", "records": 1200, "high_risk": 8, "env_quality": "Good", "lat": -36.8509, "lon": 174.7645},
            {"name": "Brisbane", "type": "Urban", "records": 1400, "high_risk": 10, "env_quality": "Good", "lat": -27.4698, "lon": 153.0251},
            {"name": "Perth", "type": "Urban", "records": 1100, "high_risk": 8, "env_quality": "Good", "lat": -31.9505, "lon": 115.8605}
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

            # Assign risk level
            risk_level = "high" if high_risk_percentage > 30 else "medium" if high_risk_percentage > 15 else "low"

            # Use the actual coordinates from the location data
            location_coords.append({
                'name': name,
                'lat': location_info.get('lat', 0),  # Use provided lat or default to 0
                'lon': location_info.get('lon', 0),  # Use provided lon or default to 0
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

class ConsolidatedDashboardView(TemplateView):
    template_name = 'dashboard/consolidated_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get data from DashboardView
        dashboard_view = DashboardView()
        dashboard_context = dashboard_view.get_context_data()
        context.update({
            'total_records': dashboard_context.get('total_records', 0),
            'distinct_people': dashboard_context.get('distinct_people', 0),
            'distinct_locations': dashboard_context.get('distinct_locations', 0),
            'recent_records': dashboard_context.get('recent_records', []),
            'severity_data': dashboard_context.get('severity_data', {'labels': [], 'data': []}),
            'risk_data': dashboard_context.get('risk_data', {'labels': [], 'data': []}),
            'outbreak_data': dashboard_context.get('outbreak_data', {'labels': [], 'data': []}),
        })

        # Get data from LocationAnalysisView
        location_view = LocationAnalysisView()
        location_context = location_view.get_context_data()
        context.update({
            'location_data': location_context.get('location_data', []),
            'map_data': location_context.get('map_data', '[]'),
            'environment_data': location_context.get('environment_data', {}),
            'resource_data': location_context.get('resource_data', {}),
            'risk_summary': location_context.get('risk_summary', {}),
        })

        # Get data from DiseasePredictionView
        prediction_view = DiseasePredictionView()
        prediction_context = prediction_view.get_context_data()
        context.update({
            'time_series': prediction_context.get('time_series', {}),
            'aqi_severity': prediction_context.get('aqi_severity', []),
            'aqi_prediction': prediction_context.get('aqi_prediction', {}),
            'locations': prediction_context.get('locations', []),
        })

        # Get data from PeopleQueriesView
        people_view = PeopleQueriesView()
        people_view.request = self.request
        people_context = people_view.get_context_data()
        context['people_queries'] = {
            'available_queries': people_context.get('available_queries', []),
            'query_results': people_context.get('query_results', None),
            'query_title': people_context.get('query_title', None),
            'is_chart': people_context.get('is_chart', False),
            'chart_labels': people_context.get('chart_labels', []),
            'chart_data': people_context.get('chart_data', []),
            'locations': people_context.get('locations', []),
            'error': people_context.get('error', None),
        }

        # Get data from DiseaseQueriesView
        disease_view = DiseaseQueriesView()
        disease_view.request = self.request
        disease_context = disease_view.get_context_data()
        context['disease_queries'] = {
            'available_queries': disease_context.get('available_queries', []),
            'query_results': disease_context.get('query_results', None),
            'query_title': disease_context.get('query_title', None),
            'is_chart': disease_context.get('is_chart', False),
            'chart_labels': disease_context.get('chart_labels', []),
            'chart_data': disease_context.get('chart_data', []),
            'diseases': disease_context.get('diseases', []),
            'error': disease_context.get('error', None),
        }

        # Get data from HealthRecordQueriesView
        health_record_view = HealthRecordQueriesView()
        health_record_view.request = self.request
        health_record_context = health_record_view.get_context_data()
        context['health_record_queries'] = {
            'available_queries': health_record_context.get('available_queries', []),
            'query_results': health_record_context.get('query_results', None),
            'query_title': health_record_context.get('query_title', None),
            'is_chart': health_record_context.get('is_chart', False),
            'chart_labels': health_record_context.get('chart_labels', []),
            'chart_data': health_record_context.get('chart_data', []),
            'error': health_record_context.get('error', None),
        }

        # Get data from DemographicQueriesView
        demographic_view = DemographicQueriesView()
        demographic_view.request = self.request
        demographic_context = demographic_view.get_context_data()
        context['demographic_queries'] = {
            'available_queries': demographic_context.get('available_queries', []),
            'query_results': demographic_context.get('query_results', None),
            'query_title': demographic_context.get('query_title', None),
            'is_chart': demographic_context.get('is_chart', False),
            'chart_labels': demographic_context.get('chart_labels', []),
            'chart_data': demographic_context.get('chart_data', []),
            'locations': demographic_context.get('locations', []),
            'error': demographic_context.get('error', None),
        }

        return context

def consolidated_dashboard(request):
    """Consolidated dashboard view for decision makers"""
    view = ConsolidatedDashboardView.as_view()
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

# Query Section Views
class PeopleQueriesView(TemplateView):
    template_name = 'dashboard/queries/people.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Define available queries for people
        context['available_queries'] = [
            {
                'id': 'people_by_location',
                'name': 'People by Location',
                'description': 'View people distribution across different locations'
            },
            {
                'id': 'people_by_demographics',
                'name': 'People by Demographics',
                'description': 'Filter people by age, gender, and socioeconomic status'
            },
            {
                'id': 'vaccination_status',
                'name': 'Vaccination Status',
                'description': 'View vaccination status distribution'
            }
        ]

        # Get all locations for filter dropdowns
        context['locations'] = Location.objects.all()

        # Always execute the people by location query
        # Group people by location
        location_counts = Person.objects.values('location__name').annotate(
            count=Count('id')
        ).order_by('-count')
        context['query_results'] = location_counts
        context['query_title'] = 'People Distribution by Location'
        context['is_chart'] = True
        context['chart_type'] = 'polarArea'  # Changed from default bar to polar area chart
        context['chart_labels'] = [item['location__name'] for item in location_counts]
        context['chart_data'] = [item['count'] for item in location_counts]

        # Handle query execution if requested (for backward compatibility)
        query_id = self.request.GET.get('query')
        if query_id:
            if query_id == 'people_by_location':
                # Already executed above
                pass
            elif query_id == 'people_by_demographics':
                # Execute people by demographics query
                age_min = self.request.GET.get('age_min')
                age_max = self.request.GET.get('age_max')
                gender = self.request.GET.get('gender')

                query = Person.objects.all()

                if age_min and age_max:
                    query = query.filter(demographics__age__gte=age_min, demographics__age__lte=age_max)

                if gender:
                    query = query.filter(demographics__gender=gender)

                context['query_results'] = query
                context['query_title'] = 'People Filtered by Demographics'
                context['is_chart'] = True
                context['chart_type'] = 'bar'  # Added bar chart (column chart)
                # Create age groups for the chart
                age_groups = {}
                for person in query:
                    if hasattr(person, 'demographics') and person.demographics and person.demographics.age:
                        age_group = 'Under 18' if person.demographics.age < 18 else \
                                   '18-29' if person.demographics.age < 30 else \
                                   '30-44' if person.demographics.age < 45 else \
                                   '45-59' if person.demographics.age < 60 else \
                                   '60-74' if person.demographics.age < 75 else '75+'
                        age_groups[age_group] = age_groups.get(age_group, 0) + 1

                context['chart_labels'] = list(age_groups.keys())
                context['chart_data'] = list(age_groups.values())

            elif query_id == 'vaccination_status':
                # Execute vaccination status query
                vaccination_counts = Person.objects.values('vaccination_status').annotate(
                    count=Count('id')
                )
                context['query_results'] = vaccination_counts
                context['query_title'] = 'Vaccination Status Distribution'
                context['is_chart'] = True
                context['chart_type'] = 'horizontalBar'  # Changed to horizontal bar chart
                context['chart_labels'] = ['Vaccinated', 'Not Vaccinated']
                context['chart_data'] = [
                    next((item['count'] for item in vaccination_counts if item['vaccination_status']), 0),
                    next((item['count'] for item in vaccination_counts if not item['vaccination_status']), 0)
                ]

        return context

class DiseaseQueriesView(TemplateView):
    template_name = 'dashboard/queries/diseases.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Define available queries for diseases
        context['available_queries'] = [
            {
                'id': 'disease_prevalence',
                'name': 'Disease Prevalence',
                'description': 'View the most common diseases'
            },
            {
                'id': 'disease_by_type',
                'name': 'Diseases by Type',
                'description': 'Group diseases by their type (Viral, Bacterial, etc.)'
            },
            {
                'id': 'disease_severity_analysis',
                'name': 'Disease Severity Analysis',
                'description': 'Analyze severity levels for different diseases'
            }
        ]

        # Get all diseases for filter dropdowns
        context['diseases'] = Disease.objects.all()

        # Always execute disease prevalence query
        disease_counts = HealthRecord.objects.values('disease__name').annotate(
            count=Count('id')
        ).order_by('-count')
        context['query_results'] = disease_counts
        context['query_title'] = 'Disease Prevalence'
        context['is_chart'] = True
        context['chart_type'] = 'radar'  # Changed from default bar to radar chart
        context['chart_labels'] = [item['disease__name'] for item in disease_counts[:10]]
        context['chart_data'] = [item['count'] for item in disease_counts[:10]]

        # Handle query execution if requested (for backward compatibility)
        query_id = self.request.GET.get('query')
        if query_id:
            if query_id == 'disease_prevalence':
                # Already executed above
                pass
            elif query_id == 'disease_by_type':
                # Execute diseases by type query
                type_counts = Disease.objects.values('type').annotate(
                    count=Count('id')
                ).order_by('-count')
                context['query_results'] = type_counts
                context['query_title'] = 'Diseases by Type'
                context['is_chart'] = True
                context['chart_type'] = 'line'  # Changed to line chart with fill (area chart)
                context['chart_labels'] = [item['type'] for item in type_counts]
                context['chart_data'] = [item['count'] for item in type_counts]

            elif query_id == 'disease_severity_analysis':
                # Execute disease severity analysis query
                disease_id = self.request.GET.get('disease')
                if disease_id:
                    try:
                        disease = Disease.objects.get(id=disease_id)
                        severity_counts = HealthRecord.objects.filter(disease=disease).values(
                            'disease_severity'
                        ).annotate(count=Count('id')).order_by('disease_severity')
                        context['query_results'] = severity_counts
                        context['query_title'] = f'Severity Analysis for {disease.name}'
                        context['is_chart'] = True
                        context['chart_type'] = 'bar'  # Changed to bar chart (column chart)
                        context['chart_labels'] = [item['disease_severity'] for item in severity_counts]
                        context['chart_data'] = [item['count'] for item in severity_counts]
                    except Disease.DoesNotExist:
                        context['error'] = 'Disease not found'
                else:
                    # Overall severity distribution
                    severity_counts = HealthRecord.objects.values('disease_severity').annotate(
                        count=Count('id')
                    ).order_by('disease_severity')
                    context['query_results'] = severity_counts
                    context['query_title'] = 'Overall Disease Severity Distribution'
                    context['is_chart'] = True
                    context['chart_type'] = 'horizontalBar'  # Changed to horizontal bar chart
                    context['chart_labels'] = [item['disease_severity'] for item in severity_counts]
                    context['chart_data'] = [item['count'] for item in severity_counts]

        return context

class HealthRecordQueriesView(TemplateView):
    template_name = 'dashboard/queries/health_records.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Define available queries for health records
        context['available_queries'] = [
            {
                'id': 'records_by_date',
                'name': 'Records by Date',
                'description': 'View health records distribution over time'
            },
            {
                'id': 'records_by_risk_level',
                'name': 'Records by Risk Level',
                'description': 'Analyze health records by infection risk level'
            },
            {
                'id': 'hospitalization_analysis',
                'name': 'Hospitalization Analysis',
                'description': 'Analyze hospitalization rates and patterns'
            }
        ]

        # Always execute records by risk level query
        risk_counts = HealthRecord.objects.values('infection_risk_level').annotate(
            count=Count('id')
        ).order_by('infection_risk_level')
        context['query_results'] = risk_counts
        context['query_title'] = 'Health Records by Risk Level'
        context['is_chart'] = True
        context['chart_type'] = 'doughnut'  # Changed from default bar to doughnut chart
        context['chart_labels'] = [item['infection_risk_level'] for item in risk_counts]
        context['chart_data'] = [item['count'] for item in risk_counts]

        # Handle query execution if requested (for backward compatibility)
        query_id = self.request.GET.get('query')
        if query_id:
            if query_id == 'records_by_date':
                # Execute records by date query
                date_counts = HealthRecord.objects.values('date_of_data_collection__date').annotate(
                    count=Count('id')
                ).order_by('date_of_data_collection__date')
                context['query_results'] = date_counts
                context['query_title'] = 'Health Records by Date'
                context['is_chart'] = True
                # Convert QuerySet to list before using negative indexing
                date_counts_list = list(date_counts)
                # Get the last 30 records or all if less than 30
                recent_records = date_counts_list[-30:] if len(date_counts_list) >= 30 else date_counts_list
                context['chart_type'] = 'line'  # Changed from default bar to line chart for time series data
                context['chart_labels'] = [item['date_of_data_collection__date'].strftime('%Y-%m-%d') for item in recent_records]
                context['chart_data'] = [item['count'] for item in recent_records]

            elif query_id == 'records_by_risk_level':
                # Already executed above
                pass

            elif query_id == 'hospitalization_analysis':
                # Execute hospitalization analysis query
                hospitalization_counts = HealthRecord.objects.values('hospitalization_required').annotate(
                    count=Count('id')
                )
                context['query_results'] = hospitalization_counts
                context['query_title'] = 'Hospitalization Analysis'
                context['is_chart'] = True
                context['chart_type'] = 'pie'  # Changed from default bar to pie chart
                context['chart_labels'] = ['Hospitalized', 'Not Hospitalized']
                context['chart_data'] = [
                    next((item['count'] for item in hospitalization_counts if item['hospitalization_required']), 0),
                    next((item['count'] for item in hospitalization_counts if not item['hospitalization_required']), 0)
                ]

        return context

class DemographicQueriesView(TemplateView):
    template_name = 'dashboard/queries/demographics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Define available queries for demographics
        context['available_queries'] = [
            {
                'id': 'age_distribution',
                'name': 'Age Distribution',
                'description': 'View population distribution by age groups'
            },
            {
                'id': 'gender_distribution',
                'name': 'Gender Distribution',
                'description': 'View population distribution by gender'
            },
            {
                'id': 'socioeconomic_analysis',
                'name': 'Socioeconomic Analysis',
                'description': 'Analyze population by socioeconomic status'
            }
        ]

        # Get all locations for filter dropdowns
        context['locations'] = Location.objects.all()

        # Default location settings
        location_filter = None
        location_name = "All Locations"

        # Always execute age distribution query
        # Create age groups
        from django.db.models import Case, When, IntegerField, Value

        # Start with base query
        query = Demographics.objects.all()

        # Annotate with age groups and count
        demographics = query.annotate(
            age_group=Case(
                When(age__lt=18, then=Value('Under 18')),
                When(age__lt=30, then=Value('18-29')),
                When(age__lt=45, then=Value('30-44')),
                When(age__lt=60, then=Value('45-59')),
                When(age__lt=75, then=Value('60-74')),
                default=Value('75+'),
                output_field=CharField(),
            )
        ).values('age_group').annotate(count=Count('id')).order_by('age_group')

        context['query_results'] = demographics
        context['query_title'] = f'Age Distribution - {location_name}'
        context['is_chart'] = True
        context['chart_type'] = 'doughnut'  # Changed from pie to doughnut chart
        context['chart_labels'] = [item['age_group'] for item in demographics]
        context['chart_data'] = [item['count'] for item in demographics]

        # Handle query execution if requested (for backward compatibility)
        query_id = self.request.GET.get('query')
        if query_id:
            # Check if location filter is applied
            location_id = self.request.GET.get('location')

            if location_id:
                try:
                    location = Location.objects.get(id=location_id)
                    location_filter = location
                    location_name = location.name
                except Location.DoesNotExist:
                    pass

            if query_id == 'age_distribution':
                # If location filter is applied, re-execute with filter
                if location_filter:
                    query = Demographics.objects.filter(person__location=location_filter)
                    demographics = query.annotate(
                        age_group=Case(
                            When(age__lt=18, then=Value('Under 18')),
                            When(age__lt=30, then=Value('18-29')),
                            When(age__lt=45, then=Value('30-44')),
                            When(age__lt=60, then=Value('45-59')),
                            When(age__lt=75, then=Value('60-74')),
                            default=Value('75+'),
                            output_field=CharField(),
                        )
                    ).values('age_group').annotate(count=Count('id')).order_by('age_group')

                    context['query_results'] = demographics
                    context['query_title'] = f'Age Distribution - {location_name}'
                    context['chart_labels'] = [item['age_group'] for item in demographics]
                    context['chart_data'] = [item['count'] for item in demographics]

            elif query_id == 'gender_distribution':
                # Execute gender distribution query
                query = Demographics.objects.all()

                # Apply location filter if specified
                if location_filter:
                    query = query.filter(person__location=location_filter)

                gender_counts = query.values('gender').annotate(
                    count=Count('id')
                ).order_by('-count')

                context['query_results'] = gender_counts
                context['query_title'] = f'Gender Distribution - {location_name}'
                context['is_chart'] = True
                context['chart_type'] = 'polarArea'  # Changed from pie to polarArea chart
                context['chart_labels'] = [item['gender'] for item in gender_counts]
                context['chart_data'] = [item['count'] for item in gender_counts]

            elif query_id == 'socioeconomic_analysis':
                # Execute socioeconomic analysis query
                query = Demographics.objects.all()

                # Apply location filter if specified
                if location_filter:
                    query = query.filter(person__location=location_filter)

                socioeconomic_counts = query.values('socioeconomic_status').annotate(
                    count=Count('id')
                ).order_by('-count')

                context['query_results'] = socioeconomic_counts
                context['query_title'] = f'Socioeconomic Status Distribution - {location_name}'
                context['is_chart'] = True
                context['chart_type'] = 'bar'  # Changed from pie to bar chart
                context['chart_labels'] = [item['socioeconomic_status'] for item in socioeconomic_counts]
                context['chart_data'] = [item['count'] for item in socioeconomic_counts]

        return context

# Function-based views for the query sections
def people_queries(request):
    """People queries view - redirects to consolidated dashboard with people section"""
    from django.shortcuts import redirect
    query = request.GET.get('query', '')
    if query:
        return redirect(f'/?query={query}&section=people')
    return redirect('/?section=people')

def disease_queries(request):
    """Disease queries view - redirects to consolidated dashboard with diseases section"""
    from django.shortcuts import redirect
    query = request.GET.get('query', '')
    if query:
        return redirect(f'/?query={query}&section=diseases')
    return redirect('/?section=diseases')

def health_record_queries(request):
    """Health record queries view - redirects to consolidated dashboard with health-records section"""
    from django.shortcuts import redirect
    query = request.GET.get('query', '')
    if query:
        return redirect(f'/?query={query}&section=health-records')
    return redirect('/?section=health-records')

def demographic_queries(request):
    """Demographic queries view - redirects to consolidated dashboard with demographics section"""
    from django.shortcuts import redirect
    query = request.GET.get('query', '')
    if query:
        return redirect(f'/?query={query}&section=demographics')
    return redirect('/?section=demographics')
