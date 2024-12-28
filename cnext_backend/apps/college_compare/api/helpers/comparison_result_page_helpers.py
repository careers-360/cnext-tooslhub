from django.db.models import Avg, Count, F, Q,Max,Min
from django.db.models.functions import Round, ExtractYear, TruncDate, Concat
from django.core.cache import cache
from functools import lru_cache
from typing import Dict,List,Optional,Any
import hashlib
from hashlib import md5
from django.db.models import Subquery, ExpressionWrapper,Window, Func, OuterRef, Sum, Case, When,Value, CharField,IntegerField,DecimalField,Prefetch,FloatField,ExpressionWrapper
from django.db.models.functions import Coalesce,Cast,Concat,RowNumber
from decimal import Decimal
from college_compare.models import (
    College, CollegeReviews,Domain,CollegeFacility,CollegePlacement,CollegePlacementCompany,CourseFeeAmountType,RankingParameters,Company,RankingUploadList,Course,FeeBifurcation,Exam,Ranking,CollegeAccrediationApproval,ApprovalsAccrediations,CourseApprovalAccrediation
)

from college_compare.models import *
from django.contrib.postgres.aggregates import StringAgg
from django.db.models.expressions import RawSQL
from collections import defaultdict

from .landing_page_helpers import DomainHelper,CollegeDataHelper
import boto3
import os
import json
import re



class GroupConcat(Func):
    """Custom aggregate function for MySQL equivalent of STRING_AGG"""
    function = 'GROUP_CONCAT'
    template = '%(function)s(%(distinct)s%(expressions)s)'

    def __init__(self, expression, distinct=False, **extra):
        super().__init__(
            expression,
            distinct='DISTINCT ' if distinct else '',
            output_field=CharField(),
            **extra
        )




import logging
import traceback

logger = logging.getLogger(__name__)

import locale


locale.setlocale(locale.LC_ALL, 'en_IN.UTF-8')


def format_fee(value):
    """
    Format the fee value to Indian currency format with ₹ symbol or return 'NA' for zero/invalid values.
    """
    try:
      
        if int(value) == 0:
            return "NA"
        
        return f"₹ {locale.format_string('%d', int(value), grouping=True)}"
    except (ValueError, TypeError):
        return "NA"



class CacheHelper:
    @staticmethod
    def get_cache_key(*args):
        key = '_'.join(str(arg) for arg in args)
        return hashlib.md5(key.encode()).hexdigest()

    @staticmethod
    def get_or_set(key, callback, timeout=3600):
        result = cache.get(key)
        if result is None:
            result = callback()

            cache.set(key, result, timeout)
        return result





class RankingAccreditationHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        """
        Generate a cache key using MD5 hashing.
        """
        key = '_'.join(map(str, args))
        return md5(key.encode()).hexdigest()
    @staticmethod

    def fetch_graduation_outcome_score(college_ids: List[int], year: Optional[int] = None) -> Dict[int, float]:
        """
        Fetch the Graduation Outcome Score for a list of colleges from the RankingParameters table.
        Optionally filter the scores by a specific year.
        """
        try:
            # Build query with optional year filter
            filters = Q(name__icontains="Graduation Outcomes", ranking_upload__college_id__in=college_ids)
            if year:
                filters &= Q(ranking_upload__ranking__year=year)

            # Query RankingParameters for 'Graduation Outcomes'
            grad_outcome_scores = (
                RankingParameters.objects
                .filter(filters)
                .values('ranking_upload__college_id')
                .annotate(graduation_outcome_score=Max('score'))  # Use Max to handle multiple records
            )

            # Convert query result into a dictionary
            grad_outcome_score_dict = {
                item['ranking_upload__college_id']: item['graduation_outcome_score']
                for item in grad_outcome_scores
            }

            return grad_outcome_score_dict

        except Exception as e:
            logger.error("Error fetching Graduation Outcome Score: %s", traceback.format_exc())
            raise


   
    @staticmethod
    def fetch_ranking_data(college_ids: List[int], selected_domain: str, year: Optional[int] = None) -> Dict:
        """
        Fetch ranking and accreditation details for a list of colleges, optionally filtered by year.
        Ensures results are in the same order as the input college_ids.
        """
        try:
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
        except (ValueError, TypeError):
            logger.error("Invalid college_ids provided: %s", college_ids)
            raise ValueError("college_ids must be a list of integers or strings.")

        logger.debug(f"Fetching ranking data with college_ids: {college_ids}, selected_domain: {selected_domain}, year: {year}")

        cache_key = RankingAccreditationHelper.get_cache_key('Ranking____Data_v_1523', selected_domain, year, '-'.join(map(str, college_ids)))

        def fetch_data():
            try:
                # Filter by year if provided
                year_filter = Q(ranking__year=year) if year else Q()


                other_ranked_domain_subquery = (
                    RankingUploadList.objects
                    .filter(college_id=OuterRef('college_id'))
                    .exclude(ranking__nirf_stream='')
                    .exclude(ranking__ranking_stream=selected_domain)
                    .annotate(
                        overall_rank_str=Cast(F('overall_rank'), CharField()),
                        other_ranked_domain=Concat(
                            F('ranking__nirf_stream'),
                            Value(' (NIRF '),
                            F('overall_rank_str'),
                            Value(')')
                        )
                    )
                    .values('overall_rank', 'other_ranked_domain')
                    .distinct()
                    .order_by('overall_rank')
                )
                min_other_ranked_domain = other_ranked_domain_subquery.values('other_ranked_domain')[2:3]


                # Fetch ranking data
                rankings = (
                    RankingUploadList.objects
                    .filter(college_id__in=college_ids)
                    .filter(year_filter)
                    .values('college_id')
                    .annotate(
                        careers360_overall_rank=Max(
                            Case(
                                When(
                                    Q(ranking__ranking_authority='Careers360') &
                                    ~Q(ranking__ranking_stream=selected_domain) &
                                    Q(Q(ranking__status=1) | Q(ranking__status__isnull=True)),
                                    then=F('overall_rating')
                                ),
                                default=None
                            )
                        ),
                        careers360_domain_rank=Max(
                            Case(
                                When(
                                    Q(ranking__ranking_authority='Careers360') &
                                    Q(ranking__ranking_stream=selected_domain) &
                                    Q(Q(ranking__status=1) | Q(ranking__status__isnull=True)),
                                    then=F('overall_rating')
                                ),
                                default=None
                            )
                        ),
                        nirf_overall_rank=Max(
                            Case(
                                When(
                                    Q(ranking__ranking_authority='NIRF') &
                                    Q(ranking__ranking_entity='Overall') &
                                    Q(Q(ranking__status=1) | Q(ranking__status__isnull=True)),
                                    then=F('overall_rank')
                                ),
                                default=None
                            )
                        ),
                        nirf_domain_rank=Max(
                            Case(
                                When(
                                    Q(ranking__ranking_authority='NIRF') &
                                    Q(ranking__ranking_entity='Stream Wise Colleges') &
                                    Q(ranking__ranking_stream=selected_domain) &
                                    Q(Q(ranking__status=1) | Q(ranking__status__isnull=True)),
                                    then=F('overall_rank')
                                ),
                                default=None
                            )
                        ),
                         other_ranked_domain=Subquery(min_other_ranked_domain),
                        domain_name=Max(
                            Case(
                                When(
                                    Q(ranking__ranking_stream=selected_domain),
                                    then=F('ranking__nirf_stream')
                                ),
                                default=None
                            )
                        )
                    )
                )
                    

                # Fetch accreditation and approval data
                all_accreditations = (
                    CollegeAccrediationApproval.objects
                    .filter(college_id__in=college_ids)
                    .select_related('value')
                    .only('college_id', 'type', 'value__short_name')
                )

                approvals_dict = {}
                accreditations_dict = {}

                for acc in all_accreditations:
                    if acc.college_id not in approvals_dict:
                        approvals_dict[acc.college_id] = set()
                    if acc.college_id not in accreditations_dict:
                        accreditations_dict[acc.college_id] = set()

                    if acc.type == 'college_approvals' and acc.value and acc.value.short_name:
                        approvals_dict[acc.college_id].add(acc.value.short_name)
                    elif acc.type == 'college_accrediation' and acc.value and acc.value.short_name:
                        accreditations_dict[acc.college_id].add(acc.value.short_name)

                approvals_dict = {
                    k: ', '.join(sorted(v)) if v else 'NA'
                    for k, v in approvals_dict.items()
                }
                accreditations_dict = {
                    k: ', '.join(sorted(v)) if v else 'NA'
                    for k, v in accreditations_dict.items()
                }

                # Fetch college details
                college_details = {
                    college['id']: {
                        'name': college['name'],
                        'ownership': college['ownership'],
                        'location': college['location'],
                    }
                    for college in College.objects.filter(id__in=college_ids)
                    .select_related('location')
                    .values('id', 'name', 'ownership', 'location')
                }

                # Fetch Graduation Outcome Scores
                graduation_outcome_scores = RankingAccreditationHelper.fetch_graduation_outcome_score(college_ids,year=year)

                # Maintain the exact order of college_ids
                result_dict = {}
                for idx, college_id in enumerate(college_ids, start=1):
                    ranking = next((r for r in rankings if r['college_id'] == college_id), {})
                    college_data = college_details.get(college_id, {})
                    location_id = college_data.get('location', 'NA')
                    location_string = 'NA'

                    if location_id != 'NA':
                        # Fetch the location string from the Location model
                        location_obj = Location.objects.filter(id=location_id).first()
                        location_string = location_obj.loc_string if location_obj else 'NA'

                    result_dict[f"college_{idx}"] = {
                        "college_id": college_id,
                        "college_name": college_data.get('name', 'NA'),
                        "ownership": dict(College.OWNERSHIP_CHOICES).get(college_data.get('ownership'), 'NA'),
                        "location": location_string,
                        "careers360_overall_rank": ranking.get('careers360_overall_rank', 'NA'),
                        "careers360_domain_rank": ranking.get('careers360_domain_rank', 'NA'),
                        "nirf_overall_rank": ranking.get('nirf_overall_rank', 'NA'),
                        "nirf_domain_rank": ranking.get('nirf_domain_rank', 'NA'),
                        "approvals": approvals_dict.get(college_id, 'NA'),
                        "accreditations": accreditations_dict.get(college_id, 'NA'),
                        "graduation_outcome_score": graduation_outcome_scores.get(college_id, 'NA'),
                         "other_ranked_domain": ranking.get('other_ranked_domain') or 'NA',
                        "domain_name": ranking.get('domain_name') or 'NA',
                 
                    }

                return result_dict

            except Exception as e:
                logger.error("Error fetching ranking and accreditation data: %s", traceback.format_exc())
                raise

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 31)





