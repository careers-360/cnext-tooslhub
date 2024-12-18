from rest_framework.views import APIView
from rest_framework.response import Response
from utils.helpers.response import SuccessResponse, CustomErrorResponse
from utils.helpers.custom_permission import ApiKeyPermission
from rest_framework import status
from .helpers import RPCmsHelper, CommonDropDownHelper


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
            return SuccessResponse({"message": msg}, status=status.HTTP_204_NO_CONTENT)


class ExamSessiondAPI(APIView):
    """
    API for Student Appeared CMS Pannel
    Endpoint : api/<int:version>/cms/rp/exam-session
    Params : product_id, year
    """

    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):
        product_id = request.GET.get('product_id')
        year = request.GET.get('year')
        if not product_id or not product_id.isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        if year and not str(year).isdigit():
            return CustomErrorResponse({"message": "year should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = int(product_id)
        # Fetch appeared student data from database and return it to client.
        cms_helper = RPCmsHelper()
        data = cms_helper._get_student_appeared_data(product_id=product_id, year=year)
        return SuccessResponse(data, status=status.HTTP_200_OK)

    def post(self, request, version):
        product_id = request.data.get('product_id')
        year = request.data.get('year')
        student_data = request.data.get('student_data')

        if not product_id or not str(product_id).isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        if year and not str(year).isdigit():
            return CustomErrorResponse({"message": "year should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)

        product_id = int(product_id)
        # add appeared student data in database.
        cms_helper = RPCmsHelper()
        resp, data = cms_helper._add_student_appeared_data(student_data=student_data, product_id=product_id, year=year)
        if resp:
            return SuccessResponse(data, status=status.HTTP_201_CREATED)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)


class CommonDropDownAPI(APIView):

    """
    API for Common Dropdown CMS Pannel
    Endpoint : api/<int:version>/cms/rp/common-dropdown
    Params : product_id, type
    """

    def get(self, request, version, **kwargs):
        field_name = request.GET.get('field_name')
        selected_id = request.GET.get('selected_id')

        if not field_name:
            return CustomErrorResponse({"message": "field_name is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if selected_id:
            if not str(selected_id).isdigit():
                return CustomErrorResponse({"message": "selected_id should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                selected_id = int(selected_id)
    
        # Fetch common dropdown data from database and return it to client.
        cms_helper = CommonDropDownHelper()
        resp = cms_helper._get_dropdown_list(field_name=field_name, selected_id=selected_id)
        return SuccessResponse(resp, status=status.HTTP_200_OK)
    

class VariationFactorAPI(APIView):
    """
    API for Student Appeared CMS Pannel
    Endpoint : api/<int:version>/cms/rp/exam-session
    Params : product_id, year
    """

    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):
        product_id = request.GET.get('product_id')

        if not product_id or not product_id.isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = int(product_id)
        # Fetch appeared student data from database and return it to client.
        cms_helper = RPCmsHelper()
        data = cms_helper._get_variation_factor_data(product_id=product_id)
        return SuccessResponse(data, status=status.HTTP_200_OK)

    def post(self, request, version):
        product_id = request.data.get('product_id')
        var_factor_data = request.data.get('var_factor_data')

        if not product_id or not str(product_id).isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)

        product_id = int(product_id)
        # add appeared student data in database.
        cms_helper = RPCmsHelper()
        resp, data = cms_helper._add_variation_factor_data(var_factor_data=var_factor_data, product_id=product_id)
        if resp:
            return SuccessResponse(data, status=status.HTTP_201_CREATED)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)
        
