from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django.core.exceptions import ValidationError
import logging
from utils.helpers.custom_permission import ApiKeyPermission

from college_compare.api.serializers.comparison_result_page_serialzers import FeedbackSubmitSerializer,UserPreferenceSaveSerializer
from utils.helpers.response import SuccessResponse, CustomErrorResponse

from college_compare.api.helpers.comparison_result_page_helpers import (RankingAccreditationHelper,FeesInsightsCalculator,CutoffAnalysisHelper,PlacementInsightsCalculator,RankingInsightsCalculator,AliasReverseChecker,SlugChecker,UserPreferenceHelper,ExamCutoffGraphHelper, CollegeReviewAiInsightHelper,FeesAiInsightHelper,ClassProfileAiInsightHelper,RankingAiInsightHelper,PlacementAiInsightHelper,NoDataAvailableError,CollegeAmenitiesHelper,PlacementInsightHelper,CollegeReviewsRatingGraphHelper,MultiYearRankingHelper,CollegeRankingService,PlacementGraphInsightsHelper,FeesGraphHelper,ProfileInsightsHelper,RankingGraphHelper,CourseFeeComparisonHelper,FeesHelper,CollegeFacilitiesHelper,ClassProfileHelper,CollegeReviewsHelper,ExamCutoffHelper,UserPreferenceOptionsHelper)

from django.core.exceptions import ObjectDoesNotExist

from college_compare.models import UserReportPreferenceMatrix

import logging
import traceback

logger = logging.getLogger(__name__)
from rest_framework import serializers

import time

current_year = time.localtime().tm_year


