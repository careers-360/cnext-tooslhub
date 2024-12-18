from requests import request
from tools.api.serializers import ToolBasicDetailSerializer
from tools.helpers.helpers import ToolsHelper
from rest_framework.views import APIView
from utils.helpers.response import SuccessResponse,ErrorResponse, CustomErrorResponse
from utils.helpers.custom_permission import ApiKeyPermission
from rest_framework import status
from rest_framework.response import Response
import json

from tools.helpers.helpers import ToolsHelper
from tools.models import CPProductCampaign, Domain, ToolsFAQ
from utils.helpers.choices import TOOL_TYPE, CONSUMPTION_TYPE, PUBLISHING_TYPE


class HealthCheck(APIView):

    def get(self, request):
        return SuccessResponse({"message": "Tools App runnning"}, status=status.HTTP_200_OK)
    
class CMSToolsFilterAPI(APIView):
    """
    Pending
    """

    permission_classes = (ApiKeyPermission,)

    def get(self, request, version, format=None, **kwargs):

        try:
            result = dict()
            tools_name = list(CPProductCampaign.objects.values('id', 'name'))
            domain = list(Domain.objects.filter(is_stream = 1).values('id','name'))

            # Construct the response payload
            result = {
                'tool_type': TOOL_TYPE,
                'consumption_type': CONSUMPTION_TYPE,
                'published_status_web_wap': PUBLISHING_TYPE,
                'published_status_app': PUBLISHING_TYPE,
                'domain': domain,
                'tools_name': tools_name,
            }
            return SuccessResponse(result,status=status.HTTP_200_OK)

        except Exception as e:
            return ErrorResponse("An unexpected error occurred.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ManagePredictorToolAPI(APIView):
    """
    Predictor List API
    Endpoint -> api/<int:version>/cms/manage-tool/list
    version -> v1 required
    GET API ->api/1/cms/manage-tool/list
    """
    permission_classes = (ApiKeyPermission,)

    def get(self, request, version, format=None, **kwargs):
        try:
            helper = ToolsHelper(request=request)
            filter_value = helper.get_manage_predictor_tools_filter()
            data = helper.get_predictor_tool_list(filter_value)
            return SuccessResponse(data, status=status.HTTP_200_OK)

        except Exception as e:
            return ErrorResponse(e.__str__(), status=status.HTTP_400_BAD_REQUEST)
        

class CMSToolsFaqAPI(APIView):
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
            product_id = request.query_params.get('product_id')
            if not product_id:
                return CustomErrorResponse({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch FAQs for the given product_id
            faqs = ToolsFAQ.objects.filter(product_id=product_id).values(
                "id", "question", "answer", "status"
            )
            return SuccessResponse({"reponse": list(faqs)})

        except Exception as e:
            return ErrorResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request, version, *args, **kwargs):
        faqs = request.data.get('faqs', [])  # List of ToolsFAQ dictionaries
        product_id = request.data.get('product_id')  # List of ToolsFAQ dictionaries

        if not product_id:
            return CustomErrorResponse({"error": 'Product id needed'}, status=status.HTTP_400_BAD_REQUEST)

        if not CPProductCampaign.objects.filter(id=product_id).exists():
            return CustomErrorResponse({"error": 'Product does not exist'}, status=status.HTTP_404_NOT_FOUND)

        user_id = request.user.id  # Assuming user authentication is enabled

        for faq in faqs:
            question = faq.get("question")
            answer = faq.get("answer")
            status = faq.get("status", True)

            if not question or not answer:
                return CustomErrorResponse({'error': 'Both question and answer are required'}, status=status.HTTP_400_BAD_REQUEST)
           
            else:  # Create new ToolsFAQ
                ToolsFAQ.objects.create(
                    product_id=product_id,
                    question=question,
                    answer=answer,
                    status=status,
                    created_by=user_id,
                    updated_by=user_id
                )
        return SuccessResponse({"message": "FAQs updated successfully"}, status=200)


    def put(self, request, version, *args, **kwargs):
        """
        Handles the creation, update, deletion of FAQs.
        """
        faqs = request.data.get('faqs', [])  # List of ToolsFAQ dictionaries
        product_id = request.data.get('product_id')  # List of ToolsFAQ dictionaries
        product_type = request.data.get('product_type')  # List of ToolsFAQ dictionaries

        if not product_id:
            return CustomErrorResponse({"error": 'Product id needed'}, status=status.HTTP_400_BAD_REQUEST)

        if not CPProductCampaign.objects.filter(id=product_id).exists():
            return CustomErrorResponse({"error": 'Product does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
        instances = ToolsFAQ.objects.filter(product_id=product_id)
        
        user_id = request.user.id
        existing_ids = set(instances.values_list('id', flat=True))

        print("this is my existing_ids : ", existing_ids)

        for faq in faqs:
            question_data = {
                'question': faq.get('question'),
                'answer': faq.get('answer'),
                'product_id': product_id,
                'product_type':  product_type,
                'updated_by': user_id,
                'status': faq.get("status", True)
            }
            question_id = faq.get('id', None)
            if question_id:
                instances.filter(id=question_id).update(**question_data)
                existing_ids.remove(question_id)
            else:
                question_data['created_by'] = user_id
                new_question = ToolsFAQ.objects.create(**question_data)

        if len(existing_ids):
            instances.filter(id__in=existing_ids).delete()
        
        
        return SuccessResponse({"message": "FAQs updated successfully"}, status=200)


class CMSToolsBasicDetailAPI(APIView):
    """
    Tools basic detail API
    Endpoint -> api/<int:version>/cms/manage-tool/basic-detail/<int:pk>
    version -> v1 required
    GET API ->api/1/cms/manage-tool/basic-detail
    """
    permission_classes = (
        ApiKeyPermission,
    )

    def get_object(self, pk):
        try:
            return CPProductCampaign.objects.get(pk=pk)
        except CPProductCampaign.DoesNotExist:
            return None

    def get(self, request, version, format=None, **kwargs):
        try:
            product_id = request.query_params.get('product_id')
            obj = self.get_object(product_id)
            if obj is None:
                return Response({'message': f'Tool with id: {product_id} does not exist.'}, status=status.HTTP_404_NOT_FOUND)
            helper = ToolsHelper(request=request)
            data = helper.get_basic_detail_data(product_id)
            return SuccessResponse(data, status=status.HTTP_200_OK)
        except Exception as e:
            return ErrorResponse(e.__str__(), status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request, version, format=None, **kwargs):
        product_id = request.POST.get('product_id')
        request_data = request.data.copy()
        smart_registration = json.loads(request_data.get('smart_registration_data', []))
        instance = self.get_object(product_id)
        helper = ToolsHelper()
        data = helper.add_edit_basic_detail(instance = instance, request_data = request_data, smart_registration = smart_registration)
        return SuccessResponse(data, status=status.HTTP_200_OK)
    

class CMSToolsResultPageAPI(APIView):

    permission_classes = (
        ApiKeyPermission,
    )

    def get_object(self, pk):
        """Helper method to get a specific object by primary key."""
        try:
            return CPProductCampaign.objects.get(id=pk)
        except CPProductCampaign.DoesNotExist:
            return None

    def get(self, request, version, format=None, **kwargs):
        try:
            # Retrieve product_id from query parameters
            pk = request.query_params.get('product_id')
            
            if not pk:
                return ErrorResponse({'message': 'Product ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Fetch the object using .get() to ensure it exists
            obj = CPProductCampaign.objects.get(id=pk)
            
            if obj is None:
                return ErrorResponse({'message': f'Tool with id: {pk} does not exist.'}, status=status.HTTP_404_NOT_FOUND)
            
            # Prepare the response data
            result = {
                'rp_disclaimer': obj.rp_disclaimer,
                'cp_cta_name': obj.cp_cta_name,
                'cp_destination_url': obj.cp_destination_url,
                'cp_pitch': obj.cp_pitch,
                'mapped_product_title': obj.mapped_product_title,
                'mapped_product_cta_label': obj.mapped_product_cta_label,
                'mapped_product_destination_url': obj.mapped_product_destination_url,
                'mapped_product_pitch': obj.mapped_product_pitch,
                # 'promotion_banner_web': obj.promotion_banner_web,
                # 'promotion_banner_wap': obj.promotion_banner_wap,
            }
            
            return SuccessResponse({"result": result}, status=status.HTTP_200_OK)

        except CPProductCampaign.DoesNotExist:
            return ErrorResponse({'message': f'Tool with id: {pk} does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return ErrorResponse(e.__str__(), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def put(self, request, version, format=None, **kwargs):
        try:
            pk = request.data.get('product_id')
            
            if not pk:
                return ErrorResponse({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the object using .get() to ensure it exists
            obj = CPProductCampaign.objects.get(id=pk)
            
            # Update fields
            print("this is the data ", request.data)
            serializer = ToolBasicDetailSerializer(data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(updated_by=request.user.id)
                return SuccessResponse({"message": "Tool updated successfully", "result": serializer.data}, status=status.HTTP_200_OK)
            else:
                return ErrorResponse({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except CPProductCampaign.DoesNotExist:
            return ErrorResponse({"error": "Tool does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return ErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


