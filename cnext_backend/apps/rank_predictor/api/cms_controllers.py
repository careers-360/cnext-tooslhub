from rank_predictor.models import CnextRpCreateInputForm, RpMeritList
from rest_framework.views import APIView
from rank_predictor.models import RpFormField
from utils.helpers.response import SuccessResponse, CustomErrorResponse, ErrorResponse
from utils.helpers.custom_permission import ApiKeyPermission
from rest_framework import status
from .helpers import RPCmsHelper, CommonDropDownHelper
from rest_framework.response import Response
import json
import pandas as pd


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
        product_id = request.GET.get('product_id')

        if not product_id or not product_id.isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        if year and not year.isdigit():
            return CustomErrorResponse({"message": "year should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)

        cms_helper = RPCmsHelper()
        resp, data = cms_helper._get_student_appeared_data_(product_id=product_id, year=year)
        if resp:
            return SuccessResponse(data, status=status.HTTP_200_OK)
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

class UploadMeritList(APIView):
    permission_classes = [ApiKeyPermission]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        selected_year = request.POST.get('year')
        product_id = request.POST.get('product_id')
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in ['csv', 'xlsx']:
            return Response({"error": "Unsupported file format. Only .csv and .xlsx are allowed."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if file_extension == 'csv':
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            # Clean column names to remove any leading/trailing spaces
            df.columns = df.columns.str.strip()

            # Validate 'year' column against selected_year
            if 'year' not in df.columns:
                return Response({"error": "'year' column not found in the file."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if all rows in the 'year' column match the selected_year
            if not df['year'].astype(str).eq(str(selected_year)).all():
                return Response({"error": "Sheet Year does not match with the selected one."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if 'input_flow_type' exists in the columns
            if 'input_flow_type' not in df.columns:
                return Response({"error": "'input_flow_type' column not found in the file."}, status=status.HTTP_400_BAD_REQUEST)

            #DELETE SAME DATA CASE
            RpMeritList.objects.filter(product_id = product_id,year = selected_year).delete()
            # Group by 'input_flow_type' and calculate mean and standard deviation for each group
            grouped = df.groupby('input_flow_type').agg(
                sheet_mean=('input', 'mean'),
                sheet_sd=('input', 'std')
            ).reset_index()

            # Process rows to calculate zscore
            processed_rows = []
            for _, row in df.iterrows():
                input_flow_type = row.get('input_flow_type')

                # Get the mean and sd for the current input_flow_type
                group_stats = grouped[grouped['input_flow_type'] == input_flow_type]
                if not group_stats.empty:
                    sheet_mean = group_stats['sheet_mean'].values[0]
                    sheet_sd = group_stats['sheet_sd'].values[0]
                else:
                    sheet_mean = None
                    sheet_sd = None

                # Add results to the row dictionary
                row_data = row.to_dict()
                row_data['sheet_mean'] = sheet_mean
                row_data['sheet_sd'] = sheet_sd

                # Calculate zscore if sheet_mean and sheet_sd are not None
                if sheet_mean is not None and sheet_sd is not None and sheet_sd != 0:
                    input_value = row.get('input')
                    if pd.notnull(input_value) and isinstance(input_value, (int, float)):
                        zscore = (input_value - sheet_mean) / sheet_sd
                        row_data['zscore'] = zscore
                    else:
                        row_data['zscore'] = None
                else:
                    row_data['zscore'] = None

                processed_rows.append(row_data)

            return Response({"message": "File processed successfully.", "data": processed_rows[:20]}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

