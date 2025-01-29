import csv
import requests
import io
import threading
import time
from collections import defaultdict
from math import sqrt
from django.utils.timezone import now
from django.conf import settings
from django.db.models import Max,F, Q, Count
from datetime import datetime, timedelta, date
from utils.helpers.choices import CASTE_CATEGORY, DIFFICULTY_LEVEL, DISABILITY_CATEGORY, FACTOR_TYPE, FORM_INPUT_PROCESS_TYPE, INPUT_TYPE, MAPPED_CATEGORY, RESULT_PROCESS_TYPE, RESULT_TYPE, RP_FIELD_TYPE, STUDENT_TYPE, FIELD_TYPE, TOOL_TYPE
from rank_predictor.models import CnextRpCreateInputForm, RpContentSection, RpFormField, RpInputFlowMaster, RpMeritList, RpMeritSheet,\
      RpResultFlowMaster, CnextRpSession, CnextRpVariationFactor, RpMeanSd, RPStudentAppeared, CnextRpUserTracking
from tools.models import CPProductCampaign, CasteCategory, CollegeCourse, CPFeedback, DisabilityCategory, Domain, Exam, UserGroups
from .static_mappings import RP_DEFAULT_FEEDBACK
from users.models import User
from rest_framework.pagination import PageNumberPagination
import chardet


