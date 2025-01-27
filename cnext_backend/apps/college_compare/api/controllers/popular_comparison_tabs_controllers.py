from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.helpers.response import SuccessResponse, ErrorResponse, CustomErrorResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django.core.exceptions import ValidationError
import logging
import traceback
from utils.helpers.custom_permission import ApiKeyPermission



from college_compare.api.helpers.popular_comparison_tabs_helpers import (
  ComparisonHelper
)

logger = logging.getLogger(__name__)

from concurrent.futures import ThreadPoolExecutor, as_completed






# class AllComparisonsView(APIView):
#     """
#     All types of comparisons (degree_branch, degree, domain, college) with cache burst support
#     """
#     permission_classes = [ApiKeyPermission]

#     @extend_schema(
#         summary="Get All Popular Comparisons",
#         description="Retrieve popular course comparisons for all types: degree_branch, degree, domain, and college.",
#         parameters=[
#             OpenApiParameter(name='degree_id', type=int, description='Degree ID (required for degree_branch, degree)', required=True),
#             OpenApiParameter(name='course_id', type=int, description='course ID (required for degree_branch)', required=True),
#             OpenApiParameter(name='branch_id', type=int, description='Branch ID (required for degree_branch)', required=True),
#             OpenApiParameter(name='domain_id', type=int, description='Domain ID (required for domain comparisons)', required=True),
#             OpenApiParameter(name='college_id', type=int, description='College ID (required for college comparisons)', required=True),
#             OpenApiParameter(name='cache_burst', type=int, description='Set to 0 to bypass cache and recompute results', required=False),
#         ],
#         responses={
#             200: OpenApiResponse(description='Successful comparison retrieval'),
#             400: OpenApiResponse(description='Invalid parameters'),
#             500: OpenApiResponse(description='Internal server error'),
#         }
#     )
#     def get(self, request):
#         """
#         Handle retrieval of popular comparisons for all types.
#         Supports cache bursting via cache_burst parameter.
#         """
#         try:
            
#             degree_id = request.query_params.get('degree_id')
#             course_id = request.query_params.get('course_id')
#             branch_id = request.query_params.get('branch_id')
#             domain_id = request.query_params.get('domain_id')
#             college_id = request.query_params.get('college_id')
#             cache_burst = request.query_params.get('cache_burst')

#             params = {
#                 'degree_id': int(degree_id) if degree_id and degree_id.isdigit() else None,
#                 'course_id': int(course_id) if course_id and course_id.isdigit() else None,
#                 'branch_id': int(branch_id) if branch_id and branch_id.isdigit() else None,
#                 'domain_id': int(domain_id) if domain_id and domain_id.isdigit() else None,
#                 'college_id': int(college_id) if college_id and college_id.isdigit() else None,
#                 'cache_burst': int(cache_burst) if cache_burst and cache_burst.isdigit() else 0
#             }

#             helper = ComparisonHelper()

#             def fetch_comparisons(key, **kwargs):
#                 """
#                 Helper function to fetch comparisons based on the key.
#                 Includes cache_burst parameter in the kwargs.
#                 """
#                 return key, helper.get_popular_comparisons(
#                     key,
#                     cache_burst=kwargs.pop('cache_burst', 0),
#                     **kwargs
#                 )


#             tasks = []
#             with ThreadPoolExecutor() as executor:
#                 if params['degree_id'] and params['branch_id']:
#                     tasks.append(executor.submit(fetch_comparisons, 'degree_branch', **params))
#                     tasks.append(executor.submit(fetch_comparisons, 'degree', **params))
#                 if params['domain_id']:
#                     tasks.append(executor.submit(fetch_comparisons, 'domain', **params))
#                 if params['college_id']:
#                     tasks.append(executor.submit(fetch_comparisons, 'college', **params))

  
#                 results = {}

#                 for future in as_completed(tasks):
#                     key, data = future.result()
                    
#                     if data and isinstance(data, list) and len(data) > 0:
#                         if key == 'degree_branch':
#                             results[data[0].get('course_name', 'unknown_course')] = data
#                         elif key == 'degree':
#                             results[data[0].get('degree_name', 'unknown_degree')] = data
#                         elif key == 'domain':
#                             results[data[0].get('domain_name', 'unknown_domain')] = data
#                         elif key == 'college':
#                              results[data[0].get('college_name', 'unknown_college')] = data
#                     else:
#                         results[f"unknown_{key}_comparisons"] = data  

#             return SuccessResponse(results, status=status.HTTP_200_OK)

