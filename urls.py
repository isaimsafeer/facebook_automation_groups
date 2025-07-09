from django.urls import path
from . import views

urlpatterns = [
    path('summary-table/', views.summary_table, name='summary_table'),
    path('get-execution-log-data/', views.get_execution_log_data, name='get_execution_log_data'),
    path('csv/', views.download_report, name='download_report'),
] 