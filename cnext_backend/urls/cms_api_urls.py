from django.urls import path
from rank_predictor.api import controllers as rp_controller
from tools.api import controllers as tools_controller

cms_prefix = 'api/<int:version>/cms'

urlpatterns = [
    path("", rp_controller.HealthCheck.as_view(), name='health_check'),

    # Tools App APIs
    path('tools', tools_controller.HealthCheck.as_view(), name='health_check'),
    path(cms_prefix + '/manage-predictor-tool', tools_controller.ManagePredictorToolAPI.as_view(), name='predictor-tools-list'),
    path(cms_prefix + '/tools/filter', tools_controller.CMSToolsFilterAPI.as_view(),name='tools-filter'),


]