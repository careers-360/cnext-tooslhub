from rest_framework.views import APIView
from rest_framework.response import Response
from utils.helpers.response import SuccessResponse, CustomErrorResponse
from utils.helpers.custom_permission import ApiKeyPermission
from rest_framework import status
from .helpers import RPCmsHelper


class FlowTypeAPI(APIView):

    """
    API for Flow Type CMS Pannel
    Endpoint : api/<int:version>/cms/rp/flow-type
    Params : product_id
    """

    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):
        # Fetch flow master data from database and return it to client.
        cms_helper = RPCmsHelper()
        data = cms_helper._get_flow_types(**request.GET)
        return SuccessResponse(data, status=status.HTTP_200_OK)
    
    def post(self, request, version):
        # Add new flow master data to database.
        # This method will be implemented in future.

        flow_type = request.data.get('flow_type')
        if not flow_type:
            return CustomErrorResponse("Missing required parameters", status=status.HTTP_400_BAD_REQUEST)
        
        cms_helper = RPCmsHelper()
        resp, msg = cms_helper._add_flow_type(**request.data)
        if not resp:
            return CustomErrorResponse(msg, status=status.HTTP_400_BAD_REQUEST)
        else:
            return SuccessResponse({"message": msg}, status=status.HTTP_201_CREATED)
        
    def delete(self, request, version):
        # Add new flow master data to database.
        # This method will be implemented in future.

        flow_type = request.data.get('flow_type')
        if not flow_type:
            return CustomErrorResponse("Missing required parameters", status=status.HTTP_400_BAD_REQUEST)
        
        cms_helper = RPCmsHelper()
        resp, msg = cms_helper._delete_flow_type(**request.data)
        if not resp:
            return CustomErrorResponse(msg, status=status.HTTP_400_BAD_REQUEST)
        else:
            return SuccessResponse({"message": msg}, status=status.HTTP_201_CREATED)