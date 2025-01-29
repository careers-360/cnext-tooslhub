from django.urls import path
from rank_predictor.api import controllers as rp_controller
from tools.api import controllers as tools_controller


urlpatterns = [
    path("", rp_controller.HealthCheck.as_view(), name='health_check'),
    # Tools App APIs
    path('tools', tools_controller.HealthCheck.as_view(), name='health_check'),
    path('api/<int:version>/cms/manage-tool/list', tools_controller.ManagePredictorToolAPI.as_view(), name='manage-tools-list'),
    path('api/<int:version>/cms/manage-tool/filter', tools_controller.CMSToolsFilterAPI.as_view(),name='manage-tools-filter'),
    path('api/<int:version>/cms/manage-tool/basic-detail', tools_controller.CMSToolsBasicDetailAPI.as_view(),name='manage-tools-basic-detail'),
    path('api/<int:version>/cms/manage-tool/tool-content', tools_controller.CMSToolContentAPI.as_view(),name='manage-tools-tool-content'),
    path('api/<int:version>/cms/manage-tool/input-page-detail', tools_controller.CMSToolsInputPageDetailAPI.as_view(),name='manage-tools-input-page-detail'),
    path('api/<int:version>/cms/manage-tool/faq', tools_controller.CMSToolsFaqAPI.as_view(),name='manage-tools-faq'),
    path('api/<int:version>/cms/manage-tool/manage-result-page', tools_controller.CMSToolsResultPageAPI.as_view(),name='manage-tools-resu'),
]