class CollegeRankingService:
    @staticmethod
    def get_state_and_ownership_ranks(
        college_ids: List[int], selected_domain: int, year: int
    ) -> Dict[str, Dict]:
        """
        Gets state-wise and ownership-wise ranks based on overall ranks for given college IDs.
        Ensures rank consistency by using overall rank as the base for calculations.

        Args:
            college_ids: List of college IDs.
            selected_domain: Domain ID.
            year: Year of the ranking.

        Returns:
            A dictionary containing rank information.
        """
        try:
            domain_id_str = str(selected_domain)

            # Get all colleges with their overall ranks
            base_queryset = RankingUploadList.objects.filter(
                ranking__ranking_stream=domain_id_str,
                ranking__year=year,
                ranking__status=1
            ).select_related('college', 'college__location')

            # Get distinct colleges to avoid duplicates
            college_ranks = base_queryset.values(
                'college_id',
                'overall_rank',
                'college__location__state_id',
                'college__location__loc_string',
                'college__ownership'
            ).distinct('college_id').order_by('college_id', 'overall_rank')

            # Group colleges by state and ownership
            state_groups = {}
            ownership_groups = {}

            for college in college_ranks:
                state_id = college['college__location__state_id']
                ownership = college['college__ownership']
                
                # Initialize groups if they don't exist
                if state_id not in state_groups:
                    state_groups[state_id] = []
                if ownership not in ownership_groups:
                    ownership_groups[ownership] = []
                
                # Add college to respective groups
                state_groups[state_id].append({
                    'college_id': college['college_id'],
                    'overall_rank': college['overall_rank'],
                    'state_name': college['college__location__loc_string']
                })
                
                ownership_groups[ownership].append({
                    'college_id': college['college_id'],
                    'overall_rank': college['overall_rank']
                })

            # Sort colleges within each group by overall rank
            for state_id in state_groups:
                state_groups[state_id].sort(key=lambda x: x['overall_rank'])
            
            for ownership in ownership_groups:
                ownership_groups[ownership].sort(key=lambda x: x['overall_rank'])

            # Calculate ranks within each group
            result = {}
            for idx, college_id in enumerate(college_ids):
                college_key = f"college_{idx + 1}"
                state_rank = ownership_rank = "Not Available"
                state_total = ownership_total = 0
                state_name = ""
                ownership_type = dict(College.OWNERSHIP_CHOICES).get(None, 'Unknown')

                
                for state_id, colleges in state_groups.items():
                    for rank, college in enumerate(colleges, 1):
                        if college['college_id'] == college_id:
                            state_rank = rank
                            state_total = len(colleges)
                            state_name = college['state_name']
                            break

                # Find ownership rank
                for ownership_id, colleges in ownership_groups.items():
                    for rank, college in enumerate(colleges, 1):
                        if college['college_id'] == college_id:
                            ownership_rank = rank
                            ownership_total = len(colleges)
                            ownership_type = dict(College.OWNERSHIP_CHOICES).get(ownership_id, 'Unknown')
                            break

                result[college_key] = {
                    "college_id": college_id,
                    "state_rank_display": (
                        f"{state_rank}{get_ordinal_suffix(state_rank)} out of {state_total} in {state_name}"
                        if isinstance(state_rank, int) else "Not Available"
                    ),
                    "ownership_rank_display": (
                        f"{ownership_rank}{get_ordinal_suffix(ownership_rank)} out of {ownership_total} in {ownership_type} Institutes"
                        if isinstance(ownership_rank, int) else "Not Available"
                    ),
                }

            return result

        except Exception as e:
            logger.error("Error calculating state and ownership ranks: %s", traceback.format_exc())
            raise

def get_ordinal_suffix(num: int) -> str:
    """Returns ordinal suffix for a number (1st, 2nd, 3rd, etc.)"""
    if 10 <= num % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(num % 10, 'th')
    return suffix
   



class MultiYearRankingHelper:
    @staticmethod
    def fetch_multi_year_ranking_data(college_ids: List[int], selected_domain: str, years: List[int]) -> Dict:
        """
        Fetch 5 years of ranking and accreditation data for a list of colleges.
        Aggregates data such as NIRF rankings, graduation outcome scores, and other ranked domains.

        Args:
            college_ids (List[int]): List of college IDs to fetch data for.
            selected_domain (str): The domain of interest for rankings.
            years (List[int]): List of years to fetch data for.

        Returns:
            Dict: Aggregated ranking and accreditation data for each college.
        """
        try:
            # Validate years
            if not years or len(years) != 5:
                raise ValueError("Exactly 5 years must be provided.")
            
            # Initialize result dictionary
            result_dict = {f"college_{i + 1}": {"college_id": college_id} for i, college_id in enumerate(college_ids)}
            
            # Fetch data for each year
            for year in years:
                yearly_data = RankingAccreditationHelper.fetch_ranking_data(college_ids, selected_domain, year)
                for key, data in yearly_data.items():
                    college = result_dict.get(key, {})
                    
                    # Append or initialize ranking and scores
                    college.setdefault("college_name", data.get("college_name", "NA"))
                    college.setdefault("nirf_overall_rank", []).append(data.get("nirf_overall_rank", "NA"))
                    college.setdefault("nirf_domain_rank", []).append(data.get("nirf_domain_rank", "NA"))
                    college.setdefault("graduation_outcome_scores", []).append(data.get("graduation_outcome_score", "NA"))
                    
                    # Handle 'other ranked domain' for ranked domains other than the selected one
                    college.setdefault("other_ranked_domain", [])
                    if "nirf_domain_rank" in data and data["nirf_domain_rank"] != "NA":
                        other_domain_entry = f"{selected_domain} (NIRF {data['nirf_domain_rank']})"
                        college["other_ranked_domain"].append(other_domain_entry)

                    result_dict[key] = college

            return result_dict

        except Exception as e:
            logger.error("Error fetching multi-year ranking data: %s", traceback.format_exc())
            raise

class RankingGraphHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        """
        Generate a unique cache key by hashing the combined arguments.
        """
        key = '_'.join(map(str, args))
        return hashlib.md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_ranking_data(
        college_ids: List[int],
        start_year: int,
        end_year: int,
        domain_id: int = None,
        ranking_entity: str = None,
    ) -> Dict:
        """
        Fetch ranking data for given colleges and year range, optionally filtered by domain and ranking entity.
        """
        try:
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
        except (ValueError, TypeError):
            raise ValueError("college_ids must be a flat list of integers or strings.")

        cache_key = RankingGraphHelper.get_cache_key(
            'ranking_graph_insight_v2', '-'.join(map(str, college_ids)), start_year, end_year, domain_id, ranking_entity
        )

        def fetch_data():
            year_range = list(range(start_year, end_year + 1))

            # Create filters for the query
            filters = Q(ranking__status=1, ranking__year__in=year_range)
            if domain_id:
                filters &= Q(ranking__ranking_stream=domain_id)
            if ranking_entity:
                filters &= Q(ranking__ranking_entity=ranking_entity)

           
            rankings = (
                RankingUploadList.objects.filter(filters, college_id__in=college_ids)
                .select_related('ranking')  
                .values(
                    "college_id",
                    "ranking__year",
                    "ranking__ranking_stream",
                    "ranking__ranking_entity",
                    "overall_score"
                )
            )

           
            college_order = {college_id: idx for idx, college_id in enumerate(college_ids)}
            result_dict = {
                f"college_{i + 1}": {"college_id": college_id, "data": {year: "NA" for year in year_range}} \
                for i, college_id in enumerate(college_ids)
            }

          
            for ranking in rankings:
                college_key = f"college_{college_order[ranking['college_id']] + 1}"
                result_dict[college_key]["data"][ranking["ranking__year"]] = ranking["overall_score"] or "NA"

            return result_dict

       
        return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 365)

    @staticmethod
    def prepare_graph_insights(
        college_ids: List[int], start_year: int, end_year: int, domain_id: int
    ) -> Dict:
        """
        Prepare data for the ranking insights graph, including overall and domain-specific data.

        Args:
            college_ids (List[int]): List of college IDs.
            start_year (int): Start year for the rankings.
            end_year (int): End year for the rankings.
            domain_id (int): Domain ID for fetching domain-specific data.

        Returns:
            Dict: A dictionary containing insights for the rankings graph.
        """
        years = list(range(start_year, end_year + 1))

        overall_data = RankingGraphHelper.fetch_ranking_data(
            college_ids, start_year, end_year, ranking_entity='Overall'
        )

      
        domain_data = RankingGraphHelper.fetch_ranking_data(
            college_ids, start_year, end_year, domain_id=domain_id, ranking_entity='Stream Wise Colleges'
        )

       
        college_names = list(
                    College.objects.filter(id__in=college_ids)
                    .annotate(order=Case(
                        *[When(id=college_id, then=Value(idx)) for idx, college_id in enumerate(college_ids)],
                        default=Value(len(college_ids)),  
                        output_field=IntegerField()
                    ))
                    .order_by('order')
                    .values_list('name', flat=True)
                )

        return {
            "years": years,
            "overall": {
                "type": "line",
                "colleges": overall_data
            },
            "domain": {
                "type": "line",
                "colleges": domain_data
            },
            "college_names": college_names
        }


    


class PlacementStatsComparisonHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = '_'.join(map(str, args))
        return md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_placement_stats(college_ids: List[int], year: int, domain_id: int) -> Dict:
        try:
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
        except (ValueError, TypeError):
            logger.error("Invalid college_ids provided: college_ids=%s", college_ids)
            raise ValueError("college_ids must be a flat list of integers or strings.")

        cache_key = PlacementStatsComparisonHelper.get_cache_key(
            'placement__stats_____comparisons_v1', '-'.join(map(str, college_ids)), year, domain_id
        )

        def fetch_data():
            try:
                # Join with the College model to include college names
                placement_stats = (
                    CollegePlacement.objects.filter(
                        college_id__in=college_ids, 
                        year=year,
                        intake_year=year - 3,
                        stream_id=domain_id
                    )
                    .annotate(college_name=F('college__name'))  # Assuming a ForeignKey field named 'college'
                    .values(
                        'college_id',
                        'college_name',
                        'max_salary_dom',
                        'max_salary_inter',
                        'avg_salary',
                        'median_salary',
                        'no_placed',
                        'inter_offers',
                        'total_offers',
                        'stream_id'
                    )
                )

                college_order = {college_id: idx for idx, college_id in enumerate(college_ids)}
                result_dict = {f"college_{i + 1}": {} for i in range(len(college_ids))}

                for stats in placement_stats:
                    college_id = stats['college_id']
                    idx = college_order[college_id] + 1
                    college_key = f"college_{idx}"
                    domain = Domain.objects.filter(id=domain_id).first()
                    domain_name = DomainHelper.format_domain_name(domain.old_domain_name) if domain else None

                    result_dict[college_key] = {
                        "college_id": stats['college_id'],
                        "college_name": stats['college_name'],  # Add college name here
                        "total_offers": stats['total_offers'] or 0,
                        "total_students_placed_in_domain": stats['no_placed'] or "N/A",
                        "highest_domestic_salary_lpa": stats['max_salary_dom'] or 0,
                        "highest_international_salary_cr": stats['max_salary_inter'] or 0,
                        "average_salary_lpa": format_fee(stats['avg_salary']),
                        "median_salary_lpa": format_fee(stats['median_salary']),
                        "domain_id": stats['stream_id'],
                        "domain_name": domain_name
                    }

                return result_dict

            except Exception as e:
                logger.error("Error fetching placement stats comparison data: %s", str(e))
                raise

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 365)

    @staticmethod
    def compare_placement_stats(stats_data: Dict) -> Dict:
        try:
            result_dict = {}
            for college_key, college_data in stats_data.items():
                result_dict[college_key] = {
                    "college_id": college_data.get("college_id"),
                    "college_name": college_data.get("college_name"),  # Include college name here
                    "total_offers": college_data.get("total_offers", 0),
                    "total_students_placed_in_domain": college_data.get("total_students_placed_in_domain", 0),
                    "highest_domestic_salary_lpa": college_data.get("highest_domestic_salary_lpa", 0),
                    "highest_international_salary_cr": college_data.get("highest_international_salary_cr", 0),
                    "average_salary_lpa": round(college_data.get("average_salary_lpa", 0), 2),
                    "median_salary_lpa": round(college_data.get("median_salary_lpa", 0), 2),
                }

            return result_dict

        except Exception as e:
            logger.error("Error in comparing placement stats: %s", str(e))
            raise





class PlacementGraphInsightsHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = '_'.join(map(str, args))
        return md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_placement_insights(
        college_ids: List[int],
        domain_id: int,
        year: int
    ) -> Dict:
        cache_key = PlacementGraphInsightsHelper.get_cache_key(
            'placement_____Insights_v3', '-'.join(map(str, college_ids)), domain_id, year
        )

        def fetch_data():
            filters = Q(year=year, published='published')
            if domain_id:
                filters &= Q(stream_id=domain_id)

          
            placements = {}
            placement_records = (
                CollegePlacement.objects.filter(
                    filters,
                    college_id__in=college_ids
                )
                .select_related('college')
                .values(
                    'college_id',
                    'total_students',
                    'no_placed',
                    'median_salary',
                    'max_salary_dom',
                    'max_salary_inter'
                )
            )

         
            for placement in placement_records:
                college_id = placement['college_id']
                if college_id not in placements:
                    placements[college_id] = {
                        'total_students': 0,
                        'no_placed': 0,
                        'max_salary_dom': 0,
                        'max_salary_inter': 0
                    }
                
               
                placements[college_id]['total_students'] += placement.get('total_students', 0) or 0
                placements[college_id]['no_placed'] += placement.get('no_placed', 0) or 0
                placements[college_id]['max_salary_dom'] = max(
                    placements[college_id]['max_salary_dom'], 
                    placement.get('max_salary_dom', 0) or 0
                )
                placements[college_id]['max_salary_inter'] = max(
                    placements[college_id]['max_salary_inter'], 
                    placement.get('max_salary_inter', 0) or 0
                )

         
            recruiter_data = {}
            for college_id in college_ids:
                recruiters = (
                    Company.objects.filter(
                        collegeplacementcompany__collegeplacement__college_id=college_id,
                        collegeplacementcompany__collegeplacement__year=year,
                        published='published'
                    )
                    .values('popular_name', 'logo', 'name')
                    .distinct()[:5]
                )
                recruiter_data[college_id] = [
                    {
                        "name": recruiter.get('popular_name') or recruiter.get('name'),
                        "logo": recruiter.get('logo'),
                    }
                    for recruiter in recruiters
                ]

         
            colleges = {
                college['id']: college['name']
                for college in College.objects.filter(id__in=college_ids).values('id', 'name')
            }

            # Prepare the result dictionary
            result_dict = {
                "placement_data": {"type": "vertical bar", "colleges": {}},
                "salary_data": {"type": "vertical bar", "colleges": {}},
                "recruiter_data": {"type": "vertical bar", "colleges": {}},
                "college_names": [colleges[college_id] for college_id in college_ids],
            }

            # Process each college in the order of college_ids
            for idx, college_id in enumerate(college_ids, 1):
                college_key = f"college_{idx}"
                placement = placements.get(college_id, {})
                logger.info(f"Processing placement data for college_id {college_id}: {placement}")

                total_students = placement.get('total_students', 0)
                placed_students = placement.get('no_placed', 0)
                logger.info(f"Total students: {total_students}, Placed students: {placed_students}")

                # Handle None or 0 for placement percentage calculation
                placement_percentage = (
                    round((placed_students / total_students) * 100, 2)
                    if total_students > 0 else 0
                )
                logger.info(f"Placement percentage for college {college_id}: {placement_percentage}")

                max_salary_dom = placement.get('max_salary_dom', 0)
                max_salary_inter = placement.get('max_salary_inter', 0)
                logger.info(f"Max salaries for college {college_id}: Domestic={max_salary_dom}, International={max_salary_inter}")

                max_salary = max(max_salary_dom, max_salary_inter)
                logger.info(f"Final max salary for college {college_id}: {max_salary}")

                result_dict["placement_data"]["colleges"][college_key] = {
                    "value": placement_percentage,
                    "college_id": college_id
                }
                result_dict["salary_data"]["colleges"][college_key] = {
                    "max_value": format_fee(max_salary),
                    "college_id": college_id
                }
                result_dict["recruiter_data"]["colleges"][college_key] = {
                    "companies": recruiter_data.get(college_id, []),
                    "college_id": college_id
                }

            return result_dict
        return cache.get_or_set(cache_key, fetch_data, 3600 * 24)

class CourseFeeComparisonHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = '_'.join(map(str, args))
        return md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_exams_for_courses(course_ids: List[int]) -> Dict[int, Dict]:
        exams_map = defaultdict(dict)

        top_exam_subquery = Exam.objects.filter(
            college_courses__college_course=OuterRef('pk')
        ).order_by('id').values('exam_name')[:2]

        for course in Course.objects.filter(id__in=course_ids):
            exams = Exam.objects.filter(
                college_courses__college_course=course
            ).order_by('id')

            top_exams = [exam.exam_short_name or exam.exam_name for exam in exams[:2]]
            all_exams = [exam.exam_short_name or exam.exam_name for exam in exams]

            exams_map[course.id] = {
                "top_exams": ", ".join(top_exams) if top_exams else "N/A",
                "all_exams": ", ".join(all_exams) if len(all_exams) > 2 else None
            }

        return exams_map

    @staticmethod
    def fetch_comparison_data(college_ids: List[int], course_ids: List[int]) -> Dict:
        try:
            try:
                course_ids = [int(course_id) for course_id in course_ids if isinstance(course_id, (int, str))]
                college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
            except (ValueError, TypeError):
                raise ValueError("course_ids and college_ids must be flat lists of integers or strings.")

            cache_key = CourseFeeComparisonHelper.get_cache_key('Courses_comparisons_v8', '-'.join(map(str, course_ids)))

            def fetch_data():
                try:
                    college_order = {college_id: idx for idx, college_id in enumerate(college_ids)}

                    fee_details = (
                        FeeBifurcation.objects.filter(
                            college_course_id__in=course_ids, category='gn'
                        )
                        .values('college_course_id')
                        .annotate(total_fees=Coalesce(Sum('total_fees'), Value(0, output_field=DecimalField())))
                    )
                    fees_map = {item['college_course_id']: format_fee(item['total_fees']) for item in fee_details}

                    exams_map = CourseFeeComparisonHelper.fetch_exams_for_courses(course_ids)

                    course_approvals = CourseApprovalAccrediation.objects.filter(
                        type='course_approval',
                        course_id__in=course_ids
                    ).values('course_id').annotate(
                        approval_names=RawSQL(
                            """
                            SELECT GROUP_CONCAT(DISTINCT aa.short_name ORDER BY aa.short_name ASC SEPARATOR ', ')
                            FROM approvals_accrediations aa
                            JOIN course_approval_accrediations caa ON caa.value = aa.id
                            WHERE caa.course_id = course_approval_accrediations.course_id
                            AND caa.type = 'course_approval'
                            """, ()
                        )
                    )
                    approvals_map = {item['course_id']: item['approval_names'] for item in course_approvals}

                    course_accreditations = CourseApprovalAccrediation.objects.filter(
                        type='course_accreditation',
                        course_id__in=course_ids
                    ).values('course_id').annotate(
                        accreditation_names=RawSQL(
                            """
                            SELECT GROUP_CONCAT(DISTINCT aa.short_name ORDER BY aa.short_name ASC SEPARATOR ', ')
                            FROM approvals_accrediations aa
                            JOIN course_approval_accrediations caa ON caa.value = aa.id
                            WHERE caa.course_id = course_approval_accrediations.course_id
                            AND caa.type = 'course_accreditation'
                            """, ()
                        )
                    )
                    accreditations_map = {item['course_id']: item['accreditation_names'] for item in course_accreditations}

                    result_dict = {f"college_{i+1}": [] for i in range(len(college_ids))}

                    courses = Course.objects.filter(id__in=course_ids, college_id__in=college_ids)
                    
                    college_courses = defaultdict(list)
                    for course in courses:
                        college_courses[course.college.id].append(course)

                    for college_id in college_ids:
                        idx = college_order[college_id] + 1
                        college_key = f"college_{idx}"
                        
                        for course in college_courses[college_id]:
                            exams = exams_map.get(course.id, {})
                            course_data = {
                                "college_name": course.college.name,
                                "college_id": course.college.id,
                                "course": course.id,
                                "course_credential": "Degree",
                                "degree": course.degree.name,
                                "branch": course.branch.name,
                                "duration": f"{course.course_duration // 12} years",
                                "mode": "offline" if course.study_mode == 2 else "online" if course.study_mode == 1 else "NA",
                                "approved_intake": course.approved_intake or "NA",
                                "total_fees": fees_map.get(course.id, 0),
                                "top_exams_accepted": exams.get("top_exams", "N/A"),
                                "all_exams_accepted": exams.get("all_exams", None),
                                "course_approval": approvals_map.get(course.id, "N/A"),
                                "course_accreditation": accreditations_map.get(course.id, "N/A"),
                                "eligibility_criteria_short": (course.eligibility_criteria or "N/A")[:100],
                                "admission_details": course.admission_procedure or "N/A",
                                "eligibility_criteria": course.eligibility_criteria or "N/A",
                            }
                            result_dict[college_key].append(course_data)

                    return result_dict

                except Exception as e:
                    logger.error("Error fetching course comparison data: %s", traceback.format_exc())
                    raise

            return cache.get_or_set(cache_key, fetch_data, 3600*24*365)

        except Exception as e:
            logger.error("Error in fetch_comparison_data: %s", traceback.format_exc())
            return {"error": "An error occurred while fetching comparison data"}



class FeesHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = '_'.join(map(str, args))
        return md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_fees_details(course_ids: List[int], college_ids: List[int], intake_year: int) -> Dict:
        try:
            course_ids = [int(course_id) for course_id in course_ids if isinstance(course_id, (int, str))]
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
        except (ValueError, TypeError):
            logger.error("Invalid course_ids or college_ids provided: course_ids=%s, college_ids=%s", course_ids, college_ids)
            raise ValueError("course_ids and college_ids must be flat lists of integers or strings.")

        cache_key = FeesHelper.get_cache_key('fees__details___v123', '-'.join(map(str, course_ids)), intake_year)
        
        def fetch_data():
            try:
                

                fee_details = (
                    Course.objects.filter(id__in=course_ids, college_id__in=college_ids)
                    .annotate(
                        gn_fees=Coalesce(
                            Sum(Case(
                                When(fees__category='GN', then=F('fees__total_fees')),
                                default=Value(0),
                                output_field=DecimalField(max_digits=10, decimal_places=2)
                            )),
                            Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
                        ),
                        obc_fees=Coalesce(
                            Sum(Case(
                                When(fees__category='OBC', then=F('fees__total_fees')),
                                default=Value(0),
                                output_field=DecimalField(max_digits=10, decimal_places=2)
                            )),
                            Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
                        ),
                        sc_fees=Coalesce(
                            Sum(Case(
                                When(fees__category='SC', then=F('fees__total_fees')),
                                default=Value(0),
                                output_field=DecimalField(max_digits=10, decimal_places=2)
                            )),
                            Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
                        ),
                        nq_fees=Coalesce(
                            Sum(Case(
                                When(fees__category='NQ', then=F('fees__total_fees')),
                                default=Value(0),
                                output_field=DecimalField(max_digits=10, decimal_places=2)
                            )),
                            Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
                        )
                    )
                    .values('id', 'college_id', 'gn_fees', 'obc_fees', 'sc_fees', 'nq_fees')
                )

                # Fetch tuition fees with consistent DecimalField output
                tuition_fees = (
                    CourseFeeAmountType.objects.filter(
                        course_fee_duration__college_course_id__in=course_ids,
                        course_fee_duration__type='year',
                        fees_type='Tution Fees' or 'Tution Fee' 
                    ).annotate(
                        course_id=F('course_fee_duration__college_course_id'),
                        duration_count=F('course_fee_duration__count'),
                        total_amount=F('amount') * F('course_fee_duration__count'),
                    ).values(
                        'course_id',
                        'total_amount'
                    )
                )
                
                tuition_fees_map = {
                    fee['course_id']: fee['total_amount']
                    for fee in tuition_fees
                }

                # Fetch scholarship data with consistent DecimalField output
                scholarships_data = (
                    CollegePlacement.objects.filter(college_id__in=college_ids, intake_year=intake_year)
                    .values('college_id')
                    .annotate(
                        total_gov=Coalesce(
                            Sum('reimbursement_gov', output_field=DecimalField(max_digits=10, decimal_places=2)),
                            Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
                        ),
                        total_institution=Coalesce(
                            Sum('reimbursement_institution', output_field=DecimalField(max_digits=10, decimal_places=2)),
                            Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
                        ),
                        total_private=Coalesce(
                            Sum('reimbursement_private_bodies', output_field=DecimalField(max_digits=10, decimal_places=2)),
                            Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
                        )
                    )
                )

                scholarships_map = {
                    data['college_id']: {
                        'total_scholarship': (
                            data['total_gov'] +
                            data['total_institution'] +
                            data['total_private']
                        ),
                        'high_scholarship_authority': FeesHelper.get_high_scholarship_authority(
                            data['total_gov'],
                            data['total_institution'],
                            data['total_private']
                        )
                    }
                    for data in scholarships_data
                }

                # Fetch college names
                colleges = {
                    college.id: college.name
                    for college in College.objects.filter(id__in=college_ids)
                }

                # Format final response
                result_dict = {}
                for idx, fee_detail in enumerate(fee_details, start=1):
                    college_id = fee_detail['college_id']
                    college_name = colleges.get(college_id, 'Unknown College')
                    course_id = fee_detail['id']
                    scholarship_data = scholarships_map.get(college_id, {
                        'total_scholarship': Decimal('0.00'),
                        'high_scholarship_authority': 'NA'
                    })

                    total_scholarship = int(scholarship_data['total_scholarship'])
                    tuition_fee = tuition_fees_map.get(course_id, Decimal('0.00'))

                    result_dict[f"college_{idx}"] = {
                        "college_id": college_id,
                        "college_name": college_name,
                        "gn_fees": format_fee(fee_detail['gn_fees']),
                        "obc_fees": format_fee(fee_detail['obc_fees']),
                        "sc_fees": format_fee(fee_detail['sc_fees']),
                        "nq_fees": format_fee(fee_detail['nq_fees']),
                        "total_scholarship_given": total_scholarship if total_scholarship > 0 else "NA",
                        "high_scholarship_authority": scholarship_data['high_scholarship_authority'],
                        "total_tuition_fees": format_fee(tuition_fee) if tuition_fee > 0 else "NA"
                    }

                # Ensure results are sorted by the original order of college_ids
                sorted_result_dict = {key: result_dict[key] for key in map(lambda x: f"college_{x}", range(1, len(college_ids) + 1))}
                
                return sorted_result_dict

            except Exception as e:
                logger.error("Error fetching fee details: %s", traceback.format_exc())
                raise

        return cache.get_or_set(cache_key, fetch_data, 3600*24)  # Cache for 24 hours

    @staticmethod
    def get_high_scholarship_authority(total_gov: Decimal, total_institution: Decimal, total_private: Decimal) -> str:
        authority_map = {
            'Government': total_gov,
            'Institution': total_institution,
            'Private': total_private
        }
        max_authority = max(authority_map, key=authority_map.get)
        return max_authority if authority_map[max_authority] > 0 else 'NA'


class FeesGraphHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = '_'.join(map(str, args))
        return hashlib.md5(key.encode()).hexdigest()
    
    @staticmethod
    def fetch_fee_data(course_ids: List[int]) -> Dict:
        try:
            course_ids = [int(course_id) for course_id in course_ids if isinstance(course_id, (int, str))]
        except (ValueError, TypeError):
            raise ValueError("course_ids must be a flat list of integers or strings.")
        
        cache_key = FeesGraphHelper.get_cache_key('fees_graph__data_v3', '-'.join(map(str, course_ids)))
        
        def fetch_data():
            static_categories = ['gn', 'obc', 'sc']
            
            courses = (
                Course.objects.filter(id__in=course_ids)
                .select_related('college')
                .values(
                    'id',
                    'college__name'
                )
            )
            
            result_dict = {
                "categories": static_categories,
                "data": {category: {"type": "vertical bar", "values": {}} for category in static_categories},
                "college_names": []
            }
            
            college_names = []
            course_id_to_name = {}
            ordered_course_ids = []
            for course in courses:
                college_names.append(course['college__name'])
                course_id_to_name[course['id']] = course['college__name']
                ordered_course_ids.append(course['id'])
            
            fees_data = (
                FeeBifurcation.objects.filter(college_course__in=course_ids)
                .values(
                    "college_course_id",
                    "category",
                    "total_fees"
                )
            )
            
            fee_mapping = {}
            for fee in fees_data:
                course_id = fee["college_course_id"]
                category = fee["category"]
                total_fees = fee["total_fees"]
                if course_id not in fee_mapping:
                    fee_mapping[course_id] = {}
                fee_mapping[course_id][category] = total_fees
            
            for idx, course_id in enumerate(ordered_course_ids, 1):
                college_name = course_id_to_name.get(course_id)
                if college_name:
                    for category in static_categories:
                        college_key = f"college_{idx}"
                        total_fees = fee_mapping.get(course_id, {}).get(category)
                        
                        result_dict["data"][category]["values"][college_key] = {
                            "course_id": course_id,
                            "fee": f"₹ {total_fees:,.0f}" if total_fees is not None else "NA"
                        }
            
            result_dict["college_names"] = college_names
            return result_dict
        
        return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 365)
    
    @staticmethod
    def prepare_fees_insights(course_ids: List[int]) -> Dict:
        return FeesGraphHelper.fetch_fee_data(course_ids)




class ClassProfileHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = '_'.join(str(arg) for arg in args)
        return md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_class_profiles(college_ids: List[int], year: int, intake_year: int, level: int) -> Dict:
        """
        Fetch Class Profile data for a list of colleges.

        Args:
            college_ids (List[int]): List of college IDs to filter.
            year (int): Year of the placement.
            intake_year (int): Intake year of students.
            level (int): level of course.

        Returns:
            Dict: Class profile data for each college.
        """
       
        college_ids = [item for sublist in college_ids for item in (sublist if isinstance(sublist, list) else [sublist])]
        
      
        logger.debug(f"Fetching class profiles for college_ids: {college_ids}")

        cache_key = ClassProfileHelper.get_cache_key(
            'Class_Profiles_V1', '-'.join(map(str, sorted(college_ids))), year, intake_year, level
        )

        def fetch_data():
            try:
                
                results = (
                    College.objects.filter(
                        id__in=college_ids,
                        collegeplacement__year=year,
                        collegeplacement__intake_year=intake_year,
                        collegeplacement__levels=level 
                    )
                    .distinct() 
                    .values('id')
                    .annotate(
                        total_students=Coalesce(Sum('collegeplacement__total_students'), Value(0, output_field=IntegerField())),
                        male_students=Coalesce(Sum('collegeplacement__male_students'), Value(0, output_field=IntegerField())),
                        female_students=Coalesce(Sum('collegeplacement__female_students'), Value(0, output_field=IntegerField())),
                        students_outside_state=Coalesce(Sum('collegeplacement__outside_state'), Value(0, output_field=IntegerField())),
                        outside_country_student=Coalesce(Sum('collegeplacement__outside_country'), Value(0, output_field=IntegerField())),
                        total_faculty=Coalesce(Sum('total_faculty'), Value(0, output_field=IntegerField())),
                        intake_year=F('collegeplacement__intake_year')
                    )
                )

                college_data = {
                    college['id']: {
                        "college_id": college['id'],
                        "total_students": college['total_students'],
                        "total_faculty": college['total_faculty'],
                        "male_students": college['male_students'],
                        "female_students": college['female_students'],
                        "students_outside_state": college['students_outside_state'],
                        "outside_country_student": college['outside_country_student'],
                        "intake_year": college['intake_year'],
                    }
                    for college in results
                }

             
                result_dict = {}
                for i, college_id in enumerate(college_ids, 1):
                    key = f"college_{i}"
                    if college_id in college_data:
                        result_dict[key] = college_data[college_id]
                    else:
                        result_dict[key] = {
                            "college_id": college_id,
                            "total_students": "NA",
                            "total_faculty": "NA",
                            "male_students": "NA",
                            "female_students": "NA",
                            "students_outside_state": "NA",
                            "outside_country_student": "NA",
                            "intake_year": intake_year
                        }

                return result_dict
            except Exception as e:
                logger.error(f"Error fetching class profiles: {e}")
                raise

        return cache.get_or_set(cache_key, fetch_data, 3600*24*365)


class ProfileInsightsHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        """
        Generate a unique cache key by hashing the combined arguments.
        """
        key = '_'.join(map(str, args))
        return hashlib.md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_student_faculty_ratio(
        college_ids: List[int],
        year: int,
        intake_year: int,
        level: int = 1
    ) -> Dict[str, Dict]:
        """
        Fetch student to faculty ratio data for given colleges as a percentage.
        """
        cache_key = ProfileInsightsHelper.get_cache_key(
            'student__faculty_ratio', '-'.join(map(str, college_ids)), year, intake_year, level
        )

        def fetch_data():
            query_result = (
                College.objects.filter(id__in=college_ids)
                .annotate(
                    students=Coalesce(
                        Sum(
                            Case(
                                When(
                                    collegeplacement__year=year,
                                    collegeplacement__intake_year=intake_year,
                                    collegeplacement__levels=level,
                                    then='collegeplacement__total_students'
                                ),
                                default=Value(0, output_field=IntegerField())
                            )
                        ),
                        Value(0, output_field=IntegerField())
                    ),
                    faculty=Coalesce(
                        F('total_faculty'),
                        Value(0, output_field=IntegerField())
                    ),
                    ratio=Case(
                        When(
                            total_faculty__gt=0,
                            then=Cast(F('students'), FloatField()) / Cast(F('faculty'), FloatField())
                        ),
                        default=Value(None, output_field=FloatField()),
                        output_field=FloatField()
                    )
                )
                .values('id', 'students', 'faculty', 'ratio')
            )

            result = {"type": "vertical bar"}
            for idx, data in enumerate(query_result, 1):
                student_faculty_ratio = data['ratio'] * 100 if data['ratio'] is not None else None
                result[f"college_{idx}"] = {
                    "college_id": str(data['id']),
                    "total_students": data['students'],
                    "total_faculty": data['faculty'],
                    "student_faculty_ratio_percentage": round(student_faculty_ratio, 2) if student_faculty_ratio is not None else None
                }
            return result

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24)

    @staticmethod
    def fetch_student_demographics(
        college_ids: List[int],
        year: int,
        intake_year: int,
        level: int = 1
    ) -> Dict[str, Dict]:
        """
        Fetch student demographics including outside state percentage.
        """
        cache_key = ProfileInsightsHelper.get_cache_key(
            'student__demographics', '-'.join(map(str, college_ids)), year, intake_year, level
        )

        def fetch_data():
            query_result = (
                CollegePlacement.objects.filter(
                    college_id__in=college_ids,
                    year=year,
                    intake_year=intake_year,
                    levels=level
                )
                .values('college_id')
                .annotate(
                    total_students=Coalesce(Sum('total_students'), Value(0, output_field=IntegerField())),
                    outside_state=Coalesce(Sum('outside_state'), Value(0, output_field=IntegerField()))
                )
                .annotate(
                    outside_state_percentage=Case(
                        When(
                            total_students__gt=0,
                            then=Cast(F('outside_state'), FloatField()) * 100.0 / Cast(F('total_students'), FloatField())
                        ),
                        default=Value(None, output_field=FloatField())
                    )
                )
            )

            result = {"type": "vertical bar"}
            for idx, data in enumerate(query_result, 1):
                result[f"college_{idx}"] = {
                    "college_id": str(data['college_id']),
                    "total_students": data['total_students'],
                    "students_outside_state": data['outside_state'],
                    "percentage_outside_state": round(data['outside_state_percentage'], 2) if data['outside_state_percentage'] is not None else None
                }
            return result

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24)

    @staticmethod
    def fetch_gender_diversity(
        college_ids: List[int],
        year: int,
        intake_year: int,
        level: int = 1
    ) -> Dict[str, Dict]:
        """
        Fetch gender diversity statistics.
        """
        cache_key = ProfileInsightsHelper.get_cache_key(
            'gender__diversity', '-'.join(map(str, college_ids)), year, intake_year, level
        )

        def fetch_data():
            query_result = (
                CollegePlacement.objects.filter(
                    college_id__in=college_ids,
                    year=year,
                    intake_year=intake_year,
                    levels=level
                )
                .values('college_id')
                .annotate(
                    male_students=Coalesce(Sum('male_students'), Value(0, output_field=IntegerField())),
                    female_students=Coalesce(Sum('female_students'), Value(0, output_field=IntegerField()))
                )
                .annotate(
                    total_students=F('male_students') + F('female_students'),
                    male_percentage=Case(
                        When(
                            total_students__gt=0,
                            then=Cast(F('male_students'), FloatField()) * 100.0 / Cast(F('total_students'), FloatField())
                        ),
                        default=Value(None, output_field=FloatField())
                    ),
                    female_percentage=Case(
                        When(
                            total_students__gt=0,
                            then=Cast(F('female_students'), FloatField()) * 100.0 / Cast(F('total_students'), FloatField())
                        ),
                        default=Value(None, output_field=FloatField())
                    )
                )
            )

            result = {"type": "vertical bar"}
            for idx, data in enumerate(query_result, 1):
                result[f"college_{idx}"] = {
                    "college_id": str(data['college_id']),
                    "male_students": data['male_students'],
                    "female_students": data['female_students'],
                    "percentage_male": round(data['male_percentage'], 2) if data['male_percentage'] is not None else None,
                    "percentage_female": round(data['female_percentage'], 2) if data['female_percentage'] is not None else None
                }
            return result

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24)

    @staticmethod
    def prepare_profile_insights(
        college_ids: List[int],
        year: int,
        intake_year: int,
        level: int = 1
    ) -> Dict:
        """
        Prepare comprehensive profile insights including all metrics.

        Args:
            college_ids (List[int]): List of college IDs to analyze
            year (int): Academic year
            intake_year (int): Year of student intake
            level (int): Academic level (defaults to 1)

        Returns:
            Dict: Combined profile insights in the specified format
        """
        

        college_details = list(
            College.objects.filter(id__in=college_ids)
            .order_by('id')
            .values(
                'id', 
                'name', 
                'short_name', 
                'ownership', 
                'institute_type_1', 
                'institute_type_2'
            )
        )

        # Add ownership display and type of institute
        for college in college_details:
            college['ownership_display'] = dict(College.OWNERSHIP_CHOICES).get(college['ownership'], '-')
            college['type_of_institute'] =  College.type_of_institute(
        college['institute_type_1'], college['institute_type_2']
    )

        student_faculty_metrics = ProfileInsightsHelper.fetch_student_faculty_ratio(
            college_ids, year, intake_year, level
        )
        demographic_metrics = ProfileInsightsHelper.fetch_student_demographics(
            college_ids, year, intake_year, level
        )
        gender_metrics = ProfileInsightsHelper.fetch_gender_diversity(
            college_ids, year, intake_year, level
        )

        return {
            "year": year,
            "intake_year": intake_year,
            "level": level,
            "student_faculty_metrics": student_faculty_metrics,
            "student_outside_student_metrics": demographic_metrics,
            "gender_metrics": gender_metrics,
            "college_details": college_details
        }





class CollegeFacilitiesHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = '_'.join(str(arg) for arg in args)
        return md5(key.encode()).hexdigest()

    @staticmethod
    def get_college_facilities(college_ids: List[int]) -> Dict:
        """
        Get aggregated facilities data for colleges with caching.
        
        Args:
            college_ids (List[int]): List of college IDs to fetch facilities for.
            
        Returns:
            Dict: Dictionary with facilities data for each college.
        """
        college_ids = [int(item) for sublist in college_ids for item in (sublist if isinstance(sublist, list) else [sublist])]
        
        logger.debug(f"Fetching facilities for college_ids: {college_ids}")

        cache_key = CollegeFacilitiesHelper.get_cache_key(
            'College_Facilities_V8',
            '-'.join(map(str, sorted(college_ids)))
        )
        
        def fetch_facilities():
            try:
             
                results = (
                    CollegeFacility.objects.filter(college_id__in=college_ids)
                    .values('college_id', 'facility')
                    .distinct()
                )

            
                result_dict = {
                    f"college_{i}": {
                        "college_id": college_id,
                        "facilities": set(), 
                        "facilities_count": 0
                    }
                    for i, college_id in enumerate(college_ids, 1)
                }
                
              
                facility_choices = {str(k): v for k, v in dict(CollegeFacility.FACILITY_CHOICES).items()}
                
             
                for result in results:
                    college_id = result['college_id']
                    facility_id = str(result['facility'])  
                    college_key = next(
                        (key for key, data in result_dict.items() 
                         if data['college_id'] == college_id),
                        None
                    )
                    
                    if college_key and facility_id in facility_choices:
                        result_dict[college_key]['facilities'].add(
                            facility_choices[facility_id]
                        )

               
                for college_data in result_dict.values():
                    college_data['facilities'] = sorted(list(college_data['facilities']))
                    college_data['facilities_count'] = len(college_data['facilities'])

                logger.debug(f"Processed facilities data: {result_dict}")
                return result_dict

            except Exception as e:
                logger.error(f"Error fetching college facilities: {e}", exc_info=True)
                raise

        return cache.get_or_set(cache_key, fetch_facilities, 3600*24*31)
    


from concurrent.futures import ThreadPoolExecutor
from botocore.config import Config