class CustomPaginator(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return {
            'to_graph':False,
            'lastPage': self.page.paginator.num_pages,
            'itemsOnPage': self.page_size,
            'current': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'totalRows': self.page.paginator.count,
            'results': data
        }




class InputPageStaticHelper:

    def __init__(self):
        pass

    def _get_content_section(self, product_id=None):
        # Fetch content section from database based on rp_id
        content_data = []

        if not product_id:
            return content_data
        
        content_data = list(RpContentSection.objects.filter(product_id=product_id, status=1).values("id", "product_id", "heading", "content", "image_web", "image_wap", "updated"))
        for content in content_data:
            content["image_web"] = f"{settings.CAREERS_BASE_IMAGES_URL}{content.get('image_web')}"
            content["image_wap"] = f"{settings.CAREERS_BASE_IMAGES_URL}{content.get('image_wap')}"

        return content_data
    
    def _get_faq_section(self, product_id=None):
        # Fetch faq section from database based on rp_id
        faq_data = []

        if not product_id:
            return faq_data
        
        # FAQ table needs to be created and implemeted
        faq_data = list(RpContentSection.objects.filter(product_id=product_id, status=1).values("id", "product_id", "heading", "content", "image_web", "image_wap", "updated"))
        for faq_ in faq_data:
            faq_["image_web"] = f"{settings.CAREERS_BASE_IMAGES_URL}{faq_.get('image_web')}"
            faq_["image_wap"] = f"{settings.CAREERS_BASE_IMAGES_URL}{faq_.get('image_wap')}"

        return faq_data
    
    def _get_user_feedback_section(self, product_id=None):
        feedback_section = []
        # Fetch user feedback section from database based on rp_id
        if product_id:
            feedback_section = list(CPFeedback.objects.filter(is_moderated=1, product_id=product_id, response_type="yes").values("id", "product_id", "custom_feedback", "user_name", "user_image", "created").order_by("-created"))
            for feedback in feedback_section:
                feedback["user_image"] = f"{settings.CAREERS_BASE_IMAGES_URL}{feedback.get('user_image')}"
                feedback["is_default"] = False

            index = 0
            while len(feedback_section) < 20 and index < len(RP_DEFAULT_FEEDBACK):
                feedback_section.append(RP_DEFAULT_FEEDBACK[index])
                index += 1

        return feedback_section
    
    def _get_exam_from_product(self, product_id=None):
        exam_id = None
        if product_id:
            # Fetch exam id from product id from database
            exam = CPProductCampaign.objects.filter(id=product_id).values("exam").first()
            if exam:
                exam_id = exam.get("exam")
        return exam_id

    def _get_colleges_from_exam(self, exam_id):
        colleges = []
        if exam_id:
            colleges = CollegeCourse.objects.filter(exam=exam_id).values("college__id", "college__name").distinct()
            for college_ in colleges:
                college_["id"] = college_.pop("college__id", None)
                college_["name"] = college_.pop("college__name", None)
        return colleges



class RPCmsHelper:

    def __init__(self):
        pass

    def _get_flow_types(self, *args, **kwargs):
        # Fetch flow types from database based
        input_id = kwargs.get("input_id")
        input_type = kwargs.get("input_type")
        input_flow_type = kwargs.get("input_flow_type")
        input_process_type = kwargs.get("input_process_type")
        detail_input_id = kwargs.get("detail_input_id")

        result_id = kwargs.get("result_id")
        result_type = kwargs.get("result_type")
        result_flow_type = kwargs.get("result_flow_type")
        result_process_type = kwargs.get("result_process_type")
        detail_result_id = kwargs.get("detail_result_id")
       
        input_flow = self._get_rp_input_flow_types(input_id=input_id, input_type=input_type, input_flow_type=input_flow_type, input_process_type=input_process_type,detail_input_id=detail_input_id)
        result_flow = self._get_rp_result_flow_types(result_id=result_id, result_type=result_type, result_flow_type=result_flow_type, result_process_type=result_process_type,detail_result_id=detail_result_id)

        data = {
            "input_flow": input_flow,
            "result_flow": result_flow
        }
        return data

    def _get_rp_input_flow_types(self, input_id=None, input_type=None, input_flow_type=None, input_process_type=None, detail_input_id=None): #TODO remove id
        # Fetch input flow type from database based on rp_id
        input_flow_type_data = []
        if input_id:
            input_flow_type_data = RpInputFlowMaster.objects.filter(id=input_id, status=1).values("id","input_flow_type", "input_type", "input_process_type").first()
        
        elif detail_input_id: #TODO COnfirm with ayush sir - removed.first
            input_flow_type_data = RpInputFlowMaster.objects.filter(id=detail_input_id, status=1).values("id","input_flow_type", "input_type", "input_process_type")
    
        elif input_flow_type:
            input_flow_type_data = list(RpInputFlowMaster.objects.filter(input_flow_type__contains=input_flow_type, status=1).values("id","input_flow_type", "input_type", "input_process_type").first())
    
        elif input_type:
            input_flow_type_data = list(RpInputFlowMaster.objects.filter(input_type__contains=input_type, status=1).values("id","input_flow_type", "input_type", "input_process_type").first())
    
        elif input_process_type:
            input_flow_type_data = list(RpInputFlowMaster.objects.filter(input_process_type__contains=input_process_type, status=1).values("id","input_flow_type", "input_type", "input_process_type").first())

        else:
            input_flow_type_data = list(RpInputFlowMaster.objects.filter(status=1).values("id","input_flow_type", "input_type", "input_process_type").order_by("-updated"))

        return input_flow_type_data
    
    def _get_rp_result_flow_types(self, result_id=None, result_type=None, result_flow_type=None, result_process_type=None, detail_result_id=None):
        # Fetch input flow type from database based on rp_id
        result_flow_type_data = []
        if result_id:
            result_flow_type_data = list(RpResultFlowMaster.objects.filter(id=result_id, status=1).values("id","result_flow_type", "result_type", "result_process_type").first())

        elif detail_result_id: #TODO COnfirm with ayush sir - removed.first
            result_flow_type_data = RpResultFlowMaster.objects.filter(id=detail_result_id, status=1).values("id","result_flow_type", "result_type", "result_process_type")

        elif result_flow_type:
            result_flow_type_data = list(RpResultFlowMaster.objects.filter(result_flow_type__contains=result_flow_type, status=1).values("id","result_flow_type", "result_type", "result_process_type").first())
    
        elif result_type:
            result_flow_type_data = list(RpResultFlowMaster.objects.filter(result_type__contains=result_type, status=1).values("id","result_flow_type", "result_type", "result_process_type").first())
    
        elif result_process_type:
            result_flow_type_data = list(RpResultFlowMaster.objects.filter(result_process_type__contains=result_process_type, status=1).values("id","result_flow_type", "result_type", "result_process_type").first())

        else:
            result_flow_type_data = list(RpResultFlowMaster.objects.filter(status=1).values("id","result_flow_type", "result_type", "result_process_type").order_by("-updated"))

        return result_flow_type_data
    
    def _add_flow_type(self, **kwargs):
        # Save input flow type data to database
        flow_type = kwargs.get("flow_type")
        if not flow_type:
            return False, "missing arguments"
        
        if flow_type == "input_flow":
            input_id= kwargs.get("input_id")
            input_type= kwargs.get("input_type")
            input_flow_type= kwargs.get("input_flow_type")
            input_process_type= kwargs.get("input_process_type")

            if not input_type or not input_flow_type or not input_process_type:
                return False, "missing result arguments"

            if input_id:
                RpInputFlowMaster.objects.filter(id=input_id).update(input_type=input_type, input_flow_type=input_flow_type, input_process_type=input_process_type)
                return True, "Updated Successfully"
            else:
                if RpInputFlowMaster.objects.filter(input_type=input_type, input_flow_type=input_flow_type, input_process_type=input_process_type).exists():
                    return False, "Data Already Exists"
                else:
                    RpInputFlowMaster.objects.create(input_type=input_type, input_flow_type=input_flow_type, input_process_type=input_process_type)
                    return True, "Created Successfully"
            
        elif flow_type == "result_flow":
            result_id= kwargs.get("result_id")
            result_type= kwargs.get("result_type")
            result_flow_type= kwargs.get("result_flow_type")
            result_process_type= kwargs.get("result_process_type")

            if not result_type or not result_flow_type or not result_process_type:
                return False, "missing result arguments"

            if result_id:
                RpResultFlowMaster.objects.filter(id=result_id).update(result_type=result_type, result_flow_type=result_flow_type, result_process_type=result_process_type)
                return True, "Updated Successfully"
            else:
                if RpResultFlowMaster.objects.filter(result_type=result_type, result_flow_type=result_flow_type, result_process_type=result_process_type).exists():
                    return False, "Data Already Exists"
                else:
                    RpResultFlowMaster.objects.create(result_type=result_type, result_flow_type=result_flow_type, result_process_type=result_process_type)
                    return True, "Created Successfully"

        return False, "Failed to create, Incorrect flow type"

    def _delete_flow_type(self, flow_type, flow_id):
        # Delete input flow type from database
        if not flow_type or not flow_id:
            return False, "missing arguments"

        if flow_type == "input_flow":
            RpInputFlowMaster.objects.filter(id=flow_id).delete()
            return True, "Deleted Successfully"
            
        elif flow_type == "result_flow":
            RpResultFlowMaster.objects.filter(id=flow_id).delete()
            return True, "Deleted Successfully"

        return False, "Failed to delete, Incorrect flow type"

    def _get_exam_session_data(self, product_id, year):
        if not product_id:
            return False, "Missing arguments"  

        if year:
            year = int(year)
    
        session_data = {
            "product_id": product_id,
            "year": year,
            "count": 0,
            "exam_session_data": []
        }
        # Fetch student appeared data from database
        rp_session_data = CnextRpSession.objects.filter(product_id=product_id, status=1)
        if year:
            rp_session_year_data = list(rp_session_data.filter(year=year).values("id", "product_id", "year", "session_date", "session_shift", "difficulty"))
            if rp_session_year_data:
                session_data["year"] = year
                session_data["count"] = len(rp_session_year_data) 
                session_data["exam_session_data"] = rp_session_year_data 
        
        if not session_data["exam_session_data"]:
            rp_max_year = rp_session_data.aggregate(Max('year'))['year__max']
            rp_session_data = list(rp_session_data.filter(year=rp_max_year).values("id", "product_id", "year", "session_date", "session_shift", "difficulty"))
            if rp_session_data:
                session_data["year"] = rp_max_year 
                session_data["count"] = len(rp_session_data) 
                session_data["exam_session_data"] = rp_session_data

        shift_choices = dict(CnextRpSession.SHIFT_ENUM)
        difficulty_choices = dict(CnextRpSession.DIFFICULTY_ENUM)

        for item in session_data["exam_session_data"]:
            item["session_shift_name"] = shift_choices.get(item["session_shift"]) if item.get("session_shift") else ""
            item["difficulty_name"] = difficulty_choices.get(item["difficulty"]) if item.get("difficulty") else ""
            item["session_date"] = item["session_date"].strftime("%Y-%m-%d") if item.get("session_date") else None

        return True, session_data
    
    def _add_exam_session_data(self, uid, session_data, product_id, year):
        
        if not year:
            year = datetime.today().year
        
        if not product_id or not uid or not year or not isinstance(session_data, list):
            return False, "Missing arguments or Incorrect data type"
        
        rp_session_ids = list(CnextRpSession.objects.filter(product_id=product_id, year=year).values_list("id",flat=True))
        incomming_ids = [row_["id"] for row_ in session_data if row_.get("id")]
        rp_session_mapping = {row_["id"]:row_ for row_ in session_data if row_.get("id")}

        error = []
        to_create = []
        to_update = CnextRpSession.objects.filter(id__in=incomming_ids)

        # Delete non existing records
        non_common_ids = set(rp_session_ids) - set(incomming_ids)
        CnextRpSession.objects.filter(product_id=product_id, year=year, id__in=non_common_ids).delete()

        # Create new records
        for new_row in session_data:
            session_date = self.convert_str_to_datetime(new_row.get('session_date'))
            session_shift = new_row.get('session_shift')
            difficulty = new_row.get('difficulty')

            if not session_date or not session_shift or not difficulty:
                error.append({"row":new_row, "message": "Incorrect data"})
                continue

            if not new_row.get("id"):
                to_create.append(CnextRpSession(product_id=product_id, year=year, session_date=session_date, session_shift=session_shift, 
                                                difficulty=difficulty, created_by=uid, updated_by=uid))
        
        if to_create:
            CnextRpSession.objects.bulk_create(to_create)

        # Update records
        for row_ in to_update:
            row_id = row_.id
            session_date = rp_session_mapping[row_id].get("session_date")
            session_shift = rp_session_mapping[row_id].get("session_shift")
            difficulty = rp_session_mapping[row_id].get("difficulty")
            if not session_date or not session_shift or not difficulty:
                error.append({"id":row_id, "message": "Incorrect data"})
                continue

            row_.session_date = self.convert_str_to_datetime(session_date)
            row_.session_shift = session_shift
            row_.difficulty = difficulty
            row_.updated_by = uid

        if incomming_ids:
            CnextRpSession.objects.bulk_update(to_update, ["session_date", "session_shift", "difficulty", "updated_by"])
        
        final_output = {
            "message": "Successfully created session",
            "error": error,
            "session_data": session_data,
            "count": len(session_data) - len(error)
        }
        return True, final_output
    
    def convert_str_to_datetime(self, str_to_datetime):
        try:
            return datetime.strptime(str_to_datetime, '%Y-%m-%d') + timedelta(hours=6, minutes=31)
        except ValueError:
            return None        
        
    def _get_student_appeared_data_(self,exam_id,year): #TODO change function name 
        if year:
            year = int(year) 
    
        data = {
            "exam_id": int(exam_id),
            "year": year,
            "count": 0,
            "student_appeared_data": []
        }
         # Filter by product_id and year (if provided)
        query = RPStudentAppeared.objects.filter(exam_id=exam_id,status=1).values('id','exam_id', 'year', 'student_type', 'min_student', 'max_student', 'status', 'category', 'disability')

        if year:
            rp_students_appeared = list(query.filter(year=year))
            if rp_students_appeared:
                data['year'] = year
                data["count"] = len(rp_students_appeared) 
                data["student_appeared_data"] = rp_students_appeared 

        # If year is not provided, get the latest year dynamically
        if not data["student_appeared_data"]:
            latest_year = query.aggregate(latest_year=Max('year'))['latest_year']
            rp_students_appeared = list(query.filter(year=latest_year))
            if rp_students_appeared:
                data["year"] = latest_year 
                data["count"] = len(rp_students_appeared) 
                data["student_appeared_data"] = rp_students_appeared 


        cast_category_dict = dict(CasteCategory.objects.annotate(key=F('id'), value=F('name')).values_list('key', 'value'))
        disability_category_dict = dict(DisabilityCategory.objects.annotate(key=F('id'), value=F('name')).values_list('key', 'value'))

        for student_data in rp_students_appeared:
            student_data['student_type'] = {"id":student_data.get('student_type',None),"name":STUDENT_TYPE.get(student_data.get('student_type',None))}
            student_data['category'] = {"id":student_data.get('category'),"name":cast_category_dict.get(student_data.get('category'))}
            student_data['disability'] = {"id":student_data.get('disability'),"name": disability_category_dict.get(student_data.get('disability'))}
        data["student_appeared_data"] = rp_students_appeared 

        
        return True, data

    def _add_update_student_appeared_data(self, student_data, exam_id, year, user_id, *args, **kwargs):
        if not year:
            year = datetime.today().year
        
        if not exam_id or not year or not isinstance(student_data, list):
            return False, "Missing arguments or Incorrect data type"
        
        rp_student_appeared = list(RPStudentAppeared.objects.filter(exam_id=exam_id, year=year).values_list('id', flat=True))
        incomming_ids = [row_["id"] for row_ in student_data if row_.get("id")]
        rp_student_appeared_mapping = {row_["id"]:row_ for row_ in student_data if row_.get("id")}

        error = []
        to_create = []
        to_update = RPStudentAppeared.objects.filter(id__in=incomming_ids)

        # Delete non existing records
        non_common_ids = set(rp_student_appeared) - set(incomming_ids)
        if non_common_ids:
            RPStudentAppeared.objects.filter(exam_id=exam_id, year=year, id__in=non_common_ids).delete()

        fields = ['student_type','category', 'disability', 'min_student', 'max_student','updated_by'] 

        # category and diability are mandatory when student_type =    category_wise

        # Create new records
        for data in student_data:
            #TODO
            # if not session_date or not session_shift or not session_difficulty:
            #     error.append({"row":new_row, "message": "Incorrect data"})
            #     continue

            if not data.get("id"):
                to_create.append(
                    RPStudentAppeared(exam_id=exam_id, year=year,created_by=user_id,updated_by=user_id, **data)
                )
        
        if to_create:
            RPStudentAppeared.objects.bulk_create(to_create)

        # Update records
        for row_ in to_update:
            row_id = row_.id
            row_.student_type = rp_student_appeared_mapping[row_id].get('student_type')
            row_.category = rp_student_appeared_mapping[row_id].get('category')
            row_.disability = rp_student_appeared_mapping[row_id].get('disability')
            row_.min_student = rp_student_appeared_mapping[row_id].get('min_student')
            row_.max_student = rp_student_appeared_mapping[row_id].get('max_student')
            row_.updated_by = user_id
            #TODO
            # if not all(row_.get(field) for field in required_fields):
            #     error.append({"id": row_id, "message": "Incorrect data"})
            #     continue

        if incomming_ids:
            RPStudentAppeared.objects.bulk_update(to_update, fields)
        
        final_output = {
            "message": "Enteries successfully created",
            "error": error,
            "student_appeared_data": student_data,
            "count": len(student_data) - len(error)
        }
        return True, final_output

    def _get_variation_factor_data(self, product_id):
        if not product_id:
            return False, "Missing arguments"   
            
        vf_data = {
            "product_id": product_id,
            "count": 0,
            "variation_factor_data": []
        }
        # Fetch variation factor data from database
        rp_var_f_data = list(CnextRpVariationFactor.objects.filter(product_id=product_id, status=1)
                             .values("id", "product_id", "result_flow_type", "result_flow_type__result_process_type", 
                                     "lower_val", "upper_val", "min_factor", "max_factor", "preset_type"))
        if rp_var_f_data:
            vf_data["count"] = len(rp_var_f_data) 
            vf_data["variation_factor_data"] = rp_var_f_data 

        preset_type_choices = dict(CnextRpVariationFactor.PRESET_TYPE_ENUM)
        for item in vf_data["variation_factor_data"]:
            item["result_flow_type_name"] = item.pop("result_flow_type__result_process_type", "")
            item["preset_type_name"] = preset_type_choices.get(item["preset_type"]) if item.get("preset_type") else ""
            for key, val in item.items():
                if key in  ["lower_val", "upper_val", "min_factor", "max_factor"]:
                    item[key] = str(val)

        return True, vf_data
    
    def _add_variation_factor_data(self, uid, var_factor_data, product_id):
        
        if not uid or not product_id or not isinstance(var_factor_data, list):
            return False, "Missing arguments or Incorrect data type"
        
        rp_session_ids = list(CnextRpVariationFactor.objects.filter(product_id=product_id).values_list("id",flat=True))
        incomming_ids = [row_["id"] for row_ in var_factor_data if row_.get("id")]
        rp_var_factor_mapping = {row_["id"]:row_ for row_ in var_factor_data if row_.get("id")}

        error = []
        to_create = []
        to_update = CnextRpVariationFactor.objects.filter(id__in=incomming_ids)

        # Delete non existing records
        non_common_ids = set(rp_session_ids) - set(incomming_ids)
        if non_common_ids:
            CnextRpVariationFactor.objects.filter(product_id=product_id, id__in=non_common_ids).delete()

        # Create new records
        for new_row in var_factor_data:

            result_flow_type = new_row.get('result_flow_type')
            lower_val = new_row.get('lower_val')
            upper_val = new_row.get('upper_val')
            min_factor = new_row.get('min_factor')
            max_factor = new_row.get('max_factor')
            preset_type = new_row.get('preset_type')

            if not result_flow_type or not preset_type or lower_val is None or upper_val is None or min_factor is None or max_factor is None:
                error.append({"row":new_row, "message": "Incorrect data"})
                continue

            if not new_row.get("id"):
                to_create.append(CnextRpVariationFactor(product_id=product_id, result_flow_type_id=result_flow_type, lower_val=lower_val, 
                                                        upper_val=upper_val, min_factor=min_factor, max_factor=max_factor, preset_type=preset_type,
                                                        created_by=uid, updated_by=uid))
        
        if to_create:
            CnextRpVariationFactor.objects.bulk_create(to_create)

        # Update records
        for row_ in to_update:
            row_id = row_.id

            result_flow_type = rp_var_factor_mapping[row_id].get('result_flow_type')
            lower_val = rp_var_factor_mapping[row_id].get('lower_val')
            upper_val = rp_var_factor_mapping[row_id].get('upper_val')
            min_factor = rp_var_factor_mapping[row_id].get('min_factor')
            max_factor = rp_var_factor_mapping[row_id].get('max_factor')
            preset_type = rp_var_factor_mapping[row_id].get('preset_type')

            if not result_flow_type or not preset_type or lower_val is None or upper_val is None or min_factor is None or max_factor is None:
                error.append({"id":row_id, "message": "Incorrect data"})
                continue

            row_.result_flow_type_id = result_flow_type
            row_.lower_val = lower_val
            row_.upper_val = upper_val
            row_.min_factor = min_factor
            row_.max_factor = max_factor
            row_.preset_type = preset_type
            row_.updated_by = uid

        if incomming_ids:
            CnextRpVariationFactor.objects.bulk_update(to_update, ["result_flow_type", "lower_val", "upper_val", "min_factor", "max_factor", "preset_type", "updated_by"])
        
        final_output = {
            "message": "Successfully created session",
            "error": error,
            "variation_factor_data": var_factor_data,
            "count": len(var_factor_data) - len(error)
        }
        return True, final_output

    def _get_custom_mean_sd_data(self, product_id, year):
        if not product_id:
            return False, "Missing arguments"  

        if year:
            year = int(year)
    
        session_data = {
            "product_id": product_id,
            "year": year,
            "count": 0,
            "custom_mean_sd_data": []
        }
        # Fetch student appeared data from database
        rp_mean_sd_data = RpMeanSd.objects.filter(product_id=product_id, status=1)
        if year:
            rp_mean_sd_year_data = list(rp_mean_sd_data.filter(year=year).values("id", "product_id", "year", "input_flow_type",
                                                                                  "sheet_mean", "sheet_sd", "admin_mean", "admin_sd", "input_flow_type__input_process_type"))
            if rp_mean_sd_year_data:
                session_data["year"] = year
                session_data["count"] = len(rp_mean_sd_year_data) 
                session_data["custom_mean_sd_data"] = rp_mean_sd_year_data 
        
        elif not session_data["custom_mean_sd_data"]:
            rp_max_year = rp_mean_sd_data.aggregate(Max('year'))['year__max']
            rp_mean_sd_data = list(rp_mean_sd_data.filter(year=rp_max_year).values("id", "product_id", "year", "input_flow_type",
                                                                                    "sheet_mean", "sheet_sd", "admin_mean", "admin_sd", "input_flow_type__input_process_type"))
            if rp_mean_sd_data:
                session_data["year"] = rp_max_year 
                session_data["count"] = len(rp_mean_sd_data) 
                session_data["custom_mean_sd_data"] = rp_mean_sd_data

        for item in session_data["custom_mean_sd_data"]:
            item["input_flow_type_name"] = item.pop("input_flow_type__input_process_type", "")
            for key, val in item.items():
                if key in  ["sheet_mean", "sheet_sd", "admin_mean", "admin_sd"]:
                    item[key] = str(val) if val else ""

        return True, session_data

    def _add_custom_mean_sd_data(self, uid, custom_mean_sd_data, product_id, year):

        #TODO : Re-Calculating Merit List’s Z-Scores on Editing Sheet Mean and SD
        
        if not year:
            year = datetime.today().year
        
        if not product_id or not uid or not year or not isinstance(custom_mean_sd_data, list):
            return False, "Missing arguments or Incorrect data type"
        
        rp_session_ids = list(RpMeanSd.objects.filter(product_id=product_id, year=year).values_list("id",flat=True))
        incomming_ids = [row_["id"] for row_ in custom_mean_sd_data if row_.get("id")]
        rp_session_mapping = {row_["id"]:row_ for row_ in custom_mean_sd_data if row_.get("id")}

        error = []
        to_create = []
        to_update = RpMeanSd.objects.filter(id__in=incomming_ids)

        # Fetch existing mean and SD before any updates
        existing_mean_sd_mapping = {
            row["input_flow_type_id"]: {"sheet_mean": row["sheet_mean"], "sheet_sd": row["sheet_sd"]}
            for row in RpMeanSd.objects.filter(product_id=product_id, year=year).values("input_flow_type_id", "sheet_mean", "sheet_sd")
        }

        # Delete non existing records
        non_common_ids = set(rp_session_ids) - set(incomming_ids)
        if non_common_ids:
            RpMeanSd.objects.filter(product_id=product_id, year=year, id__in=non_common_ids).delete()

        # Create new records
        for new_row in custom_mean_sd_data:
            input_flow_type = new_row.get('input_flow_type')
            sheet_mean = new_row.get('sheet_mean')
            sheet_sd = new_row.get('sheet_sd')
            admin_mean = new_row.get('admin_mean')
            admin_sd = new_row.get('admin_sd')

            if not input_flow_type or sheet_mean is None or sheet_sd is None:
                error.append({"row":new_row, "message": "Incorrect data"})
                continue

            if not new_row.get("id"):
                if not admin_mean: admin_mean = None
                if not admin_sd: admin_sd = None
                to_create.append(RpMeanSd(product_id=product_id, year=year, input_flow_type_id=input_flow_type, sheet_mean=sheet_mean, sheet_sd=sheet_sd,
                                                admin_mean=admin_mean, admin_sd=admin_sd, created_by=uid, updated_by=uid))
        
        if to_create:
            RpMeanSd.objects.bulk_create(to_create)

        # Update records
        for row_ in to_update:
            row_id = row_.id

            input_flow_type = rp_session_mapping[row_id].get('input_flow_type')
            sheet_mean = rp_session_mapping[row_id].get('sheet_mean')
            sheet_sd = rp_session_mapping[row_id].get('sheet_sd')
            admin_mean = rp_session_mapping[row_id].get('admin_mean')
            admin_sd = rp_session_mapping[row_id].get('admin_sd')

            if not input_flow_type or sheet_mean is None or sheet_sd is None:
                error.append({"id":row_id, "message": "Incorrect data"})
                continue

            if not admin_mean: admin_mean = None
            if not admin_sd: admin_sd = None

            row_.input_flow_type_id = input_flow_type
            row_.sheet_mean = sheet_mean
            row_.sheet_sd = sheet_sd
            row_.admin_mean = admin_mean
            row_.admin_sd = admin_sd
            row_.updated_by = uid

        if incomming_ids:
            RpMeanSd.objects.bulk_update(to_update, ["input_flow_type", "sheet_mean", "sheet_sd", "admin_mean", "admin_sd", "updated_by"])

        #thread implememtation for zscore calculation, on the change of mean or sd value
        thread = threading.Thread(
        target=self.process_input_flow_types,
        args=(product_id, year, custom_mean_sd_data, existing_mean_sd_mapping, uid))
        thread.start()

        final_output = {
            "message": "Successfully created session",
            "error": error,
            "custom_mean_sd_data": custom_mean_sd_data,
            "count": len(custom_mean_sd_data) - len(error)
        }
        return True, final_output

    def process_input_flow_types(self, product_id, year, custom_mean_sd_data, existing_mean_sd_mapping, uid):
        for input_flow_type in set(row["input_flow_type"] for row in custom_mean_sd_data if row.get("input_flow_type")):
            existing_mean_sd = existing_mean_sd_mapping.get(int(input_flow_type))
            updated_mean_sd = next((row for row in custom_mean_sd_data if row["input_flow_type"] == input_flow_type), None)

            if not updated_mean_sd:
                continue

            new_mean = float(updated_mean_sd["sheet_mean"])
            new_sd = float(updated_mean_sd["sheet_sd"])

            if existing_mean_sd:
                old_mean = float(existing_mean_sd["sheet_mean"])
                old_sd = float(existing_mean_sd["sheet_sd"])

                if new_mean == old_mean and new_sd == old_sd:
                    print(f"No changes detected for input_flow_type {input_flow_type}, skipping z-score update.")
                    continue

            # Call the Z-score update function in the same thread
            self.update_zscores(product_id, year, input_flow_type, new_mean, new_sd, uid)
    
    # Update Z-Scores
    def update_zscores(self, product_id, year, input_flow_type, mean, sd, uid):
        """
        Update the z-score column in RpMeritList for a specific input_flow_type
        when the mean or standard deviation changes.
        """
        if not product_id or not year or not input_flow_type or mean is None or sd is None:
            return False, "Missing arguments or invalid data"

        # Check if data exists in RpMeritList for the given product_id and year
        rows_to_update = RpMeritList.objects.filter(
            product_id=product_id,
            year=year,
            input_flow_type=input_flow_type
        )

        if not rows_to_update.exists():
            return False, "No data found for the given product_id, year, and input_flow_type"

        # List to hold updated rows
        updated_rows = []

        # Iterate through the rows and calculate z-scores
        for row in rows_to_update:
            z_score = self.calculate_zscore(row.input_value, mean, sd)
            row.z_score = z_score
            row.updated_by = uid
            updated_rows.append(row)

        # Bulk update the rows
        if updated_rows:
            RpMeritList.objects.bulk_update(updated_rows, ["z_score", "updated_by"])
            return True, f"Updated z-scores for {len(updated_rows)} rows"
        else:
            return False, "No rows updated"

    def _get_input_form_field_data(seld, id):
        resp = RpFormField.objects.filter(id = id).values()
        for data in resp:
            if data.get('mapped_process_type'):
                mapped_process_type = data.get('mapped_process_type')
                data['mapped_process_type'] = {'id':mapped_process_type,'label':FORM_INPUT_PROCESS_TYPE.get(mapped_process_type)}
            if data.get('field_type'):
                field_type = data.get('field_type')
                data['field_type'] = {'id':field_type,'label':RP_FIELD_TYPE.get(field_type)}

            if data.get('input_flow_type'):
                input_flow_type = data.get('input_flow_type')
                master_result_flow_type_dict = {
                    item['id']: item['input_process_type'] #TODO OPtimize this 
                    for item in RpInputFlowMaster.objects.filter(status=1).values("id", "input_process_type")
                }
                data['input_flow_type'] = {'id':input_flow_type,'label':master_result_flow_type_dict.get(input_flow_type)}


        return True, resp

    
    def validate_rp_form_fields(self,data):
        """
        Validates the incoming data for RP create form fields based on field type.

        Args:
            data (dict): The input data containing field details.

        Returns:
            dict: A validation result with `is_valid` status and missing fields, if any.
        """
        id = data.get('id')
        field_type = data.get('field_type')
        product_id = data.get('product_id')
        input_flow_type = data.get('input_flow_type')
        mapped_category = data.get('mapped_category')
        field_mapping = {
            1: {
                "mandatory_fields": ["input_flow_type", "display_name", "place_holder_text", "min_val", "max_val", "weight", "mandatory"],
                "non_mandatory_fields": ["error_message", "mapped_process_type","status"]
            },
            2: {
                "mandatory_fields": ["display_name", "place_holder_text", "weight"],
                "non_mandatory_fields": ["mandatory","error_message","status"]
            },
            3: {
                "mandatory_fields": ["display_name", "place_holder_text", "mapped_category", "weight"],
                "non_mandatory_fields": ["mandatory", "error_message", "mapped_process_type","status"]
            },
            4: {
                "mandatory_fields": ["display_name", "place_holder_text", "weight", "list_option_data"],
                "non_mandatory_fields": ["mandatory", "error_message","status"]
            },
            5: {
                "mandatory_fields": ["display_name", "list_option_data", "weight"],
                "non_mandatory_fields": ["mandatory", "mapped_process_type","status"]
            },
            6: {
                "mandatory_fields": ["display_name", "place_holder_text", "weight"],
                "non_mandatory_fields": ["error_message", "mandatory","status"]
            },
        }

        mandatory_fields = field_mapping[field_type]["mandatory_fields"]
        non_mandatory_fields = field_mapping[field_type]["non_mandatory_fields"]
        missing_fields = [
            field for field in mandatory_fields if field not in data or data[field] is None
        ]

        # missing_fields.extend(
        #     field for field in non_mandatory_fields if field not in data
        # )

        if missing_fields:
            return False, missing_fields 
        

        if field_type == 1: #User Input 
            query = RpFormField.objects.filter(input_flow_type=input_flow_type,product_id = product_id,field_type=1,status=1)
            
            if id: # update case 
                query = query.exclude(id=id)
            if query.exists():
                return False, "Combination of these (Input Flow Type, Field Type) already exists. It must be unique."
            
        elif field_type == 2: # Application Number 
            query = RpFormField.objects.filter(product_id = product_id,field_type=2,status=1)
            
            if id: # update case 
                query = query.exclude(id=id)
            if query.exists():
                return False, f"Can map only 1 application number field."
            
        elif field_type == 3: # Category Dropdown 
            query = RpFormField.objects.filter(product_id = product_id,field_type=3,mapped_category=mapped_category,status=1)
            
            if id: # update case 
                query = query.exclude(id=id)
            if query.exists():
                return False, f"Can map only 1 <selected mapped category option> id : {mapped_category} field"
            
        elif field_type == 4: # Select List Dropdown
            query = RpFormField.objects.filter(product_id = product_id,field_type=5,status=1)

            if id: # update case 
                query = query.exclude(id=id)
            if query.exists():
                return False, f"Can map only 1 list options field."
            
        elif field_type == 5: # Radio Button
            query = RpFormField.objects.filter(product_id=product_id,field_type=4,status=1)
            if id: # update case 
                query = query.exclude(id=id)
            if query.exists():
                return False, f"Can map only 1 list options field."
            
        elif field_type == 6: # Date of Birth
            query = RpFormField.objects.filter(product_id=product_id,field_type=6,status=1)
            if id: # update case 
                query = query.exclude(id=id)
            if query.exists():
                return False, f"Can map only 1 DOB field."

        return True, []
    
    def _add_update_rp_form_data(self, id, data):

        final_output = {
            "message": "Successfully add/updated form fields.",
            "error": "",
        }

        is_valid, validation_response = self.validate_rp_form_fields(data)
        if not is_valid:
            final_output["message"] = "Missing Fields"
            final_output['error'] = validation_response
            return False , final_output
        
        if id:
            RpFormField.objects.filter(id = id).update(**data)
        else:
            RpFormField.objects.create(**data)

        return True, final_output
    
    def get_input_form_data(self, pk):
        result = CnextRpCreateInputForm.objects.filter(product_id = pk).values('id','product_id','input_process_type','process_type_toggle_label','submit_cta_name','created_by','updated_by')
        input_process_type_dict = dict(RpInputFlowMaster.objects.all().values_list('id','input_process_type'))
        for value in result:
            if value['input_process_type']:
                value['input_process_type'] = {'id':value['input_process_type'],
                                               'label':input_process_type_dict.get(value['input_process_type'])}
        return result

    def create_input_form(self,*args, **kwargs):
        bulk_create_data = []
        bulk_update_data = []
        delete_ids = []
        request_data = kwargs.get('request_data')
        product_id = kwargs.get('product_id')
        existing_records = {record.id: record for record in kwargs.get('instance', [])}

        for data in request_data:
            record_id = data.get('id')
            created_by = data.get('created_by')
            updated_by = data.get('updated_by')
            submit_cta_name = data['submit_cta_name']
            input_process_type = data['input_process_type']
            process_type_toggle_label = data['process_type_toggle_label']

            if record_id and record_id in existing_records:
                if submit_cta_name is None and input_process_type is None and process_type_toggle_label is None:
                    delete_ids.append(record_id)
                else:
                    record = existing_records[record_id]
                    record.submit_cta_name = submit_cta_name
                    record.updated_by = updated_by
                    record.input_process_type = input_process_type
                    record.process_type_toggle_label = process_type_toggle_label
                    bulk_update_data.append(record)
            else:
                # Create new record
                bulk_create_data.append(CnextRpCreateInputForm(
                    product_id=product_id,
                    created_by=created_by,
                    updated_by=updated_by,
                    submit_cta_name=submit_cta_name,
                    input_process_type=input_process_type,
                    process_type_toggle_label=process_type_toggle_label
                ))

        if bulk_create_data:
            CnextRpCreateInputForm.objects.bulk_create(bulk_create_data)

        if bulk_update_data:
            CnextRpCreateInputForm.objects.bulk_update(
                bulk_update_data,
                fields=['submit_cta_name', 'input_process_type', 'process_type_toggle_label']
            )
        if delete_ids:
            CnextRpCreateInputForm.objects.filter(id__in=delete_ids).delete()

        return "Ok"

    def get_input_form_list(self,request):

        items_on_page = request.query_params.get('page_size',10)
        product_id = request.query_params.get('product_id')
        queryset = RpFormField.objects.values(
            'id', 'display_name', 'field_type', 'input_flow_type', 'min_val', 'max_val', 'mapped_process_type', 'mandatory', 'weight', 'status'
        ).order_by('weight')

        if product_id:
            queryset = queryset.filter(product_id=product_id)

        paginator = CustomPaginator()
        paginator.page_size = items_on_page
        paginated_results = paginator.paginate_queryset(queryset, request)
        for item in paginated_results:
            if item:
                item['field_name'] = FIELD_TYPE.get(item['field_type'])

        return paginator.get_paginated_response(paginated_results)
    
    def validate_sheet(self, request):
        file = request.FILES.get('file')
        selected_year = request.POST.get('year')
        product_id = request.POST.get('product_id')
        user_id = request.POST.get('uid')

        if not file:
            return False, {"error": "No file provided"}
        if not selected_year:
            return False, {"error": "year key is missing in params"}
        if not product_id:
            return False, {"error": "product_id key is missing in params"}
        if not user_id:
            return False, {"error": "uid key is missing in params"}

        # File validation
        file_extension = file.name.split('.')[-1].lower()
        if file_extension != 'csv':
            return False, {"error": "Unsupported file format. Only .csv is allowed."}

        expected_columns = [
            'product_id', 'caste', 'disability', 'slot', 'difficulty_level',
            'input_flow_type', 'input', 'z_score', 'result_flow_type', 'result', 'year'
        ]

        try:
            # Detect file encoding
            raw_data = file.read()
            detected_encoding = chardet.detect(raw_data)['encoding']
            if not detected_encoding:
                return False, {"error": "Unable to detect file encoding. Please save the file in UTF-8 format."}

            # Decode file content
            decoded_file = raw_data.decode(detected_encoding).splitlines()
            reader = csv.reader(decoded_file)
            rows = list(reader)
            headers = [header.strip() for header in rows[0]]

            # Normalize headers (fix issues like +AF8- to _)
            headers = [header.replace('+AF8-', '_') for header in headers]

            # Validate required columns
            missing_columns = [col for col in expected_columns if col not in headers]
            if missing_columns:
                return False, {"error": f"Missing columns: {', '.join(missing_columns)}"}

            # Validate rows
            for index, row in enumerate(rows[1:], start=2):
                if len(row) < len(headers):
                    return False, {"error": f"Row {index} has missing values."}
                row_data = dict(zip(headers, row))

                # Check mandatory fields
                for field in ['product_id','input_flow_type', 'input', 'result', 'result_flow_type', 'year']:
                    value = row_data.get(field)
                    if value is None or str(value).strip() == "":
                        return False, {"error": f"Missing value for '{field}' in row {index}."}

                # Validate data types
                try:
                    int_fields = [
                        'product_id', 'caste', 'disability', 'slot', 'difficulty_level',
                        'input_flow_type', 'input', 'result_flow_type', 'year'
                    ]
                    for field in int_fields:
                        try:
                            if field in row_data and row_data[field].strip():
                                int(row_data[field])  # Check if it can be converted to int
                        except ValueError:
                            raise ValueError(f"Invalid value for '{field}' in row {index}: {row_data[field]}")


                    if 'result' in row_data and row_data['result'].strip():
                        # Check if result can be float or int
                        try:
                            float(row_data['result'])  # Attempt to convert to float
                        except ValueError:
                            raise ValueError(f"Invalid value for 'result' in row {index}: {row_data['result']}")

                except ValueError as e:
                    return False, {"error": f"Row {index}: Invalid data type for field. {str(e)}"}

                # Validate product_id
                if row_data['product_id'].strip() != str(product_id):
                    return False, {"error": f"Row {index}: Product ID does not match the selected Product ID."}

            # Validate: Check if all rows have the same year
            year_values = [row[headers.index('year')].strip() for row in rows[1:] if row[headers.index('year')].strip()]
            if len(set(year_values)) > 1:
                return False, {"error": "Year is not unique in the merit list."}

            # Validate year consistency with selected_year
            year_index = headers.index('year')
            for row in rows[1:]:
                if row[year_index].strip() != str(selected_year):
                    return False, {"error": f"Sheet Year does not match with the selected one"}

            RpMeritSheet.objects.filter(product_id=product_id, year=selected_year).delete()

            # Save metadata in RpMeritSheet
            RpMeritSheet.objects.create(
                product_id=product_id,
                year=selected_year,
                file_name=file,
                created_by=user_id,
                updated_by=user_id,
                created=now(),
                updated=now()  # TODO remove it later
            )

            return True, "File validated and uploaded successfully."

        except Exception as e:
            return False, {"error": f"An error occurred: {str(e)}"}

    def upload_merit_list(self, request):
        product_id = request.data.get('product_id')
        year = request.data.get('year')
        user_id = request.data.get('uid')

        try:
            # Fetch the merit sheet
            merit_sheet = RpMeritSheet.objects.filter(product_id=product_id, year=year).first()
            if not merit_sheet:
                return False, "Merit sheet not found for the given product_id and year."

            file_path = f"{settings.CAREERS_BASE_IMAGES_URL}{merit_sheet.file_name}" if merit_sheet.file_name else None
            if not file_path:
                return False, "File path is not available."

            # Download the file
            response = requests.get(file_path)
            if response.status_code != 200:
                return False, "Failed to download the file from the provided path."

            # Read CSV file
            csv_file = io.StringIO(response.text)
            reader = csv.DictReader(csv_file)

            # Delete existing records for the product_id and year
            RpMeritList.objects.filter(product_id=product_id, year=year).delete()

            # Group data by input_flow_type
            input_data = defaultdict(list)
            for row in reader:
                input_flow_type = row['input_flow_type']
                try:
                    input_value = float(row['input'])
                    input_data[input_flow_type].append(input_value)
                except ValueError:
                    continue  # Skip invalid numeric values

            # Calculate mean and standard deviation
            stats_data = {}
            for input_flow_type, values in input_data.items():
                if values:
                    mean = sum(values) / len(values)
                    variance = sum((x - mean) ** 2 for x in values) / len(values)
                    sd = sqrt(variance)
                    stats_data[input_flow_type] = {'mean': mean, 'sd': sd}
                else:
                    stats_data[input_flow_type] = {'mean': None, 'sd': None}

            # Insert data into RpMeanSd
            for input_flow_type, stats in stats_data.items():
                if not input_flow_type:
                    return False, f"Invalid input_flow_type: {input_flow_type}."

                RpMeanSd.objects.update_or_create(
                    product_id=product_id,
                    year=year,
                    input_flow_type_id=input_flow_type,
                    defaults={
                        'sheet_mean': stats['mean'],
                        'sheet_sd': stats['sd'],
                        'created_by': user_id,
                        'updated_by': user_id,
                        'updated': now()
                    }
                )

            # Calculate z-score and insert merit list entries
            csv_file.seek(0)  # Reset CSV file pointer
            reader = csv.DictReader(csv_file)
            merit_list_entries = []
            batch_size = 1000  # Adjust batch size as needed

            for row in reader:
                input_flow_type = row['input_flow_type']
                input_value = None
                try:
                    input_value = float(row['input'])
                except ValueError:
                    pass  # Skip invalid numeric values

                stats = stats_data.get(input_flow_type, {})
                sheet_mean = stats.get('mean')
                sheet_sd = stats.get('sd')
                zscore = self.calculate_zscore(input_value, sheet_mean, sheet_sd)

                merit_list_entries.append(RpMeritList(
                    product_id=row['product_id'],
                    year=row['year'],
                    caste=row.get('caste') if row.get('caste') and row.get('caste').strip() else None,
                    disability=row.get('disability') if row.get('disability') and row.get('disability').strip() else None,
                    slot=row.get('slot') if row.get('slot') and row.get('slot').strip() else None,
                    difficulty_level=row.get('difficulty_level') if row.get('difficulty_level') and row.get('difficulty_level').strip() else None,
                    input_flow_type=input_flow_type,
                    input_value=input_value,
                    z_score=zscore,
                    result_flow_type=row.get('result_flow_type'),
                    result_value=row.get('result'),
                    created_by=user_id,
                    updated_by=user_id,
                    created=now(),
                    updated=now()
                ))

                # Bulk create in batches
                if len(merit_list_entries) == batch_size:
                    RpMeritList.objects.bulk_create(merit_list_entries)
                    merit_list_entries = []  # Reset the list after each batch

            # Insert remaining entries
            if merit_list_entries:
                RpMeritList.objects.bulk_create(merit_list_entries)

            return True, "Mean, SD, and Z-scores calculated successfully."
        except Exception as e:
            return False, str(e)

    def calculate_zscore(self, input_value, mean, sd):
        """
        Calculate the z-score for a given input value, mean, and standard deviation.
        """
        if mean is not None and sd is not None and sd != 0 and input_value is not None:
            return (input_value - mean) / sd
        return None
    
    def get_merit_list(self, request):
        try:
            items_on_page = int(request.query_params.get('page_size', 30))
            product_id = request.query_params.get('product_id')
            year = request.query_params.get('year')
            queryset = RpMeritList.objects.filter(product_id=product_id)

            if not product_id:
                return False, 'product_id is required'
            
            if not year:
                year = queryset.aggregate(latest_year=Max('year'))['latest_year']

            queryset = queryset.filter(year=year).values(
                'caste', 'disability', 'slot', 'difficulty_level', 
                'input_flow_type', 'input_value', 'z_score', 
                'result_flow_type', 'result_value', 'year'
            ).order_by('id')

            # Paginate the results
            paginator = CustomPaginator()
            paginator.page_size = items_on_page
            paginated_results = paginator.paginate_queryset(queryset, request)
            caste_dict = dict(CasteCategory.objects.values_list("id", "name"))
            disability_dict = dict(DisabilityCategory.objects.values_list("id", "name"))
            input_flow_dict = dict(RpInputFlowMaster.objects.values_list("id", "input_flow_type"))
            result_flow_dict = dict(RpResultFlowMaster.objects.values_list("id", "result_flow_type"))
            slot_dict = {
                int(key): value
                for list_option_data in RpFormField.objects.filter(field_type=4).values_list('list_option_data', flat=True)
                for key, value in (pair.split('|') for pair in list_option_data.split(','))
            }

            # Update paginated results with human-readable values
            for item in paginated_results:
                if item:
                    item['caste'] = caste_dict.get(item['caste'], item['caste'])
                    item['disability'] = disability_dict.get(item['disability'], item['disability'])
                    item['slot'] = slot_dict.get(item['slot'], item['slot'])
                    item['difficulty_level'] = DIFFICULTY_LEVEL.get(item['difficulty_level'], item['difficulty_level'])
                    item['input_flow_type'] = input_flow_dict.get(item['input_flow_type'], item['input_flow_type'])
                    item['result_flow_type'] = result_flow_dict.get(item['result_flow_type'], item['result_flow_type'])
            paginated_data = paginator.get_paginated_response(paginated_results)
            paginated_data['to_graph'] = RpMeritSheet.objects.filter(product_id=product_id,year=year).values_list('to_graph',flat=True).first()
            paginated_data['filtered_year'] = year
            return True, paginated_data

        except Exception as e:
            return False, str(e)

    def add_edit_display_graph(self, request):
        product_id = request.data.get('product_id')
        year = request.data.get('year')
        to_graph = request.data.get('to_graph','not_found')
        if to_graph == 'not_found':
            return False, "to_graph key is required"

        queryset = RpMeritSheet.objects.filter(product_id=product_id,year=year)
        if queryset.exists():
            queryset.update(to_graph=to_graph)
        return True, "Data Created Successfully"

    def get_report_filters(self, request, analytics=None):
        email = request.GET.get('email')
        usage_from = request.GET.get('usage_from')
        usage_to = request.GET.get('usage_to')
        product_id = request.GET.get('product_id')
        uid = request.GET.get('uid')
        uuid = request.GET.get('uuid')
        report_id = request.GET.get('report_id')
        device_type = request.GET.get('device_type')
        query_filters = {}

        from_status, usage_from = self.get_date_object(usage_date=usage_from)
        to_status, usage_to = self.get_date_object(usage_date=usage_to)

        if not from_status or not to_status:
            raise ValueError("Invalid date range")

        if email:
            query_filters['email'] = email

        if uid:
            query_filters['uid'] = uid

        if uuid:
            query_filters['uuid'] = uuid

        if report_id:
            query_filters['id'] = report_id

        if device_type and not analytics:
            query_filters['device_type'] = device_type

        if product_id:
            query_filters['product_id'] = product_id
    
        if usage_from:
            query_filters['form_submission_at__gte'] = usage_from
    
        if usage_to:
            query_filters['form_submission_at__lte'] = usage_to
        
        return query_filters

    
    def rp_usage_report(self, request, *args, **kwargs):
        usage_from = request.GET.get('usage_from')
        usage_to = request.GET.get('usage_to')
        product_id = request.GET.get('product_id')
        usage_data = []

        if not usage_from or not usage_to or not product_id:
            return False, "usage_from, usage_to and product_id are required"
        
        query_filters = self.get_report_filters(request)

        cast_category_dict = dict(CasteCategory.objects.annotate(key=F('id'), value=F('name')).values_list('key', 'value'))
        disability_category_dict = dict(DisabilityCategory.objects.annotate(key=F('id'), value=F('name')).values_list('key', 'value'))

        queryset = CnextRpUserTracking.objects.filter(**query_filters).values()

        if len(queryset) == 0:
            return True, usage_data

        for item in queryset:

            ## Input Flow Type
            flow_type = item['flow_type'] if item['flow_type'] else None
            if flow_type and str(flow_type).isdigit():
                flow_type = int(flow_type)
                if flow_type != 3:
                    flow_type = 1

                flow_type_data = {
                    "id": flow_type,
                    "name": FORM_INPUT_PROCESS_TYPE.get(flow_type)
                }
            else: continue

            ## category
            category_id = item['category'] if item['category'] else None
            if category_id and str(category_id).isdigit():
                category_id = int(category_id)
                category_data = {
                    "id" : category_id,
                    "name" : cast_category_dict.get(category_id)
                }
            else: category_data = None 

            ## disability
            disability_id = item['disability'] if item['disability'] else None
            if disability_id and str(disability_id).isdigit():
                disability_id = int(disability_id)
                disability_data = {
                    "id" : disability_id,
                    "name" : disability_category_dict.get(disability_id)
                }
            else: disability_data = None 

            ## Input fields
            input_fields = item['input_fields'] if item['input_fields'] else []

            ## Output fields
            output_fields = self.formate_output_data(flow_type, item['result_predictions']) if item['result_predictions'] else []

            ## exam session
            if item['exam_session']:
                exam_session = item['exam_session']
            else:
                exam_session = None

            ## Form submission
            form_submission_time = item['form_submission_at'].strftime('%Y-%m-%d %H:%M:%S')

            ## dataset
            dataset = {
                'uid': item['uid'],
                'uuid': item['uuid'],
                'login_status': item['login_status'],
                'form_submission_time': form_submission_time,
                'usage_duration': None,
                'slot': None,
                'category': category_data,
                'disability': disability_data,
                'exam_session': exam_session,
                'product_id': item['product_id'],
                'device_type': item['device_type'],
                'flow_type': flow_type_data,
                'input_fields': input_fields,
                'output_fields': output_fields,
            }
            usage_data.append(dataset)

        return True, usage_data

    def formate_output_data(self, flow_type, data):
        formated_data = []

        for item in data:
            if not isinstance(item, dict):
                continue
            is_primary = item.get('primary')
            if flow_type == 3:
                category = item.get('category')
                disability = item.get('disability')
                max_rank = item.get('max_rank')
                min_rank = item.get('min_rank')
                classification = item.get('classification')
                obj = {"classification" : classification}

                if not max_rank or not min_rank:
                    continue

                if is_primary:
                    display_name = f"Overall Rank : {min_rank} - {max_rank}"
                elif not disability or disability in ("N.A.", "N.A", "NA", "NA."):
                    display_name = f"{category} : {min_rank} - {max_rank}"
                else:
                    display_name = f"{category} {disability} : {min_rank} - {max_rank}"
            else:
                result_type = item.get('result_type')
                result_flow_type = item.get('result_flow_type')
                result_process_type = item.get('result_process_type')
                result_value = item.get('result_value')

                if not result_value:
                    continue

                obj = {"result_process_type" : result_process_type}

                if is_primary:
                    display_name = f"Overall Result : {result_value}"
                else:
                    display_name = f"{result_type} {result_flow_type} : {result_value}"

            obj["display_name"] = display_name
            formated_data.append(obj)

        return formated_data

    def get_date_object(self, *args, **kwargs):

        usage_date = kwargs.get("usage_date")
        try:
            if isinstance(usage_date, dict):
                usage_year = usage_date.get("year")
                usage_month = usage_date.get("month")
                usage_day = usage_date.get("day")
                if usage_year and usage_month and usage_day:
                    usage_date = date(usage_year, usage_month, usage_day)
                    return True, usage_date

            elif isinstance(usage_date, str):
                date_list = list(map(int, str(usage_date).split("-")))
                if date_list and len(date_list) >= 3:
                    usage_year = date_list[0]
                    usage_month = date_list[1]
                    usage_day = date_list[2]
                    if usage_year and usage_month and usage_day:
                        usage_date = date(usage_year, usage_month, usage_day)
                        return True, usage_date
        except Exception as error:
            print("def get_date_object error -> ",error)

        return False, None

    def rp_analytics_report(self, request, *args, **kwargs):
        usage_from = request.GET.get('usage_from')
        usage_to = request.GET.get('usage_to')
        product_id = request.GET.get('product_id')
        device_type = request.GET.get('device_type')
        product_alias = request.GET.get('product_alias', 'jee-main-rank-predictor')
        usage_analytics = []
        query_filters = {}

        if not usage_from or not usage_to or not product_id:
            return False, "usage_from, usage_to and product_id are required"

        usage_from_status, usage_from = self.get_date_object(usage_date=usage_from)
        usage_to_status, usage_to = self.get_date_object(usage_date=usage_to)

        if not usage_from_status or not usage_to_status:
            return False, "Invalid usage_from or usage_to date format"

        query_filters = self.get_report_filters(request, analytics=True)

        queryset = CnextRpUserTracking.objects.filter(**query_filters).values()

        # master total count
        master_total_count = queryset.count()

        # total count
        if device_type:
            queryset = queryset.filter(device_type = device_type)
            total_count = queryset.count()
        else:
            total_count = master_total_count

        if total_count <= 0:
            return True, usage_analytics

        # unique users
        total_unique_users = queryset.exclude(uid = 0).values("uid").distinct().count()

        # anonymous users
        total_anonomous_users = queryset.filter(uid = 0).count()

        # Total registered users
        from_timestamp = int(time.mktime(usage_from.timetuple()))
        to_timestamp = int(time.mktime(usage_to.timetuple()))

        total_registered_users_map = User.objects.filter(added_on__gte=from_timestamp, added_on__lte=to_timestamp, source_url__contains=product_alias).values("mobile_verify").annotate(count=Count("id"))
        
        ## Mobile Verified users
        total_verified_users = [item.get("count") for item in total_registered_users_map if item.get("mobile_verify") == 1]
        if total_verified_users:
            total_verified_users = total_verified_users[0]
        else:
            total_verified_users = 0

        ## Mobile Unverified users
        total_unverified_users = [item.get("count") for item in total_registered_users_map if item.get("mobile_verify") == 0]
        if total_unverified_users:
            total_unverified_users = total_unverified_users[0]
        else:
            total_unverified_users = 0

        ## Total Users
        total_registered_users = total_verified_users + total_unverified_users

        ## Average Count
        average_count = round(total_count / total_unique_users)

        ## Total existing users
        existing_users = total_unique_users - total_registered_users

        ## Existing users percentage
        existing_users_percentage = round((existing_users/total_unique_users) * 100, 2)

        usage_analytics = {
            "device_specific" : True if device_type else False,
            "device_type": device_type,
            "total_count" : total_count,
            "total_unique_users" : total_unique_users,
            "total_anonomous_users" : total_anonomous_users,
            "total_registered_users" : total_registered_users,
            "total_verified_users" : total_verified_users,
            "total_unverified_users" : total_unverified_users,
            "average_count" : average_count,
            "existing_users" : existing_users,
            "existing_users_percentage" : existing_users_percentage,
        }

        if device_type:
            usage_analytics["device_type_percentage"] = round((total_count/master_total_count) * 100, 2)

        return True, usage_analytics

        
class CommonDropDownHelper:

    def __init__(self, limit, page, offset=None):
        self.limit = int(limit) if limit else 20
        self.offset = int(offset) if offset else 0
        self.page = int(page) if page else 1
        if not self.offset:
            self.offset = (self.page - 1) * self.limit

    def _get_dropdown_list(self, *args, **kwargs):
        q = kwargs.get('q', '')
        field_name = kwargs.get('field_name')
        selected_id = kwargs.get('selected_id')
        product_id = kwargs.get('product_id')
        product_type = kwargs.get('product_type','')

        internal_limit = None
        dropdown_data = {
            "field": field_name,
            "message": "",
        }
        dropdown = []

        if field_name == "difficulty":
            dropdown = [{"id": key, "value": val, "selected": selected_id == key} for key, val in dict(CnextRpSession.DIFFICULTY_ENUM).items()]

        elif field_name == "session_shift":
            dropdown = [{"id": key, "value": val, "selected": selected_id == key} for key, val in dict(CnextRpSession.SHIFT_ENUM).items()]

        elif field_name == "preset_type":
            dropdown = [{"id": key, "value": val, "selected": selected_id == key} for key, val in dict(CnextRpVariationFactor.PRESET_TYPE_ENUM).items()]

        elif field_name == "input_flow_type":
            master_input_flow_type = list(RpInputFlowMaster.objects.filter(status=1).values("id", "input_flow_type"))
            dropdown = [{"id": item.get("id"), "value": item.get("input_flow_type"), "selected": selected_id == item.get("id")} for item in master_input_flow_type]

        elif field_name == "result_flow_type":
            master_result_flow_type = list(RpResultFlowMaster.objects.filter(status=1).values("id", "result_flow_type"))
            dropdown = [{"id": item.get("id"), "value": item.get("result_flow_type"), "selected": selected_id == item.get("id")} for item in master_result_flow_type]

        elif field_name == "student_type":
            dropdown = [{"id": key, "value": val, "selected": selected_id == key} for key, val in STUDENT_TYPE.items()]

        elif field_name == "result_process_type":
            dropdown = [{"id": key, "value": val, "selected": selected_id == key} for key, val in RESULT_PROCESS_TYPE.items()]

        elif field_name == "result_type":
            dropdown = [{"id": key, "value": val, "selected": selected_id == key} for key, val in RESULT_TYPE.items()]

        elif field_name == "input_type":
            dropdown = [{"id": key, "value": val, "selected": selected_id == key} for key, val in INPUT_TYPE.items()]

        elif field_name == "input_process_type":
            dropdown = [{"id": key, "value": val, "selected": selected_id == key} for key, val in FORM_INPUT_PROCESS_TYPE.items()]

        elif field_name == "mapped_category":
            dropdown = [{"id": key, "value": val, "selected": selected_id == key} for key, val in MAPPED_CATEGORY.items()]

        elif field_name == "factor_type":
            dropdown = [{"id": key, "value": val, "selected": selected_id == key} for key, val in FACTOR_TYPE.items()]

        elif field_name == "domain":
            dropdown = [
            {"id": domain.get("id"), "value": domain.get("name")}
            for domain in Domain.objects.filter(is_stream=1).values("id", "name")
        ]

        elif field_name == "category":
            dropdown = CASTE_CATEGORY

        elif field_name == "disability":
            dropdown = DISABILITY_CATEGORY

        elif field_name == "year":
            year_range = list(range(2020, 2031))
            dropdown = [{"id": year, "value": year} for year in year_range]

        elif field_name == "tools_author_name":
            pass
            # dropdown = UserGroups.objects.filter(product_id=product_id).annotate(key=F('input_process_type'), value=F('input_process_type')).values_list('key', 'value')
            dropdown = list(UserGroups.objects.filter(group_id=30, user__name__icontains=q).annotate(id=F('user__id'),value=F('user__name')).values('id', 'value')[:20])
            print("thsi sis the dropdown  ", dropdown)
            # dropdown = [{"id": key, "value": value} for key, value in dropdown]

        elif field_name == "tools_name":
            tools = CPProductCampaign.objects.filter(name__icontains=q).values("id", "name").order_by("name")
            if product_type:
                tools = tools.filter(type=product_type).values("id", "name").order_by("name")
            dropdown = [
                {"id": tool["id"], "value": tool["name"], "selected": selected_id == tool["id"]}
                for tool in tools
            ]
            
        elif field_name == "tools_type":
            dropdown = [{"id": key, "value": val, "selected": selected_id == key} for key, val in TOOL_TYPE.items()]

        elif field_name == "mapped_process_type":
            dropdown = [
                {
                    "id": key,
                    "value": FORM_INPUT_PROCESS_TYPE.get(val, "Unknown"),
                    "selected": selected_id == key
                }
                for key, val in CnextRpCreateInputForm.objects.filter(product_id=product_id)
                .annotate(key=F('input_process_type'), value=F('input_process_type'))
                .values_list('key', 'value')
            ]

        elif field_name == "rp_field_type":
            dropdown = [{"id": key, "value": val, "selected": selected_id == key} for key, val in RP_FIELD_TYPE.items()]

        elif field_name == "exam":
            published_exam_list = Exam.objects.exclude(type_of_exam='counselling').exclude(status='unpublished')
            exam_list = (
                published_exam_list
                .filter(instance_id=0)
                .filter(Q(exam_name__icontains=q) | Q(exam_short_name__icontains=q))
                .values('id', 'exam_name', 'parent_exam_id', 'exam_short_name')
            )

            dropdown = []
            exam_mappings = {exam['id']: exam for exam in exam_list if exam['parent_exam_id'] == 0}

            for exam in exam_list:
                parent_id = exam['parent_exam_id']
                if parent_id == 0:  # Parent exam
                    dropdown.append({
                        'id': exam['id'],
                        'exam_name': exam['exam_name'],
                        'exam_short_name': exam['exam_short_name']
                    })
                elif parent_id in exam_mappings:  # Child exam
                    parent_exam = exam_mappings[parent_id]
                    dropdown.append({
                        'id': exam['id'],
                        'exam_name': exam['exam_name'],
                        'exam_short_name': exam['exam_short_name'],
                        'parent_exam_name': parent_exam['exam_name'],
                        'parent_exam_short_name': parent_exam['exam_short_name']
                    })

        else:
            dropdown_data["message"] = "Invalid field name"

        if not internal_limit and dropdown:
            dropdown = dropdown[self.offset:self.offset + self.limit]

        dropdown_data[field_name] = dropdown
        return dropdown_data
