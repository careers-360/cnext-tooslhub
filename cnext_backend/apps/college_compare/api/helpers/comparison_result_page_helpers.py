from django.db.models import Avg, Count, F, Q,Max,Min
from django.db.models.functions import Round, ExtractYear, TruncDate, Concat
from django.core.cache import cache
from functools import lru_cache
from typing import Dict,List,Optional,Any,Union
import hashlib
from hashlib import md5
from django.db.models import Subquery, ExpressionWrapper,Window, Func, OuterRef, Sum, Case, When,Value, CharField,IntegerField,DecimalField,Prefetch,FloatField,ExpressionWrapper
from django.db.models.functions import Coalesce,Cast,Concat,RowNumber
from decimal import Decimal
from college_compare.models import (
    College, CollegeReviews,Domain,CollegeFacility,CollegePlacement,CollegePlacementCompany,RankingParameters,Company,RankingUploadList,Course,FeeBifurcation,Exam,Ranking,CollegeAccrediationApproval,ApprovalsAccrediations,CourseApprovalAccrediation
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

# Suppress Elasticsearch warnings
warnings.filterwarnings("ignore", category=ElasticsearchWarning)

from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)




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
        key = '_'.join(map(str, args))
        return md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_graduation_outcome_score(college_ids: List[int], year: Optional[int] = None) -> Dict[int, float]:
        """
        Fetch the Graduation Outcome Score for a list of colleges from the RankingParameters table.
        Optionally filter the scores by a specific year.
        """
        try:
            filters = Q(name__icontains="Graduation Outcomes", ranking_upload__college_id__in=college_ids)
            if year:
                filters &= Q(ranking_upload__ranking__year=year)

            grad_outcome_scores = (
                RankingParameters.objects
                .filter(filters)
                .values('ranking_upload__college_id')
                .annotate(graduation_outcome_score=Max('score'))
            )

            grad_outcome_score_dict = {
                item['ranking_upload__college_id']: item['graduation_outcome_score']
                for item in grad_outcome_scores
            }

            return grad_outcome_score_dict

        except Exception as e:
            logger.error("Error fetching Graduation Outcome Score: %s", traceback.format_exc())
            raise

    @staticmethod
    def fetch_ranking_data(college_ids: List[int], selected_domains: Dict[int, str], year: Optional[int] = None) -> Dict:
        try:
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
            if not college_ids:
                raise NoDataAvailableError("No valid college IDs provided.")

            logger.debug(f"Fetching ranking data with college_ids: {college_ids}, selected_domains: {selected_domains}, year: {year}")

            cache_key_parts = ['ranking_data', year, '-'.join(map(str, college_ids))]
            for cid in college_ids:
                cache_key_parts.append(f"{cid}-{selected_domains.get(cid, 'NA')}")
            cache_key = RankingAccreditationHelper.get_cache_key(*cache_key_parts)

            def fetch_data():
                try:
                    year_filter = Q(ranking__year=year) if year else Q()

                    rankings = []
                    for college_id in college_ids:
                        selected_domain = selected_domains.get(college_id)
                        if not selected_domain:
                            rankings.append({"college_id": college_id})
                            continue

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
                        min_other_ranked_domain = other_ranked_domain_subquery.values('other_ranked_domain')[2:3]




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
                                            Max(Case(
                                                When(Q(ranking__ranking_authority='NIRF') & Q(ranking__ranking_entity='Overall'), then=F('overall_rank')),
                                                default=None
                                            )),
                                            output_field=CharField()
                                        ),
                                        Value('NA', output_field=CharField())
                                    ),
                                    nirf_domain_rank=Coalesce(
                                        Cast(
                                            Max(Case(
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
                                    domain_name=Value(formatted_domain_name, output_field=CharField()),  # Add formatted domain name
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
                            'name': college['name'],
                            'ownership': college['ownership'],
                            'location': college['location'],
                        }
                        for college in College.objects.filter(id__in=college_ids)
                        .select_related('location')
                        .values('id', 'name', 'ownership', 'location')
                    }

                    graduation_outcome_scores = RankingAccreditationHelper.fetch_graduation_outcome_score(college_ids, year=year)

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
    def get_state_and_ownership_ranks(
        college_ids: List[int], selected_domains: Dict[int, str], year: int
    ) -> Dict[str, Dict]:
        """
        Gets state-wise and ownership-wise ranks based on overall ranks for given college IDs.
        Supports different domains for different colleges.
        
        Args:
            college_ids: List of college IDs
            selected_domains: Dictionary mapping college IDs to their respective domain IDs
            year: Year for ranking data
        """
        try:
            result = {}

            domain_groups = {}
            for college_id in college_ids:
                domain_id = selected_domains[college_id]
                if domain_id not in domain_groups:
                    domain_groups[domain_id] = []
                domain_groups[domain_id].append(college_id)
            
            for domain_id, domain_college_ids in domain_groups.items():
                base_queryset = RankingUploadList.objects.filter(
                    ranking__ranking_stream=domain_id,
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

                if not all_ranked_colleges:
                    raise NoDataAvailableError("No ranking data available for the provided college IDs and year.")

                state_ranks = {}
                college_details = {}
                ownership_groups = {} 

                for college in all_ranked_colleges:
                    try:
                        college_id = college['college_id']
                        state_id = college['college__location__state_id']
                        ownership = college['college__ownership']
                        overall_rank = int(college['overall_rank'])

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

                        if ownership not in ownership_groups:
                            ownership_groups[ownership] = []
                        ownership_groups[ownership].append({
                            'college_id': college_id,
                            'overall_rank': overall_rank
                        })

                    except ValueError as e:
                        logger.error(f"Invalid overall_rank for college_id {college.get('college_id')}: {college.get('overall_rank')}")
                        continue

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

                for idx, college_id in enumerate(domain_college_ids):
                    college_key = f"college_{idx + 1}"
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

                    result[college_key] = {
                        "college_id": college_id,
                        "domain": domain_id,
                        "state_rank_display": (
                            f"{state_rank}{get_ordinal_suffix(state_rank)} out of {state_total} in {state_name}"
                            if isinstance(state_rank, int) else "Not Available"
                        ),
                        "ownership_rank_display": (
                            f"{ownership_rank}{get_ordinal_suffix(ownership_rank)} out of {ownership_total} in {ownership_type} Institutes"
                            if isinstance(ownership_rank, int) else "Not Available"
                        ),
                    }

            if not result:
                raise NoDataAvailableError("No data available for the provided parameters.")

            return result

        except NoDataAvailableError as nde:
            logger.warning(f"No data available: {nde}")
            raise

        except Exception as e:
            logger.error(f"Error calculating state and ownership ranks: {traceback.format_exc()}")
            raise



class MultiYearRankingHelper:
    @staticmethod
    def fetch_multi_year_ranking_data(
        college_ids: List[int], 
        selected_domains: Dict[int, str], 
        years: List[int]
    ) -> Dict:
        """
        Fetch 5 years of ranking and accreditation data for colleges with different domains.
        
        Args:
            college_ids: List of college IDs
            selected_domains: Dictionary mapping college IDs to their respective domain IDs
            years: List of years to fetch data for
        """
        try:
            if not years or len(years) != 5:
                raise ValueError("Exactly 5 years must be provided.")
            
            result_dict = {
                f"college_{i + 1}": {
                    "college_id": college_id,
                    "domain": selected_domains[college_id]
                } for i, college_id in enumerate(college_ids)
            }
    
            data_found = False  
            
            for year in years:
                yearly_data = RankingAccreditationHelper.fetch_ranking_data(
                    college_ids, 
                    selected_domains,
                    year
                )
                
                if not yearly_data:
                    continue  
                
                data_found = True  
                
                for key, data in yearly_data.items():
                    college = result_dict.get(key, {})
                    
                    college.setdefault("college_name", data.get("college_name", "NA"))
                    college.setdefault("nirf_overall_rank", []).append(data.get("nirf_overall_rank", "NA"))
                    college.setdefault("nirf_domain_rank", []).append(data.get("nirf_domain_rank", "NA"))
                    college.setdefault("graduation_outcome_scores", []).append(data.get("graduation_outcome_score", "NA"))
                    
                    college.setdefault("other_ranked_domain", [])
                    if "nirf_domain_rank" in data and data["nirf_domain_rank"] != "NA":
                        domain_id = selected_domains[college["college_id"]]
                        other_domain_entry = f"{domain_id} (NIRF {data['nirf_domain_rank']})"
                        college["other_ranked_domain"].append(other_domain_entry)

                    result_dict[key] = college

            if not data_found:
                raise NoDataAvailableError("No ranking or accreditation data is available for the provided college IDs and years.")
            
            return result_dict

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
        Fetch ranking data for given colleges and year range.
        """
        try:
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
        except (ValueError, TypeError):
            raise ValueError("college_ids must be a flat list of integers or strings.")

        cache_key = RankingGraphHelper.get_cache_key(
            'ranking_graph__insight_____version3', '-'.join(map(str, college_ids)), start_year, end_year, domain_id, ranking_entity
        )

        def fetch_data():
            year_range = list(range(start_year, end_year + 1))
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
            
            if not rankings:
                raise NoDataAvailableError(f"No ranking data found for college IDs {college_ids} between {start_year} and {end_year}.")
            
            
            max_scores = {}
            for ranking in rankings:
                college_id = ranking['college_id']
                year = ranking['ranking__year']
                score = ranking['overall_score']
                
            
                if score is not None and score < 100:
                    key = (college_id, year)
                    if key not in max_scores or (max_scores[key] is None or score > max_scores[key]):
                        max_scores[key] = score

        
            college_order = {college_id: idx for idx, college_id in enumerate(college_ids)}
            result_dict = {
                f"college_{i + 1}": {"college_id": college_id, "data": {str(year): "NA" for year in year_range}}
                for i, college_id in enumerate(college_ids)
            }

            for (college_id, year), max_score in max_scores.items():
                college_key = f"college_{college_order[college_id] + 1}"
                result_dict[college_key]["data"][str(year)] = max_score

            return result_dict

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 7)
    
   

   

    @staticmethod
    def prepare_graph_insights(
        college_ids: List[int], start_year: int, end_year: int, selected_domains: Dict[int, int]
    ) -> Dict:
        """Prepare data for the ranking insights graph."""

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
            domain_id = selected_domains.get(college_id)
            try:
                domain_data[college_id] = RankingGraphHelper.fetch_ranking_data(
                    [college_id], start_year, end_year, domain_id=domain_id, ranking_entity='Stream Wise Colleges'
                )
            except NoDataAvailableError as e:
                logger.error(f"No data available for domain ranking: {str(e)}")
                domain_data[college_id] = {}  #

        all_same_domain = len(set(selected_domains.values())) <= 1
        has_na_overall = False  
        has_na_domain = False  

        result_dict = {
            "years": years,
            "data": {
                "overall": {
                    "type": "line" if all_same_domain else "tabular",  
                    "colleges": overall_data
                },
                "domain": {
                    "type": "line" if all_same_domain else "tabular", 
                    "colleges": {}
                }
            },
            "college_names": list(
                College.objects.filter(id__in=college_ids)
                .annotate(order=Case(
                    *[When(id=college_id, then=Value(idx)) for idx, college_id in enumerate(college_ids)],
                    default=Value(len(college_ids)),
                    output_field=IntegerField()
                ))
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



class PlacementInsightHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = '_'.join(map(str, args))
        return md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_placement_stats(college_ids: List[int], selected_domains: Dict[int, int], year: int) -> Dict:
        """
        Fetch placement statistics for a list of colleges and their selected domains for a given year.

        Args:
            college_ids: A list of college IDs.
            selected_domains: A dictionary mapping college IDs to domain IDs.
            year: The year for which to fetch placement stats.

        Returns:
            A dictionary containing placement statistics, keyed by college IDs.
        """
        try:
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
            if not college_ids:
                raise NoDataAvailableError("No valid college IDs provided.")

            cache_key_parts = ['placement__stats_____insights_v1', year, '-'.join(map(str, college_ids))]
            for cid in college_ids:
                cache_key_parts.append(f"{cid}-{selected_domains.get(cid, 'NA')}")
            cache_key = PlacementInsightHelper.get_cache_key(*cache_key_parts)

            def fetch_data():
                try:
                    placement_stats = []
                    for college_id in college_ids:
                        domain_id = selected_domains.get(college_id)
                        if not domain_id:
                            logger.warning(f"No selected domain found for college_id: {college_id}")
                            placement_stats.append({"college_id": college_id})
                            continue

                        domain = Domain.objects.filter(id=domain_id).first()
                        domain_name = DomainHelper.format_domain_name(domain.old_domain_name) if domain else None

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
                        if college_placement_data:
                            college_placement_data['domain_name'] = domain_name
                            placement_stats.append(college_placement_data)
                        else:
                            logger.warning(f"No placement data found for college_id: {college_id}, domain_id: {domain_id}, year: {year}")
                            placement_stats.append({"college_id": college_id, 'domain_name': domain_name, "domain_id": domain_id})

                    if not placement_stats:
                        raise NoDataAvailableError("No placement statistics data available.")

                    college_details = {
                        college['id']: {
                            'name': college['name'],
                        }
                        for college in College.objects.filter(id__in=college_ids)
                        .values('id', 'name')
                    }

                    result_dict = {}
                    for idx, college_id in enumerate(college_ids, start=1):
                        stats = next((s for s in placement_stats if s.get('college_id') == college_id), {})
                        college_data = college_details.get(college_id, {})

                        result_dict[f"college_{idx}"] = {
                            "college_id": college_id,
                            "college_name": college_data.get('name', 'NA') or 'NA',
                            "total_offers": stats.get('total_offers', 0) or 0,
                            "total_students_placed_in_domain": stats.get('no_placed', "NA") or "NA",
                            "highest_domestic_salary_lpa": stats.get('max_salary_dom', 0) or 0,
                            "highest_international_salary_cr": stats.get('max_salary_inter', 0) or 0,
                            "average_salary_lpa": format_fee(stats.get('avg_salary', 0)),
                            "median_salary_lpa": format_fee(stats.get('median_salary', 0)),
                            "domain_id": stats.get('stream_id'),
                            "domain_name": stats.get('domain_name', 'NA'),
                        }

                    return result_dict

                except NoDataAvailableError:
                    raise
                except Exception as e:
                    logger.error(f"Error fetching placement stats comparison data: {traceback.format_exc()}")
                    raise

            return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 365)

        except NoDataAvailableError as e:
            logger.warning(str(e))
            raise
        except Exception as e:
            logger.error("Error in fetch_placement_stats: %s", traceback.format_exc())
            raise

    @staticmethod
    def compare_placement_stats(stats_data: Dict) -> Dict:
        """
        Compare placement statistics for the given data.

        Args:
            stats_data: A dictionary containing placement statistics.

        Returns:
            A dictionary with the compared statistics.
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
        selected_domains: Dict[int, int],
        year: int
    ) -> Dict:
        """
        Fetches and processes placement insights for multiple colleges, allowing different domains per college.
        
        Args:
            college_ids: A list of college IDs
            selected_domains: A dictionary mapping college IDs to domain IDs
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
            cache_key_parts.append(f"{cid}-{selected_domains.get(cid, 'NA')}")
        cache_key = cls.get_cache_key(*cache_key_parts)

        def fetch_data() -> Dict:
            """Inner function to fetch and process placement data."""
            try:
                
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

                
                all_same_domain = len(set(selected_domains.values())) <= 1
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




class CourseFeeComparisonHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = '_'.join(map(str, args))
        return md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_exams_for_courses(course_ids: List[int]) -> Dict[int, Dict]:
        exams_map = defaultdict(dict)

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

        cache_key = FeesHelper.get_cache_key('fees_comparisons', '-'.join(map(str, course_ids)), intake_year)
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
                                When(fees__category='sT', then=F('fees__total_fees')),
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
                    tuition_fees = CollegeCourseFee.get_total_tuition_fee_by_course(course_id, current_year-1)
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
                colleges = {college.id: college.name for college in College.objects.filter(id__in=college_ids)}

       
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
                            "college_name": colleges.get(college_id, 'Unknown College'),
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
                            "college_name": colleges.get(college_id, 'Unknown College'),
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
        return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 365)
    
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
        level: int, 
        selected_domains: Dict[int, int]  
    ) -> Dict:
        """
        Fetch Class Profile data for a list of colleges, considering selected domains.

        Args:
            college_ids (List[int]): List of college IDs to filter.
            year (int): Year of the placement.
            intake_year (int): Intake year of students.
            level (int): Level of course.
            selected_domains (Dict[int, int]): A dictionary mapping college IDs to domain IDs.

        Returns:
            Dict: Class profile data for each college.
        """
       
        college_ids = [item for sublist in college_ids for item in (sublist if isinstance(sublist, list) else [sublist])]
        
        logger.debug(f"Fetching class profiles for college_ids: {college_ids} with selected domains: {selected_domains}")

        cache_key = ClassProfileHelper.get_cache_key(
            'Class_Profiles', '-'.join(map(str, sorted(college_ids))), year, intake_year, level,selected_domains
        )

        def fetch_data():
            try:
                results = (
                    College.objects.filter(
                        id__in=college_ids,
                        collegeplacement__year=year,
                        collegeplacement__intake_year=intake_year,
                        collegeplacement__levels=level,
                        collegeplacement__stream_id__in=list(selected_domains.values())  # Filter by domains
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

        return cache.get_or_set(cache_key, fetch_data, 3600*24*7)




class ProfileInsightsHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = '_'.join(str(arg) for arg in args)
        return md5(key.encode()).hexdigest()

    @staticmethod
    def validate_selected_domains(selected_domains):
        if not isinstance(selected_domains, dict):
            raise TypeError("selected_domains must be a dictionary with college_id as keys and domain_id as values.")

    @staticmethod
    def fetch_student_faculty_ratio(
        college_ids: List[int],
        selected_domains: Dict[int, int],
        year: int,
        intake_year: int,
        level: int = 1,
    ) -> Dict[str, Dict]:
        ProfileInsightsHelper.validate_selected_domains(selected_domains)

        cache_key = ProfileInsightsHelper.get_cache_key(
            'student__faculty__ratio', '-'.join(map(str, college_ids)), year, intake_year, level
        )

        def fetch_data():
            latest_year = (
                CollegePlacement.objects
                .filter(college_id__in=college_ids)
                .aggregate(Max('year'))['year__max'] or year
            )

            query_result = []
            for college_id in college_ids:
                domain_id = selected_domains.get(college_id)
                if not domain_id:
                    continue

                result = (
                    College.objects.filter(id=college_id)
                    .annotate(
                        students=Coalesce(
                            Sum(
                                Case(
                                    When(
                                        Q(collegeplacement__intake_year=intake_year) &
                                        Q(collegeplacement__year=latest_year) &
                                        Q(collegeplacement__stream_id=domain_id),
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
                    )
                    .values('id', 'students', 'faculty')
                )

                query_result.extend(result)

            import time
            current_year = time.localtime().tm_year
            visualization_type = "horizontal bar"
            result = {"year_tag": current_year - 1}

            for idx, data in enumerate(query_result, 1):
                if data['faculty'] > 0 and data['students'] > 0:
                    ratio = (data['students'] / data['faculty']) * 100
                else:
                    ratio = None
                    visualization_type = "tabular"

                result[f"college_{idx}"] = {
                    "college_id": str(data['id']),
                    "total_students": data['students'] or "NA",
                    "total_faculty": data['faculty'] or "NA",
                    "student_faculty_ratio_percentage": round(ratio, 2) if ratio is not None else "NA",
                    "data_status": "complete" if ratio is not None else "incomplete"
                }

            result["type"] = visualization_type
            return result

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24)

    @staticmethod
    def fetch_student_demographics(
        college_ids: List[int],
        selected_domains: Dict[int, int],
        year: int,
        intake_year: int,
        level: int = 1
    ) -> Dict[str, Dict]:
        ProfileInsightsHelper.validate_selected_domains(selected_domains)

        cache_key = ProfileInsightsHelper.get_cache_key(
            'student___demographics______', '-'.join(map(str, college_ids)), year, intake_year, level
        )

        def fetch_data():
            latest_year = (
                CollegePlacement.objects
                .filter(college_id__in=college_ids)
                .aggregate(Max('year'))['year__max'] or year
            )

            query_result = []
            for college_id in college_ids:
                domain_id = selected_domains.get(college_id)
                if not domain_id:
                    continue

                result = (
                    CollegePlacement.objects.filter(
                        college_id=college_id,
                        intake_year=intake_year,
                        year=latest_year,
                        stream_id=domain_id
                    )
                    .values('college_id')
                    .annotate(
                        total_students=Coalesce(Sum('total_students'), Value(0, output_field=IntegerField())),
                        outside_state=Coalesce(Sum('outside_state'), Value(0, output_field=IntegerField()))
                    )
                )

                # Check if results are found, else handle missing data
                if not result:
                    query_result.append({
                        'college_id': college_id,
                        'total_students': 0,
                        'outside_state': 0
                    })
                else:
                    query_result.extend(result)

            import time
            current_year = time.localtime().tm_year
            visualization_type = "horizontal bar"
            result = {"year_tag": current_year - 1}

            for idx, data in enumerate(query_result, 1):
                outside_state_percentage = (
                    (data['outside_state'] / data['total_students'] * 100)
                    if data['total_students'] > 0 else None
                )

                if outside_state_percentage is None:
                    visualization_type = "tabular"

                result[f"college_{idx}"] = {
                    "college_id": str(data['college_id']),
                    "total_students": data['total_students'] or "NA",
                    "students_outside_state": data['outside_state'] or "NA",
                    "percentage_outside_state": round(outside_state_percentage, 2) if outside_state_percentage is not None else "NA",
                    "data_status": "complete" if outside_state_percentage is not None else "incomplete"
                }

            result["type"] = visualization_type
            return result

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24)


    @staticmethod
    def fetch_gender_diversity(
        college_ids: List[int],
        selected_domains: Dict[int, int],
        year: int,
        intake_year: int,
        level: int = 1
    ) -> Dict[str, Dict]:
        ProfileInsightsHelper.validate_selected_domains(selected_domains)

        cache_key = ProfileInsightsHelper.get_cache_key(
            'gender___diversity___', '-'.join(map(str, college_ids)), year, intake_year, level
        )

        def fetch_data():
            latest_year = (
                CollegePlacement.objects
                .filter(college_id__in=college_ids)
                .aggregate(Max('year'))['year__max'] or year
            )

            query_result = []
            for college_id in college_ids:
                domain_id = selected_domains.get(college_id)
                if not domain_id:
                    continue

                result = (
                    CollegePlacement.objects.filter(
                        college_id=college_id,
                        intake_year=intake_year,
                        year=latest_year,
                        stream_id=domain_id
                    )
                    .values('college_id')
                    .annotate(
                        male_students=Coalesce(Sum('male_students'), Value(0, output_field=IntegerField())),
                        female_students=Coalesce(Sum('female_students'), Value(0, output_field=IntegerField())),
                        total_students=F('male_students') + F('female_students')
                    )
                )

         
                if not result:
                    query_result.append({
                        'college_id': college_id,
                        'male_students': 0,
                        'female_students': 0,
                        'total_students': 0
                    })
                else:
                    query_result.extend(result)

            import time
            current_year = time.localtime().tm_year
            visualization_type = "horizontal bar"
            result = {"year_tag": current_year - 1}

            for idx, data in enumerate(query_result, 1):
                if data['total_students'] > 0:
                    male_percentage = (data['male_students'] / data['total_students']) * 100
                    female_percentage = (data['female_students'] / data['total_students']) * 100
                else:
                    male_percentage = None
                    female_percentage = None
                    visualization_type = "tabular"
                

                if male_percentage is None or female_percentage is None:
                    visualization_type = "tabular"

                result[f"college_{idx}"] = {
                    "college_id": str(data['college_id']),
                    "male_students": data['male_students'] or "NA",
                    "female_students": data['female_students'] or "NA",
                    "percentage_male": round(male_percentage, 2) if male_percentage is not None else "NA",
                    "percentage_female": round(female_percentage, 2) if female_percentage is not None else "NA",
                    "data_status": "complete" if male_percentage is not None else "incomplete"
                }

            result["type"] = visualization_type
            return result

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24)
    @staticmethod
    def prepare_profile_insights(
        college_ids: List[int],
        year: int,
        intake_year: int,
        selected_domains: Dict[int, int],
        level: int = 1,
    ) -> Dict:
        """
        Prepare comprehensive profile insights including all metrics.
        """
        ProfileInsightsHelper.validate_selected_domains(selected_domains)

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

        unique_domains = set(selected_domains.values())
        visualization_type = "horizontal bar" if len(unique_domains) == 1 else "tabular"

        student_faculty_ratio_data = ProfileInsightsHelper.fetch_student_faculty_ratio(
            college_ids=college_ids,
            selected_domains=selected_domains,
            year=year,
            intake_year=intake_year,
            level=level
        )

        student_demographics_data = ProfileInsightsHelper.fetch_student_demographics(
            college_ids=college_ids,
            selected_domains=selected_domains,
            year=year,
            intake_year=intake_year,
            level=level
        )

        gender_diversity_data = ProfileInsightsHelper.fetch_gender_diversity(
            college_ids=college_ids,
            selected_domains=selected_domains,
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
            "college_details": ordered_college_details,  # Returning the reordered college details
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
        key = '_'.join(str(arg) for arg in args)
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
                es_client = Elasticsearch([es_host], retry_on_timeout=True, max_retries=3)

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
        cache_key = self.get_cache_key("api_summary", review_text, college_name)
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
            'College_Reviews_Summary_new_',
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
    def get_recent_reviews(college_ids: List[int], course_ids: Optional[List[int]] = None, limit: int = 3) -> Dict:
        """
        Get recent reviews for colleges with caching.

        Args:
            college_ids (List[int]): List of college IDs to filter
            course_ids (Optional[List[int]]): List of course IDs to filter reviews by
            limit (int, optional): Maximum number of reviews per college. Defaults to 3.

        Returns:
            Dict: Recent reviews for each college
        """
    
        college_ids = [item for sublist in college_ids for item in (sublist if isinstance(sublist, list) else [sublist])]
        
        if course_ids:
            course_ids = [item for sublist in course_ids for item in (sublist if isinstance(sublist, list) else [sublist])]
        
    
        cache_key = CollegeReviewsHelper.get_cache_key(
            'Recent_Reviews',
            '-'.join(map(str, sorted(college_ids))),
            '-'.join(map(str, sorted(course_ids or []))),
            limit
        )

        def fetch_recent():
            try:
                
                filters = {
                    'college_id__in': college_ids,
                    'title__isnull':False
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
                    result_dict[key] = reviews_by_college.get(college_id, [])

                return result_dict

            except Exception as e:
                logger.error(f"Error fetching recent reviews: {e}")
                raise

    
        return cache.get_or_set(cache_key, fetch_recent, 3600*24*7)

    



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