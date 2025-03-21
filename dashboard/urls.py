from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('prediction/', views.disease_prediction, name='prediction'),
    path('location-analysis/', views.location_analysis, name='location_analysis'),
    path('risk-computation/', views.risk_computation, name='risk_computation'),
    path('api/disease-trends/', views.api_disease_trends, name='api_disease_trends'),
    path('api/location-risk/', views.api_location_risk_data, name='api_location_risk'),
]
