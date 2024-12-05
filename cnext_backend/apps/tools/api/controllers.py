from rest_framework.views import APIView
from rest_framework.response import Response
from utils.helpers.response import SuccessResponse
from utils.helpers.custom_permission import ApiKeyPermission
from rest_framework import status


class HealthCheck(APIView):

    def get(self, request):
        return SuccessResponse({"message": "Tools App runnning"}, status=status.HTTP_200_OK)
    
# class CMSToolsFilter(APIView):

#     def get(self, request):

#         return SuccessResponse(status=status.HTTP_200_OK)