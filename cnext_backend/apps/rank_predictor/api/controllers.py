from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rank_predictor.models import CnextRpSession, CnextRpUserTracking, RpInputFlowMaster
from tools.models import CPProductCampaign
from utils.helpers.response import SuccessResponse, CustomErrorResponse
from utils.helpers.custom_permission import ApiKeyPermission
from rest_framework import status
from rank_predictor.api.helpers import InputPageStaticHelper
# from rank_predictor.helper.landing_helper import ProductHelper, RPHelper


from rank_predictor.helper.landing_helper import FeedbackHelper, ProductHelper, RPHelper, Prefill
from django.core.exceptions import ObjectDoesNotExist


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
    
    def get(self, request, version, **kwargs):
        form_id = request.GET.get('form_id')
        form_id = int(form_id)
        rp_helper = RPHelper()
        user_data = rp_helper.get_user_tracking_by_id(form_id=form_id)

        if user_data != None:
            return SuccessResponse(user_data, status=status.HTTP_200_OK)
        else:
            message = f"no user with form_id : {form_id} exists"
            return CustomErrorResponse({"message": message}, status=status.HTTP_204_NO_CONTENT)
            # SuccessResponse({response}, status=status.HTTP_204_NO_CONTENT)


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

    def get(self, request, version, *args, **kwargs):
        try:
            # Extract form_id from the request
            form_id = request.GET.get("form_id")
            if not form_id:
                return JsonResponse(
                    {"message": "form_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Retrieve flow_type using auto_increment_id (corresponding to form_id)
            try:
                user_tracking = CnextRpUserTracking.objects.get(id=form_id)
                flow_type = user_tracking.flow_type
            except ObjectDoesNotExist:
                return JsonResponse(
                    {"message": "Invalid form_id or data not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            
            # Call the appropriate method based on flow_type
            if flow_type == 3:
                return self.rank_calculation(request)
            else:
                return self.rank_predictor_workflow(request)
        
        except Exception as e:
            return JsonResponse(
                {"message": f"Error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    


    import json  # Add this import statement at the top of your script

    def rank_calculation(self, request):
        """
        Handles rank calculation for flow_type = 3.
        """
        # try:
        # Extract form_id and exam_id from the request
        form_id = request.GET.get("form_id")
        exam_id = request.GET.get("exam_id")
        
        

        # Validate and convert exam_id
        if not form_id or not exam_id:
            return CustomErrorResponse(
                {"message": "form_id and exam_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            form_id = int(form_id)
            exam_id = int(exam_id)
        except (ValueError, TypeError):
            return CustomErrorResponse(
                {"message": "Invalid data type for form_id or exam_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch category_id, disability_id, and input_fields using form_id
        try:
            user_tracking = CnextRpUserTracking.objects.get(id=form_id)
            category_id = user_tracking.category  # 'category' column exists
            disability_id = user_tracking.disability  # 'disability' column exists
            input_fields = user_tracking.input_fields  # 'input_fields' column exists
            product_id = user_tracking.product_id
            
            
            
            

            # Debugging: Log the input_fields data
            
        except ObjectDoesNotExist:
            return CustomErrorResponse(
                {"message": "Invalid form_id or data not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if input_fields is empty or None
        if not input_fields:
            return CustomErrorResponse(
                {"message": "input_fields is empty or null"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if input_fields is a list and has the expected structure
        if not isinstance(input_fields, list):
            return CustomErrorResponse(
                {"message": "input_fields is not a list"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        percentile = None
        for field in input_fields:
            if isinstance(field, dict) and field.get("input_flow_type") == 3:
                try:
                    percentile = float(field.get("value"))
                    break
                except (ValueError, TypeError):
                    return CustomErrorResponse(
                        {"message": "Invalid percentile value in input_fields"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        if percentile is None:
            return CustomErrorResponse(
                {"message": "Percentile value not found in input_fields"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set default values for category_id and disability_id if they are null or blank
        if not category_id:  # If category_id is None or blank
            category_id = 2  # Default to "General"
        if not disability_id:  # If disability_id is None or blank
            disability_id = 2  # Default to "N.A."

        # Call RPHelper to calculate rank
        rp_helper = RPHelper()
        rank_data = rp_helper.calculate_rank(
            exam_id=exam_id,
            percentile=percentile,
            category_id=category_id,
            disability_id=disability_id,
            product_id=product_id,
        )
        product_name = CPProductCampaign.objects.filter(id=product_id).values('name').first()
        # Format the response data
        formatted_data = {
            "message": "Rank Predictor Percentile to Rank Work flow.",
            "result_details": "Overall CRL Rank",
            "Product_id": product_id,
            "product_name": product_name,
            "exam_id": exam_id,
            "percentile": percentile,
            "rank_data": rank_data.get("data"),
        }

        return SuccessResponse(
            
            formatted_data,
            status=status.HTTP_200_OK,
        )

       
    
    
    def transform_data(self,input_data):
        output = []

        def parse_data(entry, primary=True):
            caste_mapping = {1: "General", 2: "OBC", 3: "SC/ST"}
            disability_mapping = {1: "PWD", 2: "N.A."}
            
            combination = entry.get("combination", {})
            factors = entry.get("factors", {})
            result_details = entry.get("result_details", {})

            output_entry = {
                "category": caste_mapping.get(combination.get("caste"), "General"),
                "max_rank": factors.get("max_range", None),
                "min_rank": factors.get("min_range", None),
                "disability": disability_mapping.get(combination.get("disability"), "N.A."),
                "classification": "Good" if entry.get("z_score", 0) >= 0 else "Average",
                "result_value": entry.get("result_value", None),
                "primary": primary,
                "result_type": result_details.get("result_type", None),
                "result_flow_type": result_details.get("result_flow_type", None),
                "result_process_type": result_details.get("result_process_type", None)
            }

            output.append(output_entry)

        # Process primary data
        for item in input_data.get("primary", {}).get("data", []):
            parse_data(item, primary=True)

        # Process secondary data
        for secondary_group in input_data.get("secondary", []):
            for item in secondary_group.get("data", []):
                parse_data(item, primary=False)

        return output


    def rank_predictor_workflow(self, request):
        """
        Handles the rank predictor workflow for other flow types.
        """
        
        # data = RpInputFlowMaster.objects.filter(id=5).values_list('id', 'input_flow_type','input_type', 'input_process_type').first()
        try:
            # Extract form_id from the request
            form_id = request.GET.get("form_id")
            
            if not form_id:
                return CustomErrorResponse(
                    {"message": "form_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                form_id = int(form_id)
            except (ValueError, TypeError):
                return CustomErrorResponse(
                    {"message": "Invalid data type for form_id"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        
        
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

            # record_id = 13

            # Fetch user_tracking data (assuming this part is working as per your original code)
            user_tracking = (
                CnextRpUserTracking.objects.filter(id=form_id)
                .values("product_id", "category", "disability", "input_fields", "additional_info", "exam_session")
                .first()
            )
            
            # Extract the slot information from additional_info
            additional_info = user_tracking.get("additional_info", [])
            record_id = user_tracking["exam_session"] if user_tracking else None
            exam_shift = CnextRpSession.objects.filter(id=record_id).values('session_date').first()
            
            slot = None  # Initialize slot as None by default

            if "Enter Slot" in additional_info:
                slot = additional_info["Enter Slot"].get("id")
            
           
            
            
            final_result_list = []

            # Get input fields from user_tracking
            for item in user_tracking.get("input_fields", []):
                score = item.get('value')
                input_flow_type = item.get('input_flow_type')
                
               

                
                rp_flow = RpInputFlowMaster.objects.filter(id=input_flow_type).values('id', 'input_flow_type','input_type', 'input_process_type').first()
            
                if rp_flow:
                    rp_flow_type = rp_flow['input_flow_type']
                    rp_flow_input_type = rp_flow['input_type']
                    rp_flow_input_process_type = rp_flow['input_process_type']
                    
                    user_input = {}
                    user_input["input_flow_type"] = rp_flow_type
                    user_input["input_type"] = rp_flow_input_type
                    user_input["input_process_type"] = rp_flow_input_process_type
                    user_input["score"] = score
           
                product_id = user_tracking.get('product_id')
                
                product_name = CPProductCampaign.objects.filter(id=product_id).values('name').first()
                disclaimer = CPProductCampaign.objects.filter(id=product_id).values('disclaimer').first()
               
                caste = user_tracking.get('category')
                disability = user_tracking.get('disability')


                # Validate score
                if not score or not score.isdigit():
                    return CustomErrorResponse(
                        {"message": "score is required and must be an integer"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                score = float(score)

                # Initialize RPHelper
                rp_helper = RPHelper()

                # Fetch session data using previously set product_id and record_id
                session_data = rp_helper.get_session_data(product_id, record_id)
            

                if not session_data:
                    return SuccessResponse(
                        f"No session data found for product_id {product_id} and id {record_id}",
                        status=status.HTTP_404_NOT_FOUND
                    )

                difficulty = session_data["difficulty"]
                year = session_data["year"]

                # Ensure input_flow_type is provided
                if not input_flow_type:
                    return SuccessResponse(
                        {"message": "No input flow type provided by the user."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Process Input Flow Types to Fetch Mean and SD
                mean, sd = rp_helper.get_mean_sd(product_id, year, input_flow_type)
                
                if not mean or not sd:

                    continue  # Skip to the next input_flow_type
                result = {
                    "input_flow_type": input_flow_type,
                    "mean": mean,
                    "sd": sd
                }
                

                # Calculate Z-Score and Fetch Closest Results
                z_score, closest_result = rp_helper.calculate_z_score_and_fetch_result(
                    score, mean, sd, year, caste, disability, product_id, difficulty, input_flow_type, slot
                )
                result.update({"z_score": z_score, "closest_result": closest_result})

                # Initialize the result list
                result_list = []
                no_results_found = []

                try:
                    # Iterate over the closest_result
                    for closest_item in closest_result:
                        closest_result_data = closest_item.get("closest_result")
                        
                        if not closest_result_data:
                            no_results_found.append({
                                "combination": closest_item.get("combination"),
                                "message": "No result details found for this combination"
                            })
                            continue  # Skip to the next closest_item
                        
                        # Check if closest_result_data exists
                        if closest_result_data:
                            try:
                                result_value = closest_result_data.get("result_value")
                                result_flow_type = closest_result_data.get("result_flow_type")

                                # Fetch the factors for the current combination
                                factors = rp_helper.get_factors(product_id, result_flow_type, result_value)

                                # Prepare the result for this combination
                                combination = closest_item.get("combination")
                                # print("combination", combination)
                                result_combination = {
                                    "combination": combination,
                                    "z_score": closest_result_data.get("z_score"),
                                    "result_value": result_value,
                                    "factors": factors
                                }

                                # Fetch result details
                                result_details = rp_helper.get_result_details(result_flow_type)
                                
                                if not result_details:
                                    no_results_found.append({
                                        "combination": closest_item.get("combination"),
                                        "message": "No result details found for this combination"
                                    })
                                    continue  # Skip to the next closest_item
                                
                                
                                if result_details:
                                    result_combination["result_details"] = result_details
                                    
                             
                                
                                # Append the combination to the result list
                                result_list.append(result_combination)
                                
                                DIFFICULTY_LEVEL = {
                                    1: "Easy",
                                    2: "Moderately Easy",
                                    3: "Moderate",
                                    4: "Moderately Difficult",
                                    5: "Difficult"
                                }

                                # Function to replace difficulty_level ID with its value
                                def replace_difficulty_level(result_list):
                                    for result in result_list:
                                        if 'combination' in result and 'difficulty_level' in result['combination']:
                                            difficulty_id = result['combination']['difficulty_level']
                                            if difficulty_id in DIFFICULTY_LEVEL:
                                                result['combination']['difficulty_level'] = DIFFICULTY_LEVEL[difficulty_id]
                                    return result_list
                                
                                result_list = replace_difficulty_level(result_list)
                                    
                                if rp_flow:
                                    rp_flow_type = rp_flow['input_flow_type']
                                

                                    result_list.append(user_input)
                                    
                            except Exception as e:
                                print(f"Error processing closest_item {closest_item}: {e}")
                                # Add this combination to no_results_found list in case of error
                                no_results_found.append({
                                    "combination": closest_item.get("combination"),
                                    "message": f"Error processing this combination: {e}"
                                })
                                
                        if not closest_result:
                            continue
                        
                        # Append the result for this input_flow_type to the final result list

                except Exception as e:
                    print(f"Error processing closest_result: {e}")
                    no_results_found.append({
                        "message": f"Error processing closest_result: {e}"
                    })
                    
                final_result_list.append({
                    
                    "data": result_list,
                })

                # Return the final response with the result list and no_results_found
            # print("final_results+++++++", final_result_list)
            primary = final_result_list[0]["data"][0] if final_result_list else None
            secondary = final_result_list[1:] if len(final_result_list) > 1 else []   
            response_data = {
                        "product_name": product_name,
                        "primary": primary,
                        "secondary": secondary,
                        "disclaimer": disclaimer,

                        }
            
            data_prepare = self.transform_data(response_data) 


            return Response(
                {
                    "result": True,
                    "message": "Rank Predictor Score to Percentile Work flow.",
                    "data": {
                        "exam_shift": exam_shift,
                        "product_name": product_name,
                        "primary": primary,
                        "secondary": secondary,
                        "disclaimer": disclaimer,

                        }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            # Handle unexpected exceptions
            return CustomErrorResponse(
                {"message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        


class ProductDetailsAPI(APIView):
    """
    API for fetching product details from CPProductCampaign table.
    Endpoint: api/<int:version>/product/details
    Params: product_id
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

        # Fetch product details using helper function
        product_helper = ProductHelper()
        product_data = product_helper.get_product_details(product_id=product_id)

        if product_data:
            return SuccessResponse(product_data, status=status.HTTP_200_OK)

        # No data found for the product
        return SuccessResponse(
            {"message": f"No details found for product_id {product_id}"},
            status=status.HTTP_404_NOT_FOUND,
        )


class PrefillProductsAPI(APIView):
    """
    API for fetching top colleges related to an exam.
    Endpoint: api/<int:version>/rank-predictor/pre-fill
    Params: product_id
    """
    permission_classes = [ApiKeyPermission]
    def get(self, request, version, **kwargs):
        product_id = request.GET.get('product_id')
        exam_id = request.GET.get('exam_id')
        if not product_id or not product_id.isdigit():
            return CustomErrorResponse(
                {"message": "product_id is required and should be an integer value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        product_id = int(product_id)
        # Fetch colleges from the database
        prefill_helper = Prefill()
        prefill_response = prefill_helper.get_prefill_fields(product_id=product_id, exam_id=exam_id)

        return SuccessResponse(prefill_response, status=status.HTTP_200_OK)



class FeedbackSubmitAPI(APIView):
    """
    API for submitting feedback.
    Endpoint : api/<int:version>/rank-predictor/feedback
    Method : POST
    Payload : {
        "is_moderated": bool,
        "feedback_type": "actual" or "custom",
        "exam_id": str,
        "counselling_id": str,
        "product_id": str,
        "response_type": str,
        "complement": str,
        "msg": str,
        "device": str,
        "created_by": int,
        "updated_by": int (optional),
        "session_id": int,
        "gd_chance_count": int,
        "tf_chance_count": int,
        "maybe_chance_count": int,
        "counselling_change": int,
        "user_type": str,
        "user_name": str,
        "user_image": str,
        "custom_feedback": str
    }
    """

    permission_classes = [ApiKeyPermission]

    def post(self, request, version, **kwargs):
        data = request.data

        # Required fields for validation
        required_fields = [
            "feedback_type", "exam_id", "counselling_id", "product_id", "response_type", 
            "msg", "created_by", "session_id", "gd_chance_count", "tf_chance_count", 
            "maybe_chance_count", "counselling_change", "user_type"
        ]

        # Check for missing fields
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return CustomErrorResponse(
                {"message": f"Missing fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Ensure fields have correct data types
            data["is_moderated"] = bool(data.get("is_moderated", False))
            data["gd_chance_count"] = int(data["gd_chance_count"])
            data["tf_chance_count"] = int(data["tf_chance_count"])
            data["maybe_chance_count"] = int(data["maybe_chance_count"])
            data["counselling_change"] = int(data["counselling_change"])
            data["session_id"] = int(data["session_id"])
        except ValueError:
            return CustomErrorResponse(
                {"message": "Integer fields must contain valid integer values."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save feedback data
        try:
            rp_helper = RPHelper()
            feedback_instance = rp_helper._save_feedback(data)  # assuming _save_feedback returns the saved instance
        except Exception as e:
            return CustomErrorResponse(
                {"message": f"An error occurred while saving feedback: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Returning saved feedback data including the id
        response_data = {
            "id": feedback_instance.id,  # id is the primary key in your model
            "feedback_type": data["feedback_type"],
            "exam_id": data["exam_id"],
            "counselling_id": data["counselling_id"],
            "product_id": data["product_id"],
            "response_type": data["response_type"],
            "complement": data.get("complement"),
            "msg": data["msg"],
            "device": data.get("device"),
            "created_by": data["created_by"],
            "updated_by": data.get("updated_by"),
            "session_id": data["session_id"],
            "gd_chance_count": data["gd_chance_count"],
            "tf_chance_count": data["tf_chance_count"],
            "maybe_chance_count": data["maybe_chance_count"],
            "counselling_change": data["counselling_change"],
            "user_type": data["user_type"],
            "user_name": data.get("user_name"),
            "user_image": data.get("user_image"),
            "custom_feedback": data.get("custom_feedback"),
        }

        return SuccessResponse(
            {"message": "Feedback submitted successfully.", "feedback_data": response_data},
            status=status.HTTP_201_CREATED
        )

        

class FeedbackAPI(APIView):
    """
    API for fetching feedbacks from cp_feedback table.
    Endpoint: api/<int:version>/feedback
    Params: product_id, page
    """

    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):
        product_id = request.GET.get('product_id')
        page = int(request.GET.get('page', 1))

        if not product_id:
            return Response(
                {
                    "result": False,
                    "message": "product_id is required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch feedback data using helper function
        feedback_helper = FeedbackHelper()
        feedbacks = feedback_helper.get_feedbacks(product_id=product_id)

        if feedbacks:
            # Paginate feedbacks
            page_size = 10
            start = (page - 1) * page_size
            end = start + page_size
            paginated_feedbacks = feedbacks[start:end]

            return Response(
                {
                    "result": True,
                    "feedbacks": paginated_feedbacks
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "result": True,
                "feedbacks": []
            },
            status=status.HTTP_200_OK,
        )

class CasteDisabilityAPI(APIView):
    """
    API for Content Section on Result Page
    Endpoint : api/<int:version>/rank-predictor/cast-disability
    Params : product_id
    Params : exam_id
    Params : flow_id
    """


    permission_classes = [ApiKeyPermission]

    def get(self, request, version, **kwargs):

        product_id = request.GET.get('product_id')
        exam_id = request.GET.get('exam_id')
        flow_id = request.GET.get('flow_id')
        
        rp_helper = RPHelper()
        
        if product_id:
            product_id = int(product_id)
            cast_disabilitys = rp_helper._get_cast_disability_mappings(product_id=product_id, exam_id=exam_id, flow_id=flow_id)
        
        flow_id = int(flow_id)

        # Fetch content from database and return it to client.
        
        cast_disabilitys = rp_helper._get_cast_disability_mappings(product_id=product_id, exam_id=exam_id, flow_id=flow_id)

        return SuccessResponse(cast_disabilitys, status=status.HTTP_200_OK)