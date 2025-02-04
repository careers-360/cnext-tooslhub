from django.db.models import Avg, Count, F, Q,Max,Min
from django.db.models.functions import Round, ExtractYear, TruncDate, Concat
from django.core.cache import cache
from functools import lru_cache
from typing import Dict,List,Optional,Any,Union
import hashlib
from hashlib import md5
from django.db.models import Subquery, ExpressionWrapper,Window, Func, OuterRef, Sum, Case, Exists,When,Value, CharField,IntegerField,DecimalField,Prefetch,FloatField,ExpressionWrapper

from django.db.models.functions import Coalesce,Cast,Concat,RowNumber
from decimal import Decimal
from college_compare.models import (
    College, CollegeReviews,Domain,CollegeFacility,CollegePlacement,BaseUrlAlias,CollegePlacementCompany,Exam,CpProductCampaign,CpProductCampaignItems,RankingParameters,RankingParameters,Company,RankingUploadList,Course,FeeBifurcation,Exam,Ranking,CollegeAccrediationApproval,ApprovalsAccrediations,CourseApprovalAccrediation,User
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

from concurrent.futures import ThreadPoolExecutor
from botocore.config import Config
import logging
import requests

from elasticsearch.exceptions import ElasticsearchWarning
import warnings
from collections import OrderedDict,defaultdict

# Suppress Elasticsearch warnings
warnings.filterwarnings("ignore", category=ElasticsearchWarning)

from elasticsearch import Elasticsearch

from django.core.exceptions import ObjectDoesNotExist


logger = logging.getLogger(__name__)

class UserPreferenceOptionsHelper:
    @staticmethod
    def fetch_user_preferences() -> list:
        """
        Fetch and return the list of available user preferences.
        In this case, it's a static list of preferences.
        """
        preferences = [
            "Fees",
            "Placement",
            "Scholarship",
            "People Perception",
            "Gender Diversity",
            "Alumni Network",
            "Location",
            "Faculty & Resources",
            "Academic Reputation",
            "Extra Curricular & Resources"
        ]
        
         

        return preferences




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


class NoDataAvailableError(Exception):
    """Custom exception to indicate no data is available."""
    pass



class RankingAccreditationHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        """
        Generate a cache key using MD5 hashing.
        """
        key = '+++++++_________________+++++'.join(map(str, args))
        return md5(key.encode()).hexdigest()
    

    @staticmethod
    def fetch_graduation_outcome_score(college_ids: List[int], year: Optional[int] = None) -> Dict[int, float]:
        """
        Fetch the Graduation Outcome Score for a list of colleges from the RankingParameters table.
        If a specific year is provided but no data is found, falls back to the latest available year for that college.
        If no year is provided, fetches the latest available year per college.
        """
        try:
            # Get valid college IDs
            colleges = set(College.objects.filter(id__in=college_ids).values_list('id', flat=True))
            
            # First attempt: Get data for specified year if provided
            grad_outcome_score_dict = {college_id: 'NA' for college_id in colleges}
            
            if year is not None:
                # Try to fetch scores for the specified year
                specific_year_scores = (
                    RankingParameters.objects
                    .filter(
                        Q(name__icontains="Graduation Outcomes") | Q(name__icontains='GO'),
                        ranking_upload__college_id__in=college_ids,
                        ranking_upload__ranking__year=year
                    )
                    .values('ranking_upload__college_id', 'score')
                )
                
                # Update dictionary with scores from specified year
                for item in specific_year_scores:
                    grad_outcome_score_dict[item['ranking_upload__college_id']] = item['score']
                
                # Get list of colleges that still have 'NA' scores
                colleges_needing_fallback = [
                    college_id for college_id in colleges 
                    if grad_outcome_score_dict[college_id] == 'NA'
                ]
                
                
                # If there are colleges without scores, fetch their latest years
                if colleges_needing_fallback:
                    print("------")
                    latest_years = (
                        RankingUploadList.objects
                        .filter(college_id__in=colleges_needing_fallback)
                        .values('college_id')
                        .annotate(latest_year=Max('ranking__year'))
                    )
                    
                    latest_years_dict = {
                        item['college_id']: item['latest_year'] 
                        for item in latest_years
                    }
                    
                    # Fetch scores for colleges using their latest years
                    fallback_scores = (
                        RankingParameters.objects
                        .filter(
                            Q(name__icontains="Graduation Outcomes") | Q(name__icontains='GO'),
                            ranking_upload__college_id__in=colleges_needing_fallback,
                            ranking_upload__ranking__year__in=[
                                latest_years_dict[cid] 
                                for cid in latest_years_dict 
                                if latest_years_dict[cid] is not None
                            ]
                        )
                        .values('ranking_upload__college_id', 'score')
                    )
                    
                    # Update dictionary with fallback scores
                    for item in fallback_scores:
                        grad_outcome_score_dict[item['ranking_upload__college_id']] = item['score']
            
            else:
                # Original logic for when no specific year is provided
                latest_years = (
                    RankingUploadList.objects
                    .filter(college_id__in=college_ids)
                    .values('college_id')
                    .annotate(latest_year=Max('ranking__year'))
                )
                
                latest_years_dict = {
                    item['college_id']: item['latest_year'] 
                    for item in latest_years
                }
                
                grad_outcome_scores = (
                    RankingParameters.objects
                    .filter(
                        Q(name__icontains="Graduation Outcomes") | Q(name__icontains='GO'),
                        ranking_upload__college_id__in=college_ids,
                        ranking_upload__ranking__year__in=[
                            latest_years_dict[cid] 
                            for cid in latest_years_dict 
                            if latest_years_dict[cid] is not None
                        ]
                    )
                    .values('ranking_upload__college_id', 'score')
                )
                
                # Update dictionary with scores
                for item in grad_outcome_scores:
                    grad_outcome_score_dict[item['ranking_upload__college_id']] = item['score']
            
            return grad_outcome_score_dict

        except Exception as e:
            logger.error("Error fetching Graduation Outcome Score: %s", traceback.format_exc())
            raise
    

  

    @staticmethod
    def fetch_ranking_data(college_ids: List[int], course_ids: Optional[List[int]] = None, year: Optional[int] = None) -> Dict:
        try:
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
            if not college_ids:
                raise NoDataAvailableError("No valid college IDs provided.")

            logger.debug(f"Fetching ranking data with college_ids: {college_ids}, course_ids: {course_ids}, year: {year}")

            cache_key_parts = ['ranking_comparison_data', year, '-'.join(map(str, college_ids))]
            if course_ids:
                cache_key_parts.append('-__---------------'.join(map(str, course_ids)))
            cache_key = RankingAccreditationHelper.get_cache_key(*cache_key_parts)

            def fetch_data():
                try:
                    year_filter = Q(ranking__year=year) if year else Q()

                    course_domain_map = {}

                    if course_ids:
                        course_ids_values = list(course_ids.values())  # Extract course IDs
                        courses = Course.objects.filter(id__in=course_ids_values).values('id', 'degree_domain')
                        print(courses)
                        course_domain_map = {course['id']: course['degree_domain'] for course in courses}

                  

                    rankings = []
                    for college_id in college_ids:
                        selected_domain = None
                        if course_ids:
                            # Ensure college_id maps to a course_id before looking up course_domain_map
                            course_id = course_ids.get(college_id)  # Get course_id for the college_id
                            if course_id:
                                selected_domain = course_domain_map.get(course_id)  # Get domain from course_id

                        
                                    
                  

                        old_domain_name = (
                            Domain.objects.filter(id=selected_domain)
                            .values_list('old_domain_name', flat=True)
                            .first()
                        )
                        formatted_domain_name = DomainHelper.format_domain_name(old_domain_name)

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
                        min_other_ranked_domain = other_ranked_domain_subquery.values('other_ranked_domain')[1:2]

                        college_rankings = (
                            RankingUploadList.objects
                            .filter(college_id=college_id)
                            .filter(year_filter)
                            .values('college_id')
                            .annotate(
                                careers360_overall_rank=Coalesce(
                                    Cast(
                                        Max(Case(
                                            When(Q(ranking__ranking_authority='Careers360') & ~Q(ranking__ranking_stream=selected_domain), then=F('overall_rating')),
                                            default=None
                                        )),
                                        output_field=CharField()
                                    ),
                                    Value('NA', output_field=CharField())
                                ),
                                careers360_domain_rank=Coalesce(
                                    Cast(
                                        Max(Case(
                                            When(Q(ranking__ranking_authority='Careers360') & Q(ranking__ranking_stream=selected_domain), then=F('overall_rating')),
                                            default=None
                                        )),
                                        output_field=CharField()
                                    ),
                                    Value('NA', output_field=CharField())
                                ),
                                nirf_overall_rank=Coalesce(
                                    Cast(
                                        Min(Case(
                                            When(Q(ranking__ranking_authority='NIRF') & Q(ranking__ranking_entity='Overall'), then=F('overall_rank')),
                                            default=None
                                        )),
                                        output_field=CharField()
                                    ),
                                    Value('NA', output_field=CharField())
                                ),
                                nirf_domain_rank=Coalesce(
                                    Cast(
                                        Min(Case(
                                            When(Q(ranking__ranking_authority='NIRF') & Q(ranking__ranking_stream=selected_domain), then=F('overall_rank')),
                                            default=None
                                        )),
                                        output_field=CharField()
                                    ),
                                    Value('NA', output_field=CharField())
                                ),
                                other_ranked_domain=Coalesce(
                                    Cast(
                                        Subquery(min_other_ranked_domain),
                                        output_field=CharField()
                                    ),
                                    Value('NA', output_field=CharField())
                                ),
                                domain_name=Value(formatted_domain_name, output_field=CharField()),
                            )
                        )
                        rankings.extend(college_rankings)

                    if not rankings:
                        raise NoDataAvailableError("No rankings data found for the provided college IDs.")

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

                    approvals_dict = {k: ', '.join(sorted(v)) if v else 'NA' for k, v in approvals_dict.items()}
                    accreditations_dict = {k: ', '.join(sorted(v)) if v else 'NA' for k, v in accreditations_dict.items()}

                    college_details = {
                        college['id']: {
                            'name': college['short_name'],
                            'ownership': college['ownership'],
                            'location': college['location'],
                        }
                        for college in College.objects.filter(id__in=college_ids)
                        .select_related('location')
                        .values('id', 'name', 'ownership', 'location',"short_name")
                    }

                    graduation_outcome_scores = RankingAccreditationHelper.fetch_graduation_outcome_score(college_ids,year)

                    result_dict = {}
                    for idx, college_id in enumerate(college_ids, start=1):
                        ranking = next((r for r in rankings if r.get('college_id') == college_id), {})
                        college_data = college_details.get(college_id, {})
                        location_id = college_data.get('location', 'NA')
                        location_string = 'NA'

                        if location_id != 'NA':
                            location_obj = Location.objects.filter(id=location_id).first()
                            location_string = location_obj.loc_string if location_obj else 'NA'

                        result_dict[f"college_{idx}"] = {
                            "college_id": college_id,
                            "college_short_name": college_data.get('name', 'NA'),
                            "ownership": dict(College.OWNERSHIP_CHOICES).get(college_data.get('ownership'), 'NA'),
                            "location": location_string,
                            "careers360_overall_rank": ranking.get('careers360_overall_rank', 'NA'),
                            "careers360_domain_rank": ranking.get('careers360_domain_rank', 'NA'),
                            "nirf_overall_rank": ranking.get('nirf_overall_rank', 'NA'),
                            "nirf_domain_rank": ranking.get('nirf_domain_rank', 'NA'),
                            "approvals": approvals_dict.get(college_id, 'NA'),
                            "accreditations": accreditations_dict.get(college_id, 'NA'),
                            "graduation_outcome_score": graduation_outcome_scores.get(college_id, 'NA'),
                            "domain_name": ranking.get('domain_name', 'NA'),
                            "other_ranked_domain": ranking.get('other_ranked_domain') or 'NA',
                        }

                    return result_dict
                except NoDataAvailableError:
                    raise
                except Exception as e:
                    logger.error("Error fetching ranking and accreditation data: %s", traceback.format_exc())
                    raise

            return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 7)

        except NoDataAvailableError as e:
            logger.warning(str(e))
            raise
        except Exception as e:
            logger.error("Error in fetch_ranking_data: %s", traceback.format_exc())
            raise







def get_ordinal_suffix(num: int) -> str:
    """Returns ordinal suffix for a number (1st, 2nd, 3rd, etc.)"""
    if 10 <= num % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(num % 10, 'th')
    return suffix






class CollegeRankingService:
    @staticmethod
    def get_cache_key(*args) -> str:
        """
        Generate a cache key using MD5 hashing.
        """
        key = '________'.join(map(str, args))
        return md5(key.encode()).hexdigest()

    @staticmethod
    def get_state_and_ownership_ranks(
        college_ids: List[int],
        course_ids: List[int],
        year: int
    ) -> Dict[str, Dict]:
        """Gets state-wise and ownership-wise ranks based on overall ranks."""
        try:
            cache_key = CollegeRankingService.get_cache_key(college_ids, course_ids, year)
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result

            # Extract course IDs and create a mapping of college_id to domain
            course_ids_values = list(course_ids.values())
            courses = Course.objects.filter(id__in=course_ids_values).values('id', 'degree_domain')
            course_domain_map = {course['id']: course['degree_domain'] for course in courses}

            # Create a mapping of college_id to domain
            college_domain_map = {}
            for college_id in college_ids:
                course_id = course_ids.get(college_id)
                if course_id:
                    college_domain_map[college_id] = course_domain_map.get(course_id)
                else:
                    college_domain_map[college_id] = None

            # Initialize the result dictionary with all college IDs
            result = {f"college_{idx + 1}": {
                "college_id": college_id,
                "domain": college_domain_map[college_id],
                "state_rank_display": "Not Available",
                "ownership_rank_display": "Not Available",
            } for idx, college_id in enumerate(college_ids)}

            # Group colleges by domain
            domain_groups = {}
            for college_id in college_ids:
                domain_id = college_domain_map[college_id]
                domain_groups.setdefault(domain_id, []).append(college_id)

            for domain_id, domain_college_ids in domain_groups.items():
                base_queryset = RankingUploadList.objects.filter(
                    ranking__ranking_stream=domain_id,
                    ranking__year=year,
                    ranking__status=1
                ).select_related('college', 'college__location')

                if not base_queryset.exists():
                    popular_stream = (
                        College.objects.filter(id__in=domain_college_ids)
                        .values_list('popular_stream', flat=True)
                        .first()
                    )

                    if popular_stream:
                        base_queryset = RankingUploadList.objects.filter(
                            ranking__ranking_stream=popular_stream,
                            ranking__year=year,
                            ranking__status=1
                        ).select_related('college', 'college__location')

                total_counts = base_queryset.values(
                    'college__location__state_id',
                    'college__ownership'
                )

                state_totals = {}
                ownership_totals = {}
                for college in total_counts:
                    state_id = college['college__location__state_id']
                    ownership = college['college__ownership']
                    if state_id:
                        state_totals[state_id] = state_totals.get(state_id, 0) + 1
                    if ownership:
                        ownership_totals[ownership] = ownership_totals.get(ownership, 0) + 1

                all_ranked_colleges = list(base_queryset.values(
                    'college_id',
                    'overall_rank',
                    'college__location__state_id',
                    'college__location__loc_string',
                    'college__ownership'
                ).filter(
                    overall_rank__isnull=False
                ).order_by('overall_rank'))

                state_ranks = {}
                college_details = {}
                ownership_groups = {}

                for college in all_ranked_colleges:
                    college_id = college['college_id']
                    state_id = college['college__location__state_id']
                    ownership = college['college__ownership']

                    overall_rank_str = college['overall_rank']

                    if overall_rank_str and overall_rank_str.isdigit():
                        overall_rank = int(overall_rank_str)
                    else:
                        logger.warning(f"Invalid overall_rank for college_id={college_id}: {overall_rank_str}")
                        continue

                    if college_id in domain_college_ids:
                        college_details[college_id] = {
                            'state_id': state_id,
                            'state_name': college['college__location__loc_string'],
                            'ownership': ownership,
                            'overall_rank': overall_rank
                        }

                    if state_id not in state_ranks:
                        state_ranks[state_id] = {}
                    current_rank = len(state_ranks[state_id]) + 1
                    state_ranks[state_id][college_id] = current_rank

                    ownership_groups.setdefault(ownership, []).append({
                        'college_id': college_id,
                        'overall_rank': overall_rank
                    })

                ownership_ranks = {}
                for ownership, colleges in ownership_groups.items():
                    colleges.sort(key=lambda x: x['overall_rank'])
                    current_rank = 1
                    prev_rank = None
                    ownership_ranks[ownership] = {}

                    for idx, college in enumerate(colleges):
                        if idx > 0 and college['overall_rank'] > prev_rank:
                            current_rank = idx + 1
                        ownership_ranks[ownership][college['college_id']] = current_rank
                        prev_rank = college['overall_rank']

                for college_id in domain_college_ids:
                    details = college_details.get(college_id, {})

                    if details:
                        state_id = details['state_id']
                        ownership = details['ownership']
                        state_name = details['state_name']

                        state_rank = state_ranks.get(state_id, {}).get(college_id, "Not Available")
                        ownership_rank = ownership_ranks.get(ownership, {}).get(college_id, "Not Available")

                        state_total = state_totals.get(state_id, 0)
                        ownership_total = ownership_totals.get(ownership, 0)
                        ownership_type = dict(College.OWNERSHIP_CHOICES).get(ownership, 'Unknown')
                    else:
                        state_rank = ownership_rank = "Not Available"
                        state_total = ownership_total = 0
                        state_name = ""
                        ownership_type = "Unknown"

                    # Update the result dictionary for the specific college
                    for key, value in result.items():
                        if value['college_id'] == college_id:
                            value.update({
                                "domain": domain_id,
                                "state_rank_display": (
                                    f"{state_rank}{get_ordinal_suffix(state_rank)} out of {state_total} in {state_name}"
                                    if isinstance(state_rank, int) else "Not Available"
                                ),
                                "ownership_rank_display": (
                                    f"{ownership_rank}{get_ordinal_suffix(ownership_rank)} out of {ownership_total} in {ownership_type} Institutes"
                                    if isinstance(ownership_rank, int) else "Not Available"
                                ),
                            })
                            break

            # Cache the result for future use
            cache.set(cache_key, result, timeout=3600 * 24 * 7)  # 7 days cache
            return result

        except NoDataAvailableError as nde:
            logger.warning(f"No data available: {nde}")
            raise

        except Exception as e:
            logger.error(f"Error calculating state and ownership ranks: {traceback.format_exc()}")
            raise


class MultiYearRankingHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        """
        Generate a cache key using MD5 hashing.
        """
        key = '_______'.join(map(str, args))
        return md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_multi_year_ranking_data(
        college_ids: List[int],
        course_ids: Dict[int, int],  # Expecting {college_id: course_id}
        years: List[int]
    ) -> Dict:
        """
        Fetch 5 years of ranking and accreditation data for colleges with different domains.
        
        Args:
            college_ids: List of college IDs
            course_ids: Dictionary mapping college_id -> course_id
            years: List of years to fetch data for
        """
        try:
            cache_key = MultiYearRankingHelper.get_cache_key(college_ids, course_ids, years)
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result

            if not years or len(years) != 5:
                raise ValueError("Exactly 5 years must be provided.")

            # Ensure course_ids is a valid dictionary before processing
            if not isinstance(course_ids, dict):
                raise ValueError("course_ids must be a dictionary mapping college_id -> course_id")

            print(course_ids)  # Debugging

            # Extract course IDs and fetch domains
            course_ids_values = list(course_ids.values())  
            courses = Course.objects.filter(id__in=course_ids_values).values('id', 'degree_domain')
            course_domain_map = {course['id']: course['degree_domain'] for course in courses}

            print(course_domain_map, "---------_")  # Debugging

            # Build result dictionary
            result_dict = {
                f"college_{i + 1}": {
                    "college_id": college_id,
                    "domain": course_domain_map.get(course_ids.get(college_id))  # Correct lookup
                } for i, college_id in enumerate(college_ids)
            }

            data_found = False

            for year in years:
                yearly_data = RankingAccreditationHelper.fetch_ranking_data(
                    college_ids=college_ids,
                    course_ids=course_ids,
                    year=year
                )

                if not yearly_data:
                    continue

                data_found = True

                for key, data in yearly_data.items():
                    college = result_dict.get(key, {})

                    # Ensure default values are set
                    college.setdefault("college_name", data.get("college_name", "NA"))
                    college.setdefault("nirf_overall_rank", []).append(data.get("nirf_overall_rank", "NA"))
                    college.setdefault("nirf_domain_rank", []).append(data.get("nirf_domain_rank", "NA"))
                    college.setdefault("graduation_outcome_scores", []).append(data.get("graduation_outcome_score", "NA"))

                    # Handle domain-based ranking
                    college.setdefault("other_ranked_domain", [])
                    if "nirf_domain_rank" in data and data["nirf_domain_rank"] != "NA":
                        course_id = course_ids.get(college["college_id"])  # Ensure course_id exists
                        if course_id:
                            domain_id = course_domain_map.get(course_id)  # Fetch domain from correct course_id
                            if domain_id:
                                other_domain_entry = f"{domain_id} (NIRF {data['nirf_domain_rank']})"
                                college["other_ranked_domain"].append(other_domain_entry)

                    result_dict[key] = college

            return result_dict if data_found else {}

        except NoDataAvailableError as e:
            logger.error(f"No data available error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error fetching multi-year ranking data: {traceback.format_exc()}")
            raise

   




class RankingGraphHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        """
        Generate a unique cache key by hashing the combined arguments.
        """
        key = '___'.join(map(str, args))
        return hashlib.md5(key.encode()).hexdigest()
    
    @staticmethod
    def fetch_ranking_data(
        college_ids: List[int],
        start_year: int,
        end_year: int,
        course_ids: Dict[int, int] = None,
        ranking_entity: str = None,
    ) -> Dict:
        """
        Fetch ranking data for given colleges and year range.
        """
        try:
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
        except (ValueError, TypeError):
            raise ValueError("college_ids must be a flat list of integers or strings.")

        # Prepare cache key with all parameters
        cache_key = RankingGraphHelper.get_cache_key(
            'ranking__graph__insight_version__', 
            '-'.join(map(str, college_ids)), 
            start_year, 
            end_year, 
            '-'.join(map(str, course_ids.values())) if course_ids else "", 
            ranking_entity
        )

        def fetch_data():
            year_range = list(range(start_year, end_year + 1))
            filters = Q(ranking__status=1, ranking__year__in=year_range)

            course_domain_map = {}
            if course_ids:
                courses = Course.objects.filter(id__in=course_ids.values()).values('id', 'degree_domain')
                course_domain_map = {course['id']: course['degree_domain'] for course in courses}
                if course_domain_map:
                    filters &= Q(ranking__ranking_stream__in=list(course_domain_map.values()))

            if ranking_entity:
                filters &= Q(ranking__ranking_entity=ranking_entity)

            rankings = (
                RankingUploadList.objects.filter(filters, college_id__in=college_ids)
                .select_related('ranking')
                .values("college_id", "ranking__year", "ranking__ranking_stream", "ranking__ranking_entity", "overall_score")
            )
            print(rankings)

            if not rankings:
                raise NoDataAvailableError(f"No ranking data found for college IDs {college_ids} between {start_year} and {end_year}.")
            
            max_scores = {}
            for ranking in rankings:
                college_id = ranking['college_id']
                year = ranking['ranking__year']
                score = ranking['overall_score']
                if score is not None and score < 100:
                    key = (college_id, year)
                    max_scores[key] = max(max_scores.get(key, 0), score)

            result_dict = {
                f"college_{i + 1}": {"college_id": college_id, "data": {str(year): "NA" for year in year_range}}
                for i, college_id in enumerate(college_ids)
            }

            for (college_id, year), max_score in max_scores.items():
                college_key = f"college_{college_ids.index(college_id) + 1}"
                result_dict[college_key]["data"][str(year)] = max_score

            return result_dict

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 7)
    
    @staticmethod
    def prepare_graph_insights(
        college_ids: List[int], 
        start_year: int, 
        end_year: int, 
        selected_courses: Dict[int, int]
    ) -> Dict:
        """
        Prepare data for the ranking insights graph.
        """
        years = list(range(start_year, end_year + 1))
        try:
            overall_data = RankingGraphHelper.fetch_ranking_data(
                college_ids, start_year, end_year, ranking_entity='Overall'
            )
        except NoDataAvailableError as e:
            logger.error(f"No data available for overall ranking: {str(e)}")
            raise

        domain_data = {}
        for college_id in college_ids:
            course_id = selected_courses.get(college_id)
            try:
                domain_data[college_id] = RankingGraphHelper.fetch_ranking_data(
                    [college_id], start_year, end_year, course_ids={college_id: course_id}, ranking_entity='Stream Wise Colleges'
                ) if course_id else {}
            except NoDataAvailableError as e:
                logger.error(f"No data available for course ranking: {str(e)}")
                domain_data[college_id] = {}

        all_same_course = len(set(selected_courses.values())) <= 1
        has_na_overall, has_na_domain = False, False

        result_dict = {
            "years": years,
            "data": {
                "overall": {"type": "line" if all_same_course else "line", "colleges": overall_data},
                "domain": {"type": "line" if all_same_course else "line", "colleges": {}}
            },
            "college_names": list(
                College.objects.filter(id__in=college_ids)
                .annotate(order=Case(*[When(id=college_id, then=Value(idx)) for idx, college_id in enumerate(college_ids)],
                    default=Value(len(college_ids)), output_field=IntegerField()))
                .order_by('order')
                .values_list('name', flat=True)
            )
        }

        for idx, college_id in enumerate(college_ids):
            college_key = f"college_{idx + 1}"
            result_dict['data']['domain']['colleges'][college_key] = domain_data[college_id].get(f"college_1", {})

        for data_type in ["overall", "domain"]:
            for college_key, college_data in result_dict['data'][data_type]['colleges'].items():
                if college_data and "data" in college_data:
                    data = college_data["data"]
                    for year in years:
                        year_str = str(year)
                        if year_str not in data:
                            data[year_str] = "NA"
                        if data[year_str] == "NA":
                            if data_type == "overall":
                                has_na_overall = True
                            elif data_type == "domain":
                                has_na_domain = True

        if has_na_overall:
            result_dict["data"]["overall"]["type"] = "tabular"
        if has_na_domain:
            result_dict["data"]["domain"]["type"] = "tabular"

        return result_dict




