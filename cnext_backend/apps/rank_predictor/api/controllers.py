from rest_framework.views import APIView
from rest_framework.response import Response
from utils.helpers.response import SuccessResponse, CustomErrorResponse
from utils.helpers.custom_permission import ApiKeyPermission
from rest_framework import status
from rank_predictor.api.helpers import ResultPageStaticHelper


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
        rp_static_helper = ResultPageStaticHelper()
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
        rp_static_helper = ResultPageStaticHelper()
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
    NOTE : UNCOPLETE API* Logic to be implement.
    """

    def get(self, request, version, **kwargs):

        product_id = request.GET.get('product_id')
        if not product_id or not product_id.isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = int(product_id)

        # Fetch faq from database and return it to client.
        rp_static_helper = ResultPageStaticHelper()
        faq_section = rp_static_helper._get_faq_section(product_id=product_id)
        resp = {
            "product_id" : product_id,
            "heading" : "What Students Are Saying",
            "faq" : faq_section,
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
        rp_static_helper = ResultPageStaticHelper()
        if not exam_id:
            exam_id = rp_static_helper._get_exam_from_product(product_id=product_id)
        
        top_collegs_section = rp_static_helper._get_colleges_from_exam(exam_id=exam_id)
        resp = {
            "product_id" : product_id,
            "heading" : "Top Colleges",
            "college" : top_collegs_section,
        }
        return SuccessResponse(resp, status=status.HTTP_200_OK)
    