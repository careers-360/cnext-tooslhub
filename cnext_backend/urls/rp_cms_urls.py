from django.urls import path
from rank_predictor.api import cms_controllers as cms_controller


urlpatterns = [
    path("api/<int:version>/cms/rp/flow-type", cms_controller.FlowTypeAPI.as_view(),  name='flow_type'),
    path("api/<int:version>/cms/rp/student-appeared", cms_controller.StudentAppearedAPI.as_view(),  name='student_appeared'),
]