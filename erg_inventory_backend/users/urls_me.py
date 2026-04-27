from django.urls import path
from .views import MeView
urlpatterns = [path('', MeView.as_view(), name='me')]
