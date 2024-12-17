from django.conf import settings
from django.db.models import Max
from datetime import datetime, timedelta
from rank_predictor.models import RpContentSection, RpInputFlowMaster, RpResultFlowMaster, CnextRpSession
from tools.models import CPProductCampaign, CollegeCourse, CPFeedback
from .static_mappings import RP_DEFAULT_FEEDBACK


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

        result_id = kwargs.get("result_id")
        result_type = kwargs.get("result_type")
        result_flow_type = kwargs.get("result_flow_type")
        result_process_type = kwargs.get("result_process_type")
       
        input_flow = self._get_rp_input_flow_types(input_id=input_id, input_type=input_type, input_flow_type=input_flow_type, input_process_type=input_process_type)
        result_flow = self._get_rp_result_flow_types(result_id=result_id, result_type=result_type, result_flow_type=result_flow_type, result_process_type=result_process_type)

        data = {
            "input_flow": input_flow,
            "result_flow": result_flow
        }
        return data

    def _get_rp_input_flow_types(self, input_id=None, input_type=None, input_flow_type=None, input_process_type=None):
        # Fetch input flow type from database based on rp_id
        input_flow_type_data = []
        if input_id:
            input_flow_type_data = list(RpInputFlowMaster.objects.filter(id=input_id, status=1).values("id","input_flow_type", "input_type", "input_process_type").first())
    
        elif input_flow_type:
            input_flow_type_data = list(RpInputFlowMaster.objects.filter(input_flow_type__contains=input_flow_type, status=1).values("id","input_flow_type", "input_type", "input_process_type").first())
    
        elif input_type:
            input_flow_type_data = list(RpInputFlowMaster.objects.filter(input_type__contains=input_type, status=1).values("id","input_flow_type", "input_type", "input_process_type").first())
    
        elif input_process_type:
            input_flow_type_data = list(RpInputFlowMaster.objects.filter(input_process_type__contains=input_process_type, status=1).values("id","input_flow_type", "input_type", "input_process_type").first())

        else:
            input_flow_type_data = list(RpInputFlowMaster.objects.filter(status=1).values("id","input_flow_type", "input_type", "input_process_type").order_by("-updated"))

        return input_flow_type_data
    
    def _get_rp_result_flow_types(self, result_id=None, result_type=None, result_flow_type=None, result_process_type=None):
        # Fetch input flow type from database based on rp_id
        result_flow_type_data = []
        if result_id:
            result_flow_type_data = list(RpResultFlowMaster.objects.filter(id=result_id, status=1).values("id","result_flow_type", "result_type", "result_process_type").first())
    
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

    def _get_student_appeared_data(self, product_id, year):
        if year:
            year = int(year) 
    
        student_data = {
            "product_id": product_id,
            "year": year,
            "count": 0,
            "student_appeared_data": []
        }
        # Fetch student appeared data from database
        rp_session_data = CnextRpSession.objects.filter(product_id=product_id, status=1)
        if year:
            rp_session_year_data = list(rp_session_data.filter(year=year).values("id", "product_id", "year", "session_date", "session_shift", "difficulty"))
            if rp_session_year_data:
                student_data["year"] = year
                student_data["count"] = len(rp_session_year_data) 
                student_data["student_appeared_data"] = rp_session_year_data 
        
        if not student_data["student_appeared_data"]:
            rp_max_year = rp_session_data.aggregate(Max('year'))['year__max']
            rp_session_data = list(rp_session_data.filter(year=rp_max_year).values("id", "product_id", "year", "session_date", "session_shift", "difficulty"))
            if rp_session_data:
                student_data["year"] = rp_max_year 
                student_data["count"] = len(rp_session_data) 
                student_data["student_appeared_data"] = rp_session_data

        shift_choices = dict(CnextRpSession.SHIFT_ENUM)
        difficulty_choices = dict(CnextRpSession.DIFFICULTY_ENUM)

        for item in student_data["student_appeared_data"]:
            item["session_shift_name"] = shift_choices.get(item["session_shift"]) if item.get("session_shift") else ""
            item["difficulty_name"] = difficulty_choices.get(item["difficulty"]) if item.get("difficulty") else ""
            item["session_date"] = item["session_date"].strftime("%Y-%m-%d") if item.get("session_date") else None

        return student_data
    
    def _add_student_appeared_data(self, student_data, product_id, year):
        
        if not year:
            year = datetime.today().year
        
        if not product_id or not year or not isinstance(student_data, list):
            return False, "Missing arguments or Incorrect data type"
        
        rp_session_ids = list(CnextRpSession.objects.filter(product_id=product_id, year=year).values_list("id",flat=True))
        incomming_ids = [row_["id"] for row_ in student_data if row_.get("id")]
        rp_session_mapping = {row_["id"]:row_ for row_ in student_data if row_.get("id")}

        error = []
        to_create = []
        to_update = CnextRpSession.objects.filter(id__in=incomming_ids)

        # Delete non existing records
        non_common_ids = set(rp_session_ids) - set(incomming_ids)
        CnextRpSession.objects.filter(product_id=product_id, year=year, id__in=non_common_ids).delete()

        # Create new records
        for new_row in student_data:
            session_date = self.convert_str_to_datetime(new_row.get('session_date'))
            session_shift = new_row.get('session_shift')
            difficulty = new_row.get('difficulty')

            if not session_date or not session_shift or not difficulty:
                error.append({"row":new_row, "message": "Incorrect data"})
                continue

            if not new_row.get("id"):
                to_create.append(CnextRpSession(product_id=product_id, year=year, session_date=session_date, session_shift=session_shift, difficulty=difficulty))
        
        if to_create:
            CnextRpSession.objects.bulk_create(to_create)

        # Update records
        for row_ in to_update:
            row_id = row_.id
            session_date = rp_session_mapping[row_id].get("session_date") #datetime.strptime(row_["session_date"], '%Y-%m-%d').date()
            session_shift = rp_session_mapping[row_id].get("session_shift")
            difficulty = rp_session_mapping[row_id].get("difficulty")
            if not session_date or not session_shift or not difficulty:
                error.append({"id":row_id, "message": "Incorrect data"})
                continue

            row_.session_date = self.convert_str_to_datetime(session_date)
            row_.session_shift = session_shift
            row_.difficulty = difficulty

        if incomming_ids:
            CnextRpSession.objects.bulk_update(to_update, ["session_date", "session_shift", "difficulty"])
        
        final_output = {
            "message": "Successfully created session",
            "error": error,
            "student_appeared_data": student_data,
            "count": len(student_data) - len(error)
        }
        return True, final_output
    
    def convert_str_to_datetime(self, str_to_datetime):
        try:
            return datetime.strptime(str_to_datetime, '%Y-%m-%d') + timedelta(hours=6, minutes=31)
        except ValueError:
            return None
