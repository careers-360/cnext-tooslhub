from cnext_backend import settings
from rank_predictor.models import CnextRpCreateInputForm
from rest_framework.views import APIView
from utils.helpers.response import SuccessResponse, CustomErrorResponse, ErrorResponse
from utils.helpers.custom_permission import ApiKeyPermission
from rest_framework import status
from .helpers import RPCmsHelper, CommonDropDownHelper
from rest_framework.response import Response

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
        data = cms_helper._get_flow_types(**request.GET.dict())# TODO - added .dict
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
    API for exam session CMS Pannel
    Endpoint : api/<int:version>/cms/rp/exam-session
    Params : product_id, year
    """

    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):
        uid = request.GET.get('uid')
        product_id = request.GET.get('product_id')
        year = request.GET.get('year')
        if not product_id or not uid or not product_id.isdigit() or not uid.isdigit():
            return CustomErrorResponse({"message": "product_id, uid are required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        if year and not str(year).isdigit():
            return CustomErrorResponse({"message": "year should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = int(product_id)
        # Fetch exam session data from database and return it to client.
        cms_helper = RPCmsHelper()
        resp, data = cms_helper._get_exam_session_data(product_id=product_id, year=year)
        if resp:
            return SuccessResponse(data, status=status.HTTP_200_OK)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, version):
        uid = request.data.get('uid')
        product_id = request.data.get('product_id')
        year = request.data.get('year')
        session_data = request.data.get('session_data')

        if not product_id or not uid or not str(product_id).isdigit() or not str(uid).isdigit():
            return CustomErrorResponse({"message": "product_id, uid are required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        if year and not str(year).isdigit():
            return CustomErrorResponse({"message": "year should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)

        product_id = int(product_id)
        # add exam session data in database.
        cms_helper = RPCmsHelper()
        resp, data = cms_helper._add_exam_session_data(uid=uid, session_data=session_data, product_id=product_id, year=year)
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
        limit = request.GET.get('limit')
        offset = request.GET.get('offset')
        page = request.GET.get('page')
        q = request.GET.get('q','')

        if not field_name:
            return CustomErrorResponse({"message": "field_name is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if selected_id:
            if not str(selected_id).isdigit():
                return CustomErrorResponse({"message": "selected_id should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                selected_id = int(selected_id)
    
        # Fetch common dropdown data from database and return it to client.
        cms_helper = CommonDropDownHelper(offset=offset, page=page, limit=limit)
        resp = cms_helper._get_dropdown_list(**request.GET.dict())
        return SuccessResponse(resp, status=status.HTTP_200_OK)
    

class VariationFactorAPI(APIView):
    """
    API for variation factor CMS Pannel
    Endpoint : api/<int:version>/cms/rp/exam-session
    Params : product_id
    """

    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):
        uid = request.GET.get('uid')
        product_id = request.GET.get('product_id')

        if not uid or not product_id or not uid.isdigit() or not product_id.isdigit():
            return CustomErrorResponse({"message": "uid, product_id are required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)

        product_id = int(product_id)
        # Fetch variation factor data from database and return it to client.
        cms_helper = RPCmsHelper()
        resp, data = cms_helper._get_variation_factor_data(product_id=product_id)
        if resp:
            return SuccessResponse(data, status=status.HTTP_200_OK)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, version):
        uid = request.data.get('uid')
        product_id = request.data.get('product_id')
        variation_factor_data = request.data.get('variation_factor_data')

        if not uid or not product_id or not str(uid).isdigit() or not str(product_id).isdigit():
            return CustomErrorResponse({"message": "product_id, uid are required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)

        product_id = int(product_id)
        # add variation factor data in database.
        cms_helper = RPCmsHelper()
        resp, data = cms_helper._add_variation_factor_data(uid=uid, var_factor_data=variation_factor_data, product_id=product_id)
        if resp:
            return SuccessResponse(data, status=status.HTTP_201_CREATED)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)
        

class CustomMeanSD(APIView):
    """
    API for Custom Mean/SD CMS Pannel
    Endpoint : api/<int:version>/cms/rp/custom-mean-sd
    Params : product_id, year
    """

    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):
        uid = request.GET.get('uid')
        product_id = request.GET.get('product_id')
        year = request.GET.get('year')

        if not product_id or not uid or not product_id.isdigit() or not uid.isdigit():
            return CustomErrorResponse({"message": "product_id, uid are required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        if year and not str(year).isdigit():
            return CustomErrorResponse({"message": "year should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = int(product_id)
        # Fetch custom mean, SD from database and return it to client.
        cms_helper = RPCmsHelper()
        resp, data = cms_helper._get_custom_mean_sd_data(product_id=product_id, year=year)
        if resp:
            return SuccessResponse(data, status=status.HTTP_200_OK)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, version):
        uid = request.data.get('uid')
        product_id = request.data.get('product_id')
        year = request.data.get('year')
        custom_mean_sd_data = request.data.get('custom_mean_sd_data')

        if not product_id or not uid or not str(product_id).isdigit() or not str(uid).isdigit():
            return CustomErrorResponse({"message": "product_id, uid are required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        if year and not str(year).isdigit():
            return CustomErrorResponse({"message": "year should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)

        product_id = int(product_id)
        # add exam session data in database.
        cms_helper = RPCmsHelper()
        resp, data = cms_helper._add_custom_mean_sd_data(uid=uid, custom_mean_sd_data=custom_mean_sd_data, product_id=product_id, year=year)
        if resp:
            return SuccessResponse(data, status=status.HTTP_201_CREATED)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)
        

class RPAppearedStudentsAPI(APIView):

    def get(self, request, version, **kwargs):
        resp = {}
        year = request.GET.get('year')
        exam_id = request.GET.get('exam_id')

        if not exam_id or not exam_id.isdigit():
            return CustomErrorResponse({"message": "exam_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        if year and not year.isdigit():
            return CustomErrorResponse({"message": "year should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)

        cms_helper = RPCmsHelper()
        resp, data = cms_helper._get_student_appeared_data_(exam_id=exam_id, year=year)
        if resp:
            return SuccessResponse(data, status=status.HTTP_200_OK)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)
        

    def post(self, request, version, **kwargs):

        """
        Handles bulk create, update, and delete operations for RPStudentAppeared model.
        """
        exam_id = request.data.get('exam_id')
        year = request.data.get('year')
        student_data = request.data.get('student_data')
        user_id = request.data.get('user_id')

        if not exam_id or not str(exam_id).isdigit():
            return CustomErrorResponse({"message": "exam_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        if year and not str(year).isdigit():
            return CustomErrorResponse({"message": "year should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)

        exam_id = int(exam_id)
        # add appeared student data in database.
        cms_helper = RPCmsHelper()
        resp, data = cms_helper._add_update_student_appeared_data(student_data=student_data, exam_id=exam_id, year=year,user_id=user_id)
        if resp:
            return SuccessResponse(data, status=status.HTTP_201_CREATED)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)


class CreateForm(APIView):

    def get(self, request, version, **kwargs):

        
        resp = {}
        id = request.GET.get('id')

        if not id or not id.isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)

        cms_helper = RPCmsHelper()
        resp, data = cms_helper._get_input_form_field_data(id=id)
        if resp:
            return SuccessResponse(data, status=status.HTTP_200_OK)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)
        pass


    def post(self, request, version, **kwargs):

        data = request.data
        id = data.get('id')
        product_id = data.get('product_id')
        # TODO get user_id from token ?

        if not product_id :
            return CustomErrorResponse("Product is mandatory for update/create")
        
        cms_helper = RPCmsHelper()
        resp, data = cms_helper._add_update_rp_form_data(id=id, data=data)
        if resp:
            return SuccessResponse(data, status=status.HTTP_201_CREATED)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)
    
    

class CreateInputForm(APIView):
    permission_classes = (
        ApiKeyPermission,
    )

    def get_object(self, pk):
        try:
            return CnextRpCreateInputForm.objects.filter(product_id=pk)
        except CnextRpCreateInputForm.DoesNotExist:
            return None

    def get(self, request, version, format=None, **kwargs):
        try:
            product_id = request.query_params.get('product_id')
            obj = self.get_object(product_id)
            if obj is None:
                return Response({'message': f'Tool with id: {product_id} does not exist.'}, status=status.HTTP_404_NOT_FOUND)
            helper = RPCmsHelper()
            data = helper.get_input_form_data(product_id)
            return SuccessResponse(data, status=status.HTTP_200_OK)
        except Exception as e:
            return ErrorResponse(e.__str__(), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, version, format=None, **kwargs):
        product_id = request.data.get('product_id')
        request_data = request.data.get('data')
        instance = self.get_object(product_id)
        helper = RPCmsHelper()
        data = helper.create_input_form(product_id = product_id,instance = instance, request_data = request_data)
        return SuccessResponse(data, status=status.HTTP_200_OK)
    
class InputFormList(APIView):
    permission_classes = (
        ApiKeyPermission,
    )
    
    def get(self, request, version, format=None, **kwargs):
        try:
            helper = RPCmsHelper()
            data = helper.get_input_form_list(request)
            return SuccessResponse(data, status=status.HTTP_200_OK)

        except Exception as e:
            return ErrorResponse(e.__str__(), status=status.HTTP_400_BAD_REQUEST)


class MeritListValidationCheck(APIView):
    """
    API for Validating Merit Sheet Uploaded
    Endpoint : /cms/rp/merit-list-validation-check
    Params : product_id, year, uid
    """
    permission_classes = [ApiKeyPermission]

    def post(self, request, *args, **kwargs):

        helper = RPCmsHelper()
        resp, data = helper.validate_sheet(request)
        if resp:
            return SuccessResponse(data, status=status.HTTP_200_OK)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)

class UploadMeritList(APIView):
    permission_classes = [ApiKeyPermission]

    def post(self, request, *args, **kwargs):

        helper = RPCmsHelper()
        resp, data = helper.upload_merit_list(request)
        if resp:
            return SuccessResponse(data, status=status.HTTP_200_OK)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)

class MeritListView(APIView):
    permission_classes = [ApiKeyPermission]

    def get(self, request, *args, **kwargs):

        helper = RPCmsHelper()
        resp, data = helper.get_merit_list(request)
        if resp:
            return SuccessResponse(data, status=status.HTTP_200_OK)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request, *args, **kwargs):
        helper = RPCmsHelper()
        resp, data = helper.add_edit_display_graph(request)
        if resp:
            return SuccessResponse(data, status=status.HTTP_200_OK)
        else:
            return CustomErrorResponse(data, status=status.HTTP_400_BAD_REQUEST)