from django.urls import path
from rank_predictor.api import cms_controllers as cms_controller


urlpatterns = [
    path("api/<int:version>/cms/rp/flow-type", cms_controller.FlowTypeAPI.as_view(),  name='flow_type'),
    path("api/<int:version>/cms/rp/exam-session", cms_controller.ExamSessiondAPI.as_view(),  name='student_appeared'),
    path("api/<int:version>/cms/rp/appeared-student", cms_controller.RPAppearedStudentsAPI.as_view(), name='student_appeared'),

]