class CollegeReviewsHelper:
    """
    A comprehensive helper class for analyzing college reviews using AWS Bedrock and caching.
    This class combines numerical ratings with AI-generated insights from review text.
    """
    
    def __init__(self, bedrock_config: Optional[Dict] = None):
        """
        Initialize the AWS Bedrock client with secure configuration.
        
        Args:
            bedrock_config (Optional[Dict]): Custom AWS configuration. If None, uses environment variables.
        """
        # Use provided config or fall back to environment variables without defaults
        config = bedrock_config or {
            'region_name': os.getenv('AWS_REGION','ap-south-1'),
            'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY')
        }
        
        # Initialize AWS Bedrock client with configuration
        self.bedrock_client = boto3.client("bedrock-runtime", **config)
        
    @staticmethod
    def get_cache_key(*args) -> str:
        """
        Generate a consistent cache key from variable arguments.
        
        Args:
            *args: Variable arguments to include in the cache key
            
        Returns:
            str: MD5 hash of the concatenated arguments
        """
        key = '_'.join(str(arg) for arg in args)
        return md5(key.encode()).hexdigest()

    def _create_summary(self, review_text: str, college_name: str) -> Optional[Dict]:
        """
        Generate AI-powered summary and insights from review text using AWS Bedrock.
        
        Args:
            review_text (str): Combined review text to analyze
            college_name (str): Name of the college for summary personalization
            
        Returns:
            Optional[Dict]: Dictionary containing attributes and summary, or None if processing fails
        """
        if not review_text.strip():
            return None
            
        # Construct a detailed prompt for the AI model
        prompt = f"""
        Analyze the college review text inside the <review></review> XML tags below and provide three distinct sections:

        1. Most Discussed Attributes
       Extract 5-10 most frequently discussed aspects of the college.
       Requirements:
       - Use clear 2-3 word phrases
       - Focus on specific, measurable aspects
       - Choose only attributes directly mentioned in the text
       - Use proper noun capitalization
       
        2. Quick Summary
           Write exactly 100-200 words focusing on key aspects.
           Requirements:
           - Start directly with "{college_name} has..."
           - Include only information present in the review
           - Use specific numbers, percentages, and facts
           - Focus on distinctive features and quantifiable aspects

        Return the response in this exact JSON format:
        {{
            "most_discussed_attributes": [],
            "short_summary": ""
        }}

        <review>
        {review_text.strip()}
        </review>
        """

        try:
            # Prepare the model request with appropriate parameters
            model_request = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "temperature": 0.0,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}]
                    }
                ]
            }

            # Call the Bedrock API and process the response
            response = self.bedrock_client.invoke_model(
                modelId=os.getenv('BEDROCK_MODEL_ID', "anthropic.claude-3-sonnet-20240229-v1:0"),
                body=json.dumps(model_request)
            )
            
            response_text = json.loads(response["body"].read())["content"][0]["text"]
            json_match = re.search(r"{.*}", response_text, re.DOTALL)
            
            if json_match:
                return json.loads(json_match.group())
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None

    def get_college_reviews_summary(self, college_ids: List[int], grad_year: int) -> Dict:
        """
        Get comprehensive review summary including ratings and AI-generated insights.
        
        Args:
            college_ids (List[int]): List of college IDs to analyze
            grad_year (int): Graduation year to filter reviews
            
        Returns:
            Dict: Combined ratings and insights for each college
        """
      
        college_ids = [item for sublist in college_ids for item in (sublist if isinstance(sublist, list) else [sublist])]
        
      
        cache_key = self.get_cache_key(
            'College_Reviews_Summary__V3',
            '-'.join(map(str, sorted(college_ids))),
            grad_year
        )

        def fetch_summary():
            try:
                # Fetch aggregate ratings for each college
                ratings = (
                    CollegeReviews.objects.filter(
                        college_id__in=college_ids,
                        graduation_year__year=grad_year,
                        status=True
                    )
                    .select_related('college')
                    .values('college_id', 'college__name')
                    .annotate(
                        grad_year=ExtractYear('graduation_year'),
                        infra_rating=Coalesce(Round(Avg(F('infra_rating') / 20), 1), Value(0.0)),
                        campus_life_ratings=Coalesce(Round(Avg(F('college_life_rating') / 20), 1), Value(0.0)),
                        academics_ratings=Coalesce(Round(Avg(F('overall_rating') / 20), 1), Value(0.0)),
                        value_for_money_ratings=Coalesce(Round(Avg(F('affordability_rating') / 20), 1), Value(0.0)),
                        placement_rating=Coalesce(Round(Avg(F('placement_rating') / 20), 1), Value(0.0)),
                        faculty_rating=Coalesce(Round(Avg(F('faculty_rating') / 20), 1), Value(0.0)),
                        review_count=Count('id')
                    )
                )

                # Fetch detailed reviews for text analysis
                reviews = (
                    CollegeReviews.objects.filter(
                        college_id__in=college_ids,
                        graduation_year__year=grad_year,
                        status=True
                    )
                    .values('college_id', 'title', 'campus_life', 'college_infra', 
                            'academics', 'placements', 'value_for_money')
                )

                # Process each college's data
                result_dict = {}
                for college_id in college_ids:
                    college_reviews = [r for r in reviews if r['college_id'] == college_id]
                    college_name = next((r['college__name'] for r in ratings if r['college_id'] == college_id), "The college")
                    
                    # Combine all review texts for analysis
                    review_texts = [
                        ' '.join(filter(None, [
                            review['title'],
                            review['campus_life'],
                            review['college_infra'],
                            review['academics'],
                            review['placements'],
                            review['value_for_money']
                        ]))
                        for review in college_reviews
                    ]
                    
                    # Generate AI insights if reviews exist
                    if review_texts:
                        full_text = ' '.join(review_texts)
                        insights = self._create_summary(full_text, college_name) or {
                            'most_discussed_attributes': [],
                            'short_summary': ''
                        }
                    else:
                        insights = {
                            'most_discussed_attributes': [],
                            'short_summary': '',
                            'status': 'No review text available'
                        }

                    # Combine ratings and insights
                    college_ratings = next((r for r in ratings if r['college_id'] == college_id), None)
                    result_dict[f"college_{college_id}"] = {
                        **(college_ratings or {
                            'grad_year': grad_year,
                            'infra_rating': 0.0,
                            'campus_life_ratings': 0.0,
                            'academics_ratings': 0.0,
                            'value_for_money_ratings': 0.0,
                            'placement_rating': 0.0,
                            'faculty_rating': 0.0,
                            'review_count': 0
                        }),
                        'most_discussed_attributes': insights.get('most_discussed_attributes', []),
                        'short_summary': insights.get('short_summary', '')
                    }

                return result_dict

            except Exception as e:
                logger.error(f"Error fetching reviews summary: {e}")
                raise

        # Return cached result or compute new one with 1-hour cache time
        return cache.get_or_set(cache_key, fetch_summary, 3600)

    @staticmethod
    def get_recent_reviews(college_ids: List[int], limit: int = 3) -> Dict:
        """
        Get recent reviews for colleges with caching.

        Args:
            college_ids (List[int]): List of college IDs to filter
            limit (int, optional): Maximum number of reviews per college. Defaults to 3.

        Returns:
            Dict: Recent reviews for each college
        """
        # Flatten nested lists if any
        college_ids = [item for sublist in college_ids for item in (sublist if isinstance(sublist, list) else [sublist])]
        
        # Generate cache key
        cache_key = CollegeReviewsHelper.get_cache_key(
            'Recent_Reviews',
            '-'.join(map(str, sorted(college_ids))),
            limit
        )

        def fetch_recent():
            try:
                # Fetch recent reviews with user information
                results = (
                    CollegeReviews.objects.filter(
                        college_id__in=college_ids,
                        title__isnull=False
                    )
                    .select_related('user')
                    .values(
                        'college_id',
                        'title',
                        'user__display_name',
                        rating=Round(F('overall_rating') / 20, 1),
                        review_date=TruncDate('created')
                    )
                    .order_by('college_id', '-created')
                )

                # Organize reviews by college
                reviews_by_college = {}
                for review in results:
                    college_id = review['college_id']
                    if college_id not in reviews_by_college:
                        reviews_by_college[college_id] = []
                    if len(reviews_by_college[college_id]) < limit:
                        reviews_by_college[college_id].append({
                            'title': review['title'],
                            'user_display_name': review['user__display_name'],
                            'rating': review['rating'],
                            'review_date': review['review_date']
                        })

                # Format final response
                result_dict = {}
                for i, college_id in enumerate(college_ids, 1):
                    key = f"college_{i}"
                    result_dict[key] = reviews_by_college.get(college_id, [])

                return result_dict

            except Exception as e:
                logger.error(f"Error fetching recent reviews: {e}")
                raise

        # Return cached result or compute new one with 36-hour cache time
        return cache.get_or_set(cache_key, fetch_recent, 1800 * 48)



