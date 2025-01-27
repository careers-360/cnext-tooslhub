from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.helpers.response import SuccessResponse, ErrorResponse, CustomErrorResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from college_compare.api.services.landing_page_services import (PeerComparisonService, TopCollegesCoursesService)
from django.core.exceptions import ValidationError
import logging
import traceback
from utils.helpers.custom_permission import ApiKeyPermission

logger = logging.getLogger(__name__)


class PeerComparisonCollegesView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Peer Comparison of Colleges",
        description="Retrieve peer comparison details for colleges with optional user-specific context.",
        parameters=[
            OpenApiParameter(name='uid', type=int, description='User ID for personalized peer comparison', required=False),
             OpenApiParameter(name='cache_burst', type=int, description='Set to 0 to bypass cache and recompute results', required=False),

        ],
        responses={
            200: OpenApiResponse(description='Successful peer comparison retrieval'),
            400: OpenApiResponse(description='Invalid user ID'),
            500: OpenApiResponse(description='Internal server error')
        }
    )
   
    def get(self, request):
        """
        Handle peer comparison retrieval with optional user context.
        """
        
        uid = request.query_params.get('uid')
        cache_burst = request.query_params.get('cache_burst')  or 0

        try:
          
            if uid and uid.isdigit():
                uid = int(uid)
            else:
                uid = None

          
            result = PeerComparisonService.get_peer_comparisons(uid,cache_burst=cache_burst)
            return SuccessResponse(result, status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
            return CustomErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TopCollegesCoursesView(APIView):
    permission_classes = [ApiKeyPermission]
    @extend_schema(
        summary="Get Top Colleges and Courses",
        description="Retrieve top colleges and courses with optional user-specific context.",
        parameters=[
            OpenApiParameter(name='uid', type=int, description='User ID for personalized recommendations', required=False),
             OpenApiParameter(name='cache_burst', type=int, description='Set to 0 to bypass cache and recompute results', required=False),

        ],
        responses={
            200: OpenApiResponse(description='Successful top colleges and courses retrieval'),
            400: OpenApiResponse(description='Invalid user ID'),
            500: OpenApiResponse(description='Internal server error')
        }
    )
    def get(self, request):
        """
        Handle the retrieval of top colleges and courses with optional user context.
        """
        uid = request.query_params.get('uid')
        cache_burst = request.query_params.get('cache_burst') or 0
        print(cache_burst,"------")

        try:

            if uid and uid.isdigit():
                uid = int(uid)
            else:
                uid = None

            result = TopCollegesCoursesService.get_top_colleges_courses(uid,cache_burst=cache_burst)
            return SuccessResponse(result, status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return CustomErrorResponse({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except CustomErrorResponse as ce:
            logger.error(f"Custom error: {str(ce)}")
            return CustomErrorResponse({"error": str(ce)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
            return ErrorResponse({
                "error": str(e),
                "stack_trace": traceback.format_exc(),
                "error_type": type(e).__name__,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
