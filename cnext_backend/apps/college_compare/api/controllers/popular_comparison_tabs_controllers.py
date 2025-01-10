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




class AllComparisonsView(APIView):
    """
    All types of comparisons (degree_branch, degree, domain, college) with cache burst support
    """
    permission_classes = [ApiKeyPermission]
    
    @extend_schema(
        summary="Get All Popular Comparisons",
        description="Retrieve popular course comparisons for all types: degree_branch, degree, domain, and college.",
        parameters=[
            OpenApiParameter(name='degree_id', type=int, description='Degree ID (required for degree_branch, degree)', required=True),
            OpenApiParameter(name='branch_id', type=int, description='Branch ID (required for degree_branch)', required=True),
            OpenApiParameter(name='domain_id', type=int, description='Domain ID (required for domain comparisons)', required=True),
            OpenApiParameter(name='college_id', type=int, description='College ID (required for college comparisons)', required=True),
            OpenApiParameter(name='cache_burst', type=int, description='Set to 1 to bypass cache and recompute results', required=False),
        ],
        responses={
            200: OpenApiResponse(description='Successful comparison retrieval'),
            400: OpenApiResponse(description='Invalid parameters'),
            500: OpenApiResponse(description='Internal server error'),
        }
    )
    def get(self, request):
        """
        Handle retrieval of popular comparisons for all types.
        Supports cache bursting via cache_burst parameter.
        """
        try:
            # Parse query parameters
            degree_id = request.query_params.get('degree_id')
            branch_id = request.query_params.get('branch_id')
            domain_id = request.query_params.get('domain_id')
            college_id = request.query_params.get('college_id')
            cache_burst = request.query_params.get('cache_burst')

            # Validate and convert parameters
            params = {
                'degree_id': int(degree_id) if degree_id and degree_id.isdigit() else None,
                'branch_id': int(branch_id) if branch_id and branch_id.isdigit() else None,
                'domain_id': int(domain_id) if domain_id and domain_id.isdigit() else None,
                'college_id': int(college_id) if college_id and college_id.isdigit() else None,
                'cache_burst': int(cache_burst) if cache_burst and cache_burst.isdigit() else 0
            }

            helper = ComparisonHelper()

            def fetch_comparisons(key, **kwargs):
                """
                Helper function to fetch comparisons based on the key.
                Includes cache_burst parameter in the kwargs.
                """
                return key, helper.get_popular_comparisons(
                    key, 
                    cache_burst=kwargs.pop('cache_burst', 0),
                    **kwargs
                )

            # Initialize thread pool for parallel execution
            tasks = []
            with ThreadPoolExecutor() as executor:
                if params['degree_id'] and params['branch_id']:
                    tasks.append(executor.submit(fetch_comparisons, 'degree_branch', **params))
                    tasks.append(executor.submit(fetch_comparisons, 'degree', **params))
                if params['domain_id']:
                    tasks.append(executor.submit(fetch_comparisons, 'domain', **params))
                if params['college_id']:
                    tasks.append(executor.submit(fetch_comparisons, 'college', **params))

                # Initialize results dictionary with empty lists
                results = {
                    'degree_branch_comparisons': [],
                    'degree_comparisons': [],
                    'domain_comparisons': [],
                    'college_comparisons': []
                }
                
                # Collect results as they complete
                for future in as_completed(tasks):
                    key, data = future.result()
                    results[f"{key}_comparisons"] = data

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