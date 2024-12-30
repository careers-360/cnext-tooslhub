from rest_framework.views import APIView
from rest_framework.response import Response
from utils.helpers.response import SuccessResponse, CustomErrorResponse
from utils.helpers.custom_permission import ApiKeyPermission
from rest_framework import status
from rank_predictor.api.helpers import InputPageStaticHelper
from rank_predictor.helper.landing_helper import RPHelper

class HealthCheck(APIView):

    def get(self, request):
        return SuccessResponse({"message": "Rank Predictor App, Running."}, status=status.HTTP_200_OK)
    

class ContentSectionAPI(APIView):
    """
    API for Content Section on Result Page
    Endpoint : api/<int:version>/rank-predictor/content-section
    Params : product_id
    """

    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):

        product_id = request.GET.get('product_id')
        if not product_id or not product_id.isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = int(product_id)

        # Fetch content from database and return it to client.
        rp_static_helper = InputPageStaticHelper()
        content = rp_static_helper._get_content_section(product_id=product_id)
        resp = {
            "product_id" : product_id,
            "content" : content,
        }
        return SuccessResponse(resp, status=status.HTTP_200_OK)
    

class FAQSectionAPI(APIView):
    """
    API for FAQ Section on Result Page
    Endpoint : api/<int:version>/rank-predictor/faq-section
    Params : product_id
    """

    permission_classes = [ApiKeyPermission]


    """
    NOTE : UNCOPLETE API* Logic to be implement.
    """

    def get(self, request, version, **kwargs):

        product_id = request.GET.get('product_id')
        if not product_id or not product_id.isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = int(product_id)

        # Fetch faq from database and return it to client.
        rp_static_helper = InputPageStaticHelper()
        faq_section = rp_static_helper._get_faq_section(product_id=product_id)
        resp = {
            "product_id" : product_id,
            "faq" : faq_section,
        }
        return SuccessResponse(resp, status=status.HTTP_200_OK)


class ReviewSectionAPI(APIView):
    """
    API for FAQ Section on Result Page
    Endpoint : api/<int:version>/rank-predictor/faq-section
    Params : product_id
    """

    permission_classes = [ApiKeyPermission]

    """
    NOTE : TABLE DB needs to update in oither projects
    """

    def get(self, request, version, **kwargs):

        product_id = request.GET.get('product_id')
        if not product_id or not product_id.isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = int(product_id)

        # Fetch faq from database and return it to client.
        rp_static_helper = InputPageStaticHelper()
        feedback_section = rp_static_helper._get_user_feedback_section(product_id=product_id)
        resp = {
            "product_id" : product_id,
            "heading" : "Top User Feedbacks",
            "feedback" : feedback_section,
        }
        return SuccessResponse(resp, status=status.HTTP_200_OK)
    

class TopCollegesSectionAPI(APIView):
    """
    API for FAQ Section on Result Page
    Endpoint : api/<int:version>/rank-predictor/faq-section
    Params : product_id
    """

    permission_classes = [ApiKeyPermission]


    """
    NOTE : UNCOPLETE API* Logic to be implement.
    """

    def get(self, request, version, **kwargs):

        product_id = request.GET.get('product_id')
        exam_id = request.GET.get('exam_id')

        if (not product_id or not product_id.isdigit()) and (not exam_id or not exam_id.isdigit()):
            return CustomErrorResponse({"message": "product_id or exam_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch top colleges from database and return it to client.
        rp_static_helper = InputPageStaticHelper()
        if not exam_id:
            exam_id = rp_static_helper._get_exam_from_product(product_id=product_id)
        
        top_collegs_section = rp_static_helper._get_colleges_from_exam(exam_id=exam_id)
        resp = {
            "product_id" : product_id,
            "heading" : "Top Colleges",
            "college" : top_collegs_section,
        }
        return SuccessResponse(resp, status=status.HTTP_200_OK)
    

class LandingDataAPI(APIView):
    """
    API for Content Section on Result Page
    Endpoint : api/<int:version>/rank-predictor/landing-data
    Params : product_id
    """

    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):

        resp = {}

        product_id = request.GET.get('product_id')
        alias = request.GET.get('alias')
        
        if product_id != None:
            product_id = int(product_id)

        # Fetch content from database and return it to client.
        rp_helper = RPHelper()
        header_content = rp_helper._get_header_section(product_id=product_id, alias=alias)
        content_section = rp_helper._get_content_section(product_id=product_id)

        if header_content:

            resp = {
            "product_id" : product_id,
            "header_content" : header_content,
            "cotent_section": content_section
            }
            return SuccessResponse(resp, status=status.HTTP_200_OK)
        
        no_such_product = f"product with id = {product_id} did not exist"
        return SuccessResponse(no_such_product, status=status.HTTP_404_NOT_FOUND)
        
        
        

class FormSectionAPI(APIView):
    """
    API for Content Section on Result Page
    Endpoint : api/<int:version>/rank-predictor/form-section
    Params : product_id
    """


    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):

        product_id = request.GET.get('product_id')
        alias = request.GET.get('alias')

        if not product_id or not product_id.isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = int(product_id)

        # Fetch content from database and return it to client.
        rp_helper = RPHelper()
        form_fields = rp_helper._get_form_section(product_id=product_id, alias=alias)

        if form_fields:
            resp = {
                "fields_list" : form_fields
            }
            return SuccessResponse(resp, status=status.HTTP_200_OK)
        
        no_such_product = f"product with id {product_id} doesnot exist"
        return SuccessResponse(no_such_product, status=status.HTTP_404_NOT_FOUND)

