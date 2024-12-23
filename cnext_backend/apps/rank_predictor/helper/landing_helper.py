from tools.models import CPProductCampaign

class RPHelper:

    def __init__(self):
        pass

    def _get_header_section(self, product_id=None):

        header_data = CPProductCampaign.objects.filter(id=product_id).values("id", "header_section", "custom_exam_name", "custom_flow_type", "custom_year", "video", "usage_count_matrix", "positive_feedback_percentage")

        return header_data
    