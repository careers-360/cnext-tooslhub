from django.urls import path
from rank_predictor.api import controllers as rp_controller
from tools.api import controllers as tools_controller

cms_prefix = 'api/<int:version>/cms/manage-tool'

urlpatterns = [
    path("", rp_controller.HealthCheck.as_view(), name='health_check'),
    # Tools App APIs
    path('tools', tools_controller.HealthCheck.as_view(), name='health_check'),
    path(cms_prefix + '/list', tools_controller.ManagePredictorToolAPI.as_view(), name='manage-tools-list'),
    path(cms_prefix + '/filter', tools_controller.CMSToolsFilterAPI.as_view(),name='manage-tools-filter'),
    path(cms_prefix + '/basic-detail', tools_controller.CMSToolsBasicDetailAPI.as_view(),name='manage-tools-basic-detail'),
    path(cms_prefix + '/tool-content', tools_controller.CMSToolContentAPI.as_view(),name='manage-tools-tool-content'),
    path(cms_prefix + '/input-page-detail', tools_controller.CMSToolsInputPageDetailAPI.as_view(),name='manage-tools-input-page-detail'),
    path(cms_prefix + '/faq', tools_controller.CMSToolsFaqAPI.as_view(),name='manage-tools-faq'),
    path(cms_prefix + '/manage-result-page', tools_controller.CMSToolsResultPageAPI.as_view(),name='manage-tools-resu'),
    # path(cms_prefix + '/manage-content', tools_controller.CMSToolsContentAPI.as_view(),name='manage-tools-filter'),
]