#         except ValidationError as ve:
#             logger.error(f"Validation error in fetching comparisons: {ve}")
#             return Response(
#                 {"error": str(ve)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         except Exception as e:
#             logger.error(f"Unexpected error in fetching comparisons: {str(e)}\n{traceback.format_exc()}")
#             return Response(
#                 {"error": "An unexpected error occurred"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


class AllComparisonsView(APIView):
    """
    API view for handling all types of course comparisons with simplified parameter structure.
    Now primarily relies on course_id and college_id, fetching other IDs from course details.
    """
    permission_classes = [ApiKeyPermission]

    @extend_schema(
        summary="Get All Popular Comparisons",
        description="Retrieve popular course comparisons with simplified parameter structure. Most IDs are now derived from course_id.",
        parameters=[
            OpenApiParameter(name='course_id', type=int, description='Course ID (primary identifier for comparisons)', required=True),
            OpenApiParameter(name='college_id', type=int, description='College ID (for college-specific comparisons)', required=False),
            OpenApiParameter(name='cache_burst', type=int, description='Set to 0 to bypass cache and recompute results', required=False),
        ],
        responses={
            200: OpenApiResponse(description='Successful comparison retrieval'),
            400: OpenApiResponse(description='Invalid parameters'),
            404: OpenApiResponse(description='Course not found'),
            500: OpenApiResponse(description='Internal server error'),
        }
    )
    def get(self, request):
        """
        Handle retrieval of popular comparisons across all types using a simplified parameter structure.
        Now uses course_id as the primary identifier, deriving other IDs from it.
        """
        try:
            # Extract and validate primary parameters
            course_id = request.query_params.get('course_id')
            college_id = request.query_params.get('college_id')
            cache_burst = request.query_params.get('cache_burst', '0')

            # Validate course_id as it's now required
            if not course_id or not course_id.isdigit():
                return Response(
                    {"error": "Valid course_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Initialize base parameters
            params = {
                'course_id': int(course_id),
                'college_id': int(college_id) if college_id and college_id.isdigit() else None,
                'cache_burst': int(cache_burst) if cache_burst.isdigit() else 0
            }

            # Initialize comparison helper and fetch course details
            helper = ComparisonHelper()
            course_details = helper._get_course_details(params['course_id'])

            # Validate if course exists and has required details
            if not course_details['degree_id']:
                return Response(
                    {"error": "Course not found or missing required details"},
                    status=status.HTTP_404_NOT_FOUND
                )

            def fetch_comparisons(key, **kwargs):
                """
                Helper function to fetch comparisons based on comparison type.
                Now handles the simplified parameter structure.

                Args:
                    key: Comparison type identifier
                    kwargs: Parameters for comparison, primarily course_id and college_id

                Returns:
                    Tuple of (key, comparison_results)
                """
                return key, helper.get_popular_comparisons(
                    key,
                    cache_burst=kwargs.pop('cache_burst', 0),
                    **kwargs
                )

            # Initialize thread pool for parallel processing
            tasks = []
            with ThreadPoolExecutor() as executor:
                # Always add degree_branch and degree comparisons since we have course_id
                tasks.append(executor.submit(fetch_comparisons, 'degree_branch', **params))
                tasks.append(executor.submit(fetch_comparisons, 'degree', **params))

                # Add domain comparison if course has domain_id
                if course_details['domain_id']:
                    tasks.append(executor.submit(fetch_comparisons, 'domain', **params))

                # Add college comparison if college_id is provided
                if params['college_id']:
                    tasks.append(executor.submit(fetch_comparisons, 'college', **params))

                # Process results and organize them by comparison type
                results = {}
                for future in as_completed(tasks):
                    key, data = future.result()
                    
                    if data and isinstance(data, list) and len(data) > 0:
                        # Map comparison types to their respective identifiers
                        if key == 'degree_branch':
                            results[data[0].get('course_name', 'unknown_course')] = data
                        elif key == 'degree':
                            results[data[0].get('degree_name', 'unknown_degree')] = data
                        elif key == 'domain':
                            results[data[0].get('domain_name', 'unknown_domain')] = data
                        elif key == 'college':
                            results[data[0].get('college_name', 'unknown_college')] = data
                    else:
                        # Handle empty or invalid results
                        results[f"unknown_{key}_comparisons"] = data

            return SuccessResponse(results, status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error(f"Validation error in fetching comparisons: {ve}")
            return Response(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in fetching comparisons: {str(e)}\n{traceback.format_exc()}")
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )