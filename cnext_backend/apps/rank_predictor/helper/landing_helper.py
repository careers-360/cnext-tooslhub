from venv import logger
from tools.models import CPFeedback, CPProductCampaign, ToolsFAQ
from rank_predictor.models import CnextRpVariationFactor, RPStudentAppeared, RpFormField, RpContentSection, CnextRpCreateInputForm, CnextRpSession, CnextRpUserTracking, RpMeanSd, RpMeritList, RpResultFlowMaster
from wsgiref import validate
from tools.models import CPProductCampaign, CPTopCollege, UrlAlias, Exam, ProductSession
from  utils.helpers.choices import HEADER_DISPLAY_PREFERANCE, CASTE_CATEGORY, DISABILITY_CATEGORY, DIFFICULTY_LEVEL
import os
from django.utils import timezone


class CombinationFactory:
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
        2: "N.A.",  # No disability
        3: "PHV",
        4: "PHH",
        5: "PHO",
        6: "CA",
        7: "TP",
        8: "PH1",
        9: "PH2",
        10: "PH-AI"
    }

    @staticmethod
    def get_key_by_value(mapping, value):
        """Fetch the key corresponding to the given value in a dictionary."""
        # logging.debug(f"Searching for value: {value} in mapping: {mapping}")
        for key, val in mapping.items():
            if val.lower() == value.lower():
                return key
        raise ValueError(f"{value} not found in the mapping.")

    @staticmethod
    def generate_combinations(category_name, disability_name):
        """Generate category and disability combinations dynamically."""
        combinations = []
        

        # Interpret inputs as None for General or N.A.
        category_id = (
            None if category_name and category_name.lower() == "general" 
            else CombinationFactory.get_key_by_value(CombinationFactory.CATEGORY_MAP, category_name)
        )

        disability_id = (
            None if disability_name and disability_name.lower() == "n.a."
            else CombinationFactory.get_key_by_value(CombinationFactory.DISABILITY_MAP, disability_name)
        )

        # Generate combinations based on the logic
        if category_id is not None and disability_id is not None:
            combinations.append({"caste": 2, "disability": 2})  # General + N.A
            combinations.append({"caste": 2, "disability": disability_id})  # General + selected disability
            combinations.append({"caste": category_id, "disability": 2})  # Specific category + N.A
            combinations.append({"caste": category_id, "disability": disability_id})  # Specific category + selected disability
        elif category_id is None and disability_id is not None:
            combinations.append({"caste": 2, "disability": 2})  # General + N.A
            combinations.append({"caste": 2, "disability": disability_id})  # General + selected disability
        elif category_id is not None and disability_id is None:
            combinations.append({"caste": 2, "disability": 2})  # General + N.A
            combinations.append({"caste": category_id, "disability": 2})  # Specific category + N.A
        elif category_id is None and disability_id is None:
            combinations.append({"caste": 2, "disability": 2})  # General + N.A

        return combinations