class TopCollegesAPI(APIView):
    """
    API for fetching top colleges related to an exam.
    Endpoint: api/<int:version>/rank-predictor/top-colleges
    Params: exam_id
    """
    permission_classes = [ApiKeyPermission]
    def get(self, request, version, **kwargs):
        exam_id = request.GET.get('exam_id')
        if not exam_id or not exam_id.isdigit():
            return CustomErrorResponse(
                {"message": "exam_id is required and should be an integer value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        exam_id = int(exam_id)
        # Fetch colleges from the database
        rp_helper = RPHelper()
        colleges = rp_helper._get_top_colleges(exam_id=exam_id)
        if colleges:
            resp = {
                "exam_id": exam_id,
                "colleges": colleges,
            }
            return SuccessResponse(resp, status=status.HTTP_200_OK)
        no_colleges_found = f"No colleges found for exam_id {exam_id}"
        return SuccessResponse({"message": no_colleges_found}, status=status.HTTP_404_NOT_FOUND)
    
# class RankCalculatorAPI(APIView):
#     """
#     API for Rank and Percentile Calculation
#     Endpoint: api/<int:version>/rank-predictor/rank-calculation
#     Params:
#         - score (optional)
#         - percentile (optional)
#         - max_score (required)
#         - total_candidates (required)
#         - caste (optional)
#         - disability (optional)
#         - slot (optional)
#         - difficulty_level (optional)
#         - year (optional)
#     """
#     permission_classes = [ApiKeyPermission]

#     def post(self, request, version, **kwargs):
#         # Parse input data
#         score = request.data.get("score")
#         percentile = request.data.get("percentile")
#         max_score = request.GET.get("max_score")
#         total_candidates = request.GET.get("total_candidates")
#         caste = request.data.get("caste", None)
#         disability = request.data.get("disability", None)
#         slot = request.data.get("slot", None)
#         difficulty_level = request.data.get("difficulty_level", None)
#         year = request.data.get("year", None)

#         # Ensure max_score and total_candidates are provided
#         if not max_score or not total_candidates:
#             return CustomErrorResponse(
#                 {"message": "max_score and total_candidates are required fields."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         try:
#             # Convert max_score and total_candidates to the correct data types
#             max_score = float(max_score)
#             total_candidates = int(total_candidates)

#             # Ensure max_score and total_candidates are positive
#             if max_score <= 0 or total_candidates <= 0:
#                 raise ValueError("max_score and total_candidates must be greater than 0.")
#         except ValueError as e:
#             return CustomErrorResponse(
#                 {"message": str(e)},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         rp_helper = RPHelper()

#         # Case 1: If the user provides score, calculate percentile
#         if score is not None:
#             try:
#                 # Convert score to float and validate
#                 score = float(score)
#                 if score < 0 or score > max_score:
#                     raise ValueError(f"Score must be between 0 and {max_score}.")
#             except ValueError as e:
#                 return CustomErrorResponse(
#                     {"message": str(e)},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Calculate percentile based on score
#             percentile = rp_helper.calculate_percentile(score, max_score)

#             # Return percentile score
#             return SuccessResponse(
#                 {"percentile_score": percentile},
#                 status=status.HTTP_200_OK
#             )

#         # Case 2: If the user provides percentile, calculate rank
#         if percentile is not None:
#             try:
#                 # Convert percentile to float and validate
#                 percentile = float(percentile)
#                 if percentile < 0 or percentile > 100:
#                     raise ValueError("Percentile must be between 0 and 100.")
#             except ValueError as e:
#                 return CustomErrorResponse(
#                     {"message": str(e)},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Calculate rank based on percentile
#             rank_data = rp_helper.calculate_category_rank(
#                 percentile=percentile,
#                 total_candidates=total_candidates,
#                 caste=caste,
#                 disability=disability,
#                 slot=slot,
#                 difficulty_level=difficulty_level,
#                 year=year,
#             )

#             # Add percentile score to the response
#             rank_data["percentile_score"] = percentile
#             return SuccessResponse(rank_data, status=status.HTTP_200_OK)

#         # If neither score nor percentile is provided
#         return CustomErrorResponse(
#             {"message": "Either score or percentile must be provided."},
#             status=status.HTTP_400_BAD_REQUEST,
#         )