class RankingAiInsightHelper:

    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY =   os.getenv("AWS_ACCESS_SECRET_KEY")

  
    REGION_NAME = 'us-east-1'
    MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'
    
    @staticmethod
    def get_cache_key(ranking_data: Dict) -> str:
        """
        Generates a cache key based on the ranking data.
        """
        data_str = json.dumps(ranking_data, sort_keys=True)
        return f"ranking_ai_insights_{hash(data_str)}"

    @staticmethod
    def create_ranking_insights(prompt: str) -> str:
        """Interacts with the Bedrock model to generate insights."""
        try:
            logger.info("Creating ranking insights using AWS Bedrock model.")
            client = boto3.client(
                "bedrock-runtime",
                region_name=RankingAiInsightHelper.REGION_NAME,
                aws_access_key_id=RankingAiInsightHelper.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=RankingAiInsightHelper.AWS_SECRET_ACCESS_KEY
            )

            native_request = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1536,
                "temperature": 0.2,
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": prompt}]}
                ]
            }

            logger.debug(f"Bedrock request payload: {json.dumps(native_request, indent=2)}")

            request = json.dumps(native_request)
            response = client.invoke_model(modelId=RankingAiInsightHelper.MODEL_ID, body=request)
            model_response = json.loads(response["body"].read())

            if not isinstance(model_response.get("content"), list):
                raise ValueError("Unexpected response structure from Bedrock")

            logger.debug(f"Bedrock raw response: {model_response}")
            return model_response["content"][0]["text"]

        except Exception as e:
            logger.error(f"Error generating insights with AWS Bedrock: {e}")
            return json.dumps({"error": str(e)})

    @staticmethod
    def format_insights(raw_insights: str) -> dict:
        """Formats raw insights into a proper dictionary."""
        try:
            logger.debug(f"Raw insights before processing: {raw_insights}")

            # Clean up and format the raw insights
            if isinstance(raw_insights, str):
                raw_insights = raw_insights.replace("\\n", "").replace("\\", "").strip()

            insights_dict = json.loads(raw_insights)

            formatted_insights = {
                key: " ".join(insights_dict.get(key, "").split())
                for key in ["graduation_outcome", "state_specific_rankings", 
                            "ownership_rankings", "past_year_changes", 
                            "highest_changes", "yearly_trends"]
            }

            return formatted_insights
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding failed: {e}")
            logger.error(f"Raw insights: {raw_insights}")
            return {"error": f"JSON decoding failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Error formatting insights: {e}")
            return {"error": f"An unexpected error occurred: {str(e)}"}




    @staticmethod
    def generate_ranking_insights(ranking_data: dict) -> str:
        """Generates AI-based ranking insights, either from cache or by invoking Bedrock."""
        try:
            
            cache_key = RankingAiInsightHelper.get_cache_key(ranking_data)
            cached_result = cache.get(cache_key)

            if cached_result:
                logger.info("Returning cached ranking insights.")
                return cached_result

            logger.info("Generating new ranking insights.")
            prompt =  f"""
        Analyze this college ranking data and generate JSON insights based on the following schema:
        {json.dumps(ranking_data, indent=2)}

        Output JSON must include these sections:

        1. "graduation_outcome": "Arrange graduation_outcome_scores[0] in descending order. Format: 'Based on current graduation outcomes, [college_short_name] scores [score] in [domain_name], followed by [college_short_name] with [score], and [college_short_name] with [score]' Include all colleges. Use exact scores from multi_year_ranking_data.",
        
        2. "state_specific_rankings": "Use state_rank_display from current_combined_ranking_data. Format: 'In state rankings, [college_short_name] is ranked [state rank], followed by [college_short_name]  is ranked [state rank] and [college_short_name]' is ranked [state rank] . List all colleges ordered by rank.",
        
        3. "ownership_rankings": "Use ownership_rank_display in descending order. Format: 'Among government institutes, [college_short_name] ranks [rank], followed by [college_short_name] ranks [rank] and [college_short_name]' ranks [rank]. Include all colleges.",
        
        4. "past_year_changes": "Compare nirf_overall_rank for current and previous years. Format: '[college_short_name] changes by [X] spots, followed by [college_short_name] changes by  [X] spots and [college_short_name] changes by  [X] spots'. Order by magnitude of change.",
        
        5. "highest_changes": "Identify the largest changes in ranks across all data. Format: '[college_short_name] shows the highest increase of [X]% among all colleges.'",
        
        6. "yearly_trends": "Analyze 5-year nirf_overall_rank. Format: '[college_short_name] shows a [trend] trend, followed by [college_short_name] and [college_short_name]'."

        Rules:
        1. Include all colleges in every insight.
        2. Use descending order for all numerical values.
        3. Ensure all sections are complete and JSON is valid.
        4. Focus only on the data provided. If data is missing, include 'No data available for [college_short_name]'.
        5. Use concise, natural transitions (e.g., "followed by", "while").
        6. Avoid using colons inside sentences.
        7.no of colleges always be 3 that depends on data and not mention (No data available for other colleges).

        IMPORTANT:
        - Only return valid JSON starting and ending with braces.
        - Do not include explanatory text or comments.
        - Ensure calculations and sorting are accurate.

        Temperature: 0.2
        """
                
            raw_insights = RankingAiInsightHelper.create_ranking_insights(prompt)
            logger.debug(f"Raw insights output: {raw_insights}")
            formatted_insights = RankingAiInsightHelper.format_insights(raw_insights)
            cache.set(cache_key, formatted_insights, timeout=3600 * 24 * 7)
            return formatted_insights
        except Exception as e:
            logger.error(f"Error in generate_ranking_insights: {str(e)}")
            return None





import re

class RankingInsightsCalculator:
    @staticmethod
    def is_valid_number(value):
        return value not in {'NA', None, ''}

    @staticmethod
    def safe_int_conversion(value):
        if RankingInsightsCalculator.is_valid_number(value):
            try:
                return int(value)
            except ValueError:
              
                if isinstance(value, str):
                    value = re.sub(r'(st|nd|rd|th)', '', value)
                try:
                    return int(value)
                except ValueError:
                    return None
        return None

    @staticmethod
    def calculate_ranking_insights(ranking_data: dict) -> dict:
        """
        Calculates ranking insights, ensuring proper sorting.
        Args:
            ranking_data (dict): Dictionary containing college ranking data.
        Returns:
            dict: Dictionary containing valid insights.
        """
        insights = {}
        try:
            current_year = ranking_data['current_year_data']
            previous_year = ranking_data['previous_year_data']
            current_combined = ranking_data['current_combined_ranking_data']
            multi_year = ranking_data['multi_year_ranking_data']

            
            graduation_parts = sorted(
                [
                    f"{data['college_short_name']} scores {data['graduation_outcome_score']} in {data['domain_name']}"
                    for college_id, data in current_year.items()
                    if RankingInsightsCalculator.is_valid_number(data.get('graduation_outcome_score'))
                ],
                key=lambda x: float(x.split("scores ")[1].split(" ")[0]),  
                reverse=True  
            )
            if graduation_parts:
                insights["graduation_outcome"] = "Based on current graduation outcomes, " + ", followed by ".join(graduation_parts)

          
            ownership_types = {data['ownership'] for data in current_year.values() if 'ownership' in data}

            state_ranking_parts = sorted(
                [
                    f"{current_year[college_id]['college_short_name']} is ranked {combined_data['state_rank_display']}"
                    for college_id, combined_data in current_combined.items()
                    if combined_data.get('state_rank_display') and combined_data['state_rank_display'] != 'Not Available'
                ],
                key=lambda x: RankingInsightsCalculator.safe_int_conversion(x.split("ranked ")[1].split(" ")[0])  
            )

            ownership_ranking_parts = sorted(
                [
                    f"{current_year[college_id]['college_short_name']} ranks {combined_data['ownership_rank_display']}"
                    for college_id, combined_data in current_combined.items()
                    if combined_data.get('ownership_rank_display') and combined_data['ownership_rank_display'] != 'Not Available'
                ],
                key=lambda x: RankingInsightsCalculator.safe_int_conversion(x.split("ranks ")[1].split(" ")[0]) 
            )

            if state_ranking_parts:
                insights['state_specific_rankings'] = ", followed by ".join(state_ranking_parts)

            if ownership_ranking_parts:
                ownership_desc = "varied ownership types" if len(ownership_types) > 1 else next(iter(ownership_types), "institutes")
                insights['ownership_rankings'] = f"Among {ownership_desc}, {', followed by '.join(ownership_ranking_parts)}"

           

            change_parts = []
            for college_id, data in current_year.items():
                current_rank = RankingInsightsCalculator.safe_int_conversion(data.get('nirf_overall_rank'))
                previous_rank = RankingInsightsCalculator.safe_int_conversion(previous_year.get(college_id, {}).get('nirf_overall_rank'))

                if current_rank is not None and previous_rank is not None:
                    change = previous_rank - current_rank
                    change_parts.append((data['college_short_name'], change))

            if change_parts:
                past_year_changes = ", followed by ".join(
                    f"{college[0]} {'dips by' if college[1] < 0 else 'improves by'} {abs(college[1])} spots"
                    for college in sorted(change_parts, key=lambda x: x[1], reverse=True)  # Descending Order
                )
                insights["past_year_changes"] = past_year_changes

               
                max_change_college = max(change_parts, key=lambda x: abs(x[1]))
                insights["highest_changes"] = (
                    f"{max_change_college[0]} shows the highest {'dip' if max_change_college[1] < 0 else 'increase'} "
                    f"of {abs(max_change_college[1])} spots among all colleges"
                )

           
            trends = sorted(
                [
                    (current_year[college_id]['college_short_name'], trend)
                    for college_id, data in multi_year.items()
                    if (ranks := [RankingInsightsCalculator.safe_int_conversion(r) for r in data['nirf_overall_rank']])
                    and (valid_ranks := [r for r in ranks if r is not None])
                    and (
                        trend := (
                            "improving" if all(valid_ranks[i] <= valid_ranks[i + 1] for i in range(len(valid_ranks) - 1))
                            else "declining" if all(valid_ranks[i] >= valid_ranks[i + 1] for i in range(len(valid_ranks) - 1))
                            else "fluctuating"
                        )
                    )
                ],
                reverse=True  # Descending Order
            )

            if trends:
                insights["yearly_trends"] = ", followed by ".join(
                    f"{college[0]} shows a {college[1]} trend"
                    for college in trends
                )

            return insights

        except Exception as e:
            print(f"Error calculating insights: {str(e)}")
            return {}




class PlacementInsightHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        """
        Generate a unique cache key by hashing the combined arguments.
        
        Args:
            *args: Variable number of arguments to be used in cache key generation
        
        Returns:
            str: MD5 hashed cache key
        """
        key = '_'.join(map(str, args))
        return md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_placement_stats(
        college_ids: List[int], 
        selected_courses: Optional[Dict[int, int]] = None, 
        year: int = None
    ) -> Dict:
        """
        Fetch placement statistics for a list of colleges with optional course filtering.

        This method provides flexible placement data retrieval with the following behaviors:
        1. If no courses are specified, it attempts to find the most relevant placement data
        2. When courses are provided, it filters placement data by those courses
        3. Handles various edge cases and potential data retrieval challenges

        Args:
            college_ids: A list of college IDs to fetch placement stats for
            selected_courses: Optional dictionary mapping college IDs to course IDs
            year: Optional year for placement stats (defaults to current year if not specified)

        Returns:
            A dictionary containing placement statistics for each college
        """
        try:
            # Use current year if not specified
            year = year 

            # Validate and convert college IDs
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
            if not college_ids:
                raise NoDataAvailableError("No valid college IDs provided.")

            # Prepare cache key parts
            cache_key_parts = ['___placement__stats_____insights_v3', year, '-'.join(map(str, college_ids))]
            if selected_courses:
                for cid in college_ids:
                    cache_key_parts.append(f"{cid}-{selected_courses.get(cid, 'NA')}")
            cache_key = PlacementInsightHelper.get_cache_key(*cache_key_parts)

            def fetch_data():
                try:
                    placement_stats = []
                    course_domain_map = {}

                    # Prepare course-to-domain mapping if courses are provided
                    if selected_courses:
                        courses = Course.objects.filter(id__in=selected_courses.values()).values('id', 'degree_domain')
                        course_domain_map = {course['id']: course['degree_domain'] for course in courses}

                    print(course_domain_map)

                    for college_id in college_ids:
                        # Determine domain for filtering
                        domain_id = None
                        course_id = None

                        if selected_courses:
                            # Use provided course mapping
                            course_id = selected_courses.get(college_id)
                            if course_id:
                                domain_id = course_domain_map.get(course_id)
                            
                            if not domain_id:
                                logger.warning(f"No domain found for college_id: {college_id}, course_id: {course_id}")
                                placement_stats.append({"college_id": college_id})
                                continue
                        else:
                            # Find most recent placement data if no specific course is provided
                            recent_placement = (
                                CollegePlacement.objects.filter(
                                    college_id=college_id,
                                    year=year
                                )
                                .order_by('-total_offers')
                                .first()
                            )
                            
                            if recent_placement:
                                print(recent_placement)
                                domain_id = recent_placement.stream_id
                            else:
                                logger.warning(f"No placement data found for college_id: {college_id}")
                                placement_stats.append({"college_id": college_id})
                                continue

                        # Fetch domain details
                        domain = Domain.objects.filter(id=domain_id).first()
                        domain_name = DomainHelper.format_domain_name(domain.old_domain_name) if domain else None

                        # Fetch placement data
                        # college_placement_data = (
                        #     CollegePlacement.objects.filter(
                        #         college_id=college_id,
                        #         year=year,
                        #         intake_year=year - 3,
                        #         stream_id=domain_id
                        #     ).values(
                        #         'college_id',
                        #         'max_salary_dom',
                        #         'max_salary_inter',
                        #         'avg_salary',
                        #         'median_salary',
                        #         'no_placed',
                        #         'inter_offers',
                        #         'total_offers',
                        #         'stream_id'
                        #     ).first()
                        # )
                        college_placement_data = (
                            CollegePlacement.objects.filter(
                                college_id=college_id,
                                year=year,
                                intake_year=year - 3,
                                stream_id=domain_id
                            ).values(
                                'college_id',
                                'max_salary_dom',
                                'max_salary_inter',
                                'avg_salary',
                                'median_salary',
                                'no_placed',
                                'inter_offers',
                                'total_offers',
                                'stream_id'
                            ).first()
                        )

                        # Fallback query without stream_id if no data found
                        if not college_placement_data:
                            college_placement_data = (
                                CollegePlacement.objects.filter(
                                    college_id=college_id,
                                    year=year,
                                    intake_year=year - 3
                                ).values(
                                    'college_id',
                                    'max_salary_dom',
                                    'max_salary_inter',
                                    'avg_salary',
                                    'median_salary',
                                    'no_placed',
                                    'inter_offers',
                                    'total_offers',
                                    'stream_id'
                                ).order_by('-no_placed','median_salary')  # Get the record with highest offers
                                .first()
                            )



                        if college_placement_data:
                            college_placement_data['domain_name'] = domain_name
                            college_placement_data['course_id'] = course_id
                            placement_stats.append(college_placement_data)
                        else:
                            logger.warning(
                                f"No placement data found for college_id: {college_id}, "
                                f"domain_id: {domain_id}, year: {year}"
                            )
                            placement_stats.append({
                                "college_id": college_id, 
                                'domain_name': domain_name, 
                                "domain_id": domain_id,
                                "course_id": course_id
                            })

                    # Validate placement stats
                    if not placement_stats:
                        raise NoDataAvailableError("No placement statistics data available.")

                    # Fetch college details
                    college_details = {
                        college['id']: {
                            'short_name': college['short_name'],
                        }
                        for college in College.objects.filter(id__in=college_ids)
                        .values('id', 'short_name')
                    }

                    # Prepare result dictionary
                    result_dict = {}
                    for idx, college_id in enumerate(college_ids, start=1):
                        stats = next((s for s in placement_stats if s.get('college_id') == college_id), {})
                        college_data = college_details.get(college_id, {})

                        result_dict[f"college_{idx}"] = {
                            "college_id": college_id,
                            "college_short_name": college_data.get('short_name', 'NA') or 'NA',
                            "total_offers": stats.get('total_offers', 0) or 0,
                            "total_students_placed_in_domain": stats.get('no_placed', "NA") or "NA",
                            "highest_domestic_salary_lpa": stats.get('max_salary_dom', 0) or 0,
                            "highest_international_salary_cr": stats.get('max_salary_inter', 0) or 0,
                            "average_salary_lpa": format_fee(stats.get('avg_salary', 0)),
                            "median_salary_lpa": format_fee(stats.get('median_salary', 0)),
                            "domain_id": stats.get('stream_id'),
                            "domain_name": stats.get('domain_name', 'NA'),
                            "course_id": stats.get('course_id'),
                            "year":year
                        }

                    return result_dict

                except NoDataAvailableError:
                    raise
                except Exception as e:
                    logger.error(f"Error fetching placement stats comparison data: {traceback.format_exc()}")
                    raise

            # Cache the result for a year
            return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 365)

        except NoDataAvailableError as e:
            logger.warning(str(e))
            raise
        except Exception as e:
            logger.error("Error in fetch_placement_stats: %s", traceback.format_exc())
            raise

    # The compare_placement_stats method remains unchanged
    @staticmethod
    def compare_placement_stats(stats_data: Dict) -> Dict:
        """
        Compare placement statistics for the given data.

        This method standardizes and rounds placement statistics 
        to facilitate easy comparison between colleges.

        Args:
            stats_data: A dictionary containing placement statistics for multiple colleges

        Returns:
            A dictionary with comparable placement statistics
        """
        try:
            result_dict = {}
            for college_key, college_data in stats_data.items():
                result_dict[college_key] = {
                    "college_id": college_data.get("college_id"),
                    "college_name": college_data.get("college_name"),
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


class PlacementAiInsightHelper:
    """
    A class to generate AI-powered insights from placement data using AWS Bedrock
    with Claude 3 Sonnet model. Includes caching functionality to optimize performance.
    The system is designed to work with any educational institution's placement data.
    """
    
    def __init__(self):
        """Initialize the Bedrock client with AWS credentials"""
        self.client = boto3.client(
            "bedrock-runtime",
            region_name="us-east-1",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=  os.getenv("AWS_ACCESS_SECRET_KEY")
            
        )
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

    @staticmethod
    def get_cache_key(placement_data: Dict) -> str:
        """Generate a unique cache key based on the input data"""
        data_str = json.dumps(placement_data, sort_keys=True)
        return f"placement_ai_insights_{hash(data_str)}"

    def _create_prompt(self, data: Dict) -> str:
        """
        Create an optimized prompt for the AI model that works with any college/institution data.
        The prompt uses generic [college_short_name] references and focuses on analyzing placement metrics
        regardless of the institution type.
        """
        return f"""
            Analyze the placement data and generate comprehensive insights for EACH COLLEGE in ALL FIVE categories, regardless of data availability. Present the analysis in JSON format:

            {{
                "highest_domestic_placement": "Format: '[Overview of Domestic Package Trends] refer[total_students_placed_in_domain]. [List ALL colleges in desc order: college_short_name reported ₹Y LPA in [Domain], college_short_name Z reported no data reported, etc.] in [Domain]. Industry insight: [Brief Salary Trend Analysis].' MUST include every college with their values or 'no data reported'",
                
                "highest_international_placement": "Format: '[Overview of International Package Distribution] refer [highest_international_salary_cr]. [List ALL colleges in desc order: college_short_name reported ₹Y Cr in [Domain], college_short_name no data reported, etc.] in [Domain]. Market observation: [Brief International Placement Trend].' MUST include every college with their values or 'no data reported'",
                
                "total_offers": "Format: '[Overview of Offer Trends] refer [total_offers]. [List ALL colleges in desc order: college_short_name reported Y offers in [Domain], college_short_name no data reported in [Domain], etc.]. Recruitment insight: [Brief Analysis of Offer Patterns].' MUST include every college with their values or 'no data reported'",
                
                "students_placed_min_time": "Format: '[Overview of Placement Success] refer [total_students_placed_in_domain]. [List ALL colleges in desc order: college_short_name reported  Y students placed in [domain], college_short_name no data reported, etc.] in [Domain]. Placement trend: [Brief Analysis of Placement Efficiency].' MUST include every college with their values or 'no data reported'",
                
                "average_salary": "Format: '[Overview of Average Compensation] refer [average_salary_lpa]. [List ALL colleges in desc order: college_short_name reported average package of ₹Y LPA in [Domain], college_short_name no data reported, etc.] in [Domain]. Compensation insight: [Brief Analysis of Average Salary Trends].' MUST include every college with their values or 'no data reported'"
            }}

            Critical Requirements:
            1. MANDATORY: Include ALL colleges in EVERY category, even if data is missing
            2. For missing/zero values, use exact phrase: 'College_Short_Name has no data reported for all/specific insights'
            3. Use short college names (e.g., 'IIT Indore' instead of 'Indian Institute of Technology Indore', DTU Delhi instead of Delhi Techincal University)
            4. List colleges in descending order by their respective metric values
            5. Include EXACT numbers for all available metrics
            6. Each insight must include a trend observation
            7. Focus on patterns and trends within each specific category
            8. Maintain analytical depth while being user-friendly
            9. Include only data-driven observations.
            10. strictly 0 as no data reported  for this insight.
            11. strictly not mismatch other's / differ refer insight criteria.
            12.  strictly for all insights consider ₹NA, ₹0 ,0 as currently no data reported. 

            Temperature: 0.5 (to balance creativity with precision)

            Input Data: {json.dumps(data, ensure_ascii=False, indent=2)}
            """

    def _invoke_model(self, prompt: str) -> Optional[str]:
        """Invoke the Bedrock model with the given prompt"""
        try:
            native_request = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "temperature": 0.5,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}],
                    }
                ],
            }
            request = json.dumps(native_request, ensure_ascii=False)
            response = self.client.invoke_model(
                modelId=self.model_id, 
                body=request.encode('utf-8')
            )
            model_response = json.loads(response["body"].read().decode('utf-8'))
            return model_response["content"][0]["text"]
        except Exception as e:
            logger.error(f"Error invoking the model: {str(e)}")
            return None

    def _format_insights(self, raw_insights: str) -> Optional[Dict]:
        """Format the raw insights into the desired structure"""
        try:
            insights_dict = json.loads(raw_insights)
            formatted_insights = {
                key: str(insights_dict.get(key, "")).strip()
                for key in [
                    "highest_domestic_placement",
                    "highest_international_placement",
                    "total_offers",
                    "students_placed_min_time",
                    "average_salary"
                ]
            }
            return formatted_insights
        except Exception as e:
            logger.error(f"Error formatting insights: {str(e)}")
            return None

    def get_ai_insights(self, placement_data: Dict) -> Optional[Dict]:
        """
        Main method to generate AI insights from placement data.
        Implements caching to avoid redundant API calls.
        """
        try:
            # Check cache first
            cache_key = self.get_cache_key(placement_data)
            cached_result = cache.get(cache_key)
            
            if cached_result:
                return cached_result
            
            # Generate new insights if not in cache
            prompt = self._create_prompt(placement_data)
            raw_insights = self._invoke_model(prompt)
            
            if not raw_insights:
                return None
            
            # Format and cache the insights
            insights = self._format_insights(raw_insights)
            if insights:
                cache.set(cache_key, insights, timeout=3600 * 24 * 180)  # Cache for 7 days
                
            return insights
            
        except Exception as e:
            logger.error(f"Error in get_ai_insights: {str(e)}")
            return None



class PlacementInsightsCalculator:
    @staticmethod
    def is_valid_number(value):
        """Check if a value is valid for numerical processing."""
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            cleaned = value.replace('₹', '').replace(',', '').strip()
            try:
                float(cleaned)
                return True
            except ValueError:
                return False
        return value not in {'NA', None, '', 0}

    @staticmethod
    def convert_salary_to_float(value):
        """Convert salary string to float value."""
        if not PlacementInsightsCalculator.is_valid_number(value):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = value.replace('₹', '').replace(',', '').strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def format_salary_lpa(salary):
        """Convert salary to LPA format (divide by 100000)"""
        return salary / 100000

    @staticmethod
    def format_number(value):
        """Format number to remove .00 if whole number, keep decimals otherwise"""
        if value == int(value):
            return f"{int(value)}"
        return f"{value:.2f}"

    @staticmethod
    def calculate_placement_insights(placement_data: dict) -> dict:
        insights = {}
        try:
            domain_name = next(iter(placement_data.values()))['domain_name']

            # Sort colleges by domestic placement salary
            domestic_parts = []
            for college_id, data in placement_data.items():
                salary = PlacementInsightsCalculator.convert_salary_to_float(data.get('highest_domestic_salary_lpa'))
                if salary and salary > 0:
                    domestic_parts.append((data['college_short_name'], salary))

            if domestic_parts:
                domestic_text = [
                    f"{college} reported ₹{PlacementInsightsCalculator.format_number(PlacementInsightsCalculator.format_salary_lpa(salary))} LPA"
                    for college, salary in sorted(domestic_parts, key=lambda x: x[1], reverse=True)
                ]
                if domestic_text:
                    insights["highest_domestic_placement"] = (
                        f"Based on domestic package trends referring to placement data, {', followed by '.join(domestic_text)} "
                        f"in {domain_name}"
                    )

            # Sort colleges by international placement salary
            international_parts = []
            for college_id, data in placement_data.items():
                salary = PlacementInsightsCalculator.convert_salary_to_float(data.get('highest_international_salary_cr'))
                if salary and salary > 0:
                    international_parts.append((data['college_short_name'], salary))

            if international_parts:
                international_text = [
                    f"{college} reported ₹{PlacementInsightsCalculator.format_number(salary)} Cr"
                    for college, salary in sorted(international_parts, key=lambda x: x[1], reverse=True)
                ]
                if international_text:
                    insights["highest_international_placement"] = (
                        f"Based on international package distribution, {', followed by '.join(international_text)} "
                        f"in {domain_name}"
                    )

            # Sort colleges by total offers
            offer_parts = []
            for college_id, data in placement_data.items():
                try:
                    offers = int(data.get('total_offers', 0))
                    if offers and offers > 0:
                        offer_parts.append((data['college_short_name'], offers))
                except (ValueError, TypeError):
                    continue

            if offer_parts:
                offer_text = [
                    f"{college} reported {offers} offers"
                    for college, offers in sorted(offer_parts, key=lambda x: x[1], reverse=True)
                ]
                if offer_text:
                    insights["total_offers"] = (
                        f"Based on placement offers, {', followed by '.join(offer_text)} "
                        f"in {domain_name}"
                    )

            # Sort colleges by students placed
            placed_parts = []
            for college_id, data in placement_data.items():
                try:
                    placed = int(data.get('total_students_placed_in_domain', 0))
                    if placed and placed > 0:
                        placed_parts.append((data['college_short_name'], placed))
                except (ValueError, TypeError):
                    continue

            if placed_parts:
                placed_text = [
                    f"{college} reported {placed} students placed"
                    for college, placed in sorted(placed_parts, key=lambda x: x[1], reverse=True)
                ]
                if placed_text:
                    insights["students_placed_min_time"] = (
                        f"Based on placement success, {', followed by '.join(placed_text)} "
                        f"in {domain_name}"
                    )

            # Sort colleges by median salary
            avg_salary_parts = []
            for college_id, data in placement_data.items():
                salary = PlacementInsightsCalculator.convert_salary_to_float(data.get('median_salary_lpa'))
                if salary and salary > 0:
                    avg_salary_parts.append((data['college_short_name'], salary))

            if avg_salary_parts:
                avg_salary_text = [
                    f"{college} reported average package of ₹{PlacementInsightsCalculator.format_number(PlacementInsightsCalculator.format_salary_lpa(salary))} LPA"
                    for college, salary in sorted(avg_salary_parts, key=lambda x: x[1], reverse=True)
                ]
                if avg_salary_text:
                    insights["average_salary"] = (
                        f"Based on average compensation, {', followed by '.join(avg_salary_text)} "
                        f"in {domain_name}"
                    )

            return insights

        except Exception as e:
            print(f"Error calculating placement insights: {str(e)}")
            return {}




