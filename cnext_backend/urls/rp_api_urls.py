from django.urls import path
from rank_predictor.api import controllers as rp_controller



urlpatterns = [
    path("rank-predictor", rp_controller.HealthCheck.as_view(), name='rank_predictor_health_check'),
    path("api/<int:version>/rank-predictor/content-section", rp_controller.ContentSectionAPI.as_view(), name='content_section'),
    path("api/<int:version>/rank-predictor/faq-section", rp_controller.FAQSectionAPI.as_view(), name='faq_section'),
    path("api/<int:version>/rank-predictor/feedback-section", rp_controller.ReviewSectionAPI.as_view(), name='feedback_section'),
    path("api/<int:version>/rank-predictor/top-college", rp_controller.TopCollegesSectionAPI.as_view(), name='top_college'),
    path("api/<int:version>/rank-predictor/landing-data", rp_controller.LandingDataAPI.as_view(), name='landing page data'),
    path("api/<int:version>/rank-predictor/form-section", rp_controller.FormSectionAPI.as_view(), name='form_section'),
    path("api/<int:version>/rank-predictor/top-colleges", rp_controller.TopCollegesAPI.as_view(), name='top_colleges_api'),
    path("api/<int:version>/rank-predictor/related-products", rp_controller.RelatedProductsAPI.as_view(), name='related_products'),
    path("api/<int:version>/rank-predictor/form-submit", rp_controller.UserTrackingAPI.as_view(), name='user_tracking'),
    path("api/<int:version>/rank-predictor", rp_controller.ProductFromAliasAPI.as_view(), name='product_id from alias'),
    path("api/<int:version>/rank-predictor/rank-predictor", rp_controller.RankPredictorAPI.as_view(), name="rank_predictor"),
    path(
        "api/<int:version>/rank-predictor/faqs", 
        rp_controller.FaqSectionAPI.as_view(), 
        name="faq_section"
    ),
    
    path(
    "api/<int:version>/product/details", 
    rp_controller.ProductDetailsAPI.as_view(), 
    name="product_details"
    ),

    path("api/<int:version>/rank-predictor/pre-fill", rp_controller.PrefillProductsAPI.as_view(), name="prefill_fields"),

    path("api/<int:version>/rank-predictor/feedback", rp_controller.FeedbackSubmitAPI.as_view(), name='submit_feedback'),
    



    path("api/<int:version>/feedback", rp_controller.FeedbackAPI.as_view(), name="feedback"),
    path("api/<int:version>/rank-predictor/form-prefill", rp_controller.UserTrackingAPI.as_view(), name='form prefill for reuse case'),
    path("api/<int:version>/rank-predictor/cast-disability", rp_controller.CasteDisabilityAPI.as_view(), name='cast disabilitys'),
    

    
]