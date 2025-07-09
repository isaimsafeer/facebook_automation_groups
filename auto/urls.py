"""
URL configuration for auto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf.urls import handler404
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path
from fb.views import display_csv, sessions_table_view, get_execution_log_data
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.interface),
    path('login/',views.login1),
    path('remove/',views.remove1),
    path('fb/',include('fb.urls')), 
    path('csv/', display_csv, name='csv-display'),   
    path('summary-table/', sessions_table_view, name='summary_table'),
    path('api/execution-log-data/', get_execution_log_data, name='get_execution_log_data'),
]
if settings.DEBUG:
    # In development, serve static files using Django's static() helper
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # In production-like settings (when DEBUG=False), manually add static file handling
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {
            'document_root': settings.STATIC_ROOT,
        }),
    ]
handler404 = 'auto.views.custom_404_view'