class CollegeReviewsRatingGraphHelper:
    """
    Helper class for generating college review rating graphs with classification of ratings
    as Very Good (>4), Good (3-4), and Average (<3).
    """
    
    @staticmethod
    def get_cache_key(*args) -> str:
        """
        Generate a consistent cache key from variable arguments.
        
        Args:
            *args: Variable arguments to include in the cache key
            
        Returns:
            str: MD5 hash of the concatenated arguments
        """
        key = '_'.join(map(str, args))
        return hashlib.md5(key.encode()).hexdigest()

    @staticmethod
    def classify_rating(rating: float) -> str:
        """
        Classify a rating value into categories.
        
        Args:
            rating (float): Rating value to classify
            
        Returns:
            str: Classification as 'V.Good', 'Good', or 'Avg'
        """
        if rating > 4:
            return 'V.Good'
        elif 3 <= rating <= 4:
            return 'Good'
        else:
            return 'Avg'

    @staticmethod
    def fetch_rating_data(college_ids: List[int], grad_year: int) -> Dict:
        """
        Fetch and process college rating data with classifications.
        
        Args:
            college_ids (List[int]): List of college IDs to analyze
            grad_year (int): Graduation year to filter reviews
            
        Returns:
            Dict: Processed rating data with classifications for each college
        """
        try:
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
        except (ValueError, TypeError):
            raise ValueError("college_ids must be a flat list of integers or strings.")

        cache_key = CollegeReviewsRatingGraphHelper.get_cache_key(
            'college_reviews_graph_data',
            '-'.join(map(str, sorted(college_ids))),
            grad_year
        )

        def fetch_data():
            
            rating_type = [
                'infra_rating',
                'campus_life_ratings',
                'academics_ratings',
                'value_for_money_ratings',
                'placement_rating'
            ]

        
            ratings = (
                CollegeReviews.objects.filter(
                    college_id__in=college_ids,
                    graduation_year__year=grad_year,
                    status=True
                )
                .select_related('college')
                .values('college_id', 'college__name')
                .annotate(
                    infra_rating=Coalesce(Round(Avg(F('infra_rating') / 20), 1), Value(0.0)),
                    campus_life_ratings=Coalesce(Round(Avg(F('college_life_rating') / 20), 1), Value(0.0)),
                    academics_ratings=Coalesce(Round(Avg(F('overall_rating') / 20), 1), Value(0.0)),
                    value_for_money_ratings=Coalesce(Round(Avg(F('affordability_rating') / 20), 1), Value(0.0)),
                    placement_rating=Coalesce(Round(Avg(F('placement_rating') / 20), 1), Value(0.0))
                )
                .order_by('college_id')  
            )

            result_dict = {
                "rating_type": rating_type,
                "rating_data": {   "type": "spider"},
                "classification_data": {   "type": "horizontal bar",},
                "college_names": []
            }

            for idx, college in enumerate(ratings, 1):
                college_key = f"college_{idx}"
                college_name = college['college__name']
                result_dict["college_names"].append(college_name)
                
                
                result_dict["rating_data"][college_key] = {
                    "college_id": college['college_id'],
                    "college_name": college_name,
                    **{param: college[param] for param in rating_type}
                }
                
                
                result_dict["classification_data"][college_key] = {
                    "college_id": college['college_id'],
                    "college_name": college_name,
                    "V.Good": sum(1 for param in rating_type if college[param] > 4),
                    "Good": sum(1 for param in rating_type if 3 <= college[param] <= 4),
                    "Avg": sum(1 for param in rating_type if college[param] < 3)
                }

            return result_dict

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24 *7) 

    @staticmethod
    def prepare_rating_insights(college_ids: List[int], grad_year: int) -> Dict:
        """
        Prepare complete rating insights including raw data and classifications.
        
        Args:
            college_ids (List[int]): List of college IDs to analyze
            grad_year (int): Graduation year to filter reviews
            
        Returns:
            Dict: Complete rating insights and classifications
        """
        return CollegeReviewsRatingGraphHelper.fetch_rating_data(college_ids, grad_year)

class ExamCutoffHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = '_'.join(str(arg) for arg in args)
        return md5(key.encode()).hexdigest()
    
    @staticmethod
    def fetch_cutoff_data(
        college_ids: List[int],
        year: int,
        exam_id: Optional[int] = None,
        category_of_admission_id: Optional[int] = None
    ) -> Dict:
        """
        Fetches exam cutoff comparison data dynamically based on the given filters.
        """
        try:
           
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
        except (ValueError, TypeError):
            logger.error("Invalid college_ids provided: college_ids=%s", college_ids)
            raise ValueError("college_ids must be a list of integers or strings.")

      
        cache_key = ExamCutoffHelper.get_cache_key(
            'exam______cutoff__comparisons',
            '-'.join(map(str, college_ids)),
            year,
            exam_id or 'NULL',
            category_of_admission_id or 'NULL'
        )

        def fetch_data():
            try:
               
                filters = {
                    'college__in': college_ids,
                    'year': year
                }
                if exam_id is not None:
                    filters['exam_sub_exam_id'] = exam_id
                if category_of_admission_id:
                    filters['category_of_admission_id'] = category_of_admission_id

              
                cutoff_data = CutoffData.objects.filter(**filters).annotate(
                    category_of_admission_id_annotated=Coalesce('category_of_admission_id', Value(1), output_field=IntegerField()),
                    category_name=Coalesce('category_of_admission__description', Value('All India'), output_field=CharField()),
                    exam_sub_exam_id_annotated=Coalesce('exam_sub_exam_id', Value('NA'), output_field=CharField()),
                    exam_name=Coalesce(
                        Case(
                            When(
                                Q(exam_sub_exam_id__exam_short_name__isnull=False) & ~Q(exam_sub_exam_id__exam_short_name=''),
                                then=F('exam_sub_exam_id__exam_short_name')
                            ),
                            default=F('exam_sub_exam_id__exam_name')
                        ),
                        Value('NA', output_field=CharField())
                    )
                )

               
                exams_data = Exam.objects.filter(
                    id__in=cutoff_data.values_list('exam_sub_exam_id', flat=True).distinct()
                ).values('id', 'exam_short_name', 'exam_name')

                categories_data = AdmissionCategory.objects.filter(
                    id__in=cutoff_data.values_list('category_of_admission_id', flat=True).distinct()
                ).values('id', 'description')

             
                exams_list = [
                    {'exam_id': exam['id'], 'exam_name': exam['exam_short_name'] or exam['exam_name']}
                    for exam in exams_data
                ]
                categories_list = [
                    {'category_id': category['id'], 'category_name': category['description']}
                    for category in categories_data
                ]

               
                seen_combinations = set()
                comparison_data = []
                
               
                unique_combinations = cutoff_data.values(
                    'category_of_admission_id',
                    'category_name',
                    'exam_sub_exam_id',
                    'exam_name'
                ).distinct()

                for combination in unique_combinations:
                  
                    unique_key = f"{combination['category_of_admission_id']}_{combination['exam_sub_exam_id']}"
                    
                    if unique_key in seen_combinations:
                        continue
                        
                    seen_combinations.add(unique_key)
                    
                    college_data = {}
                    for idx, college_id in enumerate(college_ids, 1):
                        college_cutoff_data = cutoff_data.filter(
                            college_id=college_id,
                            category_of_admission_id=combination['category_of_admission_id'],
                            exam_sub_exam_id=combination['exam_sub_exam_id']
                        )

                        
                        if college_cutoff_data.exists():
                            college_stats = {
                                'college_id': college_id,
                                'college_course_id': college_cutoff_data.first().college_course_id,
                                'round_wise_opening_cutoff': (
                                    int(college_cutoff_data.aggregate(Min('round_wise_opening_cutoff'))['round_wise_opening_cutoff__min'])
                                    if college_cutoff_data.aggregate(Min('round_wise_opening_cutoff'))['round_wise_opening_cutoff__min'] is not None
                                    else 'NA'
                                ),
                                'round_wise_closing_cutoff': (
                                    int(college_cutoff_data.aggregate(Max('round_wise_closing_cutoff'))['round_wise_closing_cutoff__max'])
                                    if college_cutoff_data.aggregate(Max('round_wise_closing_cutoff'))['round_wise_closing_cutoff__max'] is not None
                                    else 'NA'
                                ),
                                'total_counselling_rounds': college_cutoff_data.values('round').distinct().count(),
                                'lowest_closing_rank_sc_st': (
                                    int(college_cutoff_data.filter(caste_id='3').aggregate(Max('round_wise_closing_cutoff'))['round_wise_closing_cutoff__max'])
                                    if college_cutoff_data.filter(caste_id='3').aggregate(Max('round_wise_closing_cutoff'))['round_wise_closing_cutoff__max'] is not None
                                    else 'NA'
                                ),
                                'lowest_closing_rank_obc': (
                                    int(college_cutoff_data.filter(caste_id='2').aggregate(Max('round_wise_closing_cutoff'))['round_wise_closing_cutoff__max'])
                                    if college_cutoff_data.filter(caste_id='2').aggregate(Max('round_wise_closing_cutoff'))['round_wise_closing_cutoff__max'] is not None
                                    else 'NA'
                                ),
                                'lowest_closing_rank_gn': (
                                    int(college_cutoff_data.filter(caste_id='1').aggregate(Max('round_wise_closing_cutoff'))['round_wise_closing_cutoff__max'])
                                    if college_cutoff_data.filter(caste_id='1').aggregate(Max('round_wise_closing_cutoff'))['round_wise_closing_cutoff__max'] is not None
                                    else 'NA'
                                ),
                            }
                        else:
                            college_stats = {
                                'college_id': college_id,
                                'college_course_id': 'NA',
                                'round_wise_opening_cutoff': 'NA',
                                'round_wise_closing_cutoff': 'NA',
                                'total_counselling_rounds': 'NA',
                                'lowest_closing_rank_sc_st': 'NA',
                                'lowest_closing_rank_obc': 'NA',
                                'lowest_closing_rank_gn': 'NA',
                            }

                        college_data[f'college_{idx}'] = college_stats

                    if college_data:
                        comparison_entry = {
                            'category_id': combination['category_of_admission_id'],
                            'category_name': combination['category_name'],
                            'exam_id': combination['exam_sub_exam_id'],
                            'exam_name': combination['exam_name'],
                            **college_data
                        }
                        comparison_data.append(comparison_entry)

                return {
                    'exam_data': exams_list,
                    'category_data': categories_list,
                    'comparison_data': comparison_data,
                }

            except Exception as e:
                logger.error("Error fetching exam cutoff comparison data: %s", str(e))
                raise

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 7)