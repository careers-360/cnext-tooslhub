
from django.urls import path
from cnext_backend.apps.college_compare.api.controllers import compare_college_page_controllers,landing_page_controllers,popular_comparison_tabs_controllers as comparison_controllers,comparison_result_page_controllers


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
    
    path(f'{compare_prefix}blogs/all-comparisons/',
        comparison_controllers.AllComparisonsView.as_view(),
        name='all-comparisons'),
    
   
 
    path(f'{compare_prefix}resultPage/ranking-accreditation-comparison/',
    comparison_result_page_controllers.RankingAccreditationComparisonView.as_view(),
    name='ranking-accreditation-comparison'),


    path(f'{compare_prefix}resultPage/ranking-accreditation-ai-insights/',
    comparison_result_page_controllers.RankingAccreditationCombinedComparisonView.as_view(),
    name='ranking-accreditation-ai-insights'),

    path(f'{compare_prefix}resultPage/ranking-insights-graph/',
    comparison_result_page_controllers.RankingGraphInsightsView.as_view(),
    name='ranking-insights-graph'),

    

    path(f'{compare_prefix}resultPage/placement-stats-comparison/',
    comparison_result_page_controllers.PlacementStatsComparisonView.as_view(),
    name='placement-stats-comparison'),


    path(f'{compare_prefix}resultPage/placement-ai-insights/',
    comparison_result_page_controllers.PlacementStatsAIinsightsComparisonView.as_view(),
    name='placement-ai-insights'),


    path(f'{compare_prefix}resultPage/placement-graph-insights/',
    comparison_result_page_controllers.PlacementGraphInsightsView.as_view(),
    name='placement-graph-insights'),

    path(f'{compare_prefix}resultPage/course-fee-comparison/',
        comparison_result_page_controllers.CourseFeeComparisonView.as_view(),
        name='course-fee-comparison'),


        
    
    

    path(f'{compare_prefix}resultPage/fees-comparison/',
        comparison_result_page_controllers.FeesComparisonView.as_view(),
        name='fees-comparison'),

    path(f'{compare_prefix}resultPage/fees-ai-insights/',
        comparison_result_page_controllers.FeesAIinsightsComparisonView.as_view(),
        name='fees-ai-insights'),

    path(f'{compare_prefix}resultPage/fees-insights-graph/',
    comparison_result_page_controllers.FeesGraphInsightsView.as_view(),
    name='fees-insights-graph'),


    path(f'{compare_prefix}resultPage/class-profile-comparison/',
        comparison_result_page_controllers.ClassProfileComparisonView.as_view(),
        name='class-profile-comparison'),
    


    path(f'{compare_prefix}resultPage/class-profile-insights-graph/',
        comparison_result_page_controllers.ProfileInsightsView.as_view(),
        name='class-profile-insights-graph'),

    
    path(f'{compare_prefix}resultPage/class-profile-ai-insights/',
        comparison_result_page_controllers.classProfileAIInsightsView.as_view(),
        name='class-profile-ai-insights'),



    path(f'{compare_prefix}resultPage/college-facilities-comparison/',
        comparison_result_page_controllers.CollegeFacilitiesComparisonView.as_view(),
        name='college-facilities-comparison'),
    
    path(f'{compare_prefix}resultPage/college-amenities-comparison/',
        comparison_result_page_controllers.CollegeAmenitiesComparisonView.as_view(),
        name='college-amenities-comparison'),


    path(f'{compare_prefix}resultPage/college-reviews-comparison/',
        comparison_result_page_controllers.CollegeReviewsComparisonView.as_view(),
        name='college-reviews-comparison'),

    path(f'{compare_prefix}resultPage/college-reviews-ai-insights/',
        comparison_result_page_controllers.CollegeReviewsAIinsightsView.as_view(),
        name='college-reviews-ai-insights'),
    
    path(f'{compare_prefix}resultPage/college-recent-reviews/',
        comparison_result_page_controllers.SingleCollegeReviewsView.as_view(),
        name='college-recent-reviews'),

    
    path(f'{compare_prefix}resultPage/exam-cutoff-comparison/',
        comparison_result_page_controllers.ExamCutoffView.as_view(),
        name='exam-cutoff-comparison/'),

    path(f'{compare_prefix}resultPage/exam-cutoff-graph-comparison/',
        comparison_result_page_controllers.ExamCutGraphoffView.as_view(),
        name='exam-cutoff-graph-comparison/'),
    
    path(f'{compare_prefix}resultPage/college-review-rating-graph/',
        comparison_result_page_controllers.CollegeReviewRatingGraphView.as_view(),
        name='college-rating-graph'),

    path(f'{compare_prefix}resultPage/comparison-feedback',
        comparison_result_page_controllers.FeedbackSubmitView.as_view(),
        name='comparison-feedback'),

    path(f'{compare_prefix}resultPage/user-preference-options/',
    comparison_result_page_controllers.UserPreferenceOptionsView.as_view(),
    name='user-preference-options'),

    path(f'{compare_prefix}resultPage/user-preference-save/',
         comparison_result_page_controllers.UserPreferenceSaveView.as_view(),
         name='user-preference-save'),

]