class PlacementGraphInsightsHelper:
    """
    Helper class for processing and analyzing placement data across multiple colleges.
    Provides caching, data validation, and standardized formatting for placement insights.
    """

    CACHE_TIMEOUT = 3600 * 24 * 7

    @staticmethod
    def get_cache_key(*args) -> str:
        """
        Generates a consistent cache key from variable arguments.

        Args:
            *args: Variable number of arguments to include in the cache key

        Returns:
            str: MD5 hash of the concatenated arguments
        """
        key = '_'.join(map(str, args))
        return md5(key.encode()).hexdigest()

    @staticmethod
    def calculate_placement_percentage(graduating_students: int, placed_students: int) -> float:
        """
        Safely calculates the placement percentage, handling edge cases.

        Args:
            graduating_students: Total number of graduating students
            placed_students: Number of placed students

        Returns:
            float: Placement percentage rounded to 2 decimal places
        """
        if not isinstance(graduating_students, (int, float)) or not isinstance(placed_students, (int, float)):
            logger.warning(f"Invalid input types: graduating_students={type(graduating_students)}, placed_students={type(placed_students)}")
            return 'NA'

        if graduating_students <= 0:
            logger.warning("Graduating students is zero or negative")
            return 'NA'

        if placed_students < 0:
            logger.warning("Placed students is negative")
            return 'NA'

        return round((placed_students / graduating_students) * 100, 2)

    @staticmethod
    def get_max_salary(placement_data: dict) -> int:
        """
        Calculate the maximum salary from domestic and international values.

        Args:
            placement_data: Dictionary containing max_salary_dom and max_salary_inter

        Returns:
            int: Maximum salary value, defaulting to 0 if no valid salaries exist
        """
        max_salary_dom = placement_data.get('max_salary_dom')
        max_salary_inter = placement_data.get('max_salary_inter')

        if max_salary_dom is None and max_salary_inter is None:
            logger.warning(
                f"Both domestic and international salaries are None for placement record: "
                f"college_id={placement_data.get('college_id')}"
            )

        domestic = max(0, max_salary_dom) if isinstance(max_salary_dom, (int, float, Decimal)) else 0
        international = max(0, max_salary_inter) if isinstance(max_salary_inter, (int, float, Decimal)) else 0

        return max(domestic, international)

    @staticmethod
    def format_placement_data(
        college_id: int,
        placement: dict,
        index: int,
        recruiter_data: List[dict]
    ) -> tuple:
        """
        Formats placement data for a single college into the required structure.

        Args:
            college_id: ID of the college
            placement: Dictionary containing placement statistics
            index: Index of the college in the comparison
            recruiter_data: List of recruiting companies

        Returns:
            tuple: Formatted placement, salary, and recruiter data
        """
        graduating_students = placement.get('graduating_students', 0)
        placed_students = placement.get('no_placed', 0)

        placement_percentage = PlacementGraphInsightsHelper.calculate_placement_percentage(
            graduating_students, placed_students
        )

        max_salary = PlacementGraphInsightsHelper.get_max_salary(placement)

        college_key = f"college_{index}"

        placement_data = {
            "value": placement_percentage,
            "college_id": college_id,
        }

        salary_data = {
            "max_value": format_fee(max_salary),
            "college_id": college_id,
        }

        recruiter_data = {
            "companies": recruiter_data,
            "college_id": college_id,
        }

        return college_key, placement_data, salary_data, recruiter_data

    @classmethod
    def fetch_placement_insights(
        cls,
        college_ids: List[int],
        selected_courses: Dict[int, int],
        year: int
    ) -> Dict:
        """
        Fetches and processes placement insights for multiple colleges, allowing different domains per college.

        Args:
            college_ids: A list of college IDs
            selected_courses: A dictionary mapping college IDs to course IDs
            year: The year for which to fetch placement stats

        Returns:
            Dict: A dictionary containing formatted placement insights, keyed by college IDs

        Raises:
            ValueError: If invalid input parameters are provided
            Exception: For database or processing errors
            NoDataAvailableError: If no data is available for placement insights
        """

        if not college_ids:
            raise ValueError("No college IDs provided")
        if not isinstance(year, int) or year < 1900:
            raise ValueError(f"Invalid year: {year}")

        cache_key_parts = ['placement____insight', year, '-'.join(map(str, college_ids))]
        for cid in college_ids:
            cache_key_parts.append(f"{cid}-{selected_courses.get(cid, 'NA')}")
        cache_key = cls.get_cache_key(*cache_key_parts)


        def fetch_data() -> Dict:
            """Inner function to fetch and process placement data."""
            try:
                selected_domains = {}
                if selected_courses:
                    courses = Course.objects.filter(id__in=selected_courses.values()).values('id', 'degree_domain')
                    course_domain_map = {course['id']: course['degree_domain'] for course in courses}

                    for college_id in college_ids:
                        course_id = selected_courses.get(college_id)
                        if course_id:
                            selected_domains[college_id] = course_domain_map.get(course_id)

                placements = {
                    college_id: CollegePlacement.objects.filter(
                        Q(year=year, published='published', college_id=college_id) &
                        (Q(stream_id=selected_domains[college_id]) if selected_domains.get(college_id) else Q())
                    )
                    .values('graduating_students', 'no_placed', 'max_salary_dom', 'max_salary_inter')
                    .annotate(total_offers=Coalesce(Sum('no_placed'), 0))
                    .order_by('college_id')
                    .first() or {}
                    for college_id in college_ids
                }

                if not placements:
                    raise NoDataAvailableError("No placement data available for the provided colleges and year.")

                recruiter_data = {
                    college_id: [
                        {"name": rec.get('popular_name') or rec.get('name'), "logo": rec.get('logo')}
                        for rec in Company.objects.filter(
                            collegeplacementcompany__collegeplacement__college_id=college_id,
                            collegeplacementcompany__collegeplacement__year=year,
                            published='published'
                        )
                        .values('popular_name', 'logo', 'name')
                        .distinct()[:5]
                    ]
                    for college_id in college_ids
                }

                no_recruiters = all(not data for data in recruiter_data.values())

                colleges = {
                    college['id']: college['name']
                    for college in College.objects.filter(id__in=college_ids).values('id', 'name')
                }

                result_dict = {
                    "placement_percentage": {"type": "horizontal bar", "year_tag": year, "colleges": {}},
                    "salary": {"type": "horizontal bar", "year_tag": f"{year-1}-{year}", "colleges": {}},
                    "recruiter": {},
                    "college_names": [colleges[college_id] for college_id in college_ids],
                }

                all_same_domain = len(set(selected_domains.values())) <= 1 if selected_domains else True
                if all_same_domain:
                    result_dict["placement_percentage"]["type"] = "horizontal bar"
                    result_dict["salary"]["type"] = "horizontal bar"
                else:
                    result_dict["placement_percentage"]["type"] = "tabular"
                    result_dict["salary"]["type"] = "tabular"

                for idx, college_id in enumerate(college_ids, 1):
                    college_key, placement_data, salary_data, recruiters = cls.format_placement_data(
                        college_id,
                        placements.get(college_id, {}),
                        idx,
                        recruiter_data.get(college_id, [])
                    )

                    result_dict["placement_percentage"]["colleges"][college_key] = placement_data
                    result_dict["salary"]["colleges"][college_key] = salary_data
                    result_dict["recruiter"][college_key] = recruiters

                    if placement_data["value"] == 'NA':
                        result_dict["placement_percentage"]["type"] = "tabular"
                    if salary_data["max_value"] == 'NA':
                        result_dict["salary"]["type"] = "tabular"

                if no_recruiters:
                    result_dict["recruiter"] = {}

                final_result = {
                    "data": {
                        "placement_percentage": result_dict["placement_percentage"],
                        "salary": result_dict["salary"],
                        "recruiter": result_dict["recruiter"]
                    },
                    "college_names": result_dict["college_names"]
                }

                return final_result

            except NoDataAvailableError as e:
                logger.error(f"No data available for placement insights: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Error in fetch_placement_insights: {traceback.format_exc()}")
                raise

        return cache.get_or_set(cache_key, fetch_data, cls.CACHE_TIMEOUT)



from urllib.parse import quote

class CourseFeeComparisonHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = '________'.join(map(str, args))
        return md5(key.encode()).hexdigest()
    



    @staticmethod
    def fetch_exams_for_courses(course_ids: List[int]) -> Dict[int, Dict]:
        """
        Fetches exam details for each course, categorizing them into top exams and all exams.
        Uses `get_exam_display_name()` instead of `exam_short_name`.
        """
        exams_map = defaultdict(dict)

        for course in Course.objects.filter(id__in=course_ids):
            # Get the domain name and format it
            domain_name = DomainHelper.format_domain_name(course.degree_domain.old_domain_name).lower()

            exams = Exam.objects.filter(college_courses__college_course=course).select_related('parent_exam').order_by('state_of_exam_id')


            top_exams = []
            all_exams = []

            for exam in exams:
                # Determine the exam name to use for the link
                if exam.parent_exam:
                    exam_name = exam.parent_exam.exam_short_name if exam.parent_exam.exam_short_name else exam.parent_exam.exam_name
                else:
                    exam_name = exam.exam_short_name if exam.exam_short_name else exam.exam_name

                exam_name_slug = exam_name.replace(" ", "-")  # Replace spaces with hyphens
                exam_name_slug=exam_name_slug.lower()
                exam_link = f"https://{domain_name}.careers360.com/exams/{quote(exam_name_slug)}"

                # Add to top exams if we haven't reached the limit
                if len(top_exams) < 2:
                    top_exams.append({"name": exam.get_exam_display_name(), "link": exam_link})

                # Always add to all exams
                all_exams.append({"name": exam.get_exam_display_name(), "link": exam_link})

            exams_map[course.id] = {
                "top_exams": top_exams if top_exams else "N/A",
                "all_exams": all_exams if len(all_exams) > 2 else None
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

            cache_key = CourseFeeComparisonHelper.get_cache_key('course_fees_comparisons', '-'.join(map(str, course_ids)))

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

                    result_dict = {}

                    courses = Course.objects.filter(id__in=course_ids, college_id__in=college_ids)
                    
                    college_courses = defaultdict(list)
                    for course in courses:
                        college_courses[course.college.id].append(course)

                    if not college_courses:
                        raise NoDataAvailableError("No courses or colleges found for the provided IDs.")

                    for college_id in college_ids:
                        idx = college_order[college_id] + 1
                        college_key = f"college_{idx}"

                        for course in college_courses[college_id]:
                            exams = exams_map.get(course.id, {})
                            
                            
                            course_instance = Course.objects.get(id=course.id)
                            credential_label = {
                                0: "Degree",
                                1: "Diploma",
                                2: "Certificate"
                            }.get(course_instance.credential, "Degree")  

                            course_data = {
                                "college_name": course.college.name,
                                "college_id": course.college.id,
                                "course": course.id,
                                "course_credential": credential_label,
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
                            result_dict[college_key] = course_data  
                    if not result_dict:
                        raise NoDataAvailableError("No data available for the specified comparison criteria.")

                    return result_dict

                except NoDataAvailableError as e:
                    logger.error(f"Error: {e}")
                    return {"error": str(e)}

                except Exception as e:
                    logger.error("Error fetching course comparison data: %s", traceback.format_exc())
                    raise

            return cache.get_or_set(cache_key, fetch_data, 3600*24*7)

        except NoDataAvailableError as e:
            logger.error(f"Error: {e}")
            return {"error": str(e)}

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

        cache_key = FeesHelper.get_cache_key('fees_____comparisons', '-'.join(map(str, course_ids)), intake_year)
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
                                output_field=DecimalField(max_digits=10, decimal_places=2))
                            ),
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
                        st_fees=Coalesce(
                            Sum(Case(
                                When(fees__category='ST', then=F('fees__total_fees')),
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
                        ),

                    )
                    .values('id', 'college_id', 'gn_fees', 'obc_fees', 'sc_fees','st_fees' ,'nq_fees')
                )


                if not fee_details:
                    raise NoDataAvailableError("No fee details found for the specified courses and colleges")


                import time
                current_year = time.localtime().tm_year

                tuition_fees_map = defaultdict(lambda: {
                    'total_tuition_fee_general': 'NA',
                    'total_tuition_fee_sc': 'NA',
                    'total_tuition_fee_st': 'NA',
                    'total_tuition_fee_obc': 'NA'
                })

                for course_id in course_ids:
                    tuition_fees = Course.get_total_tuition_fee_by_course(course_id, current_year-1)
                    if tuition_fees:
                        tuition_fees_map[course_id] = tuition_fees

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
                colleges = {college.id: college.short_name for college in College.objects.filter(id__in=college_ids)}

       
                result_dict = {}
                for idx, college_id in enumerate(college_ids):
                    scholarship_data = scholarships_map.get(college_id, {
                        'total_scholarship': Decimal('0.00'),
                        'high_scholarship_authority': 'NA'
                    })

                    total_scholarship = int(scholarship_data['total_scholarship'])

                    course_id_for_college = [course for course in course_ids if course in Course.objects.filter(college_id=college_id).values_list('id', flat=True)]
                    tuition_fees = {}
                    if course_id_for_college:
                        tuition_fees = tuition_fees_map.get(course_id_for_college[0], {
                            'total_tuition_fee_general': 'NA',
                            'total_tuition_fee_sc': 'NA',
                            'total_tuition_fee_st': 'NA',
                            'total_tuition_fee_obc': 'NA'
                        })
                    
                    fee_detail = next((fd for fd in fee_details if fd['college_id'] == college_id), None)
                    if fee_detail:
                        result_dict[f"college_{idx + 1}"] = {
                            "college_id": college_id,
                            "college_short_name": colleges.get(college_id, 'Unknown College'),
                            "gn_fees": format_fee(fee_detail['gn_fees']),
                            "obc_fees": format_fee(fee_detail['obc_fees']),
                            "sc_fees": format_fee(fee_detail['sc_fees']),
                            "nq_fees": format_fee(fee_detail['nq_fees']),
                            "st_fees":format_fee(fee_detail['st_fees']),
                            "total_scholarship_given": total_scholarship if total_scholarship > 0 else "NA",
                            "high_scholarship_authority": scholarship_data['high_scholarship_authority'],
                            "total_tuition_fees": tuition_fees
                            }
                    else:
                        result_dict[f"college_{idx + 1}"] = {
                            "college_id": college_id,
                            "college_short_name": colleges.get(college_id, 'Unknown College'),
                            "gn_fees": "NA",
                            "obc_fees": "NA",
                            "sc_fees": "NA",
                            "nq_fees": "NA",
                            "total_scholarship_given": "NA",
                            "high_scholarship_authority": "NA",
                            "total_tuition_fees": {
                                'total_tuition_fee_general': 'NA',
                                'total_tuition_fee_sc': 'NA',
                                'total_tuition_fee_st': 'NA',
                                'total_tuition_fee_obc': 'NA'
                            }
                        } 
                return result_dict
            
            except NoDataAvailableError as e:
                    logger.error(f"Error: {e}")
                    return {"error": str(e)}


            except Exception as e:
                logger.error("Error fetching fee details: %s", traceback.format_exc())
                raise

        return cache.get_or_set(cache_key, fetch_data, 3600*24*7)

    @staticmethod
    def get_high_scholarship_authority(total_gov: Decimal, total_institution: Decimal, total_private: Decimal) -> str:
        authority_map = {
            'Government': total_gov,
            'Institution': total_institution,
            'Private': total_private
        }
        max_authority = max(authority_map, key=authority_map.get)
        return max_authority if authority_map[max_authority] > 0 else 'NA'





class FeesAiInsightHelper:
    # Class-level constants similar to RankingAiInsightHelper
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_ACCESS_SECRET_KEY")
    REGION_NAME = 'us-east-1'
    MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

    @staticmethod
    def get_cache_key(fees_data: Dict) -> str:
        """Generate a unique cache key based on the input fees data."""
        data_str = json.dumps(fees_data, sort_keys=True)
        return f"fees_ai_insights_{hash(data_str)}"

    @staticmethod
    def format_currency(amount: str) -> str:
        """Format currency values consistently."""
        try:
            if amount == "NA" or not amount:
                return "NA"
            
            clean_amount = amount.replace("₹", "").replace(" ", "").replace(",", "")
            value = float(clean_amount)
            
            if value >= 10000000:  # 1 crore
                return f"₹ {value/10000000:.2f} Cr"
            elif value >= 100000:  # 1 lakh
                return f"₹ {value/100000:.2f} L"
            else:
                return f"₹ {value:,.2f}"
            
        except (ValueError, TypeError):
            return "NA"

    @staticmethod
    def create_fees_insights(prompt: str) -> str:
        """Generate insights using Bedrock model based on the given prompt."""
        try:
            logger.info("Creating fees insights using AWS Bedrock model.")
            client = boto3.client(
                "bedrock-runtime",
                region_name=FeesAiInsightHelper.REGION_NAME,
                aws_access_key_id=FeesAiInsightHelper.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=FeesAiInsightHelper.AWS_SECRET_ACCESS_KEY
            )

            native_request = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "temperature": 0.6,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}],
                    }
                ],
            }

            logger.debug(f"Bedrock request payload: {json.dumps(native_request, indent=2)}")
            
            request = json.dumps(native_request)
            response = client.invoke_model(
                modelId=FeesAiInsightHelper.MODEL_ID, 
                body=request.encode('utf-8')
            )
            model_response = json.loads(response["body"].read().decode('utf-8'))
            
            logger.debug(f"Bedrock raw response: {model_response}")
            return model_response["content"][0]["text"]
            
        except Exception as e:
            logger.error(f"Error in create_fees_insights: {str(e)}")
            return json.dumps({"error": str(e)})

    @staticmethod
    def format_fees_insights(raw_insights: str) -> Dict:
        """Format the raw insights into structured format."""
        try:
            logger.debug(f"Raw insights before processing: {raw_insights}")

            # Clean up and format the raw insights
            if isinstance(raw_insights, str):
                raw_insights = raw_insights.replace("\\n", "").replace("\\", "").strip()

            insights_dict = json.loads(raw_insights)
            
            formatted_insights = {
                "highest_tuition_fees": insights_dict.get("highest_tuition_fees", "NA"),
                "highest_fees_element": insights_dict.get("highest_fees_element", "NA"),
                "scholarships_available": insights_dict.get("scholarships_available", "NA"),
                "scholarship_granting_authority": insights_dict.get("scholarship_granting_authority", "NA")
            }

            # Format currency values in the insights
            for key in formatted_insights:
                if isinstance(formatted_insights[key], str) and "₹" in formatted_insights[key]:
                    text = formatted_insights[key]
                    amounts = [s for s in text.split() if "₹" in s]
                    for amount in amounts:
                        formatted_amount = FeesAiInsightHelper.format_currency(amount)
                        text = text.replace(amount, formatted_amount)
                    formatted_insights[key] = text

            return formatted_insights
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding failed: {e}")
            logger.error(f"Raw insights: {raw_insights}")
            return {"error": f"JSON decoding failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Error formatting insights: {e}")
            return {"error": f"An unexpected error occurred: {str(e)}"}

    @staticmethod
    def generate_prompt(fees_data: Dict) -> str:
        """Generate the prompt for the AI model."""
        return f"""
        The agent is provided with the fee details of atmost 3 colleges.
        Generate detailed fee insights comparing the provided colleges. Return the insights as a JSON object where keys represent the specific categories, and values are descriptive sentences in **plain string format** (not lists or bullet points). Use the following structure:
        {{
            "highest_tuition_fees": "Analyze ONLY the direct fee fields (gn_fees, obc_fees, sc_fees, nq_fees, st_fees). Provide a detailed sentence comparing colleges in descending order based on their highest category fees. Include specific fee amounts where available and explicitly mention if data is missing. Start each college reference with the institution's name.",
            "highest_fees_element": "Analyze the total fee fields (total_tuition_fee_general, total_tuition_fee_sc, total_tuition_fee_st, total_tuition_fee_obc). Format the response as: 'For higest category fees, [Institution Name] charges the highest at ₹X, followed by [Institution Name] at ₹Y, and [Institution Name] at ₹Z. The SC, ST, and OBC category fees vary significantly, with [mention specific variations or missing data].' Maintain strictly descending order by category fees. Include all three institutions. Do not use the words,'total' 'tuition' in the response.",
            "scholarships_available": "[fetch data from 'scholarship_available' it denotes the number of students] write a descriptive sentence or paragraph summarizing the number of students availing scholarship for each college, or mentioning missing data if applicable.",
            "scholarship_granting_authority": "A descriptive sentence or paragraph summarizing the authority granting scholarships at each college, highlighting any missing or incomplete information."
        }}
        Fees Data: {json.dumps(fees_data, ensure_ascii=False, indent=2)}
        """

    @staticmethod
    def get_fees_insights(fees_data: Dict) -> Optional[Dict]:
        """Generate and process fees insights with caching."""
        try:
            # Check cache first
            cache_key = FeesAiInsightHelper.get_cache_key(fees_data)
            cached_result = cache.get(cache_key)

            if cached_result:
                logger.info("Returning cached fees insights.")
                return cached_result

            logger.info("Generating new fees insights.")
            
            # Generate new insights
            prompt = FeesAiInsightHelper.generate_prompt(fees_data)
            raw_insights = FeesAiInsightHelper.create_fees_insights(prompt)
            formatted_insights = FeesAiInsightHelper.format_fees_insights(raw_insights)
            
            # Cache the results
            cache.set(cache_key, formatted_insights, timeout=3600 * 24 * 7)  # Cache for 7 days
            
            return formatted_insights
            
        except Exception as e:
            logger.error(f"Error in get_fees_insights: {str(e)}")
            return None



class FeesInsightsCalculator:
    CATEGORY_MAPPING = {
        'gn_fees': 'General',
        'obc_fees': 'OBC',
        'sc_fees': 'SC',
        'st_fees': 'ST'
    }

    @staticmethod
    def is_valid_fee(value):
        """Check if a fee value is valid for numerical processing."""
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            cleaned = value.replace('₹', '').replace(',', '').strip()
            try:
                float(cleaned)
                return True
            except ValueError:
                return False
        return value not in {'NA', None, '', 0}

    @staticmethod
    def convert_fee_to_float(value):
        """Convert fee string to float value."""
        if not FeesInsightsCalculator.is_valid_fee(value):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = value.replace('₹', '').replace(',', '').strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
        
    @staticmethod
    def format_fee(value):
        """Format fee to a string with Indian currency notation."""
        if value is None:
            return "NA"
        locale.setlocale(locale.LC_ALL, 'en_IN')  # Set Indian locale
        return f"₹ {locale.format_string('%d', value, grouping=True)}.00"


    

    @staticmethod
    def find_highest_fees_category(fees_data: dict) -> dict:
        """Find the college with the highest fees in any category."""
        highest_fees_info = {
            "college_name": None,
            "highest_fees": 0,
            "category": None
        }

        for college_id, data in fees_data.items():
            for category, label in FeesInsightsCalculator.CATEGORY_MAPPING.items():
                fee_value = FeesInsightsCalculator.convert_fee_to_float(data.get(category))
                if fee_value is not None and fee_value > highest_fees_info["highest_fees"]:
                    highest_fees_info["highest_fees"] = fee_value
                    highest_fees_info["college_name"] = data.get('college_short_name', 'Unknown')
                    highest_fees_info["category"] = label

        return highest_fees_info

    @staticmethod
    def calculate_fees_insights(fees_data: dict) -> dict:
        insights = {}
        try:
            general_fees_parts = []
            scholarship_parts = []
            authority_parts = []

            for college_id, data in fees_data.items():
                college_name = data.get('college_short_name', 'Unknown')

                # Find highest tuition fee across all categories
                max_fee = max(
                    filter(None, [
                        FeesInsightsCalculator.convert_fee_to_float(data.get('gn_fees')),
                        FeesInsightsCalculator.convert_fee_to_float(data.get('obc_fees')),
                        FeesInsightsCalculator.convert_fee_to_float(data.get('sc_fees')),
                        FeesInsightsCalculator.convert_fee_to_float(data.get('st_fees'))
                    ]),
                    default=None
                )

                if max_fee is not None:
                    general_fees_parts.append((college_name, max_fee))

                # Collect scholarship-related data
                total_scholarship = data.get('total_scholarship_given', 0)
                if isinstance(total_scholarship, int) and total_scholarship > 0:
                    scholarship_parts.append((college_name, total_scholarship))

                # Scholarship granting authority
                authority = data.get('high_scholarship_authority', 'NA')
                if authority != 'NA':
                    authority_parts.append((college_name, authority))

            # Highest tuition fees insight
            if general_fees_parts:
                sorted_fees = sorted(general_fees_parts, key=lambda x: x[1], reverse=True)
                top_colleges = [college for college, _ in sorted_fees]
                insights["highest_tuition_fees"] = (
                    f"{top_colleges[0]} has the highest tuition fees among all {len(general_fees_parts)} colleges, followed by "
                    f"{', '.join(top_colleges[1:])}."
                )

            # Highest fees category insight
            highest_fees_info = FeesInsightsCalculator.find_highest_fees_category(fees_data)
            if highest_fees_info["college_name"]:
                insights["highest_fees_element"] = (
                    f"The highest fees are for {highest_fees_info['college_name']} in the "
                    f"{highest_fees_info['category']} category with fees of {FeesInsightsCalculator.format_fee(highest_fees_info['highest_fees'])}."
                )

            # Scholarship availability insight
            if scholarship_parts:
                scholarship_text = [
                    f"{college} has provided scholarships to {scholarships} students"
                    for college, scholarships in sorted(scholarship_parts, key=lambda x: x[1], reverse=True)
                ]
                insights["scholarships_available"] = (
                    f"Based on scholarship data, {', followed by '.join(scholarship_text)}."
                )

            
            if authority_parts:
                authority_text = [
                    f"{college} has scholarships granted by {authority}"
                    for college, authority in authority_parts
                ]
                insights["scholarship_granting_authority"] = (
                    f"Scholarship granting authorities include {', followed by '.join(authority_text)}."
                )

            return insights

        except Exception as e:
            print(f"Error calculating fees insights: {str(e)}")
            return {}


