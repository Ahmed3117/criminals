


app_name='about'
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('process_image/', views.process_image, name='process_image'),
]
