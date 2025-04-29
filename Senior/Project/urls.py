from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_page, name='login'),     
    path('home/', views.home_page, name='home'),
    path('gpa_calculator/', views.gpa_calculator_page, name='gpa_calculator'),
    path('gpa_improvement/', views.gpa_improvement_page, name='gpa_improvement'),
    path('schedule_suggestions/', views.schedule_suggestions_page, name='schedule_suggestions'),
]