class FeesGraphHelper:
    """
  
    """
    
    @staticmethod
    def get_cache_key(*args) -> str:
        """Creates a unique cache key from the provided arguments."""
        key = '_'.join(map(str, args))
        return hashlib.md5(key.encode()).hexdigest()
    
    @staticmethod
    def fetch_fee_data(course_ids: List[int]) -> Dict:
        """
        Fetches and processes fee data with independent display type handling per category.
        """
        try:
            course_ids = [int(course_id) for course_id in course_ids 
                         if isinstance(course_id, (int, str))]
        except (ValueError, TypeError):
            raise ValueError("course_ids must be a flat list of integers or strings.")
        
        cache_key = FeesGraphHelper.get_cache_key(
            'fees_graph',
            '-'.join(map(str, course_ids))
        )
        
        def fetch_data():
          
            static_categories = [
                'general',
                'observed_backward_class',
                'scheduled_caste'
            ]
            
            
            courses = (
                Course.objects.filter(id__in=course_ids)
                .select_related('college')
                .values('id', 'college__name')
            )

            if not courses:
                raise NoDataAvailableError("No courses found for the specified course IDs")
            
       
            result_dict = {
                "categories": static_categories,
                "year_tag": time.localtime().tm_year - 1,
                "data": {
                    category: {
                        "type": "horizontal bar",  
                        "values": {}
                    } for category in static_categories
                },
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
                .values("college_course_id", "category", "total_fees")
            )
            
         
            fee_mapping = {}
            for fee in fees_data:
                course_id = fee["college_course_id"]
                category = fee["category"]
                total_fees = fee["total_fees"]
                if course_id not in fee_mapping:
                    fee_mapping[course_id] = {}
                fee_mapping[course_id][category] = total_fees
            
         
            category_mapping = {
                "gn": "general",
                "obc": "observed_backward_class",
                "sc": "scheduled_caste"
            }
            
         
            category_has_na = {category: False for category in static_categories}
            
        
            for idx, course_id in enumerate(ordered_course_ids, 1):
                college_name = course_id_to_name.get(course_id)
                if college_name:
                    for raw_category in ['gn', 'obc', 'sc']:
                        display_category = category_mapping[raw_category]
                        college_key = f"college_{idx}"
                        total_fees = fee_mapping.get(course_id, {}).get(raw_category)
                        
                     
                        if total_fees is None:
                            category_has_na[display_category] = True
              
                        result_dict["data"][display_category]["values"][college_key] = {
                            "course_id": course_id,
                            "fee": format_fee(total_fees) if total_fees is not None else "NA"
                        }
            
    
            for category in static_categories:
                if category_has_na[category]:
                    result_dict["data"][category]["type"] = "tabular"
               
            
            result_dict["college_names"] = college_names
            return result_dict
        
        # Cache for 1 year
        return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 7)
    
    @staticmethod
    def prepare_fees_insights(course_ids: List[int]) -> Dict:
        """Prepares fee insights for the specified courses."""
        return FeesGraphHelper.fetch_fee_data(course_ids)







class ClassProfileHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = '_'.join(str(arg) for arg in args)
        return md5(key.encode()).hexdigest()
    
    @staticmethod
        
    def fetch_class_profiles(
        college_ids: List[int],
        year: int,
        intake_year: int,
        selected_courses: Optional[Dict[int, int]] = None  # Optional mapping of college ID to course ID
    ) -> Dict:
        """
        Fetch Class Profile data for a list of colleges, considering selected courses if provided.

        Args:
            college_ids (List[int]): List of college IDs to filter.
            year (int): Year of the placement.
            intake_year (int): Intake year of students.
            selected_courses (Optional[Dict[int, int]]): A dictionary mapping college IDs to course IDs (optional).

        Returns:
            Dict: Class profile data for each college.
        """

        college_ids = [item for sublist in college_ids for item in (sublist if isinstance(sublist, list) else [sublist])]

        logger.debug(f"Fetching class profiles for college_ids: {college_ids} with selected courses: {selected_courses}")

        # Map course IDs to their degree domains and levels (if provided)
        course_domain_map = {}
        if selected_courses:
            courses = Course.objects.filter(id__in=selected_courses.values()).values('id', 'degree_domain', 'level')
            course_domain_map = {course['id']: (course['degree_domain'], course['level']) for course in courses}

        logger.debug(f"Course to domain and level mapping: {course_domain_map}")

        cache_key = ClassProfileHelper.get_cache_key(
            'ClassProfilesWithCourses', '-'.join(map(str, sorted(college_ids))), year, intake_year, selected_courses or {}
        )

        def fetch_data():
            try:
                results = []

                for college_id in college_ids:
                    domain_id, level = None, None

                    if selected_courses:
                        course_id = selected_courses.get(college_id)
                        if course_id:
                            domain_id, level = course_domain_map.get(course_id, (None, None))

                    # Build the query dynamically based on the presence of domain_id and level
                    query = Q(id=college_id) & Q(collegeplacement__intake_year=intake_year)
                    if domain_id:
                        query &= Q(collegeplacement__stream_id=domain_id)
                    if level:
                        query &= Q(collegeplacement__levels=level)

                    college_result = (
                        College.objects.filter(query)
                        .distinct()
                        .values('id')
                        .annotate(
                            total_students=Coalesce(Max('collegeplacement__total_students'), Value(0, output_field=IntegerField())),
                            male_students=Coalesce(Max('collegeplacement__male_students'), Value(0, output_field=IntegerField())),
                            female_students=Coalesce(Max('collegeplacement__female_students'), Value(0, output_field=IntegerField())),
                            students_outside_state=Coalesce(Max('collegeplacement__outside_state'), Value(0, output_field=IntegerField())),
                            outside_country_student=Coalesce(Max('collegeplacement__outside_country'), Value(0, output_field=IntegerField())),
                            total_faculty=Coalesce(Max('total_faculty'), Value(0, output_field=IntegerField())),
                            intake_year=F('collegeplacement__intake_year')
                        )
                    )
                    results.extend(college_result)

                if not results:
                    raise NoDataAvailableError(
                        f"No class profile data found for colleges: {college_ids} "
                        f"year: {year}, intake_year: {intake_year}"
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
                        "year":year
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
                            "intake_year": intake_year,
                            "year":year
                        }

                return result_dict
            except Exception as e:
                logger.error(f"Error fetching class profiles: {e}")
                raise

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 7)

    







# class ProfileInsightsHelper:
#     @staticmethod
#     def get_cache_key(*args) -> str:
#         key = '_'.join(str(arg) for arg in args)
#         return md5(key.encode()).hexdigest()

#     @staticmethod
#     def validate_selected_domains(selected_domains):
#         if not isinstance(selected_domains, dict):
#             raise TypeError("selected_domains must be a dictionary with college_id as keys and domain_id as values.")

#     @staticmethod
#     def fetch_student_faculty_ratio(college_ids: List[int], course_ids: List[int], year: int, intake_year: int, level: int = 1) -> Dict[str, Dict]:
#         if not course_ids:
#             raise ValueError("course_ids must be provided and cannot be empty.")

#         courses = Course.objects.filter(id__in=course_ids).values('id', 'degree_domain', 'level')
#         course_domain_map = {course['id']: (course['degree_domain'], course['level']) for course in courses}

#         cache_key = ProfileInsightsHelper.get_cache_key('___student___faculty___new', '-'.join(map(str, college_ids)), year, intake_year, level)

#         def fetch_data():
#             latest_year = CollegePlacement.objects.filter(college_id__in=college_ids).aggregate(Max('year'))['year__max'] or year

#             query_result = []
#             total_students = 0
#             total_faculty = 0

#             for college_id in college_ids:
#                 domain_id, level = course_domain_map.get(college_id, (None, None))
#                 if not domain_id:
#                     continue

#                 result = College.objects.filter(id=college_id).annotate(
#                     students=Coalesce(Max(Case(When(Q(collegeplacement__intake_year=intake_year) & Q(collegeplacement__stream_id=domain_id), then='collegeplacement__total_students'), default=Value(0, output_field=IntegerField()))), Value(0, output_field=IntegerField())),
#                     faculty=Coalesce(Max('total_faculty'), Value(0, output_field=IntegerField()))
#                 ).values('id', 'students', 'faculty')

#                 query_result.extend(result)
#                 total_students += sum(data['students'] for data in result)
#                 total_faculty += sum(data['faculty'] for data in result)

#             average_ratio = (total_faculty / total_students * 100) if total_students else 0

#             import time
#             current_year = time.localtime().tm_year
#             visualization_type = "horizontal bar"
#             result = {"year_tag": current_year - 1, "average_ratio": round(average_ratio, 2)}

#             for idx, data in enumerate(query_result, 1):
#                 if data['faculty'] > 0 and data['students'] > 0:
#                     ratio = (data['faculty'] / data['students']) * 100
#                 else:
#                     ratio = None
#                     visualization_type = "tabular"

#                 ownership_ratio_difference_from_avg = round(ratio - average_ratio, 2) if ratio is not None else "NA"

#                 result[f"college_{idx}"] = {
#                     "college_id": str(data['id']),
#                     "total_students": data['students'] or "NA",
#                     "total_faculty": data['faculty'] or "NA",
#                     "student_faculty_ratio_percentage": round(ratio, 2) if ratio is not None else "NA",
#                     "data_status": "complete" if ratio is not None else "incomplete",
#                     "ownership_ratio_difference_from_avg": ownership_ratio_difference_from_avg
#                 }

#             result["type"] = visualization_type
#             return result

#         return cache.get_or_set(cache_key, fetch_data, 3600 * 24)

#     @staticmethod
#     def fetch_student_demographics(college_ids: List[int], course_ids: List[int], year: int, intake_year: int, level: int = 1) -> Dict[str, Dict]:
#         if not course_ids:
#             raise ValueError("course_ids must be provided and cannot be empty.")

#         courses = Course.objects.filter(id__in=course_ids).values('id', 'degree_domain', 'level')
#         course_domain_map = {course['id']: (course['degree_domain'], course['level']) for course in courses}

#         cache_key = ProfileInsightsHelper.get_cache_key('__student_____demographics_new', '-'.join(map(str, college_ids)), year, intake_year, level)

#         def fetch_data():
#             latest_year = CollegePlacement.objects.filter(college_id__in=college_ids).aggregate(Max('year'))['year__max'] or year

#             query_result = []
#             for college_id in college_ids:
#                 domain_id, level = course_domain_map.get(college_id, (None, None))
#                 if not domain_id:
#                     continue

#                 result = CollegePlacement.objects.filter(
#                     college_id=college_id,
#                     intake_year=intake_year,
#                     stream_id=domain_id
#                 ).values('college_id').annotate(
#                     total_students=Coalesce(Max('total_students'), Value(0, output_field=IntegerField())),
#                     outside_state=Coalesce(Max('outside_state'), Value(0, output_field=IntegerField()))
#                 )

#                 if not result:
#                     query_result.append({'college_id': college_id, 'total_students': 0, 'outside_state': 0})
#                 else:
#                     query_result.extend(result)

#             import time
#             current_year = time.localtime().tm_year
#             result = {"year_tag": current_year - 1}

#             for idx, data in enumerate(query_result, 1):
#                 outside_state_percentage = (data['outside_state'] / data['total_students'] * 100) if data['total_students'] > 0 else None

#                 result[f"college_{idx}"] = {
#                     "college_id": str(data['college_id']),
#                     "total_students": data['total_students'] or "NA",
#                     "students_outside_state": data['outside_state'] or "NA",
#                     "percentage_outside_state": round(outside_state_percentage, 2) if outside_state_percentage is not None else "NA",
#                     "data_status": "complete" if outside_state_percentage is not None else "incomplete"
#                 }

#             result["type"] = "tabular" if any(result[f"college_{i}"]["data_status"] == "incomplete" for i in range(1, len(query_result) + 1)) else "horizontal bar"
#             return result

#         return cache.get_or_set(cache_key, fetch_data, 3600 * 24)

#     @staticmethod
#     def fetch_gender_diversity(college_ids: List[int], course_ids: List[int], year: int, intake_year: int, level: int = 1) -> Dict[str, Dict]:
#         if not course_ids:
#             raise ValueError("course_ids must be provided and cannot be empty.")

#         courses = Course.objects.filter(id__in=course_ids).values('id', 'degree_domain', 'level')
#         course_domain_map = {course['id']: (course['degree_domain'], course['level']) for course in courses}

#         cache_key = ProfileInsightsHelper.get_cache_key('___Gender_____Diversity', '-'.join(map(str, college_ids)), year, intake_year, level)

#         def fetch_data():
#             latest_year = CollegePlacement.objects.filter(college_id__in=college_ids).aggregate(Max('year'))['year__max'] or year

#             query_result = []
#             total_male_students = 0
#             total_female_students = 0
#             total_students = 0
#             male_differences = []
#             female_differences = []
#             institute_type_differences = {}

#             for college_id in college_ids:
#                 domain_id, level = course_domain_map.get(college_id, (None, None))
#                 if not domain_id:
#                     continue

#                 result = CollegePlacement.objects.filter(
#                     college_id=college_id,
#                     intake_year=intake_year,
#                     stream_id=domain_id
#                 ).values('college_id').annotate(
#                     male_students=Coalesce(Max('male_students'), Value(0, output_field=IntegerField())),
#                     female_students=Coalesce(Max('female_students'), Value(0, output_field=IntegerField())),
#                     total_students=F('male_students') + F('female_students')
#                 )

#                 query_result.extend(result)
#                 total_male_students += sum(data['male_students'] for data in result)
#                 total_female_students += sum(data['female_students'] for data in result)
#                 total_students += sum(data['total_students'] for data in result)

#                 for data in result:
#                     male_percentage = (data['male_students'] / data['total_students'] * 100) if data['total_students'] > 0 else None
#                     female_percentage = (data['female_students'] / data['total_students'] * 100) if data['total_students'] > 0 else None

#                     if male_percentage is not None and female_percentage is not None:
#                         male_differences.append(male_percentage)
#                         female_differences.append(female_percentage)

#                         college = College.objects.get(id=college_id)
#                         institute_type = college.type_of_institute(college.institute_type_1, college.institute_type_2) or 'Not Available'
#                         if institute_type not in institute_type_differences:
#                             institute_type_differences[institute_type] = {'male': [], 'female': []}

#                         institute_type_differences[institute_type]['male'].append(male_percentage)
#                         institute_type_differences[institute_type]['female'].append(female_percentage)

#             average_male_percentage = (total_male_students / total_students * 100) if total_students else 0
#             average_female_percentage = (total_female_students / total_students * 100) if total_students else 0

#             avg_male_difference = (sum(male_differences) / len(male_differences) - average_male_percentage) if male_differences else 0
#             avg_female_difference = (sum(female_differences) / len(female_differences) - average_female_percentage) if female_differences else 0

#             institute_type_differences_from_avg = {}
#             for institute_type, differences in institute_type_differences.items():
#                 avg_male_type_diff = (sum(differences['male']) / len(differences['male']) - average_male_percentage) if differences['male'] else 0
#                 avg_female_type_diff = (sum(differences['female']) / len(differences['female']) - average_female_percentage) if differences['female'] else 0
#                 institute_type_differences_from_avg[institute_type] = {
#                     "male_difference_from_avg": round(avg_male_type_diff, 2),
#                     "female_difference_from_avg": round(avg_female_type_diff, 2)
#                 }

#             import time
#             current_year = time.localtime().tm_year
#             result = {
#                 "year_tag": current_year - 1,
#                 "average_male_percentage": round(average_male_percentage, 2),
#                 "average_female_percentage": round(average_female_percentage, 2)
#             }

#             for college_id in college_ids:
#                 idx = college_ids.index(college_id) + 1
#                 college_data = next((data for data in query_result if data['college_id'] == college_id), None)

#                 if college_data and college_data['total_students'] > 0:
#                     male_percentage = (college_data['male_students'] / college_data['total_students'] * 100)
#                     female_percentage = (college_data['female_students'] / college_data['total_students'] * 100)

#                     college = College.objects.get(id=college_id)
#                     institute_type = college.type_of_institute(college.institute_type_1, college.institute_type_2) or 'Not Available'
#                     institute_gender_diversity_diff = institute_type_differences_from_avg.get(institute_type, {"male_difference_from_avg": "NA", "female_difference_from_avg": "NA"})

#                     result[f"college_{idx}"] = {
#                         "college_id": str(college_id),
#                         "male_students": college_data['male_students'],
#                         "female_students": college_data['female_students'],
#                         "percentage_male": round(male_percentage, 2),
#                         "percentage_female": round(female_percentage, 2),
#                         "data_status": "complete",
#                         "ownership_gender_diversity_difference": round(female_percentage - avg_female_difference, 2),
#                         "type_of_institute_gender_diversity_difference_from_avg": institute_gender_diversity_diff['female_difference_from_avg']
#                     }
#                 else:
#                     result[f"college_{idx}"] = {
#                         "college_id": str(college_id),
#                         "male_students": "NA",
#                         "female_students": "NA",
#                         "percentage_male": "NA",
#                         "percentage_female": "NA",
#                         "data_status": "incomplete",
#                         "ownership_gender_diversity_difference": "NA",
#                         "type_of_institute_gender_diversity_difference_from_avg": "NA"
#                     }

#             result["type"] = "tabular" if any(result[f"college_{i}"]["data_status"] == "incomplete" for i in range(1, len(college_ids) + 1)) else "horizontal bar"
#             return result

#         return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 7)

#     @staticmethod
#     def prepare_profile_insights(
#         college_ids: List[int],
#         year: int,
#         intake_year: int,
#         course_ids: List[int],  # Changed from selected_domains to course_ids
#         level: int = 1,
#     ) -> Dict:
#         """
#         Prepare comprehensive profile insights including all metrics.
#         """
#         # Validate that course_ids is not empty
#         if not course_ids:
#             raise ValueError("course_ids must be provided and cannot be empty.")

#         college_details = list(
#             College.objects.filter(id__in=college_ids)
#             .values(
#                 'id',
#                 'name',
#                 'short_name',
#                 'ownership',
#                 'institute_type_1',
#                 'institute_type_2'
#             )
#         )

#         college_details_map = {college['id']: college for college in college_details}

#         # Reorder college details based on the order of college_ids
#         ordered_college_details = [college_details_map[college_id] for college_id in college_ids]

#         # Add additional info to college details
#         for college in ordered_college_details:
#             college['ownership_display'] = (
#                 dict(College.OWNERSHIP_CHOICES).get(college['ownership'], 'Not Available')
#             )
#             college['type_of_institute'] = (
#                 College.type_of_institute(
#                     college['institute_type_1'], 
#                     college['institute_type_2']
#                 ) or 'Not Available'
#             )

#         student_faculty_ratio_data = ProfileInsightsHelper.fetch_student_faculty_ratio(
#             college_ids=college_ids,
#             course_ids=course_ids,  # Pass course_ids instead of selected_domains
#             year=year,
#             intake_year=intake_year,
#             level=level
#         )

#         student_demographics_data = ProfileInsightsHelper.fetch_student_demographics(
#             college_ids=college_ids,
#             course_ids=course_ids,  # Pass course_ids instead of selected_domains
#             year=year,
#             intake_year=intake_year,
#             level=level
#         )

#         gender_diversity_data = ProfileInsightsHelper.fetch_gender_diversity(
#             college_ids=college_ids,
#             course_ids=course_ids,  # Pass course_ids instead of selected_domains
#             year=year,
#             intake_year=intake_year,
#             level=level
#         )

#         return {
#             "year": year,
#             "intake_year": intake_year,
#             "level": level,
#             "data": {
#                 "student_faculty_ratio": student_faculty_ratio_data,
#                 "student_from_outside_state": student_demographics_data,
#                 "gender_diversity": gender_diversity_data
#             },
#             "college_details": ordered_college_details,  
#         }

    
    

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
        # Flatten the college_ids list and ensure all values are integers, also filter out invalid values
        college_ids = [
            int(item) for sublist in college_ids 
            for item in (sublist if isinstance(sublist, list) else [sublist])
            if item is not None and str(item).isdigit()
        ]
        
        logger.debug(f"Fetching facilities for college_ids: {college_ids}")

        if not college_ids:
            logger.warning("No valid college_ids provided.")
            return {}

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

                # Initialize result_dict with colleges and default values
                result_dict = {
                    f"college_{i}": {
                        "college_id": college_id,
                        "facilities": set(),
                        "facilities_count": 0
                    }
                    for i, college_id in enumerate(college_ids, 1)
                }

                facility_choices = {str(k): v for k, v in dict(CollegeFacility.FACILITY_CHOICES).items()}

                # Process the results and populate the facilities
                for result in results:
                    college_id = result.get('college_id')
                    facility_id = str(result.get('facility', None))

                    # Skip if the facility_id or college_id is None
                    if college_id is None or facility_id is None or facility_id not in facility_choices:
                        continue

                    # Find the corresponding college entry in result_dict
                    college_key = next(
                        (key for key, data in result_dict.items() if data['college_id'] == college_id),
                        None
                    )

                    if college_key:
                        result_dict[college_key]['facilities'].add(facility_choices[facility_id])

                # Sort the facilities and update the count
                for college_data in result_dict.values():
                    college_data['facilities'] = sorted(list(college_data['facilities']))
                    college_data['facilities_count'] = len(college_data['facilities'])

                logger.debug(f"Processed facilities data: {result_dict}")
                return result_dict

            except Exception as e:
                logger.error(f"Error fetching college facilities: {e}", exc_info=True)
                raise

        return cache.get_or_set(cache_key, fetch_facilities, 3600 * 24 * 7)


class CollegeAmenitiesHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        """
        Generate a cache key by hashing the joined string of arguments.
        """
        key = '_____'.join(str(arg) for arg in args)
        return md5(key.encode()).hexdigest()

    @staticmethod
    def get_college_amenities(college_ids: List[int], es_host: str = None, es_index: str = None) -> Dict:
        """
        Get detailed amenities data for multiple colleges with caching.

        Args:
            college_ids (List[int]): List of college IDs to search for.
            es_host (str): Elasticsearch host URL (optional).
            es_index (str): Elasticsearch index name (optional).

        Returns:
            Dict: Dictionary with college amenities data and counts.
        """
        college_ids = [int(cid) for cid in college_ids]

        logger.debug(f"Fetching amenities for college_ids: {college_ids}")

    
        es_host = es_host or os.getenv('ES_HOST', 'https://elastic.careers360.de')
        es_index = es_index or os.getenv('ES_INDEX', 'college__amenities')

    
        cache_key = CollegeAmenitiesHelper.get_cache_key(
            'College_Amenities_Detailed_V1',
            '-'.join(map(str, sorted(college_ids)))
        )

        def fetch_amenities():
            """
            Fetch amenities data from Elasticsearch.
            """
            try:
                es_client = Elasticsearch([es_host], retry_on_timeout=True, max_retries=3,verify_certs=False)

                query = {
                    "query": {
                        "terms": {
                            "college_id": [str(cid) for cid in college_ids]
                        }
                    }
                }

                response = es_client.search(index=es_index, body=query)

                
                default_amenities = {
                    "hospital": 0,
                    "gym": 0,
                    "cafe": 0,
                    "restaurant": 0,
                    "park": 0,
                    "mall": 0,
                    "atm": 0,
                    "stationery": 0,
                    "police": 0
                }


                amenities_map = {
                    int(hit['_source']['college_id']): hit['_source']['amenities']
                    for hit in response['hits']['hits']
                }

        
                result = {}
                for i, cid in enumerate(college_ids, 1):
                    college_key = f"college_{i}"
                    college_amenities = amenities_map.get(cid, {})

                 
                    amenities_data = {**default_amenities, **college_amenities}

                
                    result[college_key] = {
                        "college_id": cid,
                        **amenities_data
                    }

                logger.debug(f"Processed amenities data: {result}")
                return result

            except Exception as e:
                logger.error(f"Error fetching college amenities: {e}", exc_info=True)
                raise
            finally:
                if 'es_client' in locals():
                    es_client.close()

        
        return cache.get_or_set(cache_key, fetch_amenities, 3600 * 24 * 31)


class ProfileInsightsHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = "_".join(str(arg) for arg in args)
        return md5(key.encode()).hexdigest()

    @staticmethod
    def validate_selected_domains(selected_domains):
        if not isinstance(selected_domains, dict):
            raise TypeError(
                "selected_domains must be a dictionary with college_id as keys and domain_id as values."
            )

    @staticmethod
    def fetch_student_faculty_ratio(
        college_ids: List[int],
        year: int,
        intake_year: int,
        selected_courses: Optional[Dict[int, int]] = None,
        level: int = 1,
    ) -> Dict[str, Dict]:
        """
        Fetch student-faculty ratio data for a list of colleges, considering selected courses if provided.
        """

        cache_key = ProfileInsightsHelper.get_cache_key(
            "studentfaculty",
            "-".join(map(str, college_ids)),
            year,
            intake_year,
            selected_courses or {},
            level,
        )

        def fetch_data():
            query_result = []
            total_students = 0
            total_faculty = 0

            # Map course IDs to their degree domains and levels (if provided)
            course_domain_map = {}
            if selected_courses:
                courses = Course.objects.filter(id__in=selected_courses.values()).values(
                    "id", "degree_domain", "level"
                )
                course_domain_map = {
                    course["id"]: (course["degree_domain"], course["level"])
                    for course in courses
                }

            for college_id in college_ids:
                college_total_students = 0
                college_total_faculty = 0

                domain_id, level_val = None, None
                if selected_courses and college_id in selected_courses:
                    course_id = selected_courses[college_id]
                    domain_id, level_val = course_domain_map.get(course_id, (None, None))

                query = Q(id=college_id) & Q(collegeplacement__intake_year=intake_year)
                if domain_id:
                    query &= Q(collegeplacement__stream_id=domain_id)
                if level_val:
                    query &= Q(collegeplacement__levels=level_val)

                result = (
                    College.objects.filter(query)
                    .annotate(
                        students=Coalesce(
                            Max("collegeplacement__total_students"),
                            Value(0, output_field=IntegerField()),
                        ),
                        faculty=Coalesce(
                            "total_faculty", Value(0, output_field=IntegerField())
                        ),
                    )
                    .values("id", "students", "faculty")
                    .first()
                )

                if result:
                    college_total_students += result["students"]
                    college_total_faculty += result["faculty"]

                query_result.append(
                    {
                        "id": college_id,
                        "students": college_total_students,
                        "faculty": college_total_faculty,
                    }
                )
                total_students += college_total_students
                total_faculty += college_total_faculty

            average_ratio = (
                (total_faculty / total_students * 100) if total_students else 0
            )

            current_year = time.localtime().tm_year
            visualization_type = "horizontal bar"
            result = {"year_tag": current_year - 1, "average_ratio": round(average_ratio, 2)}

            for idx, data in enumerate(query_result, 1):
                if data["faculty"] > 0 and data["students"] > 0:
                    ratio = (data["faculty"] / data["students"]) * 100
                else:
                    ratio = None
                    visualization_type = "tabular"

                ownership_ratio_difference_from_avg = (
                    round(ratio - average_ratio, 2) if ratio is not None else "NA"
                )

                result[f"college_{idx}"] = {
                    "college_id": str(data["id"]),
                    "total_students": data["students"] or "NA",
                    "total_faculty": data["faculty"] or "NA",
                    "student_faculty_ratio_percentage": round(ratio, 2)
                    if ratio is not None
                    else "NA",
                    "data_status": "complete" if ratio is not None else "incomplete",
                    "ownership_ratio_difference_from_avg": ownership_ratio_difference_from_avg,
                }

            result["type"] = visualization_type
            return result

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24)

    @staticmethod
    def fetch_student_demographics(
        college_ids: List[int],
        year: int,
        intake_year: int,
        selected_courses: Optional[Dict[int, int]] = None,
        level: int = 1,
    ) -> Dict[str, Dict]:
        """
        Fetch student demographics data for a list of colleges, considering selected courses if provided.
        """

        cache_key = ProfileInsightsHelper.get_cache_key(
            "student_demographics",
            "-".join(map(str, college_ids)),
            year,
            intake_year,
            selected_courses or {},
            level,
        )

        def fetch_data():
            query_result = []

            # Map course IDs to their degree domains and levels (if provided)
            course_domain_map = {}
            if selected_courses:
                courses = Course.objects.filter(id__in=selected_courses.values()).values(
                    "id", "degree_domain", "level"
                )
                course_domain_map = {
                    course["id"]: (course["degree_domain"], course["level"])
                    for course in courses
                }

            for college_id in college_ids:
                college_total_students = 0
                college_outside_state = 0

                domain_id, level_val = None, None
                if selected_courses and college_id in selected_courses:
                    course_id = selected_courses[college_id]
                    domain_id, level_val = course_domain_map.get(course_id, (None, None))

                query = Q(id=college_id) & Q(collegeplacement__intake_year=intake_year)
                if domain_id:
                    query &= Q(collegeplacement__stream_id=domain_id)
                if level_val:
                    query &= Q(collegeplacement__levels=level_val)

                result = (
                    College.objects.filter(query)
                    .annotate(
                        total_students=Coalesce(
                            Max("collegeplacement__total_students"),
                            Value(0, output_field=IntegerField()),
                        ),
                        outside_state=Coalesce(
                            Max("collegeplacement__outside_state"),
                            Value(0, output_field=IntegerField()),
                        ),
                    )
                    .values("id", "total_students", "outside_state")
                    .first()
                )

                if result:
                    college_total_students += result["total_students"]
                    college_outside_state += result["outside_state"]

                query_result.append(
                    {
                        "college_id": college_id,
                        "total_students": college_total_students,
                        "outside_state": college_outside_state,
                    }
                )

            current_year = time.localtime().tm_year
            result = {"year_tag": current_year - 1}

            for idx, data in enumerate(query_result, 1):
                outside_state_percentage = (
                    (data["outside_state"] / data["total_students"] * 100)
                    if data["total_students"] > 0
                    else None
                )

                result[f"college_{idx}"] = {
                    "college_id": str(data["college_id"]),
                    "total_students": data["total_students"] or "NA",
                    "students_outside_state": data["outside_state"] or "NA",
                    "percentage_outside_state": round(outside_state_percentage, 2)
                    if outside_state_percentage is not None
                    else "NA",
                    "data_status": "complete"
                    if outside_state_percentage is not None
                    else "incomplete",
                }

            result["type"] = "tabular" if any(
                result[f"college_{i}"]["data_status"] == "incomplete"
                for i in range(1, len(query_result) + 1)
            ) else "horizontal bar"
            return result

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24)

    @staticmethod
    def fetch_gender_diversity(
        college_ids: List[int],
        year: int,
        intake_year: int,
        selected_courses: Optional[Dict[int, int]] = None,
        level: int = 1,
    ) -> Dict[str, Dict]:
        """
        Fetch gender diversity data for a list of colleges, considering selected courses if provided.
        """

        cache_key = ProfileInsightsHelper.get_cache_key(
            "Gender_Diversity",
            "-".join(map(str, college_ids)),
            year,
            intake_year,
            selected_courses or {},
            level,
        )

        def fetch_data():
            query_result = []
            total_male_students = 0
            total_female_students = 0
            total_students = 0
            male_differences = []
            female_differences = []
            institute_type_differences = {}

            # Map course IDs to their degree domains and levels (if provided)
            course_domain_map = {}
            if selected_courses:
                courses = Course.objects.filter(id__in=selected_courses.values()).values(
                    "id", "degree_domain", "level"
                )
                course_domain_map = {
                    course["id"]: (course["degree_domain"], course["level"])
                    for course in courses
                }

            for college_id in college_ids:
                college_total_male = 0
                college_total_female = 0
                college_total_students = 0
                college_male_percentages = []
                college_female_percentages = []

                domain_id, level_val = None, None
                if selected_courses and college_id in selected_courses:
                    course_id = selected_courses[college_id]
                    domain_id, level_val = course_domain_map.get(course_id, (None, None))

                query = Q(id=college_id) & Q(collegeplacement__intake_year=intake_year)
                if domain_id:
                    query &= Q(collegeplacement__stream_id=domain_id)
                if level_val:
                    query &= Q(collegeplacement__levels=level_val)

                result = (
                    College.objects.filter(query)
                    .annotate(
                        male_students=Coalesce(
                            Max("collegeplacement__male_students"),
                            Value(0, output_field=IntegerField()),
                        ),
                        female_students=Coalesce(
                            Max("collegeplacement__female_students"),
                            Value(0, output_field=IntegerField()),
                        ),
                    )
                    .values("id", "male_students", "female_students")
                    .first()
                )

                if result:
                    college_total_male += result["male_students"]
                    college_total_female += result["female_students"]
                    college_total_students = college_total_male + college_total_female

                    if college_total_students > 0:
                        male_percentage = (
                            result["male_students"] / college_total_students * 100
                        )
                        female_percentage = (
                            result["female_students"] / college_total_students * 100
                        )
                        college_male_percentages.append(male_percentage)
                        college_female_percentages.append(female_percentage)

                query_result.append(
                    {
                        "college_id": college_id,
                        "male_students": college_total_male,
                        "female_students": college_total_female,
                        "total_students": college_total_students,
                        "male_percentages": college_male_percentages,
                        "female_percentages": college_female_percentages,
                    }
                )
                total_male_students += college_total_male
                total_female_students += college_total_female
                total_students += college_total_students

                if college_male_percentages and college_female_percentages:
                    male_differences.extend(college_male_percentages)
                    female_differences.extend(college_female_percentages)

                    college = College.objects.get(id=college_id)
                    institute_type = (
                        college.type_of_institute(
                            college.institute_type_1, college.institute_type_2
                        )
                        or "Not Available"
                    )
                    if institute_type not in institute_type_differences:
                        institute_type_differences[institute_type] = {
                            "male": [],
                            "female": [],
                        }

                    institute_type_differences[institute_type]["male"].extend(
                        college_male_percentages
                    )
                    institute_type_differences[institute_type]["female"].extend(
                        college_female_percentages
                    )

            average_male_percentage = (
                (total_male_students / total_students * 100) if total_students else 0
            )
            average_female_percentage = (
                (total_female_students / total_students * 100)
                if total_students
                else 0
            )

            avg_male_difference = (
                (sum(male_differences) / len(male_differences) - average_male_percentage)
                if male_differences
                else 0
            )
            avg_female_difference = (
                (
                    sum(female_differences) / len(female_differences)
                    - average_female_percentage
                )
                if female_differences
                else 0
            )

            institute_type_differences_from_avg = {}
            for institute_type, differences in institute_type_differences.items():
                avg_male_type_diff = (
                    (sum(differences["male"]) / len(differences["male"]) - average_male_percentage)
                    if differences["male"]
                    else 0
                )
                avg_female_type_diff = (
                    (
                        sum(differences["female"]) / len(differences["female"])
                        - average_female_percentage
                    )
                    if differences["female"]
                    else 0
                )
                institute_type_differences_from_avg[institute_type] = {
                    "male_difference_from_avg": round(avg_male_type_diff, 2),
                    "female_difference_from_avg": round(avg_female_type_diff, 2),
                }

            current_year = time.localtime().tm_year
            result = {
                "year_tag": current_year - 1,
                "average_male_percentage": round(average_male_percentage, 2),
                "average_female_percentage": round(average_female_percentage, 2),
            }

            for idx, data in enumerate(query_result, 1):
                college_id = data["college_id"]
                if data["total_students"] > 0:
                    male_percentage = (
                        data["male_students"] / data["total_students"] * 100
                    )
                    female_percentage = (
                        data["female_students"] / data["total_students"] * 100
                    )

                    college = College.objects.get(id=college_id)
                    institute_type = (
                        college.type_of_institute(
                            college.institute_type_1, college.institute_type_2
                        )
                        or "Not Available"
                    )
                    institute_gender_diversity_diff = (
                        institute_type_differences_from_avg.get(
                            institute_type,
                            {"male_difference_from_avg": "NA", "female_difference_from_avg": "NA"},
                        )
                    )

                    result[f"college_{idx}"] = {
                        "college_id": str(college_id),
                        "male_students": data["male_students"],
                        "female_students": data["female_students"],
                        "percentage_male": round(male_percentage, 2),
                        "percentage_female": round(female_percentage, 2),
                        "data_status": "complete",
                        "ownership_gender_diversity_difference": round(
                            female_percentage - avg_female_difference, 2
                        ),
                        "type_of_institute_gender_diversity_difference_from_avg": institute_gender_diversity_diff[
                            "female_difference_from_avg"
                        ],
                    }
                else:
                    result[f"college_{idx}"] = {
                        "college_id": str(college_id),
                        "male_students": "NA",
                        "female_students": "NA",
                        "percentage_male": "NA",
                        "percentage_female": "NA",
                        "data_status": "incomplete",
                        "ownership_gender_diversity_difference": "NA",
                        "type_of_institute_gender_diversity_difference_from_avg": "NA",
                    }

            result["type"] = "tabular" if any(
                result[f"college_{i}"]["data_status"] == "incomplete"
                for i in range(1, len(college_ids) + 1)
            ) else "horizontal bar"
            return result

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 7)

    @staticmethod
    def prepare_profile_insights(
        college_ids: List[int],
        year: int,
        intake_year: int,
        selected_courses: Dict[int, int],
        level: int = 1,
    ) -> Dict:
        """
        Prepare comprehensive profile insights including all metrics.
        """
        # Validate that selected_courses is not empty
        if not selected_courses:
            raise ValueError("selected_courses must be provided and cannot be empty.")

        college_details = list(
            College.objects.filter(id__in=college_ids)
            .values(
                'id',
                'name',
                'short_name',
                'ownership',
                'institute_type_1',
                'institute_type_2'
            )
        )

        college_details_map = {college['id']: college for college in college_details}

        # Reorder college details based on the order of college_ids
        ordered_college_details = [college_details_map[college_id] for college_id in college_ids]

        # Add additional info to college details
        for college in ordered_college_details:
            college['ownership_display'] = (
                dict(College.OWNERSHIP_CHOICES).get(college['ownership'], 'Not Available')
            )
            college['type_of_institute'] = (
                College.type_of_institute(
                    college['institute_type_1'], 
                    college['institute_type_2']
                ) or 'Not Available'
            )

        student_faculty_ratio_data = ProfileInsightsHelper.fetch_student_faculty_ratio(
            college_ids=college_ids,
            selected_courses=selected_courses,
            year=year,
            intake_year=intake_year,
            level=level
        )

        student_demographics_data = ProfileInsightsHelper.fetch_student_demographics(
            college_ids=college_ids,
            selected_courses=selected_courses,
            year=year,
            intake_year=intake_year,
            level=level
        )

        gender_diversity_data = ProfileInsightsHelper.fetch_gender_diversity(
            college_ids=college_ids,
            selected_courses=selected_courses,
            year=year,
            intake_year=intake_year,
            level=level
        )

        return {
            "year": year,
            "intake_year": intake_year,
            "level": level,
            "data": {
                "student_faculty_ratio": student_faculty_ratio_data,
                "student_from_outside_state": student_demographics_data,
                "gender_diversity": gender_diversity_data
            },
            "college_details": ordered_college_details,  
        }

class ClassProfileAiInsightHelper:
    _cache = {}  # Simple in-memory cache
    CACHE_TIMEOUT = 3600 * 24 * 7  # Cache for 7 days (in seconds)

    @staticmethod
    def _get_college_name(college_id: str, college_details: list) -> str:
        """Get college short name from college details."""
        return next(
            (c["short_name"] for c in college_details if str(c["id"]) == str(college_id)),
            "Unknown",
        )

    @staticmethod
    def _get_ownership_display(college_id: str, college_details: list) -> str:
        """Get college ownership display from college details."""
        return next(
            (
                c["ownership_display"]
                for c in college_details
                if str(c["id"]) == str(college_id)
            ),
            "Unknown",
        )

    @staticmethod
    def _has_non_zero_values(colleges_data: list) -> bool:
        """Check if any college in the list has a non-zero value."""
        return any(
            abs(college[1]["ownership_ratio_difference_from_avg"]) > 0.001
            for college in colleges_data
        )

    @staticmethod
    def _create_sorted_insights(data: Dict) -> Dict:
        """Create sorted insights for different metrics."""
        sorted_insights = {
            "student_faculty_sorted": [],
            "gender_diversity_sorted": [],
            "ownership_gender_diversity_sorted": [],
        }

        # Sort and process student faculty ratio
        colleges = [
            (k, v)
            for k, v in data["data"]["student_faculty_ratio"].items()
            if k.startswith("college_") and v["data_status"] == "complete"
        ]

        if ClassProfileAiInsightHelper._has_non_zero_values(colleges):
            sorted_colleges_faculty = sorted(
                colleges,
                key=lambda x: x[1]["ownership_ratio_difference_from_avg"],
                reverse=True,
            )

            for k, v in sorted_colleges_faculty:
                ratio = v["ownership_ratio_difference_from_avg"]
                if abs(ratio) > 0.001:  # Skip individual entries with 0.00%
                    college_name = ClassProfileAiInsightHelper._get_college_name(
                        v["college_id"], data["college_details"]
                    )
                    ownership_display = ClassProfileAiInsightHelper._get_ownership_display(
                        v["college_id"], data["college_details"]
                    )
                    ratio_text = (
                        f"lower by {abs(ratio):.2f}%"
                        if ratio < 0
                        else f"higher by {ratio:.2f}%"
                    )
                    sorted_insights["student_faculty_sorted"].append(
                        f"{college_name} ({ownership_display}) shows a faculty-student ratio {ratio_text} than the average"
                    )

        # Sort and process gender diversity
        colleges = [
            (k, v)
            for k, v in data["data"]["gender_diversity"].items()
            if k.startswith("college_") and v["data_status"] == "complete"
        ]

        metrics_map = {
            "gender_diversity_sorted": "type_of_institute_gender_diversity_difference_from_avg",
            "ownership_gender_diversity_sorted": "ownership_gender_diversity_difference",
        }

        for metric, sort_key in metrics_map.items():
            if any(abs(college[1][sort_key]) > 0.001 for college in colleges):
                sorted_colleges_gender = sorted(
                    colleges, key=lambda x: x[1][sort_key], reverse=True
                )
                for k, v in sorted_colleges_gender:
                    diff = v[sort_key]
                    if abs(diff) > 0.001:  # Skip individual entries with 0.00%
                        college_name = ClassProfileAiInsightHelper._get_college_name(
                            v["college_id"], data["college_details"]
                        )
                        if metric == "gender_diversity_sorted":
                            college_type = next(
                                (
                                    c["type_of_institute"]
                                    for c in data["college_details"]
                                    if str(c["id"]) == str(v["college_id"])
                                ),
                                "Unknown",
                            )
                            sorted_insights[metric].append(
                                f"{college_name} ({college_type}) demonstrates a gender diversity metric {abs(diff):.2f}% "
                                f"{'below' if diff < 0 else 'above'} the average"
                            )
                        else:
                            ownership = ClassProfileAiInsightHelper._get_ownership_display(
                                v["college_id"], data["college_details"]
                            )
                            diff_text = (
                                f"trails by {abs(diff):.2f}%"
                                if diff < 0
                                else f"leads by {diff:.2f}%"
                            )
                            sorted_insights[metric].append(
                                f"{college_name} ({ownership}) {diff_text} in ownership gender diversity metrics"
                            )

        return sorted_insights

    @staticmethod
    def get_cache_key(data: Dict) -> str:
        """Generate a unique cache key based on the input profile data."""
        data_str = json.dumps(data, sort_keys=True)
        return f"class_profile_ai_insights__{hashlib.md5(data_str.encode()).hexdigest()}"

    @staticmethod
    def get_profile_insights(data: Dict) -> Optional[Dict]:
        """Generate and process profile insights with caching."""
        try:
            cache_key = ClassProfileAiInsightHelper.get_cache_key(data)
            cached_result = ClassProfileAiInsightHelper._cache.get(cache_key)

            if cached_result:
                print("Returning cached profile insights.")
                return cached_result["insights"]

            print("Generating new profile insights.")
            sorted_insights = ClassProfileAiInsightHelper._create_sorted_insights(data)

            # Only include keys that have non-empty insights
            formatted_insights = {}

            insight_mapping = {
                "student_faculty_sorted": "student_faculty_ownership_ratio_difference_from_avg",
                "gender_diversity_sorted": "type_of_institute_gender_diversity_difference_from_avg",
                "ownership_gender_diversity_sorted": "ownership_gender_diversity_difference",
            }

            for sort_key, insight_key in insight_mapping.items():
                if sorted_insights[sort_key]:  # Only add if there are insights
                    formatted_insights[insight_key] = ". ".join(
                        sorted_insights[sort_key]
                    )

            ClassProfileAiInsightHelper._cache[cache_key] = {
                "insights": formatted_insights,
                "timestamp": time.time(),
            }
            return formatted_insights
        except Exception as e:
            print(f"Error in get_profile_insights: {e}")
            return None

    @staticmethod
    def format_percentage(value: float) -> str:
        """Format percentage values consistently."""
        try:
            return f"{float(value):.2f}%" if value is not None else "NA"
        except (ValueError, TypeError):
            return "NA"

    @staticmethod
    def format_ratio(value: float) -> str:
        """Format ratio values consistently."""
        try:
            return f"{float(value):.2f}" if value is not None else "NA"
        except (ValueError, TypeError):
            return "NA"





