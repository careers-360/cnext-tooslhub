from django.urls import path
from rank_predictor.api import controllers as rp_controller
from tools.api import controllers as tools_controller


urlpatterns = [
    path("", rp_controller.HealthCheck.as_view(), name="health_check"),

    # Tools App APIs
    path("tools", tools_controller.HealthCheck.as_view(), name="health_check"),
    # path("tools/filter", tools_controller.CMSToolsFilter.as_view(), name="cms_tools_filter"),

    
]