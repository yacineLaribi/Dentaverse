from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("analysis/", views.analyze, name="analyze"),
    path("create/", views.create_analysis, name="create_analysis"),
    path("analysis/<int:analysis_id>/analyze/", views.analyze_xray, name="analyze_xray"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