class CollegeReviewsHelper:
    """
    A comprehensive helper class for analyzing college reviews using an HTTP API and caching.
    This class combines numerical ratings with AI-generated insights from review text.
    """
    
    def __init__(self, api_url: Optional[str] = None):
        """
        Initialize the API configuration.
        
        Args:
            api_url (Optional[str]): Custom API URL. If None, uses environment variable.
        """
        self.api_url = api_url or os.getenv(
            'COLLEGE_REVIEWS_API_URL', 
            'https://akrfvz7sje.execute-api.ap-south-1.amazonaws.com/DEV/college-compare-summary'
        )
        
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
        Generate AI-powered summary and insights from review text using HTTP API.
        
        Args:
            review_text (str): Combined review text to analyze
            college_name (str): Name of the college for summary personalization
            
        Returns:
            Optional[Dict]: Dictionary containing attributes and summary, or None if processing fails
        """
        if not review_text.strip():
            return None
            
        try:
            # Prepare the API request
            headers = {
                'Content-Type': 'application/json'
            }
            
            payload = {
                'review_text': review_text.strip(),
                'college_name': college_name  
            }
            
            # Make the API call
            response = requests.get(
                self.api_url,
                headers=headers,
                data=json.dumps(payload)
            )
            
            # Handle the response
            if response.status_code == 200:
                response_json = response.json()
                response_body = json.loads(response_json['body'])
                
                # Return the processed response
                return {
                    'most_discussed_attributes': response_body.get('most_discussed_attributes', []),
                    'short_summary': response_body.get('short_summary', '')
                }
               
            else:
                logger.error(f"API request failed with status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None
        
    def _create_summary_cached(self, review_text: str, college_name: str) -> Optional[Dict]:
        """Cached version of _create_summary."""
        cache_key = self.get_cache_key("api_summary_new", review_text, college_name)
        summary = cache.get(cache_key)
        if summary is None:
            summary = self._create_summary(review_text, college_name)
            cache.set(cache_key, summary, 3600 * 12)  # Cache for 12 hours
        return summary

    def get_college_reviews_summary(self, college_ids: List[int], course_ids: Optional[List[int]] = None, grad_year: int = None) -> Dict:
        """
        Get comprehensive review summary including ratings and AI-generated insights.
        
        Args:
            college_ids (List[int]): List of college IDs to analyze
            course_ids (Optional[List[int]]): List of course IDs to filter reviews by
            grad_year (int): Graduation year to filter reviews
            
        Returns:
            Dict: Combined ratings and insights for each college
        """
        # Flatten nested lists if any
        college_ids = [item for sublist in college_ids for item in (sublist if isinstance(sublist, list) else [sublist])]
        
        if course_ids:
            course_ids = [item for sublist in course_ids for item in (sublist if isinstance(sublist, list) else [sublist])]
        
        # Generate cache key
        cache_key = self.get_cache_key(
            'College_Reviews_Summary_new___',
            '-'.join(map(str, sorted(college_ids))),
            '-'.join(map(str, sorted(course_ids or []))),
            grad_year
        )

        def fetch_summary():
            try:
                filters = {
                    'college_id__in': college_ids,
                    'status': True
                }

                if grad_year:
                    filters['graduation_year__year'] = grad_year
                if course_ids:
                    filters['college_course_id__in'] = course_ids 

                ratings = (
                    CollegeReviews.objects.filter(**filters)
                    .select_related('college')
                    .values('college_id', 'college__name','college__short_name')
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

                reviews = (
                    CollegeReviews.objects.filter(**filters)
                    .values('college_id', 'college_course_id', 'title', 'campus_life', 'college_infra', 
                            'academics', 'placements', 'value_for_money')
                )

                result_dict = {}
                for index, college_id in enumerate(college_ids, start=1):
                    college_reviews = [r for r in reviews if r['college_id'] == college_id]
                    college_name = next((r['college__name'] for r in ratings if r['college_id'] == college_id), "The college")

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

                    if review_texts:
                        full_text = ' '.join(review_texts)
                        insights = self._create_summary_cached(full_text, college_name) or {'most_discussed_attributes': [], 'short_summary': ''}
                    else:
                        insights = {
                            'most_discussed_attributes': [],
                            'short_summary': '',
                            'status': 'No review text available'
                        }

                    college_ratings = next((r for r in ratings if r['college_id'] == college_id), None)
                    result_dict[f"college_{index}"] = {
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

                if not result_dict:
                    raise NoDataAvailableError("No reviews or ratings data available for the given college IDs.")

                return result_dict

            except NoDataAvailableError as e:
                logger.warning(str(e))
                return {'error': str(e)}
            except Exception as e:
                logger.error(f"Error fetching reviews summary: {e}")
                raise

      
        return cache.get_or_set(cache_key, fetch_summary, 3600 * 24 * 7)
    @staticmethod
    def get_entity_type_display(type_of_entity: int) -> str:
        """
        Convert entity type integer to its display string.
        
        Args:
            type_of_entity (int): Integer value from ENTITY_TYPE_CHOICES
            
        Returns:
            str: Display string for the entity type
        """
     
        entity_types = {
            1: 'university',
            2: 'college',
            3: 'Hospital',
            4: 'Instructor',
            5:'Organization',
          
        }
        return entity_types.get(type_of_entity, 'college')  # Default to 'college' if not found

    @staticmethod
    def get_recent_reviews(college_ids: List[int], course_ids: Optional[List[int]] = None, limit: int = 3) -> Dict:
        """
        Get recent reviews for colleges with caching.

        Args:
            college_ids (List[int]): List of college IDs to filter
            course_ids (Optional[List[int]]): List of course IDs to filter reviews by
            limit (int, optional): Maximum number of reviews per college. Defaults to 3.

        Returns:
            Dict: Recent reviews for each college, including reviews page URL
        """
    
        college_ids = [item for sublist in college_ids for item in (sublist if isinstance(sublist, list) else [sublist])]
        
        if course_ids:
            course_ids = [item for sublist in course_ids for item in (sublist if isinstance(sublist, list) else [sublist])]
        
        cache_key = CollegeReviewsHelper.get_cache_key(
            'recent_reviews',
            '-'.join(map(str, sorted(college_ids))),
            '-'.join(map(str, sorted(course_ids or []))),
            limit
        )

        def fetch_recent():
            try:
                # Get college information first
                colleges = (
                    College.objects.filter(id__in=college_ids)
                    .values('id', 'name', 'type_of_entity')
                )
                
                # Create a mapping of college_id to URL-friendly names
                college_urls = {}
                for college in colleges:
                    # Convert the integer type_of_entity to its string representation
                    entity_type = CollegeReviewsHelper.get_entity_type_display(college['type_of_entity'])
                    
                    # Create the URL with proper formatting

                    clean_name = college['name'].lower().replace(',', '').replace(' ', '-')
                    
                    # Create the URL with proper formatting and single quotes
                    college_urls[college['id']] = {
                        'reviews_page': f'https://www.careers360.com/{entity_type.lower()}/{clean_name}/reviews'
                    }

                    

                filters = {
                    'college_id__in': college_ids,
                    'title__isnull': False
                }

                if course_ids:
                    filters['college_course_id__in'] = course_ids  

                results = (
                    CollegeReviews.objects.filter(**filters)
                    .select_related('user')
                    .values(
                        'college_id',
                        'college_course_id',
                        'title',
                        'user__display_name',
                        rating=Round(F('overall_rating') / 20, 1),
                        review_date=TruncDate('created')
                    )
                    .order_by('college_id', '-created')
                )

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

                result_dict = {}
                for i, college_id in enumerate(college_ids, 1):
                    key = f"college_{i}"
                    result_dict[key] = {
                        'reviews': reviews_by_college.get(college_id, []),
                        'reviews_page': college_urls.get(college_id, {}).get('reviews_page', '')
                    }
                   

                return result_dict

            except Exception as e:
                logger.error(f"Error fetching recent reviews: {e}")
                raise

        return cache.get_or_set(cache_key, fetch_recent, 3600*24*7)









class CollegeReviewAiInsightHelper:
    """Helper class for generating and formatting college review insights."""
    
    @staticmethod
    def get_cache_key(reviews_data: Dict) -> str:
        """Generate a unique cache key based on the input reviews data."""
        data_str = json.dumps(reviews_data, sort_keys=True)
        return f"college_review_ai_insights__{hash(data_str)}"

    @staticmethod
    def analyze_reviews(reviews_data: Dict) -> Dict:
        """
        Analyze college reviews and generate insights based on ratings and attributes.

        Args:
            reviews_data: Dictionary containing college reviews and ratings.

        Returns:
            A dictionary containing insights about the colleges.
        """
        insights = {
            "highest_rated_aspects": {},
            "improvement_areas": {},
            "most_discussed_attributes": {}
        }

        # Mapping of full attribute names to their keys
        attribute_mapping = {
            "infra": "infrastructure",
            "campus_life": "campus life",
            "value_for_money": "value for money",
            "placement": "placement",
            "faculty": "faculty",
            "academics": "academics"
        }

        for college_key, college_info in reviews_data.items():

            college_name = college_info.get("college__short_name") or college_info.get("college__name")
            if not college_name:
                continue 
            
            ratings = {
                "infra": college_info.get("infra_rating"),
                "campus_life": college_info.get("campus_life_ratings"),
                "academics": college_info.get("academics_ratings"),
                "value_for_money": college_info.get("value_for_money_ratings"),
                "placement": college_info.get("placement_rating"),
                "faculty": college_info.get("faculty_rating")
            }

            # Analyze highest rated aspects
            highest_rated = {aspect: rating for aspect, rating in ratings.items() if rating is not None and rating >= 4.0}
            insights["highest_rated_aspects"][college_name] = highest_rated

            # Analyze improvement areas
            low_rated = {aspect: rating for aspect, rating in ratings.items() if rating is not None and rating < 4.0}
            if low_rated:
                insights["improvement_areas"][college_name] = low_rated

            # Most discussed attributes
            insights["most_discussed_attributes"][college_name] = college_info.get("most_discussed_attributes", [])

        return insights

    @staticmethod
    def format_reviews_insights(insights: Dict) -> Dict:
        """
        Format the insights into a structured format.

        Args:
            insights (Dict): Insights generated from the reviews.

        Returns:
            Dict: Formatted insights as a dictionary.
        """
        formatted_insights = {
            "highest_rated_aspects": "",
            "improvement_areas": "",
            "most_discussed_attributes": ""
        }

        attribute_mapping = {
            "infra": "infrastructure",
            "campus_life": "campus life",
            "value_for_money": "value for money",
            "placement": "placement",
            "faculty": "faculty",
            "academics": "academics"
        }

        # Format highest rated aspects

        for college_name, aspects in insights["highest_rated_aspects"].items():
            formatted_aspects = ", ".join(f"{attribute_mapping[aspect]} ({rating})" for aspect, rating in aspects.items())
            formatted_insights["highest_rated_aspects"] += f"{college_name} stands out with its exceptional {formatted_aspects}. "
                
        # Format improvement areas, skipping if none exist

        if insights["improvement_areas"]:
            formatted_insights["improvement_areas"] = ""
            for college_name, areas in insights["improvement_areas"].items():
                formatted_areas = ", ".join(f"{attribute_mapping[aspect]} ({rating})" for aspect, rating in areas.items())
                formatted_insights["improvement_areas"] += f"{college_name} could potentially enhance its {formatted_areas}. "
            formatted_insights["improvement_areas"] += " Offering more scholarships, financial aid, and strengthening industry partnerships could help address these aspects."
        else:
            formatted_insights["improvement_areas"] = ""
            

        # Format most discussed attributes
        formatted_attributes = []
        for college_name, attributes in insights["most_discussed_attributes"].items():
            formatted_attributes.append(f"{college_name}: {', '.join(attributes)}")
        formatted_insights["most_discussed_attributes"] = f"Students frequently discuss the following attributes: {', '.join(formatted_attributes)}. These attributes directly impact the overall educational experience, career prospects, and campus environment, making them crucial areas of focus for prospective students and the institutions themselves."

        # Remove empty keys
        formatted_insights = {key: value for key, value in formatted_insights.items() if value}

        return formatted_insights

    @staticmethod
    def get_reviews_insights(reviews_data: Dict) -> Optional[Dict]:
        """
        Generate and process review insights with caching.
        
        Args:
            reviews_data (Dict): Dictionary containing college reviews and ratings
            
        Returns:
            Optional[Dict]: Processed review insights or None if there's an error
        """
        try:
            cache_key = CollegeReviewAiInsightHelper.get_cache_key(reviews_data)
            cached_result = cache.get(cache_key)

            if cached_result:
                logger.info("Returning cached review insights.")
                return cached_result

            logger.info("Generating new review insights.")
            insights = CollegeReviewAiInsightHelper.analyze_reviews(reviews_data)
            formatted_insights = CollegeReviewAiInsightHelper.format_reviews_insights(insights)

            cache.set(cache_key, formatted_insights, timeout=3600 * 24 * 7)  # Cache for 7 days
            
            return formatted_insights
            
        except Exception as e:
            logger.error(f"Error in get_reviews_insights: {str(e)}")
            return None





class CollegeReviewsRatingGraphHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        """
        Generate a consistent cache key from variable arguments.
        """
        key = '_'.join(map(str, args))
        return hashlib.md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_rating_data(college_ids: List[int], grad_year: int) -> Dict:
        """
        Fetch and process college rating data with classifications, maintaining input order.
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
                "college_infrastructure",
                "campus_life",
                "academics",
                "value_for_money",
                "placement"
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
                    college_infrastructure=Coalesce(Round(Avg(F('infra_rating') / 20), 1), Value(0.0)),
                    campus_life=Coalesce(Round(Avg(F('college_life_rating') / 20), 1), Value(0.0)),
                    academics=Coalesce(Round(Avg(F('overall_rating') / 20), 1), Value(0.0)),
                    value_for_money=Coalesce(Round(Avg(F('affordability_rating') / 20), 1), Value(0.0)),
                    placement=Coalesce(Round(Avg(F('placement_rating') / 20), 1), Value(0.0))
                )
            )

            ratings_dict = {rating['college_id']: rating for rating in ratings}

            all_colleges = College.objects.filter(id__in=college_ids).values('id', 'name')
            college_names_dict = {college['id']: college['name'] for college in all_colleges}

            result_dict = {
                "rating_type": rating_type,
                "year_tag": grad_year,
                "data": {
                    "rating": {"type": "radar", "values": {}},
                    "classification": {"type": "horizontal bar", "values": {}}
                },
                "college_names": []
            }

            for idx, college_id in enumerate(college_ids, 1):
                college_key = f"college_{idx}"
                college_name = college_names_dict.get(college_id, "Unknown")
                rating_data = ratings_dict.get(college_id, None)

                if rating_data:
                    result_dict["data"]["rating"]["values"][college_key] = {
                        "college_id": college_id,
                        "college_name": college_name,
                        **{param: rating_data[param] for param in rating_type}
                    }

                    result_dict["data"]["classification"]["values"][college_key] = {
                        "college_id": college_id,
                        "college_name": college_name,
                        "V.Good": sum(1 for param in rating_type if rating_data[param] > 4),
                        "Good": sum(1 for param in rating_type if 3 <= rating_data[param] <= 4),
                        "Avg": sum(1 for param in rating_type if rating_data[param] < 3)
                    }
                else:
                    result_dict["data"]["rating"]["type"] = "tabular"
                    result_dict["data"]["rating"]["values"][college_key] = {
                        "college_id": college_id,
                        "college_name": college_name,
                        **{param: "NA" for param in rating_type}
                    }

                    result_dict["data"]["classification"]["values"][college_key] = {
                        "college_id": college_id,
                        "college_name": college_name,
                        "V.Good": "NA",
                        "Good": "NA",
                        "Avg": "NA"
                    }

                result_dict["college_names"].append(college_name)

            return result_dict

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 7)

    @staticmethod
    def prepare_rating_insights(college_ids: List[int], grad_year: int) -> Dict:
        """
        Prepare rating insights for a given list of colleges and graduation year.
        Args:
            college_ids: List of college IDs to analyze; order will be preserved.
            grad_year: Graduation year to filter reviews.
        
        Returns:
            Dictionary containing complete rating insights and classifications.
        """
        return CollegeReviewsRatingGraphHelper.fetch_rating_data(college_ids, grad_year)




# class ExamCutoffHelper:
#     @staticmethod
#     def get_cache_key(*args) -> str:
#         """Generate a cache key using MD5 hashing."""
#         key = "1111_887777____________111".join(map(str, args))
#         return md5(key.encode()).hexdigest()

#     @staticmethod
#     def get_exam_cutoff(course_ids, exam_id=None, counseling_id=None, category_id=None):
#         if not course_ids:
#             raise ValueError("course_ids must be provided.")

#         cache_key = ExamCutoffHelper.get_cache_key(
#             course_ids, exam_id, counseling_id, category_id, 
#         )
#         cached_data = cache.get(cache_key)

#         if cached_data:
#             return cached_data

#         # MaxYearRef CTE
#         max_year_ref = (
#             CutoffData.objects.filter(college_course_id__in=course_ids)
#             .values("year")
#             .order_by("-year")
#             .first()
#         )

#         print(max_year_ref)

#         if not max_year_ref:
#             raise NoDataAvailableError("No exam & cutoff data available for the provided Course's.")


#         filtered_cutoff = (
#             CutoffData.objects.filter(
#                 college_course_id__in=course_ids, year=max_year_ref["year"]
#             )
#             .values("exam_sub_exam_id", "counselling_id", "college_course_id", "year")
#             .distinct()
#         )

#         filtered_campaign = (
#             CpProductCampaignItems.objects.filter(product__published="published")
#             .values("exam_id", "counselling_id")
#             .distinct()
#         )

#         max_rounds = (
#             CutoffData.objects.filter(
#                 college_course_id__in=course_ids, year=max_year_ref["year"]
#             )
#             .values("exam_sub_exam_id", "counselling_id", "college_course_id", "caste_id")
#             .annotate(
#                 priority_caste_id=Case(
#                     When(caste_id=5, then=Value(5)),  # ST
#                     When(caste_id=4, then=Value(4)),  # SC
#                     When(caste_id=3, then=Value(3)),  # OBC
#                     When(caste_id=2, then=Value(2)),  # General
#                     default=Value(2),  # Others
#                     output_field=IntegerField(),
#                 )
#             )
#             .order_by(
#                 "exam_sub_exam_id", "counselling_id", "college_course_id", "priority_caste_id"
#             )
#             .distinct()
#             .annotate(total_counseling_rounds=Max("round"))
#         )

#         # Base cutoffs with lowest closing rank
#         base_cutoffs = (
#             CutoffData.objects.filter(
#                 college_course_id__in=course_ids,
#                 year=max_year_ref["year"],
#                 exam_sub_exam_id__in=filtered_cutoff.values("exam_sub_exam_id"),
#                 counselling_id__in=filtered_campaign.values("counselling_id"),
#             )
#             .values(
#                 "exam_sub_exam_id",
#                 "counselling_id",
#                 "college_course_id",
#                 "college_id",
#                 "category_of_admission_id",
#             )
#             .annotate(
#                 round_wise_opening_cutoff=Coalesce(
#                     Min("round_wise_opening_cutoff"), Value("NA"), output_field=CharField()
#                 ),
#                 # Prioritize lowest caste_id (2) for final_cutoff
#                 final_cutoff=Coalesce(
#                     Subquery(
#                         CutoffData.objects.filter(
#                             year=OuterRef("year"),
#                             college_course_id=OuterRef("college_course_id"),
#                             exam_sub_exam_id=OuterRef("exam_sub_exam_id"),
#                             counselling_id=OuterRef("counselling_id"),
#                             final_cutoff__isnull=False,
#                         )
#                         .annotate(
#                             priority_caste_id=Case(
#                                 When(caste_id=5, then=Value(5)),  # ST
#                                 When(caste_id=4, then=Value(4)),  # SC
#                                 When(caste_id=3, then=Value(3)),  # OBC
#                                 When(caste_id=2, then=Value(2)),  # General
#                                 default=Value(2),  # Others
#                                 output_field=IntegerField(),
#                             )
#                         )
#                         .order_by("priority_caste_id", "final_cutoff")
#                         .values("final_cutoff")[:1]
#                     ),
#                     Value("NA"),
#                     output_field=CharField(),
#                 ),
#                 lowest_closing_rank=Coalesce(
#                     Subquery(
#                         CutoffData.objects.filter(
#                             year=OuterRef("year"),
#                             college_course_id=OuterRef("college_course_id"),
#                             exam_sub_exam_id=OuterRef("exam_sub_exam_id"),
#                             counselling_id=OuterRef("counselling_id"),
#                             final_cutoff__isnull=False,
#                         )
#                         .annotate(
#                             priority_caste_id=Case(
#                                 When(caste_id=5, then=Value(1)),  # ST
#                                 When(caste_id=4, then=Value(2)),  # SC
#                                 When(caste_id=3, then=Value(3)),  # OBC
#                                 When(caste_id=2, then=Value(4)),  # General
#                                 default=Value(5),  # Others
#                                 output_field=IntegerField(),
#                             )
#                         )
#                         .order_by(
#                             "priority_caste_id",
#                             "final_cutoff",
#                         )
#                         .values("final_cutoff")[:1]
#                     ),
#                     Value("NA"),
#                     output_field=CharField(),
#                 ),
#                 total_counseling_rounds=Subquery(

#                     max_rounds.filter(

#                         exam_sub_exam_id=OuterRef("exam_sub_exam_id"),
#                         counselling_id=OuterRef("counselling_id"),
#                         college_course_id=OuterRef("college_course_id"),
#                     )
#                     .values("total_counseling_rounds")[:1]
#                 ),
#                 caste_id=Coalesce(
#                     Subquery(
#                         CutoffData.objects.filter(
#                             year=OuterRef("year"),
#                             college_course_id=OuterRef("college_course_id"),
#                             exam_sub_exam_id=OuterRef("exam_sub_exam_id"),
#                             counselling_id=OuterRef("counselling_id"),
#                             final_cutoff__isnull=False,
#                         )
#                         .annotate(
#                             priority_caste_id=Case(
#                                 When(caste_id=5, then=Value(1)),  # ST
#                                 When(caste_id=4, then=Value(2)),  # SC
#                                 When(caste_id=3, then=Value(3)),  # OBC
#                                 When(caste_id=2, then=Value(4)),  # General
#                                 default=Value(2),  # Others
#                                 output_field=IntegerField(),
#                             )
#                         )
#                         .order_by(
#                             "priority_caste_id",
#                             "final_cutoff",
#                         )
#                         .values("caste_id")[:1]
#                     ),
#                     Value(None),
#                     output_field=IntegerField(),
#                 ),
#                  lowest_rank_caste_id=Coalesce(
#                     Subquery(
#                         CutoffData.objects.filter(
#                             year=OuterRef("year"),
#                             college_course_id=OuterRef("college_course_id"),
#                             exam_sub_exam_id=OuterRef("exam_sub_exam_id"),
#                             counselling_id=OuterRef("counselling_id"),
#                             final_cutoff__isnull=False,
#                         )
#                         .annotate(
#                             priority_caste_id=Case(
#                                 When(caste_id=5, then=Value(1)),  # ST
#                                 When(caste_id=4, then=Value(2)),  # SC
#                                 When(caste_id=3, then=Value(3)),  # OBC
#                                 When(caste_id=2, then=Value(4)),  # General
#                                 default=Value(5),  # Others
#                                 output_field=IntegerField(),
#                             )
#                         )
#                         .order_by(
#                             "priority_caste_id",
#                             "final_cutoff",
#                         )
#                         .values("caste_id")[:1]
#                     ),
#                     Value(None),
#                     output_field=IntegerField(),
#                 ),
#             )
#             .distinct()
#         )

#         # Lowest ranks with selected caste id
#         lowest_ranks = (
#             CutoffData.objects.filter(
#                 year=max_year_ref["year"],
#                 college_course_id__in=course_ids,
#                 final_cutoff__isnull=False,
#             )
#             .filter(
#                 Q(exam_sub_exam_id__in=filtered_campaign.values("exam_id"))
#                 | Q(counselling_id__in=filtered_campaign.values("counselling_id"))
#             )
#             .values("exam_sub_exam_id", "counselling_id", "college_course_id")
#             .annotate(
#                 selected_caste_id=Subquery(
#                     CutoffData.objects.filter(
#                         year=max_year_ref["year"],
#                         college_course_id=OuterRef("college_course_id"),
#                         final_cutoff__isnull=False,
#                     )
#                     .annotate(
#                         priority_caste_id=Case(
#                             When(caste_id=5, then=Value(1)),  # ST
#                             When(caste_id=4, then=Value(2)),  # SC
#                             When(caste_id=3, then=Value(3)),  # OBC
#                             When(caste_id=2, then=Value(4)),  # General
#                             default=Value(5),  # Others
#                             output_field=IntegerField(),
#                         )
#                     )
#                     .order_by(
#                         "priority_caste_id",  # Higher priority caste
#                         "final_cutoff",  # Lowest final cutoff
#                     )
#                     .values("caste_id")[:1]
#                 ),
#             )
#         )

#         result = Course.objects.filter(id__in=course_ids)

#         result = result.annotate(
#             exam_id=Subquery(
#                 CutoffData.objects.filter(college_course_id=OuterRef("id"))
#                 .values("exam_sub_exam__id")[:1]
#             ),
#             exam_sub_exam_id_ann=Subquery(
#                 CutoffData.objects.filter(college_course_id=OuterRef("id"))
#                 .values("exam_sub_exam_id")[:1]
#             ),
#             counselling_id_ann=Subquery(
#                 CutoffData.objects.filter(college_course_id=OuterRef("id"))
#                 .values("counselling_id")[:1]
#             ),
#             exam_name=Coalesce(
#                 Subquery(
#                     Exam.objects.filter(id=OuterRef("exam_sub_exam_id_ann"))
#                     .annotate(
#                         display_name=Case(
#                             When(
#                                 exam_short_name__isnull=False,
#                                 exam_short_name__gt="",
#                                 then=F("exam_short_name"),
#                             ),
#                             When(
#                                 parent_exam_id__isnull=False,
#                                 then=Concat(
#                                     "parent_exam__exam_short_name",
#                                     Value(" ("),
#                                     F("exam_name"),
#                                     Value(")"),
#                                 ),
#                             ),
#                             default=F("exam_name"),
#                             output_field=CharField(),
#                         )
#                     )
#                     .values("display_name")[:1]
#                 ),
#                 Value("NA"),
#                 output_field=CharField(),
#             ),
#             counseling_name=Coalesce(
#                 Subquery(
#                     Exam.objects.filter(id=OuterRef("counselling_id_ann")).values(
#                         "exam_name"
#                     )[:1]
#                 ),
#                 Value("NA"),
#                 output_field=CharField(),
#             ),
#         )

#         result = result.annotate(
#             exam_and_counseling=Case(
#                 When(
#                     ~Q(exam_name="NA") & ~Q(counseling_name="NA"),
#                     then=Concat(
#                         F("exam_name"), Value(" ("), F("counseling_name"), Value(")")
#                     ),
#                 ),
#                 default=Value("NA"),
#                 output_field=CharField(),
#             )
#         )

#         # result = result.annotate(
#         #     min_opening_cutoff=Coalesce(
#         #         Subquery(
#         #             base_cutoffs.filter(college_course_id=OuterRef("id"),category_of_admission__id=OuterRef("category_of_admission_id"))
#         #             .values("round_wise_opening_cutoff")[:1]
#         #         ),
#         #         Value("NA"),
#         #         output_field=CharField(),
#         #     ),
#         #     lowest_closest_rank=Coalesce(
#         #         Subquery(
#         #             base_cutoffs.filter(college_course_id=OuterRef("id"),category_of_admission__id=OuterRef("category_of_admission_id"))
#         #             .values("lowest_closing_rank")[:1]
#         #         ),
#         #         Value("NA"),
#         #         output_field=CharField(),
#         #     ),
#         #     min_closing_cutoff=Coalesce(
#         #         Subquery(
#         #             base_cutoffs.filter(college_course_id=OuterRef("id"),category_of_admission__id=OuterRef("category_of_admission_id"))
#         #             .values("final_cutoff")[:1]
#         #         ),
#         #         Value("NA"),
#         #         output_field=CharField(),
#         #     ),
#         #     caste_id=Coalesce(
#         #         NullIf(
#         #             Subquery(
#         #                 base_cutoffs.filter(college_course_id=OuterRef("id"))
#         #                 .values("caste_id")[:1]
#         #             ),
#         #             Value(""),  # Converts empty strings to NULL
#         #         ),
#         #         Value(None),
#         #         output_field=IntegerField(),
#         #     ),
#         #     lowest_rank_caste_id=Coalesce(
#         #         NullIf(
#         #             Subquery(
#         #                 lowest_ranks.filter(college_course_id=OuterRef("id"))
#         #                 .values("selected_caste_id")[:1]
#         #             ),
#         #             Value(""),  # Converts empty strings to NULL
#         #         ),
#         #         Value(None),
#         #         output_field=IntegerField(),
#         #     ),
#         #     total_counseling_rounds=Coalesce(
#         #         NullIf(
#         #             Subquery(
#         #                 max_rounds.filter(
#         #                     exam_sub_exam_id=OuterRef("exam_sub_exam_id_ann"),
#         #                     counselling_id=OuterRef("counselling_id_ann"),
#         #                     college_course_id=OuterRef("id"),
#         #                 )
#         #                 .values("total_counseling_rounds")[:1]
#         #             ),
#         #             Value(""),  # Converts empty strings to NULL
#         #         ),
#         #         Value(0),
#         #         output_field=IntegerField(),
#         #     ),
#         # )

#         result =result.annotate(
#                 min_opening_cutoff=Coalesce(
#                     Subquery(
#                         base_cutoffs.filter(
#                             college_course_id=OuterRef("id")
#                         )
#                         .values("round_wise_opening_cutoff")[:1]
#                     ),
#                     Value("NA"),
#                     output_field=CharField(),
#                 ),
#                 lowest_closest_rank=Coalesce(
#                     Subquery(
#                         base_cutoffs.filter(
#                             college_course_id=OuterRef("id")
#                         )
#                         .values("lowest_closing_rank")[:1]
#                     ),
#                     Value("NA"),
#                     output_field=CharField(),
#                 ),
#                 min_closing_cutoff=Coalesce(
#                     Subquery(
#                         base_cutoffs.filter(
#                             college_course_id=OuterRef("id")
#                         )
#                         .values("final_cutoff")[:1]
#                     ),
#                     Value("NA"),
#                     output_field=CharField(),
#                 ),
#                 caste_id=Coalesce(
#                     NullIf(
#                         Subquery(
#                             base_cutoffs.filter(college_course_id=OuterRef("id"))
#                             .values("caste_id")[:1]
#                         ),
#                         Value(""),  # Converts empty strings to NULL
#                     ),
#                     Value(None),
#                     output_field=IntegerField(),
#                 ),
#                 lowest_rank_caste_id=Coalesce(
#                     NullIf(
#                         Subquery(
#                             lowest_ranks.filter(college_course_id=OuterRef("id"))
#                             .values("selected_caste_id")[:1]
#                         ),
#                         Value(""),  # Converts empty strings to NULL
#                     ),
#                     Value(None),
#                     output_field=IntegerField(),
#                 ),
#                 total_counseling_rounds=Coalesce(
#                     NullIf(
#                         Subquery(
#                             max_rounds.filter(
#                                 exam_sub_exam_id=OuterRef("exam_sub_exam_id_ann"),
#                                 counselling_id=OuterRef("counselling_id_ann"),
#                                 college_course_id=OuterRef("id"),
#                             )
#                             .values("total_counseling_rounds")[:1]
#                         ),
#                         Value(""),  # Converts empty strings to NULL
#                     ),
#                     Value(0),
#                     output_field=IntegerField(),
#                 ),
#             )

#         result = result.annotate(
#             caste_name=Case(
#                 When(caste_id=2, then=Value("General")),
#                 When(caste_id=3, then=Value("OBC")),
#                 When(caste_id=4, then=Value("SC")),
#                 When(caste_id=5, then=Value("ST")),
#                 default=Value("NA"),
#                 output_field=CharField(),
#             ),
#             category_of_admission_id=Coalesce(
#                 Subquery(
#                     base_cutoffs.filter(college_course_id=OuterRef("id")).values(
#                         "category_of_admission_id"
#                     )[:1]
#                 ),
#                 Value("NA"),
#                 output_field=CharField(),
#             ),
#             exam_education_level=Coalesce(
#                 Subquery(
#                     Exam.objects.filter(id=OuterRef("exam_sub_exam_id_ann")).values(
#                         "preferred_education_level_id"
#                     )[:1]
#                 ),
#                 Value(1),
#                 output_field=IntegerField(),
#             ),
#         )

#         result = result.order_by(
#             Case( When(exam_education_level__in=[14, 15, 16, 18], then=Value(2)),
#                 default=Value(1),
#                 output_field=IntegerField(),
#             ),
#             "exam_sub_exam_id_ann",
#             "counselling_id_ann",
#             "id",
#         ).distinct()

#         if exam_id:
#             result = result.filter(exam_sub_exam_id_ann=exam_id)
#         if counseling_id:
#             result = result.filter(counselling_id_ann=counseling_id)
#         if category_id:
#             result = result.filter(category_of_admission_id=category_id)

#         def get_na_safe(value):
#             """Safely handles null/None values by converting them to 'NA' string"""
#             return "NA" if value is None else value

#         def get_caste_name(caste_id):
#             """Converts caste ID to corresponding caste name"""
#             caste_map = {2: "General", 3: "OBC", 4: "SC", 5: "ST"}
#             return caste_map.get(caste_id, "NA")

#         serialized_data = []
#         for course in result:
#             lowest_rank_string = (
#                 f"{course.lowest_closest_rank} ({get_caste_name(course.lowest_rank_caste_id)})"
#                 if get_na_safe(course.lowest_closest_rank) != "NA"
#                 else "NA"
#             )

#             # Safely convert category_of_admission_id to int
#             if course.category_of_admission_id == 'NA' or course.category_of_admission_id in [None, '']:
#                 category_of_admission_id = 'NA'
#             else:
#                 try:
#                     category_of_admission_id = int(course.category_of_admission_id)
#                 except (ValueError, TypeError):
#                     category_of_admission_id = 'NA'

#             category_of_admission = (
#                 "All India" if category_of_admission_id == 1
#                 else "Outside Home state" if category_of_admission_id == 2
#                 else "Home state" if category_of_admission_id == 3
#                 else "NA"
#             ) if category_of_admission_id != 'NA' else 'NA'

