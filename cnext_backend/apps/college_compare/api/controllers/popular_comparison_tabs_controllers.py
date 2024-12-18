from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.helpers.response import SuccessResponse, ErrorResponse, CustomErrorResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django.core.exceptions import ValidationError
import logging
import traceback



from college_compare.api.helpers.popular_comparison_tabs_helpers import (
  ComparisonHelper
)

logger = logging.getLogger(__name__)

from concurrent.futures import ThreadPoolExecutor, as_completed

class AllComparisonsView(APIView):
    """
    All types of comparisons (degree_branch, degree, domain, college)
    """
    
    @extend_schema(
        summary="Get All Popular Comparisons",
        description="Retrieve popular course comparisons for all types: degree_branch, degree, domain, and college.",
        parameters=[
            OpenApiParameter(name='degree_id', type=int, description='Degree ID (required for degree_branch, degree)', required=False),
            OpenApiParameter(name='branch_id', type=int, description='Branch ID (required for degree_branch)', required=False),
            OpenApiParameter(name='domain_id', type=int, description='Domain ID (required for domain comparisons)', required=False),
            OpenApiParameter(name='college_id', type=int, description='College ID (required for college comparisons)', required=False),
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
        """
        try:
            degree_id = request.query_params.get('degree_id')
            branch_id = request.query_params.get('branch_id')
            domain_id = request.query_params.get('domain_id')
            college_id = request.query_params.get('college_id')

            params = {
                'degree_id': int(degree_id) if degree_id and degree_id.isdigit() else None,
                'branch_id': int(branch_id) if branch_id and branch_id.isdigit() else None,
                'domain_id': int(domain_id) if domain_id and domain_id.isdigit() else None,
                'college_id': int(college_id) if college_id and college_id.isdigit() else None,
            }

            helper = ComparisonHelper()

            def fetch_comparisons(key, **kwargs):
                """
                Helper function to fetch comparisons based on the key.
                """
                return key, helper.get_popular_comparisons(key, **kwargs)

          
            tasks = []
            with ThreadPoolExecutor() as executor:
                if params['degree_id'] and params['branch_id']:
                    tasks.append(executor.submit(fetch_comparisons, 'degree_branch', **params))
                if params['degree_id'] and params['branch_id']:
                    tasks.append(executor.submit(fetch_comparisons, 'degree', **params))
                if params['domain_id']:
                    tasks.append(executor.submit(fetch_comparisons, 'domain', **params))
                if params['college_id']:
                    tasks.append(executor.submit(fetch_comparisons, 'college', **params))

            
                results = {key: [] for key in ['degree_branch_comparisons', 'degree_comparisons', 'domain_comparisons', 'college_comparisons']}
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