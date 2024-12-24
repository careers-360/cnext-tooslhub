from tools.models import CPProductCampaign
from rank_predictor.models import RpFormField

class RPHelper:

    def __init__(self):
        pass

    def _get_header_section(self, product_id=None):

        header_data = CPProductCampaign.objects.filter(id=product_id).values("id", "header_section", "custom_exam_name", "custom_flow_type", "custom_year", "video", "usage_count_matrix", "positive_feedback_percentage")

        return header_data
    

class RPFormHelper:

    def __init__(self):
        pass

    def _get_form_section(self, product_id=None):

        form_data = RpFormField.objects.filter(product_id=product_id).values("field_type", "input_flow_type", "display_name", "place_holder_text", "error_message", "weight", "mapped_process_type", "mandatory", "status")

        return form_data
    