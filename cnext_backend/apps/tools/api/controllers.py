from tools.helpers.helpers import ToolsHelper
from rest_framework.views import APIView
from rest_framework.response import Response
from utils.helpers.response import SuccessResponse,ErrorResponse
from utils.helpers.custom_permission import ApiKeyPermission
from rest_framework import status


class HealthCheck(APIView):

    def get(self, request):
        return SuccessResponse({"message": "Tools App runnning"}, status=status.HTTP_200_OK)
    
# class CMSToolsFilter(APIView):

#     def get(self, request):

#         return SuccessResponse(status=status.HTTP_200_OK)


class ManagePredictorToolAPI(APIView):
    """
    Predictor List API
    Endpoint -> api/<int:version>/cms/manage-predictor-tool
    version -> v1 required
    GET API ->api/1/cms/manage-predictor-tool
    """
    permission_classes = (
        ApiKeyPermission,
    )
    def get(self, request, version, format=None, **kwargs):
        try:
            helper = ToolsHelper(request=request)
            data = helper.get_predictor_tool_list()
            return SuccessResponse(data, status=status.HTTP_200_OK)
        except Exception as e:
            return ErrorResponse(e.__str__(), status=status.HTTP_404_NOT_FOUND)