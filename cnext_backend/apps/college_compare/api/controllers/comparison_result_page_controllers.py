from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django.core.exceptions import ValidationError
import logging

from college_compare.api.serializers.compare_college_page_serializers import CollegeCompareSerializer
from utils.helpers.response import SuccessResponse, CustomErrorResponse

from college_compare.api.helpers.comparison_result_page_helpers import (RankingAccreditationHelper,PlacementStatsComparisonHelper,CourseFeeComparisonHelper,FeesHelper,CollegeFacilitiesHelper,ClassProfileHelper,CollegeReviewsHelper)



import logging
import traceback

logger = logging.getLogger(__name__)





class RankingAccreditationComparisonView(APIView):
    @extend_schema(
        summary="Get Ranking and Accreditation Comparison",
        description="Retrieve ranking and accreditation data for given colleges.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='selected_domain', type=str, description='Domain for ranking', required=True),
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved ranking and accreditation comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids = request.query_params.get('college_ids')
        selected_domain = request.query_params.get('selected_domain')

        try:
            if not college_ids or not selected_domain:
                raise ValidationError("Both college_ids and selected_domain are required")

            college_ids_list = [int(cid) for cid in college_ids.split(',')]

            result = RankingAccreditationHelper.fetch_ranking_data(college_ids_list, selected_domain)
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching ranking and accreditation comparison: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class PlacementStatsComparisonView(APIView):
    @extend_schema(
        summary="Get Placement Stats Comparison",
        description="Retrieve placement stats comparison for given colleges and courses.",
        parameters=[
           
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='year', type=str, description='Year', required=True),
             OpenApiParameter(name='domain_id', type=str, description='domain_id', required=True)
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved placement stats comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        
        college_ids = request.query_params.get('college_ids')
        year = request.query_params.get('year')
        domain_id = request.query_params.get('domain_id')

        try:
            if  not college_ids or not year:
                raise ValidationError("course_ids, college_ids, and year are required")

           
            college_ids_list = [int(cid) for cid in college_ids.split(',')]

            result = PlacementStatsComparisonHelper.fetch_placement_stats(college_ids_list, year=int(year),domain_id=domain_id)
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching placement stats comparison: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
               OpenApiParameter(name='intake_year', type=str, description='year of admission ', required=True)

           
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
        intake_year = request.query_params.get('intake_year')
      

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



class ClassProfileComparisonView(APIView):
    @extend_schema(
        summary="Get Class Profile Comparison",
        description="Retrieve class profile comparison data for given colleges",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='year', type=str, description='year', required=True),
            OpenApiParameter(name='intake_year', type=str, description='year of admission ', required=True),
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
        year = request.query_params.get('year')

        intake_year = int(request.query_params.get('intake_year'))
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
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved reviews comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids = request.query_params.get('college_ids')
        grad_year = request.query_params.get('grad_year')

        try:
            if not college_ids or not grad_year:
                raise ValidationError("Both college_ids and grad_year are required")

            college_ids_list = [int(cid) for cid in college_ids.split(',')]
            
            
            reviews_summary = CollegeReviewsHelper.get_college_reviews_summary(
                college_ids_list,
                int(grad_year)
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
        except Exception as e:
            logger.error(f"Error fetching reviews comparison: {e}")
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
                required=True
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
        grad_year = request.query_params.get('grad_year')

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