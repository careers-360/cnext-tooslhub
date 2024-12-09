from django.urls import path
from rank_predictor.api import controllers as rp_controller


urlpatterns = [
    path("rank-predictor", rp_controller.HealthCheck.as_view(), name='rank_predictor_health_check'),
    path("api/<int:version>/rank-predictor/content-section", rp_controller.ContentSectionAPI.as_view(), name='content_section'),
]