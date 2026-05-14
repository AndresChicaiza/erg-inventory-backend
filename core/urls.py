from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, GlobalSearchView

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='audit-logs')

urlpatterns = [
    path('', include(router.urls)),
    path('search/', GlobalSearchView.as_view(), name='global-search'),
]
