from rest_framework.views import APIView
from rest_framework.response import Response
from utils.helpers.response import SuccessResponse, CustomErrorResponse
from utils.helpers.custom_permission import ApiKeyPermission
from rest_framework import status
from rank_predictor.api.helpers import InputPageStaticHelper
from rank_predictor.helper.landing_helper import RPHelper

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
        rp_static_helper = InputPageStaticHelper()
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
        rp_static_helper = InputPageStaticHelper()
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
    NOTE : TABLE DB needs to update in oither projects
    """

    def get(self, request, version, **kwargs):

        product_id = request.GET.get('product_id')
        if not product_id or not product_id.isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = int(product_id)

        # Fetch faq from database and return it to client.
        rp_static_helper = InputPageStaticHelper()
        feedback_section = rp_static_helper._get_user_feedback_section(product_id=product_id)
        resp = {
            "product_id" : product_id,
            "heading" : "Top User Feedbacks",
            "feedback" : feedback_section,
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
        rp_static_helper = InputPageStaticHelper()
        if not exam_id:
            exam_id = rp_static_helper._get_exam_from_product(product_id=product_id)
        
        top_collegs_section = rp_static_helper._get_colleges_from_exam(exam_id=exam_id)
        resp = {
            "product_id" : product_id,
            "heading" : "Top Colleges",
            "college" : top_collegs_section,
        }
        return SuccessResponse(resp, status=status.HTTP_200_OK)
    

class LandingDataAPI(APIView):
    """
    API for Content Section on Result Page
    Endpoint : api/<int:version>/rank-predictor/landing-data
    Params : product_id
    """

    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):

        resp = {}

        product_id = request.GET.get('product_id')
        alias = request.GET.get('alias')
        
        if product_id != None:
            product_id = int(product_id)

        # Fetch content from database and return it to client.
        rp_helper = RPHelper()
        header_content = rp_helper._get_header_section(product_id=product_id, alias=alias)
        content_section = rp_helper._get_content_section(product_id=product_id)

        if header_content:

            resp = {
            "product_id" : product_id,
            "header_content" : header_content,
            "cotent_section": content_section
            }
            return SuccessResponse(resp, status=status.HTTP_200_OK)
        
        no_such_product = f"product with id = {product_id} did not exist"
        return SuccessResponse(no_such_product, status=status.HTTP_404_NOT_FOUND)
        
        
        

class FormSectionAPI(APIView):
    """
    API for Content Section on Result Page
    Endpoint : api/<int:version>/rank-predictor/form-section
    Params : product_id
    """


    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):

        product_id = request.GET.get('product_id')
        alias = request.GET.get('alias')

        if not product_id or not product_id.isdigit():
            return CustomErrorResponse({"message": "product_id is required and should be a integer value"}, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = int(product_id)

        # Fetch content from database and return it to client.
        rp_helper = RPHelper()
        form_fields = rp_helper._get_form_section(product_id=product_id, alias=alias)

        if form_fields:
            resp = {
                "fields_list" : form_fields
            }
            return SuccessResponse(resp, status=status.HTTP_200_OK)
        
        no_such_product = f"product with id {product_id} doesnot exist"
        return SuccessResponse(no_such_product, status=status.HTTP_404_NOT_FOUND)

class TopCollegesAPI(APIView):
    """
    API for fetching top colleges related to an exam.
    Endpoint: api/<int:version>/rank-predictor/top-colleges
    Params: exam_id
    """
    permission_classes = [ApiKeyPermission]
    def get(self, request, version, **kwargs):
        exam_id = request.GET.get('exam_id')
        if not exam_id or not exam_id.isdigit():
            return CustomErrorResponse(
                {"message": "exam_id is required and should be an integer value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        exam_id = int(exam_id)
        # Fetch colleges from the database
        rp_helper = RPHelper()
        colleges = rp_helper._get_top_colleges(exam_id=exam_id)
        if colleges:
            resp = {
                "exam_id": exam_id,
                "colleges": colleges,
            }
            return SuccessResponse(resp, status=status.HTTP_200_OK)
        no_colleges_found = f"No colleges found for exam_id {exam_id}"
        return SuccessResponse({"message": no_colleges_found}, status=status.HTTP_404_NOT_FOUND)
    
class RelatedProductsAPI(APIView):
    """
    API for fetching top colleges related to an exam.
    Endpoint: api/<int:version>/rank-predictor/related-products
    Params: product_id
    """
    permission_classes = [ApiKeyPermission]
    def get(self, request, version, **kwargs):
        product_id = request.GET.get('product_id')
        alias = request.GET.get('alias')
        if not product_id or not product_id.isdigit():
            return CustomErrorResponse(
                {"message": "product_id is required and should be an integer value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        product_id = int(product_id)
        # Fetch colleges from the database
        rp_helper = RPHelper()
        related_products = rp_helper._related_products(product_id=product_id, alias=alias)

        return SuccessResponse(related_products, status=status.HTTP_200_OK)
    
class UserTrackingAPI(APIView):
    """
    API for fetching top colleges related to an exam.
    Endpoint: api/<int:version>/rank-predictor/form-submit
    """
    permission_classes = [ApiKeyPermission]
    def post(self, request, version, **kwargs):
        user_data = request.data
        # print(f"user data got as {user_data}")
        product_id = user_data['product_id']
        alias = user_data['alias']
        if not product_id:
            return CustomErrorResponse(
                {"message": "product_id is required and should be an integer value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        product_id = int(product_id)
        rp_helper = RPHelper()
        user_data_id = rp_helper._user_tracking(product_id=product_id, alias=alias, user_data=user_data)

        return SuccessResponse({"id": user_data_id}, status=status.HTTP_200_OK)

class ProductFromAliasAPI(APIView):
    """
    API for fetching top colleges related to an exam.
    Endpoint: api/<int:version>/rank-predictor?alias=""
    """
    permission_classes = [ApiKeyPermission]
    def get(self, request, version, **kwargs):
        alias = request.GET.get('alias')
        rp_helper = RPHelper()
        product_exam_id = rp_helper._get_product__exam_from_alias(alias=alias)
        return SuccessResponse( product_exam_id, status=status.HTTP_200_OK)
    
    
class RankPredictorAPI(APIView):
    """
    API for Rank Predictor Workflow and Rank Calculation.
    Endpoint: api/<int:version>/rank-predictor
    Params:
      - flow_type: To determine rank calculation or predictor workflow.
      - Additional parameters based on the flow type.
    """

    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):
        try:
            flow_type = int(request.GET.get("flow_type"))
            if flow_type == 3:
                return self.rank_calculation(request)
            else:
                return self.rank_predictor_workflow(request)
        except Exception as e:
            return CustomErrorResponse(
                {"message": f"Error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def rank_calculation(self, request):
        """
        Handles rank calculation for flow_type = 3.
        """
        try:
            exam_id = int(request.GET.get("exam_id"))
            percentile = float(request.GET.get("percentile"))
            category_id = request.GET.get("category_id")
            disability_id = request.GET.get("disability_id")

            rp_helper = RPHelper()
            rank_data = rp_helper.calculate_rank(
                exam_id=exam_id,
                percentile=percentile,
                category_id=category_id,
                disability_id=disability_id,
            )

            formatted_data = {
                "exam_id": exam_id,
                "percentile": percentile,
                "rank_data": rank_data.get("data"),
            }

            return SuccessResponse(
                formatted_data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return CustomErrorResponse(
                {"message": f"Error occurred while calculating rank: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def rank_predictor_workflow(self, request):
        """
        Handles the rank predictor workflow for other flow types.
        """
        try:
            # Extract parameters
            
        
            CATEGORY_MAP = {
                2: "General", 
                3: "OBC", 
                4: "SC", 
                5: "ST", 
                6: "SEBC", 
                7: "NA", 
                8: "OE", 
                9: "EWS"
            }
            DISABILITY_MAP = {
                1: "PWD",  # Person with disability
                2: "N.A.", # No disability
                3: "PHV",
                4: "PHH",
                5: "PHO",
                6: "CA",
                7: "TP",
                8: "PH1",
                9: "PH2",
                10: "PH-AI"
            }
            product_id = request.GET.get('product_id')
            record_id = request.GET.get('id')
            caste = request.GET.get('category_id', 'General')
            disability = request.GET.get('disability_id', 'N.A.').lower()
            slot = request.GET.get('slot', None)
            score = request.GET.get('score')

            if not product_id or not product_id.isdigit() or not record_id or not record_id.isdigit():
                return CustomErrorResponse(
                    {"message": "product_id and id are required and must be integers"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not score or not score.isdigit():
                return CustomErrorResponse(
                    {"message": "score is required and must be an integer"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            product_id = int(product_id)
            record_id = int(record_id)
            score = float(score)

            rp_helper = RPHelper()

            # Step 1: Fetch session data
            session_data = rp_helper.get_session_data(product_id, record_id)
            if not session_data:
                return SuccessResponse(
                    f"No session data found for product_id {product_id} and id {record_id}",
                    status=status.HTTP_404_NOT_FOUND
                )

            difficulty = session_data["difficulty"]
            year = session_data["year"]
            

            # Step 2: Fetch Input Flow Types
            input_flow_results = rp_helper.get_input_flow_type(caste, disability, slot, difficulty, year)
            if not input_flow_results:
                return SuccessResponse(
                    {"message": "No input flow type found for the given parameters."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Step 3: Process Input Flow Types to Fetch Mean and SD
            for result in input_flow_results:
                combination = result.get("combination", {})
                product_id = combination.get("product_id")
                year = combination.get("year")
                input_flow_type = combination.get("input_flow_type")

                if input_flow_type:
                    mean, sd = rp_helper.get_mean_sd(product_id, year, input_flow_type)
                    result.update({"mean": mean, "sd": sd})

            # Step 4: Calculate Z-Score and Fetch Closest Results
            for result in input_flow_results:
                mean = result.get("mean")
                sd = result.get("sd")
                z_score, closest_result = rp_helper.calculate_z_score_and_fetch_result(score, mean, sd, year)
                result.update({"z_score": z_score, "closest_result": closest_result})

            # Step 5: Fetch Factors for Closest Results
            for result in input_flow_results:
                closest_result = result.get("closest_result")
                if closest_result:
                    result_value = closest_result.get("result_value")
                    result_flow_type = closest_result.get("result_flow_type")
                    factors = rp_helper.get_factors(product_id, result_flow_type, result_value)
                    result.update({"factors": factors})

            # Step 6: Fetch Result Details for Input Flow Types
            for result in input_flow_results:
                result_flow_type = result.get("closest_result", {}).get("result_flow_type")
                if result_flow_type:
                    result_details = rp_helper.get_result_details(result_flow_type)
                    result.update({"result_details": result_details})

            return SuccessResponse(
                {"message": "Rank Predictor Workflow executed successfully.", "data": input_flow_results},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return CustomErrorResponse(
                {"message": f"Error occurred while executing rank predictor workflow: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class FaqSectionAPI(APIView):
    """
    API for fetching FAQ section for Result Predictor's input pages.
    Endpoint : api/<int:version>/rank-predictor/faqs
    Params : product_id
    """

    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):
        product_id = request.GET.get('product_id')

        if not product_id or not product_id.isdigit():
            return CustomErrorResponse(
                {"message": "product_id is required and should be an integer value"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product_id = int(product_id)

        # Fetch FAQ data using the helper
        rp_helper = RPHelper()
        faq_data = rp_helper._get_faq_section(product_id=product_id)

        if faq_data:
            response = {
                "product_id": product_id,
                "section_heading": f"{faq_data['display_name']} FAQs",
                "faqs": faq_data["faqs"],
            }
            return SuccessResponse(response, status=status.HTTP_200_OK)

        # No FAQs found for the product
        return SuccessResponse(
            {"message": f"No FAQs found for product_id {product_id}"},
            status=status.HTTP_404_NOT_FOUND,
        )
        
