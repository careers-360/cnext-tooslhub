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
    