class UserPreferenceOptionsView(APIView):
    permission_classes = [ApiKeyPermission]

    @extend_schema(
        summary="Get all available user preferences",
        description="Retrieve the full list of 10 possible preferences that a user can select from.",
        responses={
            200: OpenApiResponse(description='Successfully retrieved the preferences list'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        try:
            # Get the user preferences using the helper
            available_preferences = UserPreferenceOptionsHelper.fetch_user_preferences()

            # Return the response
            return SuccessResponse({"available_preferences": available_preferences}, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error fetching user preferences: {str(e)}")
            return CustomErrorResponse({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserPreferenceOptionsForm2View(APIView):
    permission_classes = [ApiKeyPermission]

    @extend_schema(
        summary="Get all available user preferences from 2",
        responses={
            200: OpenApiResponse(description='Successfully retrieved the preferences list for location ,fees budget &  exams'),
            500: OpenApiResponse(description='Internal server error'),
            
        },
    )
    def get(self, request):
        try:
            # Get the user preferences using the helper

            preference_id = request.query_params.get('preference_id') 
            
            result = UserPreferenceHelper.get_user_preference_data(preference_id=preference_id)

            # Return the response
            return SuccessResponse(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error fetching user preferences: {str(e)}")
            return CustomErrorResponse({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 

class UserPreferenceSaveView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Save User Preferences",
        description="Allows users to save their top 5 college comparison preferences.",
        responses={
            201: OpenApiResponse(description="User preferences saved successfully."),
            400: OpenApiResponse(description="Invalid input data."),
        },
    )
    def post(self, request):
        serializer = UserPreferenceSaveSerializer(data=request.data)
        if serializer.is_valid():
            user_preference = serializer.save()
            return Response({"message": "User preferences saved successfully.", "id": user_preference.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






class UserPreferenceUpdateView(APIView):
    permission_classes = [ApiKeyPermission]

    @extend_schema(
        summary="Update User Preferences",
        description="Allows users to update their preference matrix, including optional fields like fees_budget, location_states, and exams.",
        request=UserPreferenceSaveSerializer,
        responses={
            200: OpenApiResponse(
                description="User preferences updated successfully.",
                examples={"message": "User preferences updated successfully."},
            ),
            404: OpenApiResponse(
                description="User preference matrix not found.",
                examples={"error": "No UserReportPreferenceMatrix found with id 123"},
            ),
            400: OpenApiResponse(
                description="Invalid input data.",
                examples={"fees_budget": "Must be a string representation of budget"},
            ),
        },
    )
    def patch(self, request):
        """
        Update fields in UserReportPreferenceMatrix for the given ID.
        """
        try:
            user_preference_id = request.query_params.get("user_preference_id")
            updated_preference = UserPreferenceSaveSerializer.update_user_preference_matrix(
                user_preference_id, request.data
            )

            return Response(
                {"message": "User preferences updated successfully.", "id": updated_preference.id},
                status=status.HTTP_200_OK,
            )

        except UserReportPreferenceMatrix.DoesNotExist:
            return Response(
                {"error": f"No UserReportPreferenceMatrix found with id {user_preference_id}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except serializers.ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
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
        year = request.query_params.get('year') or current_year -1

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

            print(course_ids_dict)

            year = int(year_str)

            # Fetch ranking data for current and previous years
            ranking_data_current_year = RankingAccreditationHelper.fetch_ranking_data(
                college_ids_list, course_ids_dict, year
            )
            
            ranking_data_previous_year = RankingAccreditationHelper.fetch_ranking_data(
                college_ids_list, course_ids_dict, year -1
            )

            # Rest of the code remains the same...
            combined_ranking_data_current_year = CollegeRankingService.get_state_and_ownership_ranks(
                college_ids_list, course_ids_dict, year
            )

            combined_ranking_data_previous_year = CollegeRankingService.get_state_and_ownership_ranks(
                college_ids_list, course_ids_dict, year -1
            )

            years = [year - i for i in range(5)]
            multi_year_ranking_data = MultiYearRankingHelper.fetch_multi_year_ranking_data(
                college_ids_list, course_ids_dict, years
            )
            print(years)

            result = {
                "current_year_data": ranking_data_current_year,
                "previous_year_data": ranking_data_previous_year,
                "current_combined_ranking_data": combined_ranking_data_current_year,
                "previous_combined_ranking_data": combined_ranking_data_previous_year,
                "multi_year_ranking_data": multi_year_ranking_data,
            }

            print(result)
            

    

          
            insights = RankingInsightsCalculator.calculate_ranking_insights(result)
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
        description="Retrieve ranking graph insights (overall and course-specific) for given colleges over a specified year range.",
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
                name="course_ids",
                type=str,
                description="Comma-separated list of Course IDs corresponding to the college IDs",
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
        """
        Retrieve ranking graph insights for specified colleges and year range.
        
        The method performs the following key steps:
        1. Validate and parse input parameters
        2. Ensure matching numbers of college IDs and course IDs
        3. Validate year range
        4. Fetch ranking graph insights using RankingGraphHelper
        5. Handle various potential error scenarios
        
        Returns:
        - Successful response with ranking insights
        - Error responses for invalid inputs or data unavailability
        """
        # Extract query parameters with fallback to default values
        college_ids = request.query_params.get("college_ids")
        start_year = request.query_params.get("start_year") or current_year - 6
        end_year = request.query_params.get("end_year") or current_year - 1
        selected_courses = request.query_params.get("course_ids")

        try:
            # Validate required parameters are present
            if not all([college_ids, selected_courses]):
                raise ValidationError(
                    "college_ids, start_year, end_year, and selected_courses are required."
                )

            # Convert and validate input parameters
            try:
                college_ids_list = [int(cid.strip()) for cid in college_ids.split(",") if cid.strip()]
                selected_courses_list = [int(cid.strip()) for cid in selected_courses.split(",") if cid.strip()]
            except ValueError:
                raise ValidationError("Invalid format for college_ids or selected_courses. Must be comma-separated integers.")

            # Validate matching number of college and course IDs
            if len(college_ids_list) != len(selected_courses_list):
                raise ValidationError(
                    "The number of college_ids must exactly match the number of selected_courses."
                )

            # Convert and validate year parameters
            start_year = int(start_year)
            end_year = int(end_year)

            # Validate year range
            if start_year > end_year:
                raise ValidationError("start_year must be less than or equal to end_year.")

            # Create mapping of college IDs to course IDs
            course_mapping = dict(zip(college_ids_list, selected_courses_list))

            print(course_mapping)

            # Fetch ranking graph insights
            result = RankingGraphHelper.prepare_graph_insights(
                college_ids_list, 
                start_year, 
                end_year, 
                course_mapping
            )

            # Validate result
            if not result:
                raise NoDataAvailableError(
                    "No ranking graph insights available for the provided inputs."
                )

            # Return successful response
            return SuccessResponse(result, status=status.HTTP_200_OK)

        except ValidationError as ve:
            # Handle validation errors with detailed error message
            logger.warning(f"Validation error in ranking graph insights: {ve}")
            return CustomErrorResponse(
                {"error": str(ve)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        except NoDataAvailableError as nde:
            # Handle cases where no data is found
            logger.warning(f"No data available for ranking graph insights: {nde}")
            return CustomErrorResponse(
                {"error": str(nde)}, 
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error in ranking graph insights: {traceback.format_exc()}")
            return CustomErrorResponse(
                {"error": "An unexpected error occurred while fetching ranking graph insights"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class PlacementStatsComparisonView(APIView):
    permission_classes = [ApiKeyPermission]

    @extend_schema(
        summary="Get Placement Stats Comparison",
        description="Retrieve placement stats comparison for given colleges and courses, allowing different courses per college.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='year', type=str, description='Year', required=False),
            OpenApiParameter(name='selected_courses', type=str, description='Comma-separated list of Course IDs corresponding to the college IDs', required=True)
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
        course_ids_str = request.query_params.get('course_ids')

        try:
            if not college_ids_str:
                raise ValidationError("college_ids is required")

            try:
                college_ids = [int(cid) for cid in college_ids_str.split(',')]

                course_ids = (
                    [int(course_id) for course_id in course_ids_str.split(',')]
                    if course_ids_str else None
                )

               
                course_ids_dict = (
                    {college_ids[i]: course_ids[i] for i in range(len(college_ids))}
                    if course_ids else {}
                )
                print(course_ids_dict)
                
                year = int(year_str)
            except ValueError:
                raise ValidationError("college_ids, course_ids and year must be integers")

            
           

            result = PlacementInsightHelper.fetch_placement_stats(college_ids, course_ids_dict, year)
            result['year']=year
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
        summary="Get Placement Stats AI Insights Comparison",
        description="Retrieve placement stats comparison for given colleges and courses, allowing different courses per college.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='year', type=str, description='Year', required=False),
            OpenApiParameter(name='selected_courses', type=str, description='Comma-separated list of Course IDs corresponding to the college IDs', required=True)
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved placement stats and AI insights comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids_str = request.query_params.get('college_ids')
        year_str = request.query_params.get('year') or str(current_year - 2)
        course_ids_str = request.query_params.get('course_ids')

        try:
            if not college_ids_str or not course_ids_str:
                raise ValidationError("college_ids and selected_courses are required")

            try:
                college_ids = [int(cid) for cid in college_ids_str.split(',')]
                course_ids = [int(course_id) for course_id in course_ids_str.split(',')]
                year = int(year_str)
            except ValueError:
                raise ValidationError("college_ids, selected_courses, and year must be integers")

            if len(college_ids) != len(course_ids):
                raise ValidationError("The number of college_ids must match the number of selected_courses")

            selected_courses = {college_id: course_id for college_id, course_id in zip(college_ids, course_ids)}

            result = PlacementInsightHelper.fetch_placement_stats(college_ids, selected_courses, year)

        
            insights = PlacementInsightsCalculator.calculate_placement_insights(result)

            result['insights'] = insights
            return SuccessResponse(result['insights'], status=status.HTTP_200_OK)

        except NoDataAvailableError as e:
            logger.error(f"No data available for placement AI insights comparison: {str(e)}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching placement AI insights comparison: {traceback.format_exc()}")
            return CustomErrorResponse({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlacementGraphInsightsView(APIView):
    permission_classes = [ApiKeyPermission]

    @extend_schema(
        summary="Get Placement Graph Insights",
        description="Retrieve placement insights including placement percentages, salary data, and recruiter information for given colleges, allowing different courses per college.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='course_ids', type=str, description='Comma-separated list of Course IDs corresponding to the college IDs', required=True),
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
        course_ids_str = request.query_params.get('course_ids')
        year_str = request.query_params.get('year') or str(current_year - 2)

        try:
            if not college_ids_str or not course_ids_str:
                raise ValidationError("college_ids and course_ids are required parameters")

            try:
                college_ids = [int(cid) for cid in college_ids_str.split(',')]
                course_ids = [int(did) for did in course_ids_str.split(',')]
                year = int(year_str)
            except ValueError:
                raise ValidationError("college_ids, course_ids, and year must be integers")

            if len(college_ids) != len(course_ids):
                raise ValidationError("The number of college_ids must match the number of course_ids")

            selected_courses = {college_id: course_id for college_id, course_id in zip(college_ids, course_ids)}

            result = PlacementGraphInsightsHelper.fetch_placement_insights(
                college_ids=college_ids,
                selected_courses=selected_courses,
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

            insights=FeesInsightsCalculator.calculate_fees_insights(fees_data=result)
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
            OpenApiParameter(name='course_ids', type=str, description='Comma-separated list of Course IDs corresponding to the college IDs', required=False),
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
        course_ids_str = request.query_params.get('course_ids')

        try:
            # Validate college_ids and parse them into a list of integers
            if not college_ids_str:
                raise ValidationError("college_ids is required")

            try:
                college_ids = [int(cid) for cid in college_ids_str.split(",")]
                year = int(year_str)
                intake_year = int(intake_year_str)
            except ValueError:
                raise ValidationError("college_ids, year, and intake_year must be integers")

            # Validate and parse course_ids (if provided)
            if course_ids_str:
                try:
                    course_ids = [int(cid) for cid in course_ids_str.split(",")]
                    if len(college_ids) != len(course_ids):
                        raise ValidationError("The number of college_ids must match the number of course_ids")
                    selected_courses = {college_id: course_id for college_id, course_id in zip(college_ids, course_ids)}
                except ValueError:
                    raise ValidationError("course_ids must be integers")
            else:
                selected_courses = None  # No courses provided

            if intake_year > year:
                raise ValidationError("intake_year must be less than or equal to year")

            # Fetch class profiles
            result = ClassProfileHelper.fetch_class_profiles(
                college_ids=college_ids,
                year=year,
                intake_year=intake_year,
                selected_courses=selected_courses  # Pass course mapping (can be None)
            )
            result['year']=year

            return SuccessResponse(result, status=status.HTTP_200_OK)
        except NoDataAvailableError as e:
            logger.error(f"No data available for class profile comparison: {str(e)}")
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
                name="course_ids",
                type=str,
                description="Comma-separated list of Course IDs corresponding to the college IDs",
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
        year_str = request.query_params.get("year") or str(current_year - 2)
        intake_year_str = request.query_params.get("intake_year") or str(current_year - 5)
        level = request.query_params.get("level", 1)
        course_ids_str = request.query_params.get("course_ids")

        try:
            if not college_ids_str or not course_ids_str:
                raise ValidationError("college_ids and course_ids are required")

            try:
                college_ids = [int(cid) for cid in college_ids_str.split(",")]
                course_ids = [int(did) for did in course_ids_str.split(",")]
                year = int(year_str)
                intake_year = int(intake_year_str)
                level = int(level)
            except ValueError:
                raise ValidationError("college_ids, course_ids, year, and intake_year must be integers")

            if len(college_ids) != len(course_ids):
                raise ValidationError("The number of college_ids must match the number of course_ids")

            if intake_year > year:
                raise ValidationError("intake_year must be less than or equal to year")

            # Create a mapping of college IDs to course IDs
            selected_courses = {college_id: course_id for college_id, course_id in zip(college_ids, course_ids)}

            # Fetch and prepare the profile insights
            result = ProfileInsightsHelper.prepare_profile_insights(
                college_ids=college_ids,
                year=year,
                intake_year=intake_year,
                selected_courses=selected_courses,  # Pass course_ids instead of selected_domains
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
                name="course_ids",
                type=str,
                description="Comma-separated list of Course IDs corresponding to the college IDs",
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
        year_str = request.query_params.get("year") or str(current_year - 2)
        intake_year_str = request.query_params.get("intake_year") or str(current_year - 6)
        level = request.query_params.get("level", 1)
        course_ids_str = request.query_params.get("course_ids")

        try:
            if not college_ids_str or not course_ids_str:
                raise ValidationError("college_ids and course_ids are required")

            try:
                college_ids = [int(cid) for cid in college_ids_str.split(",")]
                course_ids = [int(did) for did in course_ids_str.split(",")]
                year = int(year_str)
                intake_year = int(intake_year_str)
                level = int(level)
            except ValueError:
                raise ValidationError("college_ids, course_ids, year, and intake_year must be integers")

            if len(college_ids) != len(course_ids):
                raise ValidationError("The number of college_ids must match the number of course_ids")

            # if intake_year > year:
            #     raise ValidationError("intake_year must be less than or equal to year")

            selected_courses = {college_id: course_id for college_id, course_id in zip(college_ids, course_ids)}

            result = ProfileInsightsHelper.prepare_profile_insights(
                college_ids=college_ids,
                year=year,
                intake_year=intake_year,
                selected_courses=selected_courses,  # Pass course_ids instead of selected_domains
                level=level,
            )

            insights = ClassProfileAiInsightHelper.get_profile_insights(data=result)
            result['insights'] = insights

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

            if 'error' in result:
                print("---------")
            
            result['year']=current_year-2

        

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
            result['year']=current_year-2

        

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



class ExamCutoffInsightsView(APIView):
    permission_classes = [ApiKeyPermission]

    @extend_schema(
        summary="Get Cutoff Insights",
        description="Retrieve cutoff analysis insights for given courses.",
        parameters=[
            OpenApiParameter(
                name='course_ids',
                type=str,
                description='Comma-separated list of course IDs',
                required=True
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Successfully retrieved cutoff insights',
                response=dict,
                examples=[
                    {
                        "cutoff_differences": "B.Tech CSE IIT Delhi has 20% higher cut off as compared to B.Tech CSE (IIT Bombay).",
                        "closing_rank_changes": "There is a 20% increase in closing rank for B.Tech CSE (IIT Delhi).",
                        "lowest_cutoff_degree": "B.Tech CSE (IIT Delhi) has the lowest closing rank of 650 for ST category.",
                        "lowest_cutoff_branch": "B.Tech Mechanical (IIT Bombay) has the lowest closing rank of 700 for ST category."
                    }
                ]
            ),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        }
    )
    def get(self, request):
        """
        GET endpoint to retrieve cutoff analysis insights.
        """
        course_ids = request.query_params.get('course_ids')

        try:
            if not course_ids:
                raise ValidationError("course_ids is a required parameter")

            try:
                course_ids_list = [int(cid.strip()) for cid in course_ids.split(',') if cid.strip()]
                if not course_ids_list:
                    raise ValidationError("At least one valid course id is required")
            except ValueError:
                raise ValidationError("Invalid course ID format - must be comma-separated integers")

            # Fetch cutoff analysis insights
            cutoff_insights = CutoffAnalysisHelper.compare_cutoffs(course_ids_list)

            # Return only the cutoff insights
            return SuccessResponse(cutoff_insights, status=status.HTTP_200_OK)

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
        summary="Submit or Update Comparison Feedback",
        description="Submit new feedback or update existing feedback for college and course comparison including the voted choices.",
        responses={
            201: OpenApiResponse(description='Feedback submitted/updated successfully.'),
            400: OpenApiResponse(description='Invalid input data.'),
        },
    )
    def post(self, request):
        serializer = FeedbackSubmitSerializer(data=request.data)
        if serializer.is_valid():
            feedback, message = serializer.create_or_update(serializer.validated_data)
            return SuccessResponse({
                "message": message,
                "id": feedback.id
            }, status=status.HTTP_201_CREATED)
        return CustomErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



class SlugCheckerView(APIView):
    permission_classes = [ApiKeyPermission]  

    @extend_schema(
        summary="Get Parameterized Slug for College Comparison",
        description="Retrieve the parameterized slug for comparing two colleges, with optional course parameters.",
        parameters=[
            OpenApiParameter(
                name='college_ids',
                type=int,
                description='List of two college IDs to compare',
                required=True
            ),
            OpenApiParameter(
                name='course_ids',
                type=int,
                description='List of two course IDs to include in the comparison',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved the alias and parameterized slug'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
       

      
        college_ids = request.query_params.get('college_ids')
        
        course_ids = request.query_params.get('course_ids')

        

      
        try:
            
            
            college_ids_list = [int(cid) for cid in college_ids.split(',')]

            if course_ids:
               
                course_ids_list = [int(cid) for cid in course_ids.split(',')]
                
            else:
                course_ids_list = None  
            
            
           
            slug_checker = SlugChecker(college_ids_list, course_ids_list)
            result = slug_checker.get_result()  

            if "error" in result:
                return CustomErrorResponse(
                    result,
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return SuccessResponse(result, status=status.HTTP_200_OK)

           

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse(
                {"error": str(ve)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error fetching alias: {e}")
            return CustomErrorResponse(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AliasReverseCheckerView(APIView):
    permission_classes = [ApiKeyPermission]
    
    @extend_schema(
        summary="Get College IDs and Parameters from Alias",
        description="Retrieve college IDs and generate parameterized URL from a comparison alias.",
        parameters=[
            OpenApiParameter(
                name='alias',
                type=str,
                description='The alias to look up',
                required=True
            ),
            OpenApiParameter(
                name='college_ids',
                type=int,
                description='Optional list of two college IDs',
                required=False
            ),
            OpenApiParameter(
                name='course_ids',
                type=int,
                description='Optional list of two course IDs to include in the comparison',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved the college IDs and parameterized URL'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        alias = request.query_params.get('alias')
        college_ids = request.query_params.get('college_ids')
        course_ids = request.query_params.get('course_ids')
        
        try:
            # Process college_ids if provided
            college_ids_list = None
            if college_ids:
                college_ids_list = [int(cid) for cid in college_ids.split(',')]
            
            # Process course_ids if provided
            course_ids_list = None
            if course_ids:
                course_ids_list = [int(cid) for cid in course_ids.split(',')]
            
            # Initialize checker and get result
            checker = AliasReverseChecker(alias, college_ids_list, course_ids_list)
            result = checker.get_result()
            
            if "error" in result:
                return CustomErrorResponse(
                    result,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return SuccessResponse(result, status=status.HTTP_200_OK)
            
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error processing alias: {e}")
            return CustomErrorResponse(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        


