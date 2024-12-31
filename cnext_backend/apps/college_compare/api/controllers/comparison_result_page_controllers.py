from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django.core.exceptions import ValidationError
import logging

from college_compare.api.serializers.comparison_result_page_serialzers import FeedbackSubmitSerializer
from utils.helpers.response import SuccessResponse, CustomErrorResponse

from college_compare.api.helpers.comparison_result_page_helpers import (RankingAccreditationHelper,PlacementInsightHelper,CollegeReviewsRatingGraphHelper,MultiYearRankingHelper,CollegeRankingService,PlacementGraphInsightsHelper,FeesGraphHelper,ProfileInsightsHelper,RankingGraphHelper,CourseFeeComparisonHelper,FeesHelper,CollegeFacilitiesHelper,ClassProfileHelper,CollegeReviewsHelper,ExamCutoffHelper)



import logging
import traceback

logger = logging.getLogger(__name__)

import time

current_year = time.localtime().tm_year






class RankingAccreditationComparisonView(APIView):
    @extend_schema(
        summary="Get Ranking and Accreditation Comparison",
        description="Retrieve ranking and accreditation data for given colleges, optionally filtered by year. Accepts a comma-separated list of selected domains.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='selected_domains', type=str, description='Comma-separated list of selected domains (e.g., 1,2,3 or 1,1,1). Must be the same length as college_ids.', required=True),
            OpenApiParameter(name='year', type=int, description='Year for filtering rankings (optional)', required=False),
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved ranking and accreditation comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids_str = request.query_params.get('college_ids')
        selected_domains_str = request.query_params.get('selected_domains')
        year = request.query_params.get('year') or current_year-1

        try:
            if not college_ids_str or not selected_domains_str:
                raise ValidationError("Both college_ids and selected_domains are required")

            college_ids = [int(cid) for cid in college_ids_str.split(',')]
            selected_domains = [int(sd) for sd in selected_domains_str.split(',')]

            if len(college_ids) != len(selected_domains):
                raise ValidationError("The number of college_ids and selected_domains must be the same.")

            selected_domains_dict = {college_ids[i]: str(selected_domains[i]) for i in range(len(college_ids))}

            year = int(year) if year else None

            result = RankingAccreditationHelper.fetch_ranking_data(college_ids, selected_domains_dict, year)
            return SuccessResponse(result, status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            logger.error("Invalid input format. college_ids and selected_domains must be comma-separated integers.")
            return CustomErrorResponse({"error": "Invalid input format. college_ids and selected_domains must be comma-separated integers."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching ranking and accreditation comparison: {traceback.format_exc()}") # Log the full traceback
            return CustomErrorResponse({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class RankingAccreditationCombinedComparisonView(APIView):
    @extend_schema(
        summary="Get Ranking and Accreditation Comparison",
        description="Retrieve ranking and accreditation data for given colleges, optionally filtered by year, and includes combined and multi-year data.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='selected_domains', type=str, description='Comma-separated list of domains for ranking', required=True),
            OpenApiParameter(name='year', type=int, description='Year for filtering rankings (optional)', required=False),
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved ranking and accreditation comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids = request.query_params.get('college_ids')
        selected_domains_str = request.query_params.get('selected_domains')
        year_str = request.query_params.get('year') or current_year-1

        try:
            if not college_ids or not selected_domains_str or not year_str:
                raise ValidationError("Both college_ids, selected_domains, and year are required")

            college_ids_list = [int(cid) for cid in college_ids.split(',')]


            selected_domains = [int(sd) for sd in selected_domains_str.split(',')]


            if len(college_ids_list) != len(selected_domains):
                raise ValidationError("The number of college_ids must match the number of selected_domains.")

            selected_domains_dict = {college_ids_list[i]: str(selected_domains[i]) for i in range(len(college_ids_list))}

            year = int(year_str)


            ranking_data_current_year = RankingAccreditationHelper.fetch_ranking_data(college_ids_list, selected_domains_dict, year)

      
            ranking_data_previous_year = RankingAccreditationHelper.fetch_ranking_data(college_ids_list, selected_domains_dict, year - 1)

  
            combined_ranking_data_current_year = CollegeRankingService.get_state_and_ownership_ranks(college_ids_list, selected_domains_dict, year)

            combined_ranking_data_previous_year = CollegeRankingService.get_state_and_ownership_ranks(college_ids_list, selected_domains_dict, year - 1)


            years = [year - i for i in range(5)]
            multi_year_ranking_data = MultiYearRankingHelper.fetch_multi_year_ranking_data(college_ids_list, selected_domains_dict, years)

            result = {
                "current_year_data": ranking_data_current_year,
                "previous_year_data": ranking_data_previous_year,
                "current_combined_ranking_data": combined_ranking_data_current_year,
                "previous_combined_ranking_data": combined_ranking_data_previous_year,
                "multi_year_ranking_data": multi_year_ranking_data,
            }

            return SuccessResponse(result, status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching ranking and accreditation comparison: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RankingGraphInsightsView(APIView):
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
            200: OpenApiResponse(
                description="Successfully retrieved ranking graph insights",
                examples={
                    "application/json": {
                        "years": [2019, 2020, 2021, 2022, 2023],
                        "overall": {
                            "type": "line",
                            "colleges": {
                                "college_1": {
                                    "college_id": 112,
                                    "data": {
                                        "2019": "87.5",
                                        "2020": "85.0",
                                        "2021": "88.2",
                                        "2022": "NA",
                                        "2023": "90.1",
                                    },
                                },
                                "college_2": {
                                    "college_id": 2,
                                    "data": {
                                        "2019": "75.3",
                                        "2020": "NA",
                                        "2021": "80.0",
                                        "2022": "81.2",
                                        "2023": "83.0",
                                    },
                                },
                            },
                        },
                        "domain": {
                            "type": "line",
                            "colleges": {
                                "college_1": {
                                    "college_id": 112,
                                    "data": {
                                        "2019": "70.2",
                                        "2020": "72.5",
                                        "2021": "75.0",
                                        "2022": "NA",
                                        "2023": "78.4",
                                    },
                                },
                                "college_2": {
                                    "college_id": 2,
                                    "data": {
                                        "2019": "60.1",
                                        "2020": "65.0",
                                        "2021": "67.3",
                                        "2022": "69.5",
                                        "2023": "70.0",
                                    },
                                },
                            },
                        },
                        "college_names": [
                            "ABC College of Engineering",
                            "XYZ Institute of Technology",
                        ],
                    }
                },
            ),
            400: OpenApiResponse(description="Invalid parameters"),
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
                raise ValidationError("college_ids, start_year, end_year, and selected_domains are required")

            college_ids_list = [int(cid) for cid in college_ids.split(",")]
            selected_domains_list = [int(did) for did in selected_domains.split(",")]

            if len(college_ids_list) != len(selected_domains_list):
                raise ValidationError("The number of college_ids must match the number of selected_domains")

            start_year = int(start_year)
            end_year = int(end_year)

            if start_year > end_year:
                raise ValidationError("start_year must be less than or equal to end_year")

            # Mapping college_ids to their respective domain_ids
            domain_mapping = dict(zip(college_ids_list, selected_domains_list))

            result = RankingGraphHelper.prepare_graph_insights(
                college_ids_list, start_year, end_year, domain_mapping
            )
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except ValidationError as ve:
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching ranking graph insights: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class PlacementStatsComparisonView(APIView):
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
        year_str = request.query_params.get('year') or str(current_year - 1)
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

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching placement stats comparison: {traceback.format_exc()}") #use traceback for more detail error
            return CustomErrorResponse({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlacementGraphInsightsView(APIView):
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
        year_str = request.query_params.get('year') or str(current_year - 1)

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

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching placement insights: {traceback.format_exc()}")
            return CustomErrorResponse({"error": "An error occurred while fetching placement insights"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CourseFeeComparisonView(APIView):
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
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching course fee comparison: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeesComparisonView(APIView):
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
        intake_year = request.query_params.get('intake_year') or current_year-1 
      

        try:
            if not college_ids and course_ids:
                raise ValidationError("Both  college_ids and course_ids are required")

            college_ids_list = [int(cid) for cid in college_ids.split(',')]
            course_ids_list = [int(cid) for cid in course_ids.split(',')]

            print(college_ids_list,course_ids_list)
            

            result = FeesHelper.fetch_fees_details(course_ids_list,college_ids_list,intake_year)
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching fees comparison: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeesGraphInsightsView(APIView):
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
    @extend_schema(
        summary="Get Class Profile Comparison",
        description="Retrieve class profile comparison data for given colleges",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='year', type=str, description='year', required=True),
            OpenApiParameter(name='intake_year', type=str, description='year of admission ', required=False),
             OpenApiParameter(name='level', type=str, description='level', required=True)

           
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved summary comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids = request.query_params.get('college_ids')
        year = request.query_params.get('year') or current_year -1

        intake_year = int(request.query_params.get('intake_year')) or current_year -4
        level = int( request.query_params.get('level'))
      

        try:
            if not college_ids and intake_year:
                raise ValidationError("Both  college_ids and intake_year are required")

            college_ids_list = [int(cid) for cid in college_ids.split(',')],
           
            

            result = ClassProfileHelper.fetch_class_profiles(college_ids_list,year,intake_year,level)
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching class profile comparison: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileInsightsView(APIView):
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
                        "student_faculty_metrics": {
                            "type": "line",
                            "college_1": {
                                "college_id": "2",
                                "total_students": 850,
                                "total_faculty": 125,
                                "student_faculty_ratio": 6.8
                            },
                            "college_2": {
                                "college_id": "16",
                                "total_students": 920,
                                "total_faculty": 135,
                                "student_faculty_ratio": 6.81
                            }
                        },
                        "demographic_metrics": {
                            "type": "line",
                            "college_1": {
                                "college_id": "2",
                                "total_students": 850,
                                "students_outside_state": 680,
                                "percentage_outside_state": 80.0
                            },
                            "college_2": {
                                "college_id": "16",
                                "total_students": 920,
                                "students_outside_state": 736,
                                "percentage_outside_state": 80.0
                            }
                        },
                        "gender_metrics": {
                            "type": "line",
                            "college_1": {
                                "college_id": "2",
                                "male_students": 595,
                                "female_students": 255,
                                "percentage_male": 70.0,
                                "percentage_female": 30.0
                            },
                            "college_2": {
                                "college_id": "16",
                                "male_students": 644,
                                "female_students": 276,
                                "percentage_male": 70.0,
                                "percentage_female": 30.0
                            }
                        },
                        "college_names": [
                            "Indian Institute of Technology Delhi",
                            "Indian Institute of Technology Bombay"
                        ]
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
        college_ids = request.query_params.get("college_ids")
        year = request.query_params.get("year") or current_year -1
        intake_year = request.query_params.get("intake_year") or current_year -4
        level = request.query_params.get("level", 1)  

        try:
          
            if not all([college_ids, year, intake_year]):
                raise ValidationError(
                    "college_ids, year, and intake_year are required parameters"
                )

           
            college_ids_list = [int(cid) for cid in college_ids.split(",")]
            year = int(year)
            intake_year = int(intake_year)
            level = int(level)

            if intake_year > year:
                raise ValidationError(
                    "intake_year must be less than or equal to year"
                )

           
            result = ProfileInsightsHelper.prepare_profile_insights(
                college_ids=college_ids_list,
                year=year,
                intake_year=intake_year,
                level=level
            )

            return SuccessResponse(result, status=status.HTTP_200_OK)

        except ValidationError as ve:
            return CustomErrorResponse(
                {"error": str(ve)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as ve:
            return CustomErrorResponse(
                {"error": "Invalid parameter values. Please check the input types."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error fetching profile insights: {e}")
            return CustomErrorResponse(
                {"error": "Internal server error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CollegeFacilitiesComparisonView(APIView):
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


class CollegeReviewsComparisonView(APIView):
    """
    API view for comparing reviews across multiple colleges.
    Provides both detailed review summaries and recent reviews.
    """
    
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
                - grad_year: Graduation year for filtering reviews
                
        Returns:
            Response: JSON response containing reviews summary and recent reviews
        """
        try:
           
            college_ids = request.query_params.get('college_ids')
            grad_year = request.query_params.get('grad_year') or current_year -1

            if not college_ids or not grad_year:
                raise ValidationError("Both college_ids and grad_year are required")

     
            college_ids_list = [int(cid) for cid in college_ids.split(',')]
            
          
            reviews_summary = self.reviews_helper.get_college_reviews_summary(
                college_ids=college_ids_list,
                grad_year=int(grad_year)
            )
            
            recent_reviews = CollegeReviewsHelper.get_recent_reviews(
                college_ids_list,
                limit=3
            )
            
            
            result = {
                'reviews_summary': reviews_summary,
                'recent_reviews': recent_reviews
            }
            
            return SuccessResponse(result, status=status.HTTP_200_OK)

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
        grad_year = request.query_params.get('grad_year') or current_year -1

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
            grad_year = request.query_params.get('grad_year') or current_year -1

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
    @extend_schema(
        summary="Get Exam Cutoff Comparison",
        description="Retrieve exam cutoff comparison data for given colleges, including opening/closing ranks and counselling rounds.",
        parameters=[
            OpenApiParameter(
                name='college_ids',
                type=str,
                description='Comma-separated list of college IDs',
                required=True
            ),
            OpenApiParameter(
                name='year',
                type=int,
                description='Academic year for cutoff data',
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
        college_ids = request.query_params.get('college_ids')
        year = request.query_params.get('year') or current_year-1
        exam_id = request.query_params.get('exam_id')
        category_id = request.query_params.get('category_id')

        try:
          
            if not college_ids or not year:
                raise ValidationError("college_ids and year are required parameters")

          
            try:
                college_ids_list = [int(cid.strip()) for cid in college_ids.split(',') if cid.strip()]
                if not college_ids_list:
                    raise ValidationError("At least one valid college ID is required")
            except ValueError:
                raise ValidationError("Invalid college ID format - must be comma-separated integers")

            try:
                year_int = int(year)
                if year_int < 2022 or year_int > 2100:  
                    raise ValidationError("Year must be between 2022 and 2100")
            except ValueError:
                raise ValidationError("Invalid year format - must be an integer")

  
            optional_params = {}
            if exam_id:
                try:
                    optional_params['exam_id'] = int(exam_id)
                except ValueError:
                    raise ValidationError("Invalid exam_id format - must be an integer")

            if category_id:
                try:
                    optional_params['category_of_admission_id'] = int(category_id)
                except ValueError:
                    raise ValidationError("Invalid category_id format - must be an integer")

            result = ExamCutoffHelper.fetch_cutoff_data(
                college_ids=college_ids_list,
                year=year_int,
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