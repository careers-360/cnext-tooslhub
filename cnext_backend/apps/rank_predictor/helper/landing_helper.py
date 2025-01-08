from tools.models import CPProductCampaign
from rank_predictor.models import RpFormField, RpContentSection, CnextRpCreateInputForm, CnextRpSession, CnextRpUserTracking
from wsgiref import validate
from tools.models import CPProductCampaign, CPTopCollege, UrlAlias, Exam, ProductSession
from  utils.helpers.choices import HEADER_DISPLAY_PREFERANCE, CASTE_CATEGORY, DISABILITY_CATEGORY, DIFFICULTY_LEVEL
import os
from django.utils import timezone

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
    
    def _get_product_from_alias(self , alias):

        base_url_alias = UrlAlias.objects.filter(alias=alias).first()
        split_string = base_url_alias.source.split("/")

        product_id = int(split_string[1])

        return product_id
        
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

    # def calculate_percentile(self, score, max_score):
    #     """
    #     Calculate percentile from score
    #     Formula: (score / max_score) * 100
    #     ""
    #     try:
    #         percentile = (score / max_score) * 100
    #         return round(percentile, 2)
    #     except ZeroDivisionError:
    #         raise ValueError("max_score cannot be zero.")
    #     except Exception as e:
    #         raise ValueError(f"Error calculating percentile: {str(e)}")

    # def calculate_category_rank(self, percentile, total_candidates, caste=None, disability=None, slot=None, difficulty_level=None, year=None):
    #     """
    #     Calculate the rank based on percentile
    #     Formula: rank = ((100 - percentile) / 100) * total_candidates
    #     """
    #     try:
    #         # Calculate overall rank from percentile
    #         rank = ((100 - percentile) / 100) * total_candidates
    #         rank = int(rank)

    #         # Adjust rank for category-wise considerations if provided (caste, disability, etc.)
    #         category_rank_data = {
    #             "general": rank,  # Default to overall rank for general category
    #             "obc": rank + 200,  # Example adjustment, can be based on actual data
    #             "sc": rank + 400,   # Example adjustment
    #             "st": rank + 600,   # Example adjustment
    #         }

    #         # Can adjust the rank further based on caste, disability, etc.
    #         if caste:
    #             category_rank_data["caste_rank"] = category_rank_data.get(caste.lower(), rank)
    #         if disability:
    #             category_rank_data["disability_rank"] = category_rank_data.get(disability.lower(), rank)
    #         if slot:
    #             category_rank_data["slot_rank"] = category_rank_data.get(slot.lower(), rank)
    #         if difficulty_level:
    #             category_rank_data["difficulty_level_rank"] = category_rank_data.get(difficulty_level.lower(), rank)
    #         if year:
    #             category_rank_data["year_rank"] = category_rank_data.get(year, rank)

    #         # Return rank and category-specific ranks
    #         return {
    #             "rank": rank,
    #             "category_rank": category_rank_data
    #         }

    #     except Exception as e:
    #         raise ValueError(f"Error calculating rank: {str(e)}")
