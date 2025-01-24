from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django.core.exceptions import ValidationError
import logging
from utils.helpers.custom_permission import ApiKeyPermission

from college_compare.api.serializers.comparison_result_page_serialzers import FeedbackSubmitSerializer
from utils.helpers.response import SuccessResponse, CustomErrorResponse

from college_compare.api.helpers.comparison_result_page_helpers import (RankingAccreditationHelper,ExamCutoffGraphHelper,CollegeReviewAiInsightHelper,FeesAiInsightHelper,ClassProfileAiInsightHelper,RankingAiInsightHelper,PlacementAiInsightHelper,NoDataAvailableError,CollegeAmenitiesHelper,PlacementInsightHelper,CollegeReviewsRatingGraphHelper,MultiYearRankingHelper,CollegeRankingService,PlacementGraphInsightsHelper,FeesGraphHelper,ProfileInsightsHelper,RankingGraphHelper,CourseFeeComparisonHelper,FeesHelper,CollegeFacilitiesHelper,ClassProfileHelper,CollegeReviewsHelper,ExamCutoffHelper)



import logging
import traceback

logger = logging.getLogger(__name__)

import time

current_year = time.localtime().tm_year



class RankingAccreditationComparisonView(APIView):
    permission_classes = [ApiKeyPermission]

    @extend_schema(
        summary="Get Ranking and Accreditation Comparison",
        description="Retrieve ranking and accreditation data for given colleges, optionally filtered by year. Accepts a comma-separated list of course IDs.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='course_ids', type=str, description='Comma-separated list of course IDs (optional). Must align with college_ids.', required=False),
            OpenApiParameter(name='year', type=int, description='Year for filtering rankings (optional)', required=False),
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved ranking and accreditation comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            404: OpenApiResponse(description='No data available for the provided inputs'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids_str = request.query_params.get('college_ids')
        course_ids_str = request.query_params.get('course_ids')
        year = request.query_params.get('year') or current_year - 1

        try:
            if not college_ids_str:
                raise ValidationError("college_ids parameter is required.")

            college_ids = [int(cid) for cid in college_ids_str.split(',')]

            course_ids = (
                [int(course_id) for course_id in course_ids_str.split(',')]
                if course_ids_str else None
            )

            if course_ids and len(college_ids) != len(course_ids):
                raise ValidationError("The number of college_ids and course_ids must be the same if course_ids are provided.")

            course_ids_dict = (
                {college_ids[i]: course_ids[i] for i in range(len(college_ids))}
                if course_ids else {}
            )

            print(course_ids_dict)

            year = int(year) if year else None

            result = RankingAccreditationHelper.fetch_ranking_data(college_ids, course_ids_dict, year)
            return SuccessResponse(result, status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)

        except NoDataAvailableError as nde:
            logger.warning(f"No data available: {nde}")
            return CustomErrorResponse({"error": str(nde)}, status=status.HTTP_404_NOT_FOUND)

        except ValueError:
            logger.error("Invalid input format. college_ids and course_ids must be comma-separated integers.")
            return CustomErrorResponse({"error": "Invalid input format. college_ids and course_ids must be comma-separated integers."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error fetching ranking and accreditation comparison: {traceback.format_exc()}")
            return CustomErrorResponse({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class RankingAccreditationCombinedComparisonView(APIView):
    permission_classes = [ApiKeyPermission]

    @extend_schema(
        summary="Get Ranking and Accreditation Comparison",
        description="Retrieve ranking and accreditation data for given colleges, optionally filtered by year, and includes combined and multi-year data.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='course_ids', type=str, description='Comma-separated list of course IDs for ranking', required=True),
            OpenApiParameter(name='year', type=int, description='Year for filtering rankings (optional)', required=False),
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved ranking and accreditation comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            404: OpenApiResponse(description='No data available for the provided inputs'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids = request.query_params.get('college_ids')
        course_ids_str = request.query_params.get('course_ids')
        print(course_ids_str)
        year_str = request.query_params.get('year') or current_year - 1

        try:
            if not college_ids or not course_ids_str or not year_str:
                raise ValidationError("Both college_ids, course_ids, and year are required.")

            college_ids_list = [int(cid) for cid in college_ids.split(',')]
            course_ids_list = [int(cid) for cid in course_ids_str.split(',')]

            if len(college_ids_list) != len(course_ids_list):
                raise ValidationError("The number of college_ids must match the number of course_ids.")

            # Create course_ids_dict using college_ids_list and course_ids_list
            course_ids_dict = dict(zip(college_ids_list, course_ids_list))

            year = int(year_str)

            # Fetch ranking data for current and previous years
            ranking_data_current_year = RankingAccreditationHelper.fetch_ranking_data(
                college_ids_list, course_ids_dict, year
            )
            
            ranking_data_previous_year = RankingAccreditationHelper.fetch_ranking_data(
                college_ids_list, course_ids_dict, year - 1
            )

            # Rest of the code remains the same...
            combined_ranking_data_current_year = CollegeRankingService.get_state_and_ownership_ranks(
                college_ids_list, course_ids_list, year
            )

            combined_ranking_data_previous_year = CollegeRankingService.get_state_and_ownership_ranks(
                college_ids_list, course_ids_list, year - 1
            )

            years = [year - i for i in range(5)]
            multi_year_ranking_data = MultiYearRankingHelper.fetch_multi_year_ranking_data(
                college_ids_list, course_ids_list, years
            )
            result = {
                "current_year_data": ranking_data_current_year,
                "previous_year_data": ranking_data_previous_year,
                "current_combined_ranking_data": combined_ranking_data_current_year,
                "previous_combined_ranking_data": combined_ranking_data_previous_year,
                "multi_year_ranking_data": multi_year_ranking_data,
            }

            print(result)

          
            insights = RankingAiInsightHelper.generate_ranking_insights(result)
            result['insights'] = insights

            # Return successful response with insights
            return SuccessResponse(result['insights'], status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)

        except NoDataAvailableError as nde:
            logger.warning(f"No data available: {nde}")
            return CustomErrorResponse({"error": str(nde)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error fetching ranking and accreditation comparison: {traceback.format_exc()}")
            return CustomErrorResponse({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RankingGraphInsightsView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Ranking Graph Insights",
        description="Retrieve ranking graph insights (overall and domain-specific) for given colleges over a specified year range.",
        parameters=[
            OpenApiParameter(
                name="college_ids",
                type=str,
                description="Comma-separated list of college IDs",
                required=True,
            ),
            OpenApiParameter(
                name="start_year",
                type=int,
                description="Starting year for the range",
                required=False,
            ),
            OpenApiParameter(
                name="end_year",
                type=int,
                description="Ending year for the range",
                required=False,
            ),
            OpenApiParameter(
                name="selected_domains",
                type=str,
                description="Comma-separated list of Domain IDs corresponding to the college IDs",
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(description="Successfully retrieved ranking graph insights"),
            400: OpenApiResponse(description="Invalid parameters"),
            404: OpenApiResponse(description="No data available for the provided inputs"),
            500: OpenApiResponse(description="Internal server error"),
        },
    )
    def get(self, request):
        college_ids = request.query_params.get("college_ids")
        start_year = request.query_params.get("start_year") or current_year - 6
        end_year = request.query_params.get("end_year") or current_year - 1
        selected_domains = request.query_params.get("selected_domains")

        try:
            if not college_ids or not start_year or not end_year or not selected_domains:
                raise ValidationError("college_ids, start_year, end_year, and selected_domains are required.")

            college_ids_list = [int(cid) for cid in college_ids.split(",")]
            selected_domains_list = [int(did) for did in selected_domains.split(",")]

            if len(college_ids_list) != len(selected_domains_list):
                raise ValidationError("The number of college_ids must match the number of selected_domains.")

            start_year = int(start_year)
            end_year = int(end_year)

            if start_year > end_year:
                raise ValidationError("start_year must be less than or equal to end_year.")

            domain_mapping = dict(zip(college_ids_list, selected_domains_list))

            result = RankingGraphHelper.prepare_graph_insights(college_ids_list, start_year, end_year, domain_mapping)
            if not result:
                raise NoDataAvailableError("No ranking graph insights available for the provided inputs.")

            return SuccessResponse(result, status=status.HTTP_200_OK)

        except ValidationError as ve:
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)

        except NoDataAvailableError as nde:
            logger.warning(f"No data available: {nde}")
            return CustomErrorResponse({"error": str(nde)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error fetching ranking graph insights: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlacementStatsComparisonView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Placement Stats Comparison",
        description="Retrieve placement stats comparison for given colleges and courses, allowing different domains per college.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='year', type=str, description='Year', required=False),
            OpenApiParameter(name='selected_domains', type=str, description='Comma-separated list of Domain IDs corresponding to the college IDs', required=True)
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved placement stats comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids_str = request.query_params.get('college_ids')
        year_str = request.query_params.get('year') or str(current_year - 2)
        domain_ids_str = request.query_params.get('selected_domains')

        try:
            if not college_ids_str or not domain_ids_str:
                raise ValidationError("college_ids and domain_ids are required")

            try:
                college_ids = [int(cid) for cid in college_ids_str.split(',')]
                domain_ids = [int(did) for did in domain_ids_str.split(',')]
                year = int(year_str)
            except ValueError:
                raise ValidationError("college_ids, domain_ids and year must be integers")
            
            if len(college_ids) != len(domain_ids):
                raise ValidationError("The number of college_ids must match the number of domain_ids")

            selected_domains = {college_id: domain_id for college_id, domain_id in zip(college_ids, domain_ids)}
            
            result = PlacementInsightHelper.fetch_placement_stats(college_ids, selected_domains, year)
            return SuccessResponse(result, status=status.HTTP_200_OK)

        except NoDataAvailableError as e:
            logger.error(f"No data available for placement stats comparison: {str(e)}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching placement stats comparison: {traceback.format_exc()}")  # Use traceback for more detailed error
            return CustomErrorResponse({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlacementStatsAIinsightsComparisonView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Placement Stats AI insights Comparison",
        description="Retrieve placement stats comparison for given colleges and courses, allowing different domains per college.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='year', type=str, description='Year', required=False),
            OpenApiParameter(name='selected_domains', type=str, description='Comma-separated list of Domain IDs corresponding to the college IDs', required=True)
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved placement stats comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids_str = request.query_params.get('college_ids')
        year_str = request.query_params.get('year') or str(current_year - 2)
        domain_ids_str = request.query_params.get('selected_domains')

        try:
            if not college_ids_str or not domain_ids_str:
                raise ValidationError("college_ids and domain_ids are required")

            try:
                college_ids = [int(cid) for cid in college_ids_str.split(',')]
                domain_ids = [int(did) for did in domain_ids_str.split(',')]
                year = int(year_str)
            except ValueError:
                raise ValidationError("college_ids, domain_ids and year must be integers")
            
            if len(college_ids) != len(domain_ids):
                raise ValidationError("The number of college_ids must match the number of domain_ids")

            selected_domains = {college_id: domain_id for college_id, domain_id in zip(college_ids, domain_ids)}
            
            result = PlacementInsightHelper.fetch_placement_stats(college_ids, selected_domains, year)

            ai_helper = PlacementAiInsightHelper()
            insights = ai_helper.get_ai_insights(result)
            
         
            result['insights']=insights
            return SuccessResponse( result['insights'], status=status.HTTP_200_OK)

        except NoDataAvailableError as e:
            logger.error(f"No data available for placement ai insights comparison: {str(e)}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching placement ai insights  comparison: {traceback.format_exc()}")  # Use traceback for more detailed error
            return CustomErrorResponse({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlacementGraphInsightsView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Placement Graph Insights",
        description="Retrieve placement insights including placement percentages, salary data, and recruiter information for given colleges, allowing different domains per college.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='selected_domains', type=str, description='Comma-separated list of Domain IDs corresponding to the college IDs', required=True),
            OpenApiParameter(name='year', type=str, description='Academic year', required=False),
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved placement insights'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids_str = request.query_params.get('college_ids')
        domain_ids_str = request.query_params.get('selected_domains')
        year_str = request.query_params.get('year') or str(current_year - 2)

        try:
            if not college_ids_str or not domain_ids_str:
                raise ValidationError("college_ids and selected_domains are required parameters")

            try:
                college_ids = [int(cid) for cid in college_ids_str.split(',')]
                domain_ids = [int(did) for did in domain_ids_str.split(',')]
                year = int(year_str)
            except ValueError:
                raise ValidationError("college_ids, selected_domains, and year must be integers")

            if len(college_ids) != len(domain_ids):
                raise ValidationError("The number of college_ids must match the number of selected_domains")
            
            selected_domains = {college_id: domain_id for college_id, domain_id in zip(college_ids, domain_ids)}

            result = PlacementGraphInsightsHelper.fetch_placement_insights(
                college_ids=college_ids,
                selected_domains=selected_domains,
                year=year
            )

            return SuccessResponse(result, status=status.HTTP_200_OK)

        except NoDataAvailableError as e:
            logger.error(f"No data available for placement insights: {str(e)}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching placement insights: {traceback.format_exc()}")
            return CustomErrorResponse({"error": "An error occurred while fetching placement insights"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CourseFeeComparisonView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Course Fee Comparison",
        description="Retrieve course fee comparison for given colleges and courses.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='course_ids', type=str, description='Comma-separated list of course IDs', required=True),
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved course fee comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids = request.query_params.get('college_ids')
        course_ids = request.query_params.get('course_ids')

        try:
            if not college_ids or not course_ids:
                raise ValidationError("Both college_ids and course_ids are required")

            college_ids_list = [int(cid) for cid in college_ids.split(',')]
            course_ids_list = [int(cid) for cid in course_ids.split(',')]

            result = CourseFeeComparisonHelper.fetch_comparison_data(college_ids_list, course_ids_list)
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except NoDataAvailableError as e:
            logger.error(f"No data available for course_and_fees insights: {str(e)}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching course fee comparison: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeesComparisonView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Fees Comparison",
        description="Retrieve Fees comparison data for given colleges and courses.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
              OpenApiParameter(name='course_ids', type=str, description='Comma-separated list of coursee IDs', required=True),
               OpenApiParameter(name='intake_year', type=str, description='year of admission ', required=False)

           
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved summary comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids = request.query_params.get('college_ids')
        course_ids = request.query_params.get('course_ids')
        intake_year = request.query_params.get('intake_year') or current_year-2
      

        try:
            if not college_ids and course_ids:
                raise ValidationError("Both  college_ids and course_ids are required")

            college_ids_list = [int(cid) for cid in college_ids.split(',')]
            course_ids_list = [int(cid) for cid in course_ids.split(',')]

            print(college_ids_list,course_ids_list)
            

            result = FeesHelper.fetch_fees_details(course_ids_list,college_ids_list,intake_year)            
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except NoDataAvailableError as e:
            logger.error(f"No data available for fees comparison: {str(e)}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching fees comparison: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class FeesAIinsightsComparisonView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Fees ai insights Comparison",
        description="Retrieve Fees comparison data for given colleges and courses.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
              OpenApiParameter(name='course_ids', type=str, description='Comma-separated list of coursee IDs', required=True),
               OpenApiParameter(name='intake_year', type=str, description='year of admission ', required=False)

           
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved summary comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids = request.query_params.get('college_ids')
        course_ids = request.query_params.get('course_ids')
        intake_year = request.query_params.get('intake_year') or current_year-2
      

        try:
            if not college_ids and course_ids:
                raise ValidationError("Both  college_ids and course_ids are required")

            college_ids_list = [int(cid) for cid in college_ids.split(',')]
            course_ids_list = [int(cid) for cid in course_ids.split(',')]


            

            result = FeesHelper.fetch_fees_details(course_ids_list,college_ids_list,intake_year)
            # helper = FeesAiInsightHelper()

            insights=FeesAiInsightHelper.get_fees_insights(fees_data=result)
            result['insights']=insights
            return SuccessResponse( result['insights'], status=status.HTTP_200_OK)
        except NoDataAvailableError as e:
            logger.error(f"No data available for fees ai insights comparison: {str(e)}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching fees comparison: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class FeesGraphInsightsView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Fees Graph Insights",
        description="Retrieve fee graph insights for given course IDs.",
        parameters=[
            OpenApiParameter(
                name="course_ids",
                type=str,
                description="Comma-separated list of course IDs",
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Successfully retrieved fee graph insights",
                examples={
                    "application/json": {
                        "categories": ["gn", "obc", "sc"],
                        "data": {
                            "gn": {
                                "college_1": {
                                    "college_id": 55,
                                    "fee": "₹ 850,000"
                                },
                                "college_2": {
                                    "college_id": 5658,
                                    "fee": "₹ 900,000"
                                }
                            },
                            "obc": {
                                "college_1": {
                                    "college_id": None,
                                    "fee": "NA"
                                }
                            },
                            "sc": {
                                "college_1": {
                                    "college_id": 57,
                                    "fee": "₹ 750,000"
                                }
                            }
                        },
                        "college_names": [
                            "Indian Institute of Technology Delhi",
                            "Indian Institute of Technology Gandhinagar",
                            "Indian Institute of Technology Roorkee"
                        ]
                    }
                },
            ),
            400: OpenApiResponse(description="Invalid parameters"),
            500: OpenApiResponse(description="Internal server error"),
        },
    )
    def get(self, request):
        course_ids = request.query_params.get("course_ids")

        try:
            if not course_ids:
                raise ValidationError("course_ids is required")

            course_ids_list = [int(cid) for cid in course_ids.split(",")]

            result = FeesGraphHelper.prepare_fees_insights(course_ids_list)
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except ValidationError as ve:
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching fee graph insights: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class ClassProfileComparisonView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Class Profile Comparison",
        description="Retrieve class profile comparison data for given colleges",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='year', type=str, description='Year', required=True),
            OpenApiParameter(name='intake_year', type=str, description='Year of admission', required=False),
            OpenApiParameter(name='level', type=str, description='Level of course', required=True),
            OpenApiParameter(name='selected_domains', type=str, description='Comma-separated list of Domain IDs corresponding to the college IDs', required=True)
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved summary comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids_str = request.query_params.get('college_ids')
        year_str = request.query_params.get('year') or str(current_year - 2)
        intake_year_str = request.query_params.get('intake_year') or str(current_year - 5)
        level = request.query_params.get('level', 1)
        domain_ids_str = request.query_params.get("selected_domains")

        try:
         
            if not college_ids_str or not domain_ids_str:
                raise ValidationError("Both college_ids and selected_domains are required")

    
            try:
                college_ids = [int(cid) for cid in college_ids_str.split(",")]
                domain_ids = [int(did) for did in domain_ids_str.split(",")]
                year = int(year_str)
                intake_year = int(intake_year_str)
                level = int(level)
            except ValueError:
                raise ValidationError("college_ids, selected_domains, year, and intake_year must be integers")

            if len(college_ids) != len(domain_ids):
                raise ValidationError("The number of college_ids must match the number of domain_ids")

            if intake_year > year:
                raise ValidationError("intake_year must be less than or equal to year")

   
            selected_domains = {college_id: domain_id for college_id, domain_id in zip(college_ids, domain_ids)}

        
            result = ClassProfileHelper.fetch_class_profiles(
                college_ids=college_ids,
                year=year,
                intake_year=intake_year,
                level=level,
                selected_domains=selected_domains  #
            )

            return SuccessResponse(result, status=status.HTTP_200_OK)
        except NoDataAvailableError as e:
            logger.error(f"No data available for class Profile comparison: {str(e)}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching class profile comparison: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProfileInsightsView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Profile Insights",
        description="Retrieve comprehensive profile insights including student-faculty ratio, demographics, and gender diversity for given colleges.",
        parameters=[
            OpenApiParameter(
                name="college_ids",
                type=str,
                description="Comma-separated list of college IDs",
                required=True,
            ),
            OpenApiParameter(
                name="year",
                type=int,
                description="Academic year",
                required=False,
            ),
            OpenApiParameter(
                name="intake_year",
                type=int,
                description="Year of student intake",
                required=False,
            ),
            OpenApiParameter(
                name="selected_domains",
                type=str,
                description="Comma-separated list of Domain IDs corresponding to the college IDs",
                required=True,
            ),
            OpenApiParameter(
                name="level",
                type=int,
                description="Academic level (defaults to 1)",
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Successfully retrieved profile insights",
                examples={
                    "application/json": {
                        "year": 2023,
                        "intake_year": 2019,
                        "level": 1,
                        "type": "tabular",
                        "data": {
                            "student_faculty_ratio": {...},
                            "student_from_outside_state": {...},
                            "gender_diversity": {...},
                        },
                        "college_details": [...],
                    }
                },
            ),
            400: OpenApiResponse(description="Invalid parameters"),
            500: OpenApiResponse(description="Internal server error"),
        },
    )
    def get(self, request):
        """
        GET endpoint to retrieve profile insights for specified colleges.
        """
        college_ids_str = request.query_params.get("college_ids")
        year_str = request.query_params.get("year") or str(current_year - 1)
        intake_year_str = request.query_params.get("intake_year") or str(current_year - 5)
        level = request.query_params.get("level", 1)
        domain_ids_str = request.query_params.get("selected_domains")

        try:
            
            if not college_ids_str or not domain_ids_str:
                
                raise ValidationError("college_ids and selected_domains are required")

        
            try:
                college_ids = [int(cid) for cid in college_ids_str.split(",")]
                domain_ids = [int(did) for did in domain_ids_str.split(",")]
                year = int(year_str)
                intake_year = int(intake_year_str)
                level = int(level)
            except ValueError:
                raise ValidationError("college_ids, selected_domains, year, and intake_year must be integers")

            if len(college_ids) != len(domain_ids):
                raise ValidationError("The number of college_ids must match the number of domain_ids")

            if intake_year > year:
                raise ValidationError("intake_year must be less than or equal to year")

            # Create a mapping of college IDs to domain IDs
            selected_domains = {college_id: domain_id for college_id, domain_id in zip(college_ids, domain_ids)}

            # Fetch and prepare the profile insights
            print(selected_domains)
            result = ProfileInsightsHelper.prepare_profile_insights(
                college_ids=college_ids,
                year=year,
                intake_year=intake_year,
                selected_domains=selected_domains,
                level=level,
            )

            return SuccessResponse(result, status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching profile insights: {traceback.format_exc()}")
            return CustomErrorResponse({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class classProfileAIInsightsView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Profile Insights",
        description="Retrieve comprehensive profile insights including student-faculty ratio, demographics, and gender diversity for given colleges.",
        parameters=[
            OpenApiParameter(
                name="college_ids",
                type=str,
                description="Comma-separated list of college IDs",
                required=True,
            ),
            OpenApiParameter(
                name="year",
                type=int,
                description="Academic year",
                required=False,
            ),
            OpenApiParameter(
                name="intake_year",
                type=int,
                description="Year of student intake",
                required=False,
            ),
            OpenApiParameter(
                name="selected_domains",
                type=str,
                description="Comma-separated list of Domain IDs corresponding to the college IDs",
                required=True,
            ),
            OpenApiParameter(
                name="level",
                type=int,
                description="Academic level (defaults to 1)",
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Successfully retrieved profile insights",
                examples={
                    "application/json": {
                        "year": 2023,
                        "intake_year": 2019,
                        "level": 1,
                        "type": "tabular",
                        "data": {
                            "student_faculty_ratio": {...},
                            "student_from_outside_state": {...},
                            "gender_diversity": {...},
                        },
                        "college_details": [...],
                    }
                },
            ),
            400: OpenApiResponse(description="Invalid parameters"),
            500: OpenApiResponse(description="Internal server error"),
        },
    )
    def get(self, request):
        """
        GET endpoint to retrieve profile insights for specified colleges.
        """
        college_ids_str = request.query_params.get("college_ids")
        year_str = request.query_params.get("year") or str(current_year - 1)
        intake_year_str = request.query_params.get("intake_year") or str(current_year - 5)
        level = request.query_params.get("level", 1)
        domain_ids_str = request.query_params.get("selected_domains")

        try:
            
            if not college_ids_str or not domain_ids_str:
                raise ValidationError("college_ids and selected_domains are required")

        
            try:
                college_ids = [int(cid) for cid in college_ids_str.split(",")]
                domain_ids = [int(did) for did in domain_ids_str.split(",")]
                year = int(year_str)
                intake_year = int(intake_year_str)
                level = int(level)
            except ValueError:
                raise ValidationError("college_ids, selected_domains, year, and intake_year must be integers")

            if len(college_ids) != len(domain_ids):
                raise ValidationError("The number of college_ids must match the number of domain_ids")

            # if intake_year > year:
            #     raise ValidationError("intake_year must be less than or equal to year")

    
            selected_domains = {college_id: domain_id for college_id, domain_id in zip(college_ids, domain_ids)}

        
            
            result = ProfileInsightsHelper.prepare_profile_insights(
                college_ids=college_ids,
                year=year,
                intake_year=intake_year,
                selected_domains=selected_domains,
                level=level,
            )

            

            insights=ClassProfileAiInsightHelper.get_profile_insights(data=result)
            result['insights']=insights

            return SuccessResponse(result['insights'], status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching profile insights: {traceback.format_exc()}")
            return CustomErrorResponse({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CollegeFacilitiesComparisonView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get College Facilities Comparison",
        description="Retrieve  college facilities comparison data for given colleges",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),           
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved summary comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids = request.query_params.get('college_ids')

        try:
            if not college_ids:
                raise ValidationError("Here college_ids  are required")

            college_ids_list = [int(cid) for cid in college_ids.split(',')],
                   
            result = CollegeFacilitiesHelper.get_college_facilities(college_ids_list)
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching college Facilities comparison: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CollegeAmenitiesComparisonView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get College Amenities Comparison",
        description="Retrieve college amenities comparison data for given colleges",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved amenities comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        """
        Retrieve amenities comparison data for the specified colleges.
        """
        college_ids = request.query_params.get('college_ids')

        try:
            if not college_ids:
                raise ValidationError("The 'college_ids' parameter is required.")

        
            college_ids_list = [int(cid) for cid in college_ids.split(',')]

    
            result = CollegeAmenitiesHelper.get_college_amenities(college_ids_list)
            return SuccessResponse(result, status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching college amenities comparison: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CollegeReviewsComparisonView(APIView):
    """
    API view for comparing reviews across multiple colleges.
    Provides both detailed review summaries and recent reviews.
    """
    permission_classes = [ApiKeyPermission]
    
    def __init__(self, **kwargs):
        """
        Initialize the view with a CollegeReviewsHelper instance.
        """
        super().__init__(**kwargs)
        self.reviews_helper = CollegeReviewsHelper()

    @extend_schema(
        summary="Get College Reviews Comparison",
        description="Retrieve reviews summary and recent reviews for multiple colleges",
        parameters=[
            OpenApiParameter(
                name='college_ids', 
                type=str, 
                description='Comma-separated list of college IDs',
                required=True
            ),
            OpenApiParameter(
                name='course_ids', 
                type=str, 
                description='Comma-separated list of course IDs for filtering reviews',
                required=False
            ),
            OpenApiParameter(
                name='grad_year',
                type=int,
                description='Graduation year for filtering reviews',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved reviews comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        """
        Handle GET requests for college reviews comparison.
        
        Args:
            request: HTTP request object with query parameters
                - college_ids: Comma-separated list of college IDs
                - course_ids: Comma-separated list of course IDs (optional)
                - grad_year: Graduation year for filtering reviews
                
        Returns:
            Response: JSON response containing reviews summary and recent reviews
        """
        try:
            college_ids = request.query_params.get('college_ids')
            course_ids = request.query_params.get('course_ids')
            grad_year = request.query_params.get('grad_year') or current_year -2

            if not college_ids or not grad_year:
                raise ValidationError("Both college_ids and grad_year are required")

            college_ids_list = [int(cid) for cid in college_ids.split(',')]
            course_ids_list = [int(cid) for cid in course_ids.split(',')] if course_ids else []

            reviews_summary = self.reviews_helper.get_college_reviews_summary(
                college_ids=college_ids_list,
                grad_year=int(grad_year)
            )
            
            recent_reviews = CollegeReviewsHelper.get_recent_reviews(
                college_ids_list,
                limit=3
            )
            
        
            if course_ids_list:

                reviews_summary = self.reviews_helper.get_college_reviews_summary(
                    college_ids=college_ids_list,
                    course_ids_list=course_ids_list,
                    grad_year=int(grad_year)
                )
            
            


            


            result = {
                'reviews_summary': reviews_summary,
                'recent_reviews': recent_reviews,
            }
            
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except NoDataAvailableError as e:
            logger.error(f"No data available for college rating & reviews: {str(e)}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse(
                {"error": str(ve)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as ve:
            logger.error(f"Value error: {ve}")
            return CustomErrorResponse(
                {"error": "Invalid college ID format"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error fetching college reviews: {e}")
            return CustomErrorResponse(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class CollegeReviewsAIinsightsView(APIView):
    """
    API view for comparing reviews across multiple colleges.
    Provides both detailed review summaries and recent reviews.
    """
    permission_classes = [ApiKeyPermission]
    
    def __init__(self, **kwargs):
        """
        Initialize the view with a CollegeReviewsHelper instance.
        """
        super().__init__(**kwargs)
        self.reviews_helper = CollegeReviewsHelper()

    @extend_schema(
        summary="Get College Reviews Comparison",
        description="Retrieve reviews summary and recent reviews for multiple colleges",
        parameters=[
            OpenApiParameter(
                name='college_ids', 
                type=str, 
                description='Comma-separated list of college IDs',
                required=True
            ),
            OpenApiParameter(
                name='course_ids', 
                type=str, 
                description='Comma-separated list of course IDs for filtering reviews',
                required=False
            ),
            OpenApiParameter(
                name='grad_year',
                type=int,
                description='Graduation year for filtering reviews',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved reviews comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        """
        Handle GET requests for college reviews comparison.
        
        Args:
            request: HTTP request object with query parameters
                - college_ids: Comma-separated list of college IDs
                - course_ids: Comma-separated list of course IDs (optional)
                - grad_year: Graduation year for filtering reviews
                
        Returns:
            Response: JSON response containing reviews summary and recent reviews
        """
        try:
            college_ids = request.query_params.get('college_ids')
            course_ids = request.query_params.get('course_ids')
            grad_year = request.query_params.get('grad_year') or current_year -1

            if not college_ids or not grad_year:
                raise ValidationError("Both college_ids and grad_year are required")

            college_ids_list = [int(cid) for cid in college_ids.split(',')]
            course_ids_list = [int(cid) for cid in course_ids.split(',')] if course_ids else []

            reviews_summary = self.reviews_helper.get_college_reviews_summary(
                college_ids=college_ids_list,
                grad_year=int(grad_year)
            )
            
        
            
        
            if course_ids_list:

                reviews_summary = self.reviews_helper.get_college_reviews_summary(
                    college_ids=college_ids_list,
                    course_ids_list=course_ids_list,
                    grad_year=int(grad_year)
                )
            
            


            insights=CollegeReviewAiInsightHelper.get_reviews_insights(reviews_summary)


            result = {
                
                'insights':insights
            }
            
            return SuccessResponse(result['insights'], status=status.HTTP_200_OK)
        except NoDataAvailableError as e:
            logger.error(f"No data available for college rating & reviews: {str(e)}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse(
                {"error": str(ve)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as ve:
            logger.error(f"Value error: {ve}")
            return CustomErrorResponse(
                {"error": "Invalid college ID format"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error fetching college reviews: {e}")
            return CustomErrorResponse(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SingleCollegeReviewsView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Single College Reviews",
        description="Retrieve detailed reviews for a single college",
        parameters=[
            OpenApiParameter(
                name='college_id',
                type=int,
                description='College ID',
                required=True
            ),
            OpenApiParameter(
                name='grad_year',
                type=int,
                description='Graduation year for filtering reviews',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved college reviews'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_id = request.query_params.get('college_id')
        grad_year = request.query_params.get('grad_year') or current_year -2

        try:
            if not college_id or not grad_year:
                raise ValidationError("Both college_id and grad_year are required")

       
            
           
            recent_reviews = CollegeReviewsHelper.get_recent_reviews(
                [int(college_id)],
                limit=10
            )
            
            result = {
               
                'recent_reviews': recent_reviews.get('college_1', [])
            }
            
            return SuccessResponse(result, status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse(
                {"error": str(ve)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error fetching college reviews: {e}")
            return CustomErrorResponse(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class CollegeReviewRatingGraphView(APIView):
    """
    API view for generating and retrieving college review rating graphs.
    Provides both raw rating data and classified insights.
    """
    permission_classes = [ApiKeyPermission]

    @extend_schema(
        summary="Get College Review Rating Graph",
        description="Retrieve rating data and classification insights for multiple colleges",
        parameters=[
            OpenApiParameter(
                name='college_ids', 
                type=str, 
                description='Comma-separated list of college IDs',
                required=True
            ),
            OpenApiParameter(
                name='grad_year',
                type=int,
                description='Graduation year for filtering reviews',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved rating graph data'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        """
        Handle GET requests for college review rating graph data.
        
        Args:
            request: HTTP request object with query parameters
                - college_ids: Comma-separated list of college IDs
                - grad_year: Graduation year for filtering reviews
                
        Returns:
            Response: JSON response containing rating data and classification insights
        """
        try:
            
            college_ids = request.query_params.get('college_ids')
            grad_year = request.query_params.get('grad_year') or current_year -2

            if not college_ids or not grad_year:
                raise ValidationError("Both college_ids and grad_year are required.")

          
            college_ids_list = [int(cid) for cid in college_ids.split(',')]

            rating_insights = CollegeReviewsRatingGraphHelper.prepare_rating_insights(
                college_ids=college_ids_list,
                grad_year=int(grad_year)
            )

            return SuccessResponse(rating_insights, status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse(
                {"error": str(ve)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as ve:
            logger.error(f"Value error: {ve}")
            return CustomErrorResponse(
                {"error": "Invalid college ID format."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error fetching rating insights: {e}")
            return CustomErrorResponse(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ExamCutoffView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Exam Cutoff Comparison",
        description="Retrieve exam cutoff comparison data for given colleges, including opening/closing ranks and counselling rounds.",
        parameters=[
            OpenApiParameter(
                name='course_ids',
                type=str,
                description='Comma-separated list of course IDs',
                required=True
            ),
            OpenApiParameter(
                name='counseling_id',
                type=int,
                description='counseling_id',
                required=False
            ),
            OpenApiParameter(
                name='exam_id',
                type=int,
                description='Filter by specific exam ID',
                required=False
            ),
            OpenApiParameter(
                name='category_id',
                type=int,
                description='Filter by specific admission category ID',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Successfully retrieved exam cutoff comparison',
                response=dict,
                examples=[
                    {
                        "exams_data": [
                            {
                                "exam_id": 2,
                                "exam_name": "Paper 1"
                            }
                        ],
                        "category_data": [
                            {
                                "category_id": 2,
                                "category_name": "Outside Home State"
                            }
                        ],
                        "comparison_data": [
                            {
                                "exam_id": 2,
                                "category_id": 2,
                                "college_1": {
                                    "college_id": 151,
                                    "college_course_id": 8072,
                                    "opening_rank": 12,
                                    "closing_rank": 932296,
                                    "total_counselling_rounds": 6,
                                    "lowest_closing_rank_sc_st": 724665,
                                    "lowest_closing_rank_obc": 932296,
                                    "lowest_closing_rank_gn": "NA"
                                }
                            }
                        ]
                    }
                ]
            ),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        }
    )
    def get(self, request):
        """
        GET endpoint to retrieve exam cutoff comparison data.
        Supports filtering by exam_id and category_id.
        """
        course_ids = request.query_params.get('course_ids')
        exam_id = request.query_params.get('exam_id')
        category_id = request.query_params.get('category_id')
        counseling_id = request.query_params.get('counseling_id')

        try:
          
            if not course_ids:
                raise ValidationError("course_ids is required parameters")

          
            try:
                course_ids_list = [int(cid.strip()) for cid in course_ids.split(',') if cid.strip()]
                if not course_ids_list:
                    raise ValidationError("At least one valid course id is required")
            except ValueError:
                raise ValidationError("Invalid college ID format - must be comma-separated integers")

           
  
            optional_params = {}
            if exam_id:
                try:
                    optional_params['exam_id'] = int(exam_id)
                except ValueError:
                    raise ValidationError("Invalid exam_id format - must be an integer")
            
            if counseling_id:
                try:
                    optional_params['counseling_id'] = int(counseling_id)
                except ValueError:
                    raise ValidationError("Invalid counseling_id format - must be an integer")

            if category_id:
                try:
                    optional_params['category_id'] = int(category_id)
                except ValueError:
                    raise ValidationError("Invalid category_id format - must be an integer")

            result = ExamCutoffHelper.get_exam_cutoff(
                course_ids=course_ids_list,
                **optional_params
            )

        

            return SuccessResponse(result, status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error("Validation error in ExamCutoffView: %s", str(ve))
            return CustomErrorResponse(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error("Error in ExamCutoffView: %s", str(e))
            return CustomErrorResponse(
                {"error": "An unexpected error occurred while processing your request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExamCutGraphoffView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Exam Cutoff Comparison",
        description="Retrieve exam cutoff comparison data for given colleges, including opening/closing ranks and counselling rounds.",
        parameters=[
            OpenApiParameter(
                name='course_ids',
                type=str,
                description='Comma-separated list of course IDs',
                required=True
            ),
            OpenApiParameter(
                name='counseling_id',
                type=int,
                description='counseling_id',
                required=False
            ),
            OpenApiParameter(
                name='exam_id',
                type=int,
                description='Filter by specific exam ID',
                required=False
            ),
            OpenApiParameter(
                name='category_id',
                type=int,
                description='Filter by specific admission category ID',
                required=False
            ),
             OpenApiParameter(
                name='caste_id',
                type=int,
                description='Filter by specific  caste ID',
                required=False
            ),
             OpenApiParameter(
                name='gender_id',
                type=int,
                description='Filter by specific admission category ID',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Successfully retrieved exam cutoff comparison',
                response=dict,
                examples=[
                    {
                        "exams_data": [
                            {
                                "exam_id": 2,
                                "exam_name": "Paper 1"
                            }
                        ],
                        "category_data": [
                            {
                                "category_id": 2,
                                "category_name": "Outside Home State"
                            }
                        ],
                        "comparison_data": [
                            {
                                "exam_id": 2,
                                "category_id": 2,
                                "college_1": {
                                    "college_id": 151,
                                    "college_course_id": 8072,
                                    "opening_rank": 12,
                                    "closing_rank": 932296,
                                    "total_counselling_rounds": 6,
                                    "lowest_closing_rank_sc_st": 724665,
                                    "lowest_closing_rank_obc": 932296,
                                    "lowest_closing_rank_gn": "NA"
                                }
                            }
                        ]
                    }
                ]
            ),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        }
    )
    def get(self, request):
        """
        GET endpoint to retrieve exam cutoff comparison data.
        Supports filtering by exam_id and category_id.
        """
        course_ids = request.query_params.get('course_ids')
        exam_id = request.query_params.get('exam_id')
        category_id = request.query_params.get('category_id')
        counseling_id = request.query_params.get('counseling_id')
        caste_id=request.query_params.get('caste_id')
        gender_id=request.query_params.get('gender_id')

        try:
          
            if not course_ids:
                raise ValidationError("course_ids is required parameters")

          
            try:
                course_ids_list = [int(cid.strip()) for cid in course_ids.split(',') if cid.strip()]
                if not course_ids_list:
                    raise ValidationError("At least one valid course id is required")
            except ValueError:
                raise ValidationError("Invalid college ID format - must be comma-separated integers")

           
  
            optional_params = {}
            if exam_id:
                try:
                    optional_params['exam_id'] = int(exam_id)
                except ValueError:
                    raise ValidationError("Invalid exam_id format - must be an integer")
            
            if counseling_id:
                try:
                    optional_params['counseling_id'] = int(counseling_id)
                except ValueError:
                    raise ValidationError("Invalid counseling_id format - must be an integer")

            if category_id:
                try:
                    optional_params['category_id'] = int(category_id)
                except ValueError:
                    raise ValidationError("Invalid category_id format - must be an integer")
            if caste_id:
                try:
                    optional_params['caste_id'] = int(caste_id)
                except ValueError:
                    raise ValidationError("Invalid caste_id format - must be an integer")
            if gender_id:
                try:
                    optional_params['gender_id'] = int(gender_id)
                except ValueError:
                    raise ValidationError("Invalid gender_id format - must be an integer")
            
            
            

            result = ExamCutoffGraphHelper.fetch_cutoff_data(
                course_ids=course_ids_list,
                **optional_params
            )

        

            return SuccessResponse(result, status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error("Validation error in ExamCutoffView: %s", str(ve))
            return CustomErrorResponse(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error("Error in ExamCutoffView: %s", str(e))
            return CustomErrorResponse(
                {"error": "An unexpected error occurred while processing your request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FeedbackSubmitView(APIView):
    @extend_schema(
        summary="Submit Comparison Feedback",
        description="Submit feedback for college and course comparison including the voted choices.",
        responses={
            201: OpenApiResponse(description='Feedback submitted successfully.'),
            400: OpenApiResponse(description='Invalid input data.'),
        },
    )
    def post(self, request):
        serializer = FeedbackSubmitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return SuccessResponse("Feedback submitted successfully.", status=status.HTTP_201_CREATED)
        return CustomErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)