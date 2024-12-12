
from django.urls import path
from cnext_backend.apps.college_compare.api.controllers import compare_college_page_controllers,landing_page_controllers,popular_comparison_tabs_controllers as comparison_controllers


compare_prefix = 'api/1/college_compare/'


urlpatterns = [
    # College Compare Controllers

    path(f'{compare_prefix}college-dropdown/', compare_college_page_controllers.CollegeDropdownView.as_view(), name='college-dropdown'),
    path(f'{compare_prefix}degree-dropdown/', compare_college_page_controllers.DegreeDropdownView.as_view(), name='degree-dropdown'),
    path(f'{compare_prefix}course-dropdown/', compare_college_page_controllers.CourseDropdownView.as_view(), name='course-dropdown'),
    path(f'{compare_prefix}summary-comparison/', compare_college_page_controllers.SummaryComparisonView.as_view(), name='summary-comparison'),
    path(f'{compare_prefix}quick-facts/', compare_college_page_controllers.QuickFactsView.as_view(), name='quick-facts'),
    path(f'{compare_prefix}card-display/', compare_college_page_controllers.CardDisplayServiceView.as_view(), name='card-display'),
    path(f'{compare_prefix}college-compare-submit', compare_college_page_controllers.CollegeCompareController.as_view(), name='college-compare'),

    # Landing Page Controllers

    path('api/1/landing_page/peer-comparison/', landing_page_controllers.PeerComparisonCollegesView.as_view(), name='peer-comparison'),
    path('api/1/landing_page/top-colleges-courses/', landing_page_controllers.TopCollegesCoursesView.as_view(), name='top-colleges-courses'),
    
    path(f'{compare_prefix}blogs/degree-branch-comparison/',
         comparison_controllers.DegreeBranchComparisonView.as_view(),
         name='degree-branch-comparison'),
    
    path(f'{compare_prefix}blogs/degree-comparison/',
         comparison_controllers.DegreeComparisonView.as_view(),
         name='degree-comparison'),
    
    path(f'{compare_prefix}blogs/domain-comparison/',
         comparison_controllers.DomainComparisonView.as_view(),
         name='domain-comparison'),
    
    path(f'{compare_prefix}blogs/college-comparison/',
         comparison_controllers.CollegeComparisonView.as_view(),
         name='college-comparison'),
]