from django.urls import path
from rank_predictor.api import controllers


urlpatterns = [
    path("", controllers.HealthCheck.as_view(), name="health_check"),
]