from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('prediction/', views.disease_prediction, name='prediction'),
    path('location-analysis/', views.location_analysis, name='location_analysis'),
    path('risk-computation/', views.risk_computation, name='risk_computation'),

    # Query section URLs
    path('queries/people/', views.people_queries, name='people_queries'),
    path('queries/diseases/', views.disease_queries, name='disease_queries'),
    path('queries/health-records/', views.health_record_queries, name='health_record_queries'),
    path('queries/demographics/', views.demographic_queries, name='demographic_queries'),

    # API endpoints
    path('api/disease-trends/', views.api_disease_trends, name='api_disease_trends'),
    path('api/location-risk/', views.api_location_risk_data, name='api_location_risk'),
]
