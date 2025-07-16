from django.contrib import admin
from django.urls import path,include
from . import views
from django.urls import path
from .views import display_csv
from django.views.generic import TemplateView

urlpatterns = [
    path('facebook/', views.facebook, name='facebook'),
    path('conversations/', views.conversations_view, name='conversations'),
    path('csv/', display_csv, name='download_report'),
    path('messages/', views.message_display, name='message-display'),
    path('summary-table/', views.sessions_table_view, name='summary_table'),
    path('get-execution-log-data/', views.get_execution_log_data, name='get_execution_log_data'),
    path('users/', views.users_view, name='users_view'),
    path('predict/', views.ethnicity_form_view, name='ethnicity-form'),
]
