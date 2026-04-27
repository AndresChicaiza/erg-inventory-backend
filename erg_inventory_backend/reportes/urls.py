from django.urls import path
from .views import ResumenView

urlpatterns = [
    path('resumen/', ResumenView.as_view(), name='reportes-resumen'),
]
