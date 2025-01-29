from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django.core.exceptions import ValidationError
import logging
from utils.helpers.custom_permission import ApiKeyPermission

from college_compare.api.serializers.compare_college_page_serializers import CollegeCompareSerializer
from utils.helpers.response import SuccessResponse, CustomErrorResponse
from college_compare.api.services.compare_college_page_services import (
    DropdownService, SummaryComparisonService, QuickFactsService, CardDisplayService,NoDataAvailableError
)

logger = logging.getLogger(__name__)


class CollegeDropdownView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get College Dropdown",
        description="Retrieve a list of colleges for the dropdown, with optional search input and UID.",
        parameters=[
            OpenApiParameter(name='search_input', type=str, description='Search string to filter colleges', required=False),
            OpenApiParameter(name='uid', type=int, description='User ID to fetch domain-specific college data', required=False),
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=False),
            OpenApiParameter(name='cache_burst', type=int, description='Set to 0 to bypass cache and recompute results', required=False),
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved colleges dropdown'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        search_input = request.query_params.get('search_input')
        uid = request.query_params.get('uid')
        college_ids = request.query_params.get('college_ids')
        cache_burst = request.query_params.get('cache_burst') or 0

        uid = int(uid) if uid else None

        
        college_ids_list = (
            [int(cid.strip()) for cid in college_ids.split(',') if cid.strip().isdigit()]
            if college_ids
            else None
        )

        print(f"UID: {uid}, Search Input: {search_input}, College IDs: {college_ids_list}")

        try:
            result = DropdownService.get_colleges_dropdown(
                search_input=search_input, 
                country_id=1, 
                uid=uid, 
                college_ids=college_ids_list,
                cache_burst=int(cache_burst)
            )
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching colleges dropdown: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DegreeDropdownView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Degree Dropdown",
        description="Retrieve a list of degrees available in a specific college.",
        parameters=[
            OpenApiParameter(name='college_id', type=int, description='ID of the college', required=True),
            OpenApiParameter(name='cache_burst', type=int, description='Set to 0 to bypass cache and recompute results', required=False),
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved degrees dropdown'),
            400: OpenApiResponse(description='Invalid college ID'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_id = request.query_params.get('college_id')
        cache_burst = request.query_params.get('cache_burst') or 0

        try:
            if not college_id or not college_id.isdigit():
                raise ValidationError("Invalid college_id parameter")

            result = DropdownService.get_degrees_dropdown(int(college_id),int(cache_burst))
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching degrees dropdown: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CourseDropdownView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Course Dropdown",
        description="Retrieve a list of courses available in a specific college for a degree.",
        parameters=[
            OpenApiParameter(name='college_id', type=int, description='ID of the college', required=True),
            OpenApiParameter(name='degree_id', type=int, description='ID of the degree', required=True),
            OpenApiParameter(name='cache_burst', type=int, description='Set to 0 to bypass cache and recompute results', required=False),
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved courses dropdown'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_id = request.query_params.get('college_id')
        degree_id = request.query_params.get('degree_id')
        cache_burst = request.query_params.get('cache_burst') or 0

        try:
            if not college_id or not college_id.isdigit() or not degree_id or not degree_id.isdigit():
                raise ValidationError("Invalid college_id or degree_id parameter")

            result = DropdownService.get_courses_dropdown(int(college_id), int(degree_id),int(cache_burst))
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching courses dropdown: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SummaryComparisonView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Summary Comparison",
        description="Retrieve summary comparison for given colleges and courses.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='course_ids', type=str, description='Comma-separated list of course IDs', required=True),
            OpenApiParameter(name='cache_burst', type=int, description='Set to 0 to bypass cache and recompute results', required=False),
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved summary comparison'),
            400: OpenApiResponse(description='Invalid parameters'),
            404: OpenApiResponse(description='No data available for the provided college IDs and course IDs'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids = request.query_params.get('college_ids')
        course_ids = request.query_params.get('course_ids')
        cache_burst = request.query_params.get('cache_burst') or 0

        try:
            if not college_ids or not course_ids:
                raise ValidationError("Both college_ids and course_ids are required")

            college_ids_list = [int(cid) for cid in college_ids.split(',')]
            course_ids_list = [int(csid) for csid in course_ids.split(',')]

            result = SummaryComparisonService.get_summary_comparison(college_ids_list, course_ids_list,int(cache_burst))
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except NoDataAvailableError as e:
            logger.error(f"No data available error: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching summary comparison: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class QuickFactsView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Quick Facts",
        description="Retrieve quick facts for given colleges and courses.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='course_ids', type=str, description='Comma-separated list of course IDs', required=True),
             OpenApiParameter(name='cache_burst', type=int, description='Set to 0 to bypass cache and recompute results', required=False),
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved quick facts'),
            400: OpenApiResponse(description='Invalid parameters'),
            404: OpenApiResponse(description='No data available for the provided college IDs'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids = request.query_params.get('college_ids')
        course_ids = request.query_params.get('course_ids')
        cache_burst = request.query_params.get('cache_burst') or 0

        try:
            if not college_ids:
                raise ValidationError("Both college_ids and course_ids are required")

            college_ids_list = [int(cid) for cid in college_ids.split(',')]
            if course_ids:
                course_ids_list = [int(csid) for csid in course_ids.split(',')]
                result = QuickFactsService.get_quick_facts(college_ids_list, course_ids_list,int(cache_burst))
            else: 
                result = QuickFactsService.get_quick_facts(college_ids_list,int(cache_burst))
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except NoDataAvailableError as e:
            logger.error(f"No data available error: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching quick facts: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CardDisplayServiceView(APIView):
    permission_classes = [ApiKeyPermission]

    @extend_schema(
        summary="Get Card Display Details",
        description="Retrieve card display details for colleges and courses, including social media links.",
        parameters=[
            OpenApiParameter(name='college_ids', type=str, description='Comma-separated list of college IDs', required=True),
            OpenApiParameter(name='course_ids', type=str, description='Comma-separated list of course IDs (optional)', required=False),
            OpenApiParameter(name='cache_burst', type=int, description='Set to 0 to bypass cache and recompute results', required=False),
        ],
        responses={
            200: OpenApiResponse(description='Successfully retrieved card display details'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        },
    )
    def get(self, request):
        college_ids = request.query_params.get('college_ids')
        course_ids = request.query_params.get('course_ids')
        cache_burst = request.query_params.get('cache_burst') or 0

        try:
            if not college_ids:
                raise ValidationError("college_ids is required")

            college_ids_list = list(map(int, college_ids.split(',')))
            course_ids_list = list(map(int, course_ids.split(','))) if course_ids else None

            result = CardDisplayService.get_card_display_details(college_ids_list, course_ids_list, int(cache_burst))
            return SuccessResponse(result, status=status.HTTP_200_OK)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching card display details: {e}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CollegeCompareController(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Save Comparison Data",
        description="Save the comparison data for colleges and courses.",
        responses={
            201: OpenApiResponse(description='Comparison data saved successfully.'),
            400: OpenApiResponse(description='Invalid input data.'),
        },
    )
    def post(self, request):
        serializer = CollegeCompareSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return SuccessResponse("Comparison data saved successfully.", status=status.HTTP_201_CREATED)
        return CustomErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