class RPHelper:

    def __init__(self):
        self.base_image_url = os.getenv("CAREERS_BASE_IMAGES_URL","https://cnextassets.careers360.de/media_tools/")
        self.exam_logo_base_url = os.getenv("CAREERS_EXAM_BASE_IMAGES_URL", "https://cache.careers360.mobi/media/presets/45X45/")
        pass

    def parse_choice(self, data_dic=dict)->list:
        datalist = []
        for key , value in data_dic.items():
            print(f"Key: {key}, Value: {value}")
            datalist.append({"id": key, "value": value})

        return datalist

    def _get_header_section(self, product_id=None, alias=None):

        if alias != None:
            product_id = self._get_product_from_alias(alias=alias)


        header_data = CPProductCampaign.objects.filter(id=product_id).values("id", "header_section", "custom_exam_name", "custom_flow_type", "custom_year", "video", "usage_count_matrix", "positive_feedback_percentage", "display_preference", "gif", "secondary_image", 'image', 'exam_other_content')
        # print(header_data['result'])

        header_data_list = list(header_data)

        for data in header_data_list:

            removable_fields = {key: value for key, value in HEADER_DISPLAY_PREFERANCE.items() if key != data.get('display_preference')}
            # print(removable_fields)

            for k in removable_fields:
                data.pop(HEADER_DISPLAY_PREFERANCE.get(k), None)

        return header_data
    
    def _get_form_section(self, product_id=None, alias=None):

        if alias != None:
            product_id = self._get_product_from_alias(alias=alias)

        # flow_type_count = RpFormField.objects.filter(product_id=product_id, status=1, mapped_process_type__isnull=False).values('mapped_process_type').distinct().count()

        SHIFTS = [
        {"id": shift.get("session_shift"), "value": shift.get("session_shift")}
        for shift in CnextRpSession.objects.filter(product_id=product_id).values('session_shift').distinct()
        ]

        input_form_mapping = CnextRpCreateInputForm.objects.filter(product_id=product_id).values('input_process_type', 'process_type_toggle_label', 'submit_cta_name')

        input_process_type_mapping = {}
        input_process_type_list = []

        # fetch cta submit button once
        for process_type in input_form_mapping:
            input_process_type_mapping[process_type['input_process_type']] = {
                'process_type_toggle_label': process_type['process_type_toggle_label'],
                'submit_cta_name': process_type['submit_cta_name']
        }
            input_process_type_list.append(input_process_type_mapping)
        
        # print(f"process type mapping {input_process_type_mapping}")

        form_data = RpFormField.objects.filter(product_id=product_id, status=1).values("field_type", "input_flow_type", "display_name", "place_holder_text", "error_message", "weight", "mapped_process_type", "mandatory", "mapped_category", "status", 'min_val', 'max_val', 'list_option_data').order_by('weight')

        modified_form_data_list = []

        for fdata in form_data.values():
            # print(f"form data list {type(fdata)}")
            if fdata['list_option_data'] is not None:
                fdata['list_option_data'] = [{"id": sp.split("|")[0], "val": sp.split("|")[1]} for sp in fdata['list_option_data'].split(",")]
            modified_form_data_list.append(fdata)

        with_appended_cta = {'form_data': modified_form_data_list, 'input_process_type_mapping': input_process_type_mapping , 'cast_category': CASTE_CATEGORY, 'disability_category': DISABILITY_CATEGORY, 'dificulty_level': self.parse_choice(DIFFICULTY_LEVEL), 'sessions': SHIFTS}

        return with_appended_cta
    
    def _get_top_colleges(self, exam_id=None):
        """
        Fetch top colleges related to a specific exam ID.
        """
        return CPTopCollege.objects.filter(exam_id=exam_id, status=1).values(
            "id",
            "exam_id",
            "college_id",
            "college_name",
            "college_short_name",
            "college_url",
            "review_count",
            "aggregate_rating",
            "course_id",
            "course_name",
            "course_url",
            "final_cutoff",
            "rank_type",
            "process_type",
            "submenu_data"
        )
    
    def _get_content_section(self, product_id=None):

        """
        Fetch content for the product
        """

        content_response = []

        content_list = RpContentSection.objects.filter(product_id=product_id).values("heading", "content", "image_web", "image_wap")
        
        # print(content_list)

        for content in content_list:
            content['image_web'] = self.base_image_url+content.get('image_web', None)
            content['image_wap'] = self.base_image_url+content.get('image_wap', None)
            content_response.append(content)

        return content_response
    
    def _get_product__exam_from_alias(self , alias):

        base_url_alias = UrlAlias.objects.filter(alias=alias).first()
        split_string = base_url_alias.source.split("/")

        product_id = int(split_string[1])

        exam_dict = CPProductCampaign.objects.filter(id=product_id).values("exam").first()

        # print(f"exam dictionary {exam_dict.get('exam')}")

        return { "product_id": product_id, "exam_id": exam_dict.get("exam", "")}
        
    def _related_products(self, product_id=None, alias=None):

        if alias != None:
            product_id = self._get_product_from_alias(alias=alias)

        exam_dict = CPProductCampaign.objects.filter(id=product_id).values("exam").first()
        
        exam_domain_education_level = Exam.objects.filter(id=exam_dict['exam']).values('domain_id', 'preferred_education_level_id').first()

        exam_ids_and_logos = Exam.objects.filter(domain_id=exam_domain_education_level['domain_id'], preferred_education_level_id=exam_domain_education_level['preferred_education_level_id'])[:4].values('id', 'ecb_logo')

        # print(f"exam ids {exam_ids_and_logos} type {type(exam_ids_and_logos)} value {[exam['id'] for exam in exam_ids_and_logos]}")
        exam_logo_mapping = {}

        for exam in exam_ids_and_logos:
            exam_logo_mapping[exam['id']] = exam['ecb_logo']

        # print(f"exam mapping {exam_logo_mapping}")

        exam_list = [exam['id'] for exam in exam_ids_and_logos]
        product_list = []

        for exam_id in exam_list:
            # print(f"data {exam_id}")
            product = CPProductCampaign.objects.filter(exam=exam_id).values("id", "exam", "custom_exam_name", "custom_flow_type", "custom_year").first()
            # print(f"product data {product}")

            if product != None:
                product['logo'] = self.exam_logo_base_url+exam_logo_mapping.get(product['exam'], '')

            # print(f"product data {product}")
            product_list.append(product)

        return product_list
    
    def _user_tracking(self, product_id=None, alias=None,**kwargs):

        user_data = kwargs.get('user_data', {})
        
        id = user_data.get('id', None)
        login_status = user_data.get('login_status', None)

        if id is not None:
            CnextRpUserTracking.objects.filter(id=id).update(login_status=login_status)
            return id
        
        else:
            product_session_id = ProductSession.objects.filter(product_id=int(user_data['product_id'])).values('id').last()
            user_tracking = CnextRpUserTracking(
                device_type=user_data.get('device_type', None),
                product_id=user_data.get('product_id', None),
                input_flow_type=user_data.get('input_flow_type', None),
                flow_type=user_data.get('flow_type', None),
                login_status=user_data.get('login_status', None),
                uid=user_data.get('uid', None),
                uuid=user_data.get('uuid', None),
                category=user_data.get('category', None),
                disability=user_data.get('disability', None),
                application=user_data.get('application', None),
                dob=user_data.get('dob', None),
                exam_session=user_data.get('exam_session', None),
                tool_session_id=product_session_id.get('id', None),
                input_fields=user_data.get('input_fields', None),
                result_predictions=user_data.get('result_predictions', None),
                additional_info=user_data.get('additional_info', None)
            )
            user_tracking.save()
            return user_tracking.id

    def calculate_rank(self, exam_id, percentile, category_id=None, disability_id=None):
        """
        Calculate ranks for the given combination of category and disability according to specific rules.
        :param exam_id: ID of the exam
        :param percentile: User's percentile
        :param category_id: User's category ID (integer, optional)
        :param disability_id: User's disability ID (integer, optional)
        :return: List of ranks for selected combinations
        """
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
            1: "PWD",
            2: "N.A.",
            3: "PHV",
            4: "PHH",
            5: "PHO",
            6: "CA",
            7: "TP",
            8: "PH1",
            9: "PH2",
            10: "PH-AI"
        }


        get_cast = self.get_caste_by_id(category_id)
        get_disability_id = self.get_disability_by_id(disability_id)


        user_category = get_cast['name']  
        user_disability = get_disability_id["name"]  

        combinations = CombinationFactory.generate_combinations(user_category, user_disability)

        results = []

        for combination in combinations:
            try:
                category = combination.get("caste")
                disability = combination.get("disability")

                # Fetch candidates data from the database
                candidates_data = RPStudentAppeared.objects.filter(
                    exam_id=exam_id,
                    category=category,
                    disability=disability,
                ).values("min_student", "max_student").first()
                

                if not candidates_data:
                    results.append({
                        "category": category,
                        "disability": disability,
                        "rank": None,
                        "appeared_candidates": None,
                        "classification": None,
                        "message": "No data found for this combination"
                    })
                    continue

                # Calculate rank
                appeared_candidates = candidates_data["max_student"]
                rank = (100 - percentile) * (appeared_candidates / 100)
                
                appeared_candidates = candidates_data["min_student"]
                rank2 = (100 - percentile) * (appeared_candidates / 100)

                # Classify the result based on percentile
                if percentile >= 90:
                    classification = "Excellent"
                elif 85 <= percentile < 90:
                    classification = "Good"
                elif 75 <= percentile < 85:
                    classification = "Bad"
                else:
                    classification = "Very Bad"

                results.append({
                    "category": CATEGORY_MAP.get(category, "Unknown"),
                    "disability": DISABILITY_MAP.get(disability, "Unknown"),
                    "max_rank": round(rank, 2),
                    "min_rank": round(rank2, 2),
                    "appeared_candidates": appeared_candidates,
                    "classification": classification
                })
            except Exception as e:
                results.append({
                    "category": "Unknown",
                    "disability": "Unknown",
                    "rank": None,
                    "appeared_candidates": None,
                    "classification": None,
                    "message": f"Error: {str(e)}"
                })

        return {
            "result": True,
            "data": results
        }

    
     
    """
    Helper class to fetch and process data related to Rank Predictor functionality.
    """
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


    
    
    def get_caste_by_id(self, caste_id):
        """Fetch caste by ID from CATEGORY_MAP."""
        try:
            caste_id = int(caste_id)  
        except ValueError:
            return {"id": caste_id, "name": "Invalid ID"}
        return {"id": caste_id, "name": self.CATEGORY_MAP.get(caste_id, "Unknown")}

  
    
    def get_disability_by_id(self, disability_id):
        """Fetch disability by ID from DISABILITY_MAP."""
        try:
            disability_id = int(disability_id)  
        except ValueError:
            return {"id": disability_id, "name": "Invalid ID"}
        return {"id": disability_id, "name": self.DISABILITY_MAP.get(disability_id, "Unknown")}

        

    def get_session_data(self, product_id, record_id):
        """Fetch data from CnextRpSession table."""
        return CnextRpSession.objects.filter(product_id=product_id, id=record_id).values(
        "difficulty",  # This is the correct field for CnextRpSession
        "year", 
        
        ).first()
        
 
 
    def get_input_flow_type(self, caste_id, disability_id, slot, difficulty_level, year):
        """Fetch input_flow_type from RpMeritList table."""
        query = {
            "difficulty_level": difficulty_level,  # Correct field for RpMeritList
            "year": year,
            "product_id": 39,
        }

        results = []
        result2 = []



        get_cast = self.get_caste_by_id(caste_id)
        get_disability_id = self.get_disability_by_id(disability_id)



        user_category = get_cast['name']  # User-provided category name
        user_disability = get_disability_id["name"]  # User-provided disability name

 

        combinations = CombinationFactory.generate_combinations(user_category, user_disability)

        # Loop over the combinations
        for combination in combinations:
            # Start with the base query
            temp_query = query.copy()  # Create a copy of the base query
            
            # Add current combination to the query dictionary
            temp_query.update(combination)

            # Filter data from RpMeritList
            result = RpMeritList.objects.filter(**temp_query).values("input_flow_type").first()

            # Output the result of the filter

            if result:  # Ensure result is not None
                input_flow_type = result["input_flow_type"]
                
                # Update the query with the result (if needed) and store it for later use
                temp_query['input_flow_type'] = input_flow_type

                # Store the result in the result2 list
                result2.append({
                    "combination": temp_query
                })

            
        # Return or print the accumulated results
        return result2



    def get_mean_sd(self,product_id, year, input_flow_type):
        """Fetch mean and sd from RpMeanSd table."""
        record = RpMeanSd.objects.filter(
            product_id=product_id, year=year, input_flow_type=input_flow_type
        ).values("admin_mean", "admin_sd", "sheet_mean", "sheet_sd").first()
        
        

        if not record:
            return None, None

        mean = record['admin_mean'] if record['admin_mean'] is not None else record['sheet_mean']
        sd = record['admin_sd'] if record['admin_sd'] is not None else record['sheet_sd']
        return mean, sd


        


    def calculate_z_score_and_fetch_result(self,score, mean, sd, year):
        """Calculate Z-Score and fetch the closest result details."""
        if mean is None or sd is None or sd == 0:  # Handle missing or invalid data
            print("Invalid mean or standard deviation. Skipping calculation.")
            return None, None

        z_score = (score - mean) / sd

        # Fetch all records for the specified year
        result_data = RpMeritList.objects.filter(year=year).values(
            "z_score", "result_flow_type", "result_value"
        )

        if not result_data:
            print("No results found for the specified year.")
            return z_score, None

        # Find the closest z_score
        closest_result = min(
            result_data,
            key=lambda result: abs(float(result["z_score"]) - z_score)  # Convert Decimal to float
        )

        return z_score, closest_result


       

    def get_factors(self,product_id, result_flow_type, result_value):
        """Fetch factors from CnextRpVariationFactor table."""
        factor = CnextRpVariationFactor.objects.filter(
            product_id=product_id,
            result_flow_type=result_flow_type,
            lower_val__lte=result_value,
            upper_val__gte=result_value
        ).values("min_factor", "max_factor").first()

        if not factor:
            print(f"No factors found for result_value {result_value} and result_flow_type {result_flow_type}")
            return None

        min_factor = factor['min_factor']
        max_factor = factor['max_factor']

        return {
            "min_range": result_value - min_factor,
            "max_range": result_value + max_factor
        }


        
    def get_result_details(self,input_flow_type):
        """Fetch result details from RpResultFlowMaster table using input_flow_type."""
        result_details = RpResultFlowMaster.objects.filter(id=input_flow_type).values(
            "result_flow_type", "result_type", "result_process_type"
        ).first()
        return result_details
    
    
    def _get_faq_section(self, product_id=None):
        """
        Fetch the FAQ section data for a specific product.

        :param product_id: ID of the product
        :return: A dictionary containing display name and FAQs
        """
        if not product_id:
            return None

        # Fetch FAQs for the given product_id
        faqs = ToolsFAQ.objects.filter(product_id=product_id, status=True).order_by("created")
        if not faqs.exists():
            return None

        # Placeholder for display name logic (replace with actual implementation)
        display_name = self._get_predictor_display_name(product_id)

        # Format the FAQs
        faq_list = [
            {"question": faq.question, "answer": faq.answer}
            for faq in faqs
        ]

        return {
            "display_name": display_name,
            "faqs": faq_list,
        }

    def _get_predictor_display_name(self, product_id):
        """
        Fetch the display name for the predictor (placeholder function).

        Replace this with actual logic to fetch the predictor's display name.
        """
        return "Predictor Name"
    
    
    def _save_feedback(self, feedback_data):
        """
        Save feedback data to the cp_feedback table.

        :param feedback_data: Dictionary containing feedback data
        """
        feedback_record = {
            "is_moderated": feedback_data["is_moderated"],
            "feedback_type": feedback_data["feedback_type"],
            "exam_id": feedback_data["exam_id"],
            "counselling_id": feedback_data["counselling_id"],
            "product_id": feedback_data["product_id"],
            "response_type": feedback_data["response_type"],
            "complement": feedback_data.get("complement"),
            "msg": feedback_data["msg"],
            "device": feedback_data.get("device"),
            "created_by": feedback_data["created_by"],
            "updated_by": feedback_data.get("updated_by"),
            "session_id": feedback_data["session_id"],
            "gd_chance_count": feedback_data["gd_chance_count"],
            "tf_chance_count": feedback_data["tf_chance_count"],
            "maybe_chance_count": feedback_data["maybe_chance_count"],
            "counselling_change": feedback_data["counselling_change"],
            "user_type": feedback_data["user_type"],
            "user_name": feedback_data.get("user_name"),
            "user_image": feedback_data.get("user_image"),
            "custom_feedback": feedback_data.get("custom_feedback"),
        }
        # CPFeedback.objects.create(**feedback_record)
        
        feedback_instance = CPFeedback.objects.create(**feedback_record)
        return feedback_instance  # Ensure this is returned to prevent 'NoneType' error.



    
class ProductHelper:
    def get_product_details(self, product_id=None):
        """
        Fetch product details for a specific product ID from CPProductCampaign table.

        :param product_id: ID of the product
        :return: A dictionary containing product details
        """
        if not product_id:
            return None

        # Fetch product details
        try:
            product = CPProductCampaign.objects.filter(id=product_id).values(
                # "header_section",
                # "disclaimer",
                "cp_cta_name",
                "cp_destination_url",
                "cp_pitch",
                "mapped_product_title",
                "mapped_product_cta_label",
                "mapped_product_destination_url",
                "mapped_product_pitch",
                "promotion_banner_web",
                "promotion_banner_wap",
                "banner_destination",
            ).first()

            if product:
                return product
            return None

        except Exception as e:
            logger.error(f"Error fetching product details: {e}")
            return None

