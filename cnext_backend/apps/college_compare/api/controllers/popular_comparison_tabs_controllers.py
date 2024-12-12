from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.helpers.response import SuccessResponse, ErrorResponse, CustomErrorResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django.core.exceptions import ValidationError
import logging
import traceback

# Import comparison helpers
from college_compare.api.helpers.popular_comparison_tabs_helpers import (
    PopularDegreeBranchComparisonHelper,
    PopularDegreeComparisonHelper,
    PopularDomainComparisonHelper,
    PopularComparisonOnCollegeHelper
)

logger = logging.getLogger(__name__)

class DegreeBranchComparisonView(APIView):
    @extend_schema(
        summary="Get Popular Comparisons by Degree and Branch",
        description="Retrieve popular course comparisons filtered by degree and branch IDs.",
        parameters=[
            OpenApiParameter(name='degree_id', type=int, description='Degree ID to filter comparisons', required=True),
            OpenApiParameter(name='branch_id', type=int, description='Branch ID to filter comparisons', required=True)
        ],
        responses={
            200: OpenApiResponse(description='Successful comparison retrieval'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error')
        }
    )
    def get(self, request):
        """
        Handle retrieval of popular comparisons filtered by degree and branch.
        """
        try:
            degree_id = request.query_params.get('degree_id')
            branch_id = request.query_params.get('branch_id')
            
            if not all([degree_id, branch_id]) or not all(param.isdigit() for param in [degree_id, branch_id]):
                raise ValidationError("Both degree_id and branch_id are required and must be integers")
            
            comparisons = PopularDegreeBranchComparisonHelper.get_popular_courses(
                int(degree_id),
                int(branch_id)
            )
            return SuccessResponse(comparisons, status=status.HTTP_200_OK)
            
        except ValidationError as ve:
            logger.error(f"Validation error in degree-branch comparison: {ve}")
            return CustomErrorResponse(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in degree-branch comparison: {str(e)}\n{traceback.format_exc()}")
            return CustomErrorResponse(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DegreeComparisonView(APIView):
    @extend_schema(
        summary="Get Popular Comparisons by Degree",
        description="Retrieve popular course comparisons filtered by degree ID.",
        parameters=[
            OpenApiParameter(name='degree_id', type=int, description='Degree ID to filter comparisons', required=True)
        ],
        responses={
            200: OpenApiResponse(description='Successful comparison retrieval'),
            400: OpenApiResponse(description='Invalid degree ID'),
            500: OpenApiResponse(description='Internal server error')
        }
    )
    def get(self, request):
        """
        Handle retrieval of popular comparisons filtered by degree.
        """
        try:
            degree_id = request.query_params.get('degree_id')
            
            if not degree_id or not degree_id.isdigit():
                raise ValidationError("Valid degree_id is required")
            
            comparisons = PopularDegreeComparisonHelper.get_popular_courses(int(degree_id))
            return SuccessResponse(comparisons, status=status.HTTP_200_OK)
            
        except ValidationError as ve:
            logger.error(f"Validation error in degree comparison: {ve}")
            return CustomErrorResponse(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in degree comparison: {str(e)}\n{traceback.format_exc()}")
            return CustomErrorResponse(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DomainComparisonView(APIView):
    @extend_schema(
        summary="Get Popular Comparisons by Domain",
        description="Retrieve popular course comparisons filtered by domain ID.",
        parameters=[
            OpenApiParameter(name='degree_id', type=int, description='Degree ID to filter comparisons', required=True),
            OpenApiParameter(name='domain_id', type=int, description='Domain ID to filter comparisons', required=True)
        ],
        responses={
            200: OpenApiResponse(description='Successful comparison retrieval'),
            400: OpenApiResponse(description='Invalid domain ID'),
            500: OpenApiResponse(description='Internal server error')
        }
    )
    def get(self, request):
        """
        Handle retrieval of popular comparisons filtered by domain.
        """
        try:
            degree_id = request.query_params.get('degree_id')
            domain_id = request.query_params.get('domain_id')
            
            if not all([degree_id, domain_id]) or not all(param.isdigit() for param in [degree_id, domain_id]):
                raise ValidationError("Both degree_id and domain_id are required and must be integers")
            
            comparisons = PopularDomainComparisonHelper.get_popular_courses(int(domain_id),int(degree_id))
            return SuccessResponse(comparisons, status=status.HTTP_200_OK)
            
        except ValidationError as ve:
            logger.error(f"Validation error in domain comparison: {ve}")
            return CustomErrorResponse(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in domain comparison: {str(e)}\n{traceback.format_exc()}")
            return CustomErrorResponse(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CollegeComparisonView(APIView):
    @extend_schema(
        summary="Get Popular Comparisons for College",
        description="Retrieve popular comparisons for a specific college ID.",
        parameters=[
            OpenApiParameter(name='college_id', type=int, description='College ID to fetch comparisons', required=True)
        ],
        responses={
            200: OpenApiResponse(description='Successful comparison retrieval'),
            400: OpenApiResponse(description='Invalid college ID'),
            500: OpenApiResponse(description='Internal server error')
        }
    )
    def get(self, request):
        """
        Handle retrieval of popular comparisons for a specific college.
        """
        try:
            college_id = request.query_params.get('college_id')
            
            if not college_id or not college_id.isdigit():
                raise ValidationError("Valid college_id is required")
            
            comparisons = PopularComparisonOnCollegeHelper.fetch_popular_comparisons(int(college_id))
            return SuccessResponse(comparisons, status=status.HTTP_200_OK)
            
        except ValidationError as ve:
            logger.error(f"Validation error in college comparison: {ve}")
            return CustomErrorResponse(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in college comparison: {str(e)}\n{traceback.format_exc()}")
            return CustomErrorResponse(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )