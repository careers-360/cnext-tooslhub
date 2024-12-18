from rest_framework.views import APIView
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
        

class RPAppearedStudentsAPI(APIView):

    def get(self, request, version, **kwargs):
        resp = {}
        year = request.GET.get('year')
        product_id = request.GET.get('product_id')

        if not product_id or not product_id.isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        if year and not year.isdigit():
            return CustomErrorResponse({"message": "year should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)

        cms_helper = RPCmsHelper()
        resp, data = cms_helper._get_student_appeared_data_(product_id=product_id, year=year)
        if resp:
            return SuccessResponse(data, status=status.HTTP_201_CREATED)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)
        

    def post(self, request, version, **kwargs):

        """
        Handles bulk create, update, and delete operations for RPStudentAppeared model.
        """
        product_id = request.data.get('product_id')
        year = request.data.get('year')
        student_data = request.data.get('student_data')
        user_id = request.data.get('user_id')

        if not product_id or not str(product_id).isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        if year and not str(year).isdigit():
            return CustomErrorResponse({"message": "year should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)

        product_id = int(product_id)
        # add appeared student data in database.
        cms_helper = RPCmsHelper()
        resp, data = cms_helper._add_update_student_appeared_data(student_data=student_data, product_id=product_id, year=year,user_id=user_id)
        if resp:
            return SuccessResponse(data, status=status.HTTP_201_CREATED)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)