#             serialized_data.append({
#                 "id": get_na_safe(course.id),
#                 "exam_id": get_na_safe(course.exam_id),
#                 "counselling_id": get_na_safe(course.counselling_id_ann),
#                 "exam_and_counseling": get_na_safe(course.exam_and_counseling),
#                 "min_opening_cutoff": get_na_safe(course.min_opening_cutoff),
#                 "min_closing_cutoff": get_na_safe(course.min_closing_cutoff),
#                 "caste_name": get_na_safe(course.caste_name),
#                 "counseling_name": get_na_safe(course.counseling_name),
#                 "category_of_admission_id": get_na_safe(course.category_of_admission_id) or 'NA',
#                 "category_of_admission": category_of_admission,
#                 "lowest_closing_rank": lowest_rank_string,
#                 "college_id": get_na_safe(course.college_id),
#                 "exam_name": get_na_safe(course.exam_name),
#                 "total_counseling_rounds": get_na_safe(course.total_counseling_rounds),
#                 "caste_id": get_na_safe(course.caste_id)
#             })

#         transformed_data = {
#             "year": max_year_ref["year"] if max_year_ref else "NA",
#             "exams": []
#         }

#         exam_map = {}

#         if not serialized_data:
#             raise NoDataAvailableError("No exam & cutoff data available for the provided Course's.")

#         # Initialize categories from base_cutoffs
#         for item in base_cutoffs:
#             exam_id = item["exam_sub_exam_id"]
#             if exam_id == 'NA':
#                 continue
#             category_id = item["category_of_admission_id"]
            
#             if exam_id not in exam_map:
#                 exam_map[exam_id] = {
#                     "exam_id": exam_id,
#                     "exam_name": "NA",  # Will be updated later
#                     "counselling_id": item["counselling_id"],
#                     "counselling_name": "NA", # Will be updated later
#                     "exam_and_counseling": "NA", # Will be updated later
#                     "categories": {}
#                 }
            
#             if category_id not in exam_map[exam_id]["categories"]:
#                 try:
#                     category_id_int = int(category_id)
#                 except (ValueError, TypeError):
#                     category_id_int = 'NA'
                
#                 category_name = (
#                     "All India" if category_id_int == 1
#                     else "Outside Home state" if category_id_int == 2
#                     else "Home state" if category_id_int == 3
#                     else "NA"
#                 ) if category_id_int != 'NA' else 'NA'
                
#                 exam_map[exam_id]["categories"][category_id] = {
#                     "category_id": category_id,
#                     "category_name": category_name,
#                     "cutoff_data": OrderedDict()
#                 }
                
#                 for idx, course_id in enumerate(course_ids, 1):
#                     college_key = f"college_{idx}"
#                     exam_map[exam_id]["categories"][category_id]["cutoff_data"][college_key] = {
#                         "college_course_id": course_id,
#                         "college_id": "NA",
#                         "opening_rank": "NA",
#                         "closing_rank": "NA",
#                         # "caste_id": "NA",
#                         # "caste_name": "NA",
#                         "total_counselling_rounds": "NA",
#                         "lowest_closing_rank": "NA"
#                     }
        
#         for item in serialized_data:
            
#             exam_id = item["exam_id"]
#             if exam_id == 'NA':
#                 continue
            
#             if exam_id not in exam_map:
#                 continue

#             exam_map[exam_id]["exam_name"] = item["exam_name"]
#             exam_map[exam_id]["counselling_name"] = item["counseling_name"]
#             exam_map[exam_id]["exam_and_counseling"] = item["exam_and_counseling"]
        
#         # Populate cutoff data from base_cutoffs
#         for item in base_cutoffs:
#             exam_id = item["exam_sub_exam_id"]
#             if exam_id == 'NA':
#                 continue
#             category_id = item["category_of_admission_id"]
#             college_course_id = item["college_course_id"]
            
#             if exam_id in exam_map and category_id in exam_map[exam_id]["categories"]:
#                 for idx, course_id in enumerate(course_ids, 1):
#                     if college_course_id == course_id:
#                         college_key = f"college_{idx}"
#                         exam_map[exam_id]["categories"][category_id]["cutoff_data"][college_key] = {
#                             "college_course_id": item["college_course_id"],
#                             "college_id": item["college_id"],
#                             "opening_rank": item["round_wise_opening_cutoff"],
#                             "closing_rank": item["final_cutoff"],
#                             # "caste_id": item["caste_id"],
#                             # "caste_name": get_caste_name(item["caste_id"]),
#                             "total_counseling_rounds": item["total_counseling_rounds"],
#                             "lowest_closing_rank": "NA" # lowest_closing_rank will be added later
#                         }

#         for item in serialized_data:
#             exam_id = item["exam_id"]
#             if exam_id == 'NA':
#                 continue
#             category_id = item["category_of_admission_id"]
#             college_course_id = item["id"]

#             if exam_id in exam_map and category_id in exam_map[exam_id]["categories"]:
#                 for idx, course_id in enumerate(course_ids, 1):
#                     if college_course_id == course_id:
#                         college_key = f"college_{idx}"
#                         exam_map[exam_id]["categories"][category_id]["cutoff_data"][college_key]["lowest_closing_rank"] = item["lowest_closing_rank"]

#         for exam_id in exam_map:
#             categories_list = []
#             for category_id, category_data in exam_map[exam_id]["categories"].items():
#                 categories_list.append({
#                     "category_id": category_id,
#                     "category_name": category_data["category_name"],
#                     "cutoff_data": category_data["cutoff_data"]
#                 })
#             exam_map[exam_id]["categories"] = categories_list

#         transformed_data["exams"] = list(exam_map.values())

#         if transformed_data["exams"] == []:
#             raise NoDataAvailableError("No exam & cutoff data available for the provided Course's.")

#         return transformed_data


class ExamCutoffHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        """Generate a cache key using MD5 hashing."""
        key = "11110777_____________111".join(map(str, args))
        return md5(key.encode()).hexdigest()

    @staticmethod
    def get_exam_cutoff(
        course_ids, exam_id=None, counseling_id=None, category_id=None
    ):
        if not course_ids:
            raise ValueError("course_ids must be provided.")

        cache_key = ExamCutoffHelper.get_cache_key(
            course_ids, exam_id, counseling_id, category_id
        )
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        # MaxYearRef CTE
        max_year_ref = (
            CutoffData.objects.filter(college_course_id__in=course_ids)
            .values("year")
            .order_by("-year")
            .first()
        )

        print(max_year_ref)

        if not max_year_ref:
            raise NoDataAvailableError(
                "No exam & cutoff data available for the provided Course's."
            )

        filtered_cutoff = (
            CutoffData.objects.filter(
                college_course_id__in=course_ids, year=max_year_ref["year"]
            )
            .values("exam_sub_exam_id", "counselling_id", "college_course_id", "year")
            .distinct()
        )

        filtered_campaign = (
            CpProductCampaignItems.objects.filter(product__published="published")
            .values("exam_id", "counselling_id")
            .distinct()
        )

        max_rounds = (
            CutoffData.objects.filter(
                college_course_id__in=course_ids, year=max_year_ref["year"]
            )
            .values("exam_sub_exam_id", "counselling_id", "college_course_id", "caste_id")
            .annotate(
                priority_caste_id=Case(
                    When(caste_id=5, then=Value(5)),  # ST
                    When(caste_id=4, then=Value(4)),  # SC
                    When(caste_id=3, then=Value(3)),  # OBC
                    When(caste_id=2, then=Value(2)),  # General
                    default=Value(2),  # Others
                    output_field=IntegerField(),
                )
            )
            .order_by(
                "exam_sub_exam_id",
                "counselling_id",
                "college_course_id",
                "priority_caste_id",
            )
            .distinct()
            .annotate(total_counseling_rounds=Max("round"))
        )

        # Base cutoffs with lowest closing rank

        base_cutoffs = (
            CutoffData.objects.filter(
                college_course_id__in=course_ids,
                year=max_year_ref["year"],
                exam_sub_exam_id__in=filtered_cutoff.values("exam_sub_exam_id"),
                counselling_id__in=filtered_campaign.values("counselling_id"),
            )
            .values(
                "exam_sub_exam_id",
                "counselling_id",
                "college_course_id",
                "college_id",
                "category_of_admission_id",
            )
            .annotate(
                round_wise_opening_cutoff=Coalesce(
                    Min("round_wise_opening_cutoff"), Value("NA"), output_field=CharField()
                ),
                # Prioritize lowest caste_id (2) for final_cutoff
                final_cutoff=Coalesce(
                    Subquery(
                        CutoffData.objects.filter(
                            year=OuterRef("year"),
                            college_course_id=OuterRef("college_course_id"),
                            exam_sub_exam_id=OuterRef("exam_sub_exam_id"),
                            counselling_id=OuterRef("counselling_id"),
                            category_of_admission_id=OuterRef("category_of_admission_id"),
                            final_cutoff__isnull=False,
                        )
                        .annotate(
                            priority_caste_id=Case(
                                When(caste_id=5, then=Value(5)),  # ST
                                When(caste_id=4, then=Value(4)),  # SC
                                When(caste_id=3, then=Value(3)),  # OBC
                                When(caste_id=2, then=Value(2)),  # General
                                default=Value(2),  # Others
                                output_field=IntegerField(),
                            )
                        )
                        .order_by("priority_caste_id", "final_cutoff")
                        .values("final_cutoff")[:1]
                    ),
                    Value("NA"),
                    output_field=CharField(),
                ),
                lowest_closing_rank=Coalesce(
                    Subquery(
                        CutoffData.objects.filter(
                            year=OuterRef("year"),
                            college_course_id=OuterRef("college_course_id"),
                            exam_sub_exam_id=OuterRef("exam_sub_exam_id"),
                            counselling_id=OuterRef("counselling_id"),
                            category_of_admission_id=OuterRef("category_of_admission_id"),
                            final_cutoff__isnull=False,
                        )
                        .annotate(
                            priority_caste_id=Case(
                                When(caste_id=5, then=Value(1)),  # ST
                                When(caste_id=4, then=Value(2)),  # SC
                                When(caste_id=3, then=Value(3)),  # OBC
                                When(caste_id=2, then=Value(4)),  # General
                                default=Value(5),  # Others
                                output_field=IntegerField(),
                            )
                        )
                        .order_by(
                            "priority_caste_id",
                            "final_cutoff",
                        )
                        .values("final_cutoff")[:1]
                    ),
                    Value("NA"),
                    output_field=CharField(),
                ),
                total_counseling_rounds=Subquery(
                    max_rounds.filter(
                        exam_sub_exam_id=OuterRef("exam_sub_exam_id"),
                        counselling_id=OuterRef("counselling_id"),
                        college_course_id=OuterRef("college_course_id"),
                    )
                    .values("total_counseling_rounds")[:1]
                ),
                caste_id=Coalesce(
                    Subquery(
                        CutoffData.objects.filter(
                            year=OuterRef("year"),
                            college_course_id=OuterRef("college_course_id"),
                            exam_sub_exam_id=OuterRef("exam_sub_exam_id"),
                            counselling_id=OuterRef("counselling_id"),
                            category_of_admission_id=OuterRef("category_of_admission_id"),
                            final_cutoff__isnull=False,
                        )
                        .annotate(
                            priority_caste_id=Case(
                                When(caste_id=5, then=Value(1)),  # ST
                                When(caste_id=4, then=Value(2)),  # SC
                                When(caste_id=3, then=Value(3)),  # OBC
                                When(caste_id=2, then=Value(4)),  # General
                                default=Value(2),  # Others
                                output_field=IntegerField(),
                            )
                        )
                        .order_by(
                            "priority_caste_id",
                            "final_cutoff",
                        )
                        .values("caste_id")[:1]
                    ),
                    Value(None),
                    output_field=IntegerField(),
                ),
                lowest_rank_caste_id=Coalesce(
                    Subquery(
                        CutoffData.objects.filter(
                            year=OuterRef("year"),
                            college_course_id=OuterRef("college_course_id"),
                            exam_sub_exam_id=OuterRef("exam_sub_exam_id"),
                            counselling_id=OuterRef("counselling_id"),
                            category_of_admission_id=OuterRef("category_of_admission_id"),
                            final_cutoff__isnull=False,
                        )
                        .annotate(
                            priority_caste_id=Case(
                                When(caste_id=5, then=Value(1)),  # ST
                                When(caste_id=4, then=Value(2)),  # SC
                                When(caste_id=3, then=Value(3)),  # OBC
                                When(caste_id=2, then=Value(4)),  # General
                                default=Value(5),  # Others
                                output_field=IntegerField(),
                            )
                        )
                        .order_by(
                            "priority_caste_id",
                            "final_cutoff",
                        )
                        .values("caste_id")[:1]
                    ),
                    Value(None),
                    output_field=IntegerField(),
                ),
            )
            .distinct()
        )

        # Lowest ranks with selected caste id
        lowest_ranks = (
            CutoffData.objects.filter(
                year=max_year_ref["year"],
                college_course_id__in=course_ids,
                final_cutoff__isnull=False,
            )
            .filter(
                Q(exam_sub_exam_id__in=filtered_campaign.values("exam_id"))
                | Q(counselling_id__in=filtered_campaign.values("counselling_id"))
            )
            .values("exam_sub_exam_id", "counselling_id", "college_course_id")
            .annotate(
                selected_caste_id=Subquery(
                    CutoffData.objects.filter(
                        year=max_year_ref["year"],
                        college_course_id=OuterRef("college_course_id"),
                        final_cutoff__isnull=False,
                    )
                    .annotate(
                        priority_caste_id=Case(
                            When(caste_id=5, then=Value(1)),  # ST
                            When(caste_id=4, then=Value(2)),  # SC
                            When(caste_id=3, then=Value(3)),  # OBC
                            When(caste_id=2, then=Value(4)),  # General
                            default=Value(5),  # Others
                            output_field=IntegerField(),
                        )
                    )
                    .order_by(
                        "priority_caste_id",  # Higher priority caste
                        "final_cutoff",  # Lowest final cutoff
                    )
                    .values("caste_id")[:1]
                ),
            )
        )

        result = Course.objects.filter(id__in=course_ids)

        result = result.annotate(
            exam_id=Subquery(
                CutoffData.objects.filter(college_course_id=OuterRef("id"))
                .values("exam_sub_exam__id")[:1]
            ),
            exam_sub_exam_id_ann=Subquery(
                CutoffData.objects.filter(college_course_id=OuterRef("id"))
                .values("exam_sub_exam_id")[:1]
            ),
            counselling_id_ann=Subquery(
                CutoffData.objects.filter(college_course_id=OuterRef("id"))
                .values("counselling_id")[:1]
            ),
            exam_name=Coalesce(
                Subquery(
                    Exam.objects.filter(id=OuterRef("exam_sub_exam_id_ann"))
                    .annotate(
                        display_name=Case(
                            When(
                                exam_short_name__isnull=False,
                                exam_short_name__gt="",
                                then=F("exam_short_name"),
                            ),
                            When(
                                parent_exam_id__isnull=False,
                                then=Concat(
                                    "parent_exam__exam_short_name",
                                    Value(" ("),
                                    F("exam_name"),
                                    Value(")"),
                                ),
                            ),
                            default=F("exam_name"),
                            output_field=CharField(),
                        )
                    )
                    .values("display_name")[:1]
                ),
                Value("NA"),
                output_field=CharField(),
            ),
            counseling_name=Coalesce(
                Subquery(
                    Exam.objects.filter(id=OuterRef("counselling_id_ann")).values(
                        "exam_name"
                    )[:1]
                ),
                Value("NA"),
                output_field=CharField(),
            ),
            min_opening_cutoff=Coalesce(
                Subquery(
                    base_cutoffs.filter(
                        college_course_id=OuterRef("id"),
                    ).values("round_wise_opening_cutoff")[:1]
                ),
                Value("NA"),
                output_field=CharField(),
            ),
            lowest_closest_rank=Coalesce(
                Subquery(
                    base_cutoffs.filter(
                        college_course_id=OuterRef("id"),
                    ).values("lowest_closing_rank")[:1]
                ),
                Value("NA"),
                output_field=CharField(),
            ),
            min_closing_cutoff=Coalesce(
                Subquery(
                    base_cutoffs.filter(
                        college_course_id=OuterRef("id"),
                    ).values("final_cutoff")[:1]
                ),
                Value("NA"),
                output_field=CharField(),
            ),
            caste_id=Coalesce(
                NullIf(
                    Subquery(
                        base_cutoffs.filter(college_course_id=OuterRef("id"))
                        .values("caste_id")[:1]
                    ),
                    Value(""),  # Converts empty strings to NULL
                ),
                Value(None),
                output_field=IntegerField(),
            ),
             lowest_rank_caste_id=Coalesce(
                NullIf(
                    Subquery(
                        lowest_ranks.filter(college_course_id=OuterRef("id"))
                        .values("selected_caste_id")[:1]
                    ),
                    Value(""),  # Converts empty strings to NULL
                ),
                Value(None),
                output_field=IntegerField(),
            ),
            total_counseling_rounds=Coalesce(
                NullIf(
                    Subquery(
                        max_rounds.filter(
                            exam_sub_exam_id=OuterRef("exam_sub_exam_id_ann"),
                            counselling_id=OuterRef("counselling_id_ann"),
                            college_course_id=OuterRef("id"),
                        )
                        .values("total_counseling_rounds")[:1]
                    ),
                    Value(""),  # Converts empty strings to NULL
                ),
                Value(0),
                output_field=IntegerField(),
            ),
        )

        result = result.annotate(
            exam_and_counseling=Case(
                When(
                    ~Q(exam_name="NA") & ~Q(counseling_name="NA"),
                    then=Concat(
                        F("exam_name"), Value(" ("), F("counseling_name"), Value(")")
                    ),
                ),
                default=Value("NA"),
                output_field=CharField(),
            )
        )




        result = result.annotate(
            min_opening_cutoff=Coalesce(
                Subquery(
                    base_cutoffs.filter(
                        college_course_id=OuterRef("id"),
               
                    ).values("round_wise_opening_cutoff")[:1]
                ),
                Value("NA"),
                output_field=CharField(),
            ),
            lowest_closest_rank=Coalesce(
                Subquery(
                    base_cutoffs.filter(
                        college_course_id=OuterRef("id"),
                       
                    ).values("lowest_closing_rank")[:1]
                ),
                Value("NA"),
                output_field=CharField(),
            ),
            min_closing_cutoff=Coalesce(
                Subquery(
                    base_cutoffs.filter(
                        college_course_id=OuterRef("id"),
                    
                    ).values("final_cutoff")[:1]
                ),
                Value("NA"),
                output_field=CharField(),
            ),
            caste_id=Coalesce(
                NullIf(
                    Subquery(
                        base_cutoffs.filter(college_course_id=OuterRef("id"))
                        .values("caste_id")[:1]
                    ),
                    Value(""),  # Converts empty strings to NULL
                ),
                Value(None),
                output_field=IntegerField(),
            ),
            lowest_rank_caste_id=Coalesce(
                NullIf(
                    Subquery(
                        lowest_ranks.filter(college_course_id=OuterRef("id"))
                        .values("selected_caste_id")[:1]
                    ),
                    Value(""),  # Converts empty strings to NULL
                ),
                Value(None),
                output_field=IntegerField(),
            ),
            total_counseling_rounds=Coalesce(
                NullIf(
                    Subquery(
                        max_rounds.filter(
                            exam_sub_exam_id=OuterRef("exam_sub_exam_id_ann"),
                            counselling_id=OuterRef("counselling_id_ann"),
                            college_course_id=OuterRef("id"),
                        )
                        .values("total_counseling_rounds")[:1]
                    ),
                    Value(""),  # Converts empty strings to NULL
                ),
                Value(0),
                output_field=IntegerField(),
            ),
        )
        result = result.annotate(
            caste_name=Case(
                When(caste_id=2, then=Value("General")),
                When(caste_id=3, then=Value("OBC")),
                When(caste_id=4, then=Value("SC")),
                When(caste_id=5, then=Value("ST")),
                default=Value("NA"),
                output_field=CharField(),
            ),
            category_of_admission_id=Coalesce(
                Subquery(
                    base_cutoffs.filter(college_course_id=OuterRef("id")).values(
                        "category_of_admission_id"
                    )[:1]
                ),
                Value("NA"),
                output_field=CharField(),
            ),
            exam_education_level=Coalesce(
                Subquery(
                    Exam.objects.filter(id=OuterRef("exam_sub_exam_id_ann")).values(
                        "preferred_education_level_id"
                    )[:1]
                ),
                Value(1),
                output_field=IntegerField(),
            ),
        )

        result = result.order_by(
            Case(
                When(exam_education_level__in=[14, 15, 16, 18], then=Value(2)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            "exam_sub_exam_id_ann",
            "counselling_id_ann",
            "id",
        ).distinct()

        if exam_id:
            result = result.filter(exam_sub_exam_id_ann=exam_id)
        if counseling_id:
            result = result.filter(counselling_id_ann=counseling_id)
        if category_id:
            result = result.filter(category_of_admission_id=category_id)

        def get_na_safe(value):
            """Safely handles null/None values by converting them to 'NA' string"""
            return "NA" if value is None else value

        def get_caste_name(caste_id):
            """Converts caste ID to corresponding caste name"""
            caste_map = {2: "General", 3: "OBC", 4: "SC", 5: "ST"}
            return caste_map.get(caste_id, "NA")

        serialized_data = []
        for course in result:
            lowest_rank_string = (
                f"{course.lowest_closest_rank} ({get_caste_name(course.lowest_rank_caste_id)})"
                if get_na_safe(course.lowest_closest_rank) != "NA"
                else "NA"
            )

            # Safely convert category_of_admission_id to int
            if (
                course.category_of_admission_id == "NA"
                or course.category_of_admission_id in [None, ""]
            ):
                category_of_admission_id = "NA"
            else:
                try:
                    category_of_admission_id = int(course.category_of_admission_id)
                except (ValueError, TypeError):
                    category_of_admission_id = "NA"

            category_of_admission = (
                "All India"
                if category_of_admission_id == 1
                else "Outside Home state"
                if category_of_admission_id == 2
                else "Home state"
                if category_of_admission_id == 3
                else "NA"
            ) if category_of_admission_id != "NA" else "NA"

            serialized_data.append(
                {
                    "id": get_na_safe(course.id),
                    "exam_id": get_na_safe(course.exam_id),
                    "counselling_id": get_na_safe(course.counselling_id_ann),
                    "exam_and_counseling": get_na_safe(course.exam_and_counseling),
                    "min_opening_cutoff": get_na_safe(course.min_opening_cutoff),
                    "min_closing_cutoff": get_na_safe(course.min_closing_cutoff),
                    "caste_name": get_na_safe(course.caste_name),
                    "counseling_name": get_na_safe(course.counseling_name),
                    "category_of_admission_id": get_na_safe(
                        course.category_of_admission_id
                    )
                    or "NA",
                    "category_of_admission": category_of_admission,
                    "lowest_closing_rank": lowest_rank_string,
                    "college_id": get_na_safe(course.college_id),
                    "exam_name": get_na_safe(course.exam_name),
                    "total_counseling_rounds": get_na_safe(
                        course.total_counseling_rounds
                    ),
                    "caste_id": get_na_safe(course.caste_id),
                }
            )

        transformed_data = {"year": max_year_ref["year"] if max_year_ref else "NA", "exams": []}

        exam_map = {}

        if not serialized_data:
            raise NoDataAvailableError(
                "No exam & cutoff data available for the provided Course's."
            )

        # Initialize categories from base_cutoffs
        for item in base_cutoffs:
            exam_id = item["exam_sub_exam_id"]
            if exam_id == "NA":
                continue
            category_id = item["category_of_admission_id"]

            if exam_id not in exam_map:
                exam_map[exam_id] = {
                    "exam_id": exam_id,
                    "exam_name": "NA",  # Will be updated later
                    "counselling_id": item["counselling_id"],
                    "counselling_name": "NA",  # Will be updated later
                    "exam_and_counseling": "NA",  # Will be updated later
                    "categories": {},
                }

            if category_id not in exam_map[exam_id]["categories"]:
                try:
                    category_id_int = int(category_id)
                except (ValueError, TypeError):
                    category_id_int = "NA"

                category_name = (
                    "All India"
                    if category_id_int == 1
                    else "Outside Home state"
                    if category_id_int == 2
                    else "Home state"
                    if category_id_int == 3
                    else "NA"
                ) if category_id_int != "NA" else "NA"

                exam_map[exam_id]["categories"][category_id] = {
                    "category_id": category_id,
                    "category_name": category_name,
                    "cutoff_data": OrderedDict(),
                }

                for idx, course_id in enumerate(course_ids, 1):
                    college_key = f"college_{idx}"
                    exam_map[exam_id]["categories"][category_id]["cutoff_data"][
                        college_key
                    ] = {
                        "college_course_id": course_id,
                        "college_id": "NA",
                        "opening_rank": "NA",
                        "closing_rank": "NA",
                        # "caste_id": "NA",
                        # "caste_name": "NA",
                        "total_counselling_rounds": "NA",
                        "lowest_closing_rank": "NA",
                    }

        for item in serialized_data:
            exam_id = item["exam_id"]
            if exam_id == "NA":
                continue

            if exam_id not in exam_map:
                continue

            exam_map[exam_id]["exam_name"] = item["exam_name"]
            exam_map[exam_id]["counselling_name"] = item["counseling_name"]
            exam_map[exam_id]["exam_and_counseling"] = item["exam_and_counseling"]

        # Populate cutoff data from base_cutoffs
        for item in base_cutoffs:
            exam_id = item["exam_sub_exam_id"]
            if exam_id == "NA":
                continue
            category_id = item["category_of_admission_id"]
            college_course_id = item["college_course_id"]

            if (
                exam_id in exam_map
                and category_id in exam_map[exam_id]["categories"]
            ):
                for idx, course_id in enumerate(course_ids, 1):
                    if college_course_id == course_id:
                        college_key = f"college_{idx}"
                        exam_map[exam_id]["categories"][category_id]["cutoff_data"][
                            college_key
                        ] = {
                            "college_course_id": item["college_course_id"],
                            "college_id": item["college_id"],
                            "opening_rank": item["round_wise_opening_cutoff"],
                            "closing_rank": item["final_cutoff"],
                            # "caste_id": item["caste_id"],
                            # "caste_name": get_caste_name(item["caste_id"]),
                            "total_counseling_rounds": item["total_counseling_rounds"],
                            "lowest_closing_rank": "NA",  # lowest_closing_rank will be added later
                        }

        for item in serialized_data:
            exam_id = item["exam_id"]
            if exam_id == "NA":
                continue
            category_id = item["category_of_admission_id"]
            college_course_id = item["id"]

            if (
                exam_id in exam_map
                and category_id in exam_map[exam_id]["categories"]
            ):
                for idx, course_id in enumerate(course_ids, 1):
                    if college_course_id == course_id:
                        college_key = f"college_{idx}"
                        exam_map[exam_id]["categories"][category_id]["cutoff_data"][
                            college_key
                        ]["lowest_closing_rank"] = item["lowest_closing_rank"]

        for exam_id in exam_map:
            categories_list = []
            for category_id, category_data in exam_map[exam_id]["categories"].items():
                categories_list.append(
                    {
                        "category_id": category_id,
                        "category_name": category_data["category_name"],
                        "cutoff_data": category_data["cutoff_data"],
                    }
                )
            exam_map[exam_id]["categories"] = categories_list

        transformed_data["exams"] = list(exam_map.values())

        if transformed_data["exams"] == []:
            raise NoDataAvailableError(
                "No exam & cutoff data available for the provided Course's."
            )

        return transformed_data




       




class ExamCutoffGraphHelper:

    @staticmethod
    def get_cache_key(*args) -> str:
        """Generate a cache key using MD5 hashing."""
        key = "_".join(map(str, args))
        return hashlib.md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_cutoff_data(course_ids, exam_id=None, counseling_id=None, category_id=None, caste_id=None, gender_id=None):
        """Fetches cutoff data based on course IDs, exam ID, counseling ID, category ID, caste ID, and gender ID."""
        if not course_ids:
            raise ValueError("course_ids must be provided.")

    
        cache_key = ExamCutoffGraphHelper.get_cache_key(course_ids, exam_id, counseling_id, category_id, caste_id, gender_id)
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

  
        max_year = CutoffData.objects.filter(college_course_id__in=course_ids).aggregate(Max("year"))["year__max"]
        if not max_year:
            return []

        filtered_cutoff = (
            CutoffData.objects.filter(
                college_course_id__in=course_ids, year=max_year
            )
            .values("exam_sub_exam_id", "counselling_id")
            .distinct()
        )

        filtered_campaign = (
            CpProductCampaignItems.objects.filter(product__published="published")
            .values("exam_id", "counselling_id")
            .distinct()
        )

        base_cutoffs = CutoffData.objects.filter(
            college_course_id__in=course_ids,
            year=max_year,
            exam_sub_exam_id__in=filtered_cutoff.values("exam_sub_exam_id"),
            counselling_id__in=filtered_campaign.values("counselling_id"),
        )

        all_caste_gender_combinations = [
            (2, 1), (2, 2), (3, 1), (3, 2), (4, 1), (4, 2), (5, 1), (5, 2)
        ]

        all_exam_counseling_combinations = list(filtered_cutoff)

        result_list = []

        for course_id in course_ids:
            for exam_counseling in all_exam_counseling_combinations:
                for caste_id_val, gender_id_val in all_caste_gender_combinations:
                    filtered_base_cutoffs = base_cutoffs.filter(
                        college_course_id=course_id,
                        exam_sub_exam_id=exam_counseling['exam_sub_exam_id'],
                        counselling_id=exam_counseling['counselling_id'],
                        caste_id=caste_id_val,
                    )

                    annotated_cutoffs = filtered_base_cutoffs.aggregate(
                        min_opening_rank=Coalesce(Min("round_wise_opening_cutoff"), Value("NA"), output_field=CharField()),
                        min_closing_rank=Coalesce(Min("final_cutoff"), Value("NA"), output_field=CharField()),
                    )

                    exam = Exam.objects.filter(id=exam_counseling['exam_sub_exam_id']).first()
                    counseling = Exam.objects.filter(id=exam_counseling['counselling_id']).first()

                    exam_name_result = exam.get_exam_display_name() if exam else "NA"
                    counseling_name_result = counseling.exam_name if counseling else "NA"

                    caste_name = "NA"
                    if caste_id_val == 2:
                        caste_name = "General"
                    elif caste_id_val == 3:
                        caste_name = "OBC"
                    elif caste_id_val == 4:
                        caste_name = "SC"
                    elif caste_id_val == 5:
                        caste_name = "ST"

                    category_of_admission = "NA"
                    category_of_admission_id = 'NA'
                    if filtered_base_cutoffs.filter(category_of_admission_id=1).exists():
                        category_of_admission = "All India"
                        category_of_admission_id = 1
                    elif filtered_base_cutoffs.filter(category_of_admission_id=2).exists():
                        category_of_admission = "Outside Home State"
                        category_of_admission_id = 2
                    elif filtered_base_cutoffs.filter(category_of_admission_id=3).exists():
                        category_of_admission = "Home State"
                        category_of_admission_id = 3

                    result_dict = {
                        "college_course_id": course_id,
                        "exam_sub_exam_id": exam_counseling['exam_sub_exam_id'],
                        "counselling_id": exam_counseling['counselling_id'],
                        "exam_name": exam_name_result,
                        "counseling_name": counseling_name_result,
                        "caste_name": caste_name,
                        "category_of_admission": category_of_admission,
                        "category_id": category_of_admission_id,
                        "min_closing_cutoff": annotated_cutoffs['min_closing_rank'],
                        "caste_id": caste_id_val,
                        "gender_id": gender_id_val,
                    }
                    result_list.append(result_dict)

       
        if exam_id:
            result_list = [item for item in result_list if item['exam_sub_exam_id'] == exam_id]
        if counseling_id:
            result_list = [item for item in result_list if item['counselling_id'] == counseling_id]
        if category_id:
            result_list = [item for item in result_list if item['category_of_admission'] != "NA" and  CutoffData.objects.filter(college_course_id=item['college_course_id'],exam_sub_exam_id=item['exam_sub_exam_id'],counselling_id=item['counselling_id'],caste_id=item['caste_id'],category_of_admission_id=category_id).exists()]
        if caste_id:
            result_list = [item for item in result_list if item['caste_id'] == caste_id]
        if gender_id:
            result_list = [item for item in result_list if item['gender_id'] == gender_id]

        formatted_result = {"exams_data": [], "college_names": []}
        exam_counseling_groups = {}
        
        for item in result_list:
            key = (item['exam_sub_exam_id'], item['counselling_id'])
            if key not in exam_counseling_groups:
                exam_counseling_groups[key] = []
            exam_counseling_groups[key].append(item)

        for (exam_id, counseling_id), items in exam_counseling_groups.items():
            exam_data = {
                "id": exam_id,
                "name": items[0]['exam_name'],
                "counseling": []
            }

            counseling_data = {
                "id": counseling_id,
                "name": items[0]['counseling_name'],
                "categories": []
            }

            all_category_ids = set(item['category_id'] for item in items if item['category_id'] != 'NA')
            if not all_category_ids:
                all_category_ids.add('NA')

            for category_id_val in all_category_ids:
                category_items = [item for item in items if item['category_id'] == category_id_val]
                
                if not category_items:
                    continue

                category_data = {
                    "id": category_id_val,
                    "name": category_items[0]['category_of_admission'],
                    "caste": []
                }

                all_caste_ids = set(item['caste_id'] for item in category_items)

                for caste_id_val in all_caste_ids:
                    caste_items = [item for item in category_items if item['caste_id'] == caste_id_val]
                    
                    if not caste_items:
                        continue

                    caste_data = {
                        "id": caste_id_val,
                        "name": caste_items[0]['caste_name'],
                        "gender": []
                    }

                    all_gender_ids = set(item['gender_id'] for item in caste_items)

                    for gender_id_val in all_gender_ids:
                        gender_items = [item for item in caste_items if item['gender_id'] == gender_id_val]
                        
                        cutoff_data_dict = {}
                        all_na = True

                        for item in gender_items:
                            college_course_id = item['college_course_id']
                            closing_rank = item['min_closing_cutoff']
                            college_key = f"college_{course_ids.index(college_course_id) + 1}"
                            
                            cutoff_data_dict[college_key] = {
                                "closing_rank": closing_rank,
                                "course_id": college_course_id
                            }
                            
                            if closing_rank != "NA":
                                all_na = False

                        # Fill missing colleges
                        for i, course_id in enumerate(course_ids):
                            
                            college_key = f"college_{i + 1}"
                            if college_key not in cutoff_data_dict:
                                all_na=True
                                cutoff_data_dict[college_key] = {
                                    "closing_rank": "NA",
                                    "course_id": course_id
                                }

                        gender_data = {
                            "id": gender_id_val,
                            "name": "Male" if gender_id_val == 1 else "Female",
                            "cutoff_data": {
                                "type": "tabular" if all_na else "vertical bar",
                                **cutoff_data_dict
                            }
                        }
                        caste_data["gender"].append(gender_data)

                    category_data["caste"].append(caste_data)
                counseling_data["categories"].append(category_data)
            exam_data["counseling"].append(counseling_data)
            formatted_result["exams_data"].append(exam_data)

        # Get college names
        college_names_dict = {
            course_id: college_name 
            for course_id, college_name in Course.objects.filter(id__in=course_ids)
            .select_related('college')
            .values_list('id', 'college__name')
        }
        formatted_result["college_names"] = [college_names_dict[course_id] for course_id in course_ids]

        cache.set(cache_key, formatted_result, timeout=3600)
        return formatted_result




class UserPreferenceHelper:
    """
    Helper class to manage user preferences, fees, locations, courses, and exam data.
    """

    @staticmethod
    def get_user_preference_data(preference_id):
        """
        Retrieve user preferences, fees, locations, courses, and exam data.

        Args:
            preference_id (int): The ID of the UserReportPreferenceMatrix entry.

        Returns:
            dict: A dictionary containing fees, location, and exams data.
        """
     
        response = {
            "fees": [],
            "location": [],
            "exams": []
        }

        try:
           
            user_pref = UserReportPreferenceMatrix.objects.filter(id=preference_id).values(
                'preference_1', 'preference_2', 'preference_3', 'preference_4', 'preference_5',
                'course_1', 'course_2', 'course_3'
            ).first()

            if not user_pref:
                return response

    
            fees_values = [user_pref.get(f'preference_{i}') for i in range(1, 6)]


            fee_ranges = {
                1: "up to 1 lakh",
                2: "up to 2 lakh",
                3: "up to 3 lakh",
                4: "up to 5 lakh",
                5: "up to 10 lakh",
                6: "10 lakh and above",
                7: "no budget constraints"
            }

            if 'Fees' in fees_values:
                response['fees'] = list(fee_ranges.values())

        
            city_names = Location.get_active_cities_in_country()
           
            if 'Location' in fees_values:
                response['location'] = city_names

          
            course_ids = [user_pref.get(f'course_{i}') for i in range(1, 4) if user_pref.get(f'course_{i}')]

            if course_ids:
              
                exam_ids = CollegeCourseExam.objects.filter(
                    college_course__in=course_ids
                ).values_list('exam_id', flat=True)

            
                exams = Exam.objects.filter(id__in=exam_ids).order_by(
                    Coalesce('parent_exam', Value(-1)), 
                    'state_of_exam_id',
                    'exam_name'
                )

                response['exams'] = [exam.get_exam_display_name() for exam in exams]

        except Exception as e:
           
            print(f"Error fetching user preference data: {e}")

        return response




class SlugChecker:
    """Helper class for handling slug checking and generation."""
    
    @staticmethod
    def get_cache_key(*args) -> str:
        """Generate a cache key using MD5 hashing."""
        key = "_".join(map(str, args))
        return hashlib.md5(key.encode()).hexdigest()

    def __init__(self, college_ids: List[int], course_ids: Optional[List[int]] = None):
        """
        Initialize SlugChecker with college IDs and optional course IDs.
        
        Args:
            college_ids (List[int]): List of two college IDs
            course_ids (Optional[List[int]]): Optional list of two course IDs
        """
        logger.debug(f"Initializing SlugChecker with colleges: {college_ids}, courses: {course_ids}")
        self.college_ids = college_ids
        self.course_ids = course_ids
        self.validate_input()

    def validate_input(self):
        """Validate the college_ids and course_ids."""
        if not isinstance(self.college_ids, list):
            raise ValueError("college_ids must be a list")
            
        if len(self.college_ids) != 2:
            raise ValueError("college_ids must contain exactly two college IDs.")

        if self.course_ids is not None:
            if not isinstance(self.course_ids, list):
                raise ValueError("course_ids must be a list")
                
            if len(self.course_ids) != 2:
                raise ValueError("course_ids must contain exactly two course IDs if provided.")

    def get_alias(self) -> str:
        """
        Retrieve the alias from the database.
        
        Returns:
            str: The alias string
            
        Raises:
            NoDataAvailableError: If no matching alias is found
        """
        source_1 = f"compare-colleges/{self.college_ids[0]}/{self.college_ids[1]}"
        source_2 = f"compare-colleges/{self.college_ids[1]}/{self.college_ids[0]}"

        alias_query = BaseUrlAlias.objects.filter(
            url_meta_pattern_id=102,
            source__in=[source_1, source_2]
        ).values('alias').first()

        if not alias_query:
            raise NoDataAvailableError(
                f"No matching alias found for the provided college_ids: {self.college_ids}"
            )

        return alias_query['alias']

    def generate_alias_parameterized(self, alias: str) -> str:
        """
        Generate the parameterized alias with query parameters.
        
        Args:
            alias (str): Base alias to parameterize
            
        Returns:
            str: Parameterized alias string
        """
        college_ids_str = ",".join(map(str, self.college_ids))
        if not self.course_ids:
            return f"{alias}?college_ids={college_ids_str}"

        course_ids_str = ",".join(map(str, self.course_ids))
        return f"{alias}?college_ids={college_ids_str}&course_ids={course_ids_str}"

    def get_result(self) -> Dict:
        """
        Get the final result containing alias and parameterized alias with caching.
        
        Returns:
            Dict: Dictionary containing alias information or error message
        """
        cache_key = self.get_cache_key(
            'slug_checker_v1',
            '_'.join(map(str, sorted(self.college_ids))),
            '_'.join(map(str, sorted(self.course_ids))) if self.course_ids else 'no_courses'
        )

        cached_result = cache.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for key: {cache_key}")
            return cached_result

        try:
            alias = self.get_alias()
            alias_parameterized = self.generate_alias_parameterized(alias)

            result = {
                "alias": alias,
                "alias_parameterized": alias_parameterized,
                "college_ids": self.college_ids,
                "course_ids": self.course_ids or 'NA'
            }

            logger.debug(f"Caching result for key: {cache_key}")
            cache.set(cache_key, result, timeout=3600)  
            return result

        except NoDataAvailableError as e:
            logger.warning(f"No data available: {str(e)}")
            error_result = {"error": str(e)}
            cache.set(cache_key, error_result, timeout=3600*24)  
            return error_result
        except Exception as e:
            logger.error(f"Error in get_result: {str(e)}", exc_info=True)
            raise


class AliasReverseChecker:
    """Helper class for reverse checking aliases and handling parameterization."""
    
    @staticmethod
    def get_cache_key(*args) -> str:
        """Generate a cache key using MD5 hashing."""
        key = "_".join(map(str, args))
        return hashlib.md5(key.encode()).hexdigest()
        
    def __init__(self, alias: str, college_ids: Optional[List[int]] = None, 
                 course_ids: Optional[List[int]] = None):
        """
        Initialize AliasReverseChecker with alias and optional IDs.
        
        Args:
            alias (str): The alias to check
            college_ids (Optional[List[int]]): Optional list of two college IDs
            course_ids (Optional[List[int]]): Optional list of two course IDs
        """
        logger.debug(f"Initializing AliasReverseChecker with alias: {alias}, "
                    f"colleges: {college_ids}, courses: {course_ids}")
        self.alias = alias
        self.provided_college_ids = college_ids
        self.course_ids = course_ids
        self.source_college_ids = None
        self.validate_input()
    
    def validate_input(self):
        """
        Validate the alias and optional parameters.
        
        Raises:
            ValueError: If input validation fails
        """
        if not self.alias:
            raise ValueError("Alias must be provided.")
            
        if self.provided_college_ids is not None:
            if not isinstance(self.provided_college_ids, list):
                raise ValueError("college_ids must be a list.")
            if len(self.provided_college_ids) != 2:
                raise ValueError("college_ids must contain exactly two college IDs.")
            
        if self.course_ids is not None:
            if not isinstance(self.course_ids, list):
                raise ValueError("course_ids must be a list.")
            if len(self.course_ids) != 2:
                raise ValueError("course_ids must contain exactly two course IDs.")
    
    def extract_college_ids(self, source: str) -> Optional[List[int]]:
        """
        Extract college IDs from the source field.
        
        Args:
            source (str): Source string containing college IDs
            
        Returns:
            Optional[List[int]]: List of extracted college IDs or None
        """
        try:
            parts = source.split('/')
            if len(parts) >= 3:
                return [int(parts[-2]), int(parts[-1])]
        except (IndexError, ValueError) as e:
            logger.warning(f"Error extracting college IDs from source {source}: {str(e)}")
            return None
        return None
    
    def validate_college_ids_match(self):
        """
        Validate that provided college IDs match the source if both exist.
        
        Raises:
            ValueError: If college IDs don't match
        """
        if self.provided_college_ids and self.source_college_ids:
            provided_set = set(self.provided_college_ids)
            source_set = set(self.source_college_ids)
            if provided_set != source_set:
                raise ValueError(
                    f"Provided college IDs {self.provided_college_ids} do not match "
                    f"the IDs in the source {self.source_college_ids}"
                )
    
    def get_alias_data(self) -> Dict:
        """
        Get alias data and extract college IDs from source.
        
        Returns:
            Dict: Alias data dictionary
            
        Raises:
            NoDataAvailableError: If no matching record is found
            ValueError: If college IDs cannot be extracted
        """
        alias_data = BaseUrlAlias.objects.filter(
            alias=self.alias,
            url_meta_pattern_id=102
        ).values('source', 'alias').first()
        
        if not alias_data:
            raise NoDataAvailableError(
                f"No matching record found for the provided alias: {self.alias}"
            )
        
        self.source_college_ids = self.extract_college_ids(alias_data['source'])
        if not self.source_college_ids:
            raise ValueError(f"Could not extract college IDs from source: {alias_data['source']}")
        
        self.validate_college_ids_match()
        return alias_data
    
    def get_final_college_ids(self) -> List[int]:
        """
        Get the final college IDs to use, preferring provided IDs if they exist.
        
        Returns:
            List[int]: Final list of college IDs to use
        """
        return self.provided_college_ids if self.provided_college_ids else self.source_college_ids
    
    def get_college_details(self, college_ids: List[int]) -> List[Dict]:
        """
        Get college details for the given college IDs in the same sequence as input college_ids.
        
        Args:
            college_ids (List[int]): List of college IDs
            
        Returns:
            List[Dict]: List of college details including id, name, and short_name in same order as college_ids
        """
        # Fetch all colleges in one query
        colleges_dict = {
            college['id']: college 
            for college in College.objects.filter(id__in=college_ids).values('id', 'name', 'short_name')
        }
        
        # Return colleges in the same order as college_ids
        return [colleges_dict[college_id] for college_id in college_ids]
    
    def generate_alias_parameterized(self) -> str:
        """
        Generate the parameterized alias with parameters.
        
        Returns:
            str: Parameterized alias string
            
        Raises:
            ValueError: If college IDs are not available
        """
        college_ids = self.get_final_college_ids()
        if not college_ids:
            raise ValueError("College IDs must be available before generating parameterized alias.")
        
        college_ids_str = ",".join(map(str, college_ids))
        parameterized = f"{self.alias}?college_ids={college_ids_str}"
        
        if self.course_ids:
            course_ids_str = ",".join(map(str, self.course_ids))
            parameterized = f"{parameterized}&course_ids={course_ids_str}"
        
        return parameterized
    
    def get_result(self) -> Dict:
        """
        Get the final result containing alias, parameterized alias, and college details with caching.
        
        Returns:
            Dict: Dictionary containing alias information or error message
        """
        cache_key = self.get_cache_key(
            'alias_reverse_v1',
            self.alias,
            '_'.join(map(str, sorted(self.provided_college_ids))) if self.provided_college_ids else 'no_colleges',
            '_'.join(map(str, sorted(self.course_ids))) if self.course_ids else 'no_courses'
        )

        cached_result = cache.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for key: {cache_key}")
            return cached_result

        try:
            alias_data = self.get_alias_data()
            alias_parameterized = self.generate_alias_parameterized()
            final_college_ids = self.get_final_college_ids()
            college_details = self.get_college_details(final_college_ids)
            
            result = {
                "alias": self.alias,
                "alias_parameterized": alias_parameterized,
                "college_ids": final_college_ids,
                "college_details": college_details,
                "course_ids": self.course_ids or 'NA'
            }

            logger.debug(f"Caching result for key: {cache_key}")
            cache.set(cache_key, result, timeout=3600)  # 1 hour cache
            return result
            
        except NoDataAvailableError as e:
            logger.warning(f"No data available: {str(e)}")
            error_result = {"error": str(e)}
            cache.set(cache_key, error_result, timeout=3600*24)  # 24 hour cache for errors
            return error_result
        except Exception as e:
            logger.error(f"Error in get_result: {str(e)}", exc_info=True)
            raise

# class AliasReverseChecker:
#     """Helper class for reverse checking aliases and handling parameterization."""
    
#     @staticmethod
#     def get_cache_key(*args) -> str:
#         """Generate a cache key using MD5 hashing."""
#         key = "_".join(map(str, args))
#         return hashlib.md5(key.encode()).hexdigest()
        
#     def __init__(self, alias: str, college_ids: Optional[List[int]] = None, 
#                  course_ids: Optional[List[int]] = None):
#         """
#         Initialize AliasReverseChecker with alias and optional IDs.
        
#         Args:
#             alias (str): The alias to check
#             college_ids (Optional[List[int]]): Optional list of two college IDs
#             course_ids (Optional[List[int]]): Optional list of two course IDs
#         """
#         logger.debug(f"Initializing AliasReverseChecker with alias: {alias}, "
#                     f"colleges: {college_ids}, courses: {course_ids}")
#         self.alias = alias
#         self.provided_college_ids = college_ids
#         self.course_ids = course_ids
#         self.source_college_ids = None
#         self.validate_input()
    
#     def validate_input(self):
#         """
#         Validate the alias and optional parameters.
        
#         Raises:
#             ValueError: If input validation fails
#         """
#         if not self.alias:
#             raise ValueError("Alias must be provided.")
            
#         if self.provided_college_ids is not None:
#             if not isinstance(self.provided_college_ids, list):
#                 raise ValueError("college_ids must be a list.")
#             if len(self.provided_college_ids) != 2:
#                 raise ValueError("college_ids must contain exactly two college IDs.")
            
#         if self.course_ids is not None:
#             if not isinstance(self.course_ids, list):
#                 raise ValueError("course_ids must be a list.")
#             if len(self.course_ids) != 2:
#                 raise ValueError("course_ids must contain exactly two course IDs.")
    
#     def extract_college_ids(self, source: str) -> Optional[List[int]]:
#         """
#         Extract college IDs from the source field.
        
#         Args:
#             source (str): Source string containing college IDs
            
#         Returns:
#             Optional[List[int]]: List of extracted college IDs or None
#         """
#         try:
#             parts = source.split('/')
#             if len(parts) >= 3:
#                 return [int(parts[-2]), int(parts[-1])]
#         except (IndexError, ValueError) as e:
#             logger.warning(f"Error extracting college IDs from source {source}: {str(e)}")
#             return None
#         return None
    
#     def validate_college_ids_match(self):
#         """
#         Validate that provided college IDs match the source if both exist.
        
#         Raises:
#             ValueError: If college IDs don't match
#         """
#         if self.provided_college_ids and self.source_college_ids:
#             provided_set = set(self.provided_college_ids)
#             source_set = set(self.source_college_ids)
#             if provided_set != source_set:
#                 raise ValueError(
#                     f"Provided college IDs {self.provided_college_ids} do not match "
#                     f"the IDs in the source {self.source_college_ids}"
#                 )
    
#     def get_alias_data(self) -> Dict:
#         """
#         Get alias data and extract college IDs from source.
        
#         Returns:
#             Dict: Alias data dictionary
            
#         Raises:
#             NoDataAvailableError: If no matching record is found
#             ValueError: If college IDs cannot be extracted
#         """
#         alias_data = BaseUrlAlias.objects.filter(
#             alias=self.alias,
#             url_meta_pattern_id=102
#         ).values('source', 'alias').first()
        
#         if not alias_data:
#             raise NoDataAvailableError(
#                 f"No matching record found for the provided alias: {self.alias}"
#             )
        
#         self.source_college_ids = self.extract_college_ids(alias_data['source'])
#         if not self.source_college_ids:
#             raise ValueError(f"Could not extract college IDs from source: {alias_data['source']}")
        
#         self.validate_college_ids_match()
#         return alias_data
    
#     def get_final_college_ids(self) -> List[int]:
#         """
#         Get the final college IDs to use, preferring provided IDs if they exist.
        
#         Returns:
#             List[int]: Final list of college IDs to use
#         """
#         return self.provided_college_ids if self.provided_college_ids else self.source_college_ids
    
#     def generate_alias_parameterized(self) -> str:
#         """
#         Generate the parameterized alias with parameters.
        
#         Returns:
#             str: Parameterized alias string
            
#         Raises:
#             ValueError: If college IDs are not available
#         """
#         college_ids = self.get_final_college_ids()
#         if not college_ids:
#             raise ValueError("College IDs must be available before generating parameterized alias.")
        
#         college_ids_str = ",".join(map(str, college_ids))
#         parameterized = f"{self.alias}?college_ids={college_ids_str}"
        
#         if self.course_ids:
#             course_ids_str = ",".join(map(str, self.course_ids))
#             parameterized = f"{parameterized}&course_ids={course_ids_str}"
        
#         return parameterized
    
#     def get_result(self) -> Dict:
#         """
#         Get the final result containing alias and parameterized alias with caching.
        
#         Returns:
#             Dict: Dictionary containing alias information or error message
#         """
#         cache_key = self.get_cache_key(
#             'alias_reverse_v1',
#             self.alias,
#             '_'.join(map(str, sorted(self.provided_college_ids))) if self.provided_college_ids else 'no_colleges',
#             '_'.join(map(str, sorted(self.course_ids))) if self.course_ids else 'no_courses'
#         )

#         cached_result = cache.get(cache_key)
#         if cached_result:
#             logger.debug(f"Cache hit for key: {cache_key}")
#             return cached_result

#         try:
#             alias_data = self.get_alias_data()
#             alias_parameterized = self.generate_alias_parameterized()
#             final_college_ids = self.get_final_college_ids()
            
#             result = {
#                 "alias": self.alias,
#                 "alias_parameterized": alias_parameterized,
#                 "college_ids": final_college_ids,
#                 "course_ids": self.course_ids or 'NA'
#             }

#             logger.debug(f"Caching result for key: {cache_key}")
#             cache.set(cache_key, result, timeout=3600)  # 1 hour cache
#             return result
            
#         except NoDataAvailableError as e:
#             logger.warning(f"No data available: {str(e)}")
#             error_result = {"error": str(e)}
#             cache.set(cache_key, error_result, timeout=3600*24)  # 5 minutes cache for errors
#             return error_result
#         except Exception as e:
#             logger.error(f"Error in get_result: {str(e)}", exc_info=True)
#             raise