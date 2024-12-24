from wsgiref import validate
from tools.models import CPProductCampaign, CPTopCollege

class RPHelper:

    def __init__(self):
        pass

    def _get_header_section(self, product_id=None):

        header_data = CPProductCampaign.objects.filter(id=product_id).values("id", "header_section", "custom_exam_name", "custom_flow_type", "custom_year", "video")

        return header_data
    

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
        
        
    # def calculate_percentile(self, score, max_score):
    #     """
    #     Calculate percentile from score
    #     Formula: (score / max_score) * 100
    #     """
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