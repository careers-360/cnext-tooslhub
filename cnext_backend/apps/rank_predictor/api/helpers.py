from django.conf import settings
from rank_predictor.models import RpContentSection, RpInputFlowMaster, RpResultFlowMaster
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

