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
    College, CollegeReviews,Domain,CollegeFacility,CollegePlacement,RankingUploadList,Course,FeeBifurcation,Exam,Ranking,CollegeAccrediationApproval,ApprovalsAccrediations,CourseApprovalAccrediation
)

from college_compare.models import *
from django.contrib.postgres.aggregates import StringAgg
from django.db.models.expressions import RawSQL
from collections import defaultdict

from .landing_page_helpers import DomainHelper



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
    def fetch_ranking_data(college_ids: List[int], selected_domain: str, year: Optional[int] = None) -> Dict:
        """
        Fetch ranking and accreditation details for a list of colleges, optionally filtered by year.
        """
        try:
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
        except (ValueError, TypeError):
            logger.error("Invalid college_ids provided: %s", college_ids)
            raise ValueError("college_ids must be a list of integers or strings.")

        logger.debug(f"Fetching ranking data with college_ids: {college_ids}, selected_domain: {selected_domain}, year: {year}")

        cache_key = RankingAccreditationHelper.get_cache_key('Ranking_Data_v8', selected_domain, year, '-'.join(map(str, college_ids)))

        def fetch_data():
            try:
               
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

               
                college_names = dict(
                    College.objects.filter(id__in=college_ids).values_list('id', 'name')
                )

                
                result_dict = {}
                for idx, ranking in enumerate(rankings, start=1):
                    college_id = ranking['college_id']

                    result_dict[f"college_{idx}"] = {
                        "college_id": college_id,
                        "college_name": college_names.get(college_id, 'NA'),
                        "careers360_overall_rank": ranking.get('careers360_overall_rank') or 'NA',
                        "careers360_domain_rank": ranking.get('careers360_domain_rank') or 'NA',
                        "nirf_overall_rank": ranking.get('nirf_overall_rank') or 'NA',
                        "nirf_domain_rank": ranking.get('nirf_domain_rank') or 'NA',
                        "other_ranked_domain": ranking.get('other_ranked_domain') or 'NA',
                        "domain_name": ranking.get('domain_name') or 'NA',
                        "approvals": approvals_dict.get(college_id, 'NA'),
                        "accreditations": accreditations_dict.get(college_id, 'NA'),
                    }

                return result_dict

            except Exception as e:
                logger.error("Error fetching ranking and accreditation data: %s", traceback.format_exc())
                raise

        return cache.get_or_set(cache_key, fetch_data, 3600 * 24 * 31)
   



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
            College.objects.filter(id__in=college_ids).values_list('name', flat=True)
        )

        return {
            "years": years,
            "overall": {
                "type": "wave",
                "colleges": overall_data
            },
            "domain": {
                "type": "wave",
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
    def fetch_placement_stats(college_ids: List[int], year: int,domain_id:int) -> Dict:
        try:
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
        except (ValueError, TypeError):
            logger.error("Invalid college_ids provided: college_ids=%s", college_ids)
            raise ValueError("college_ids must be a flat list of integers or strings.")

        cache_key = PlacementStatsComparisonHelper.get_cache_key('placement__stats_____comparisons', '-'.join(map(str, college_ids)), year,domain_id)

        def fetch_data():
            try:
                placement_stats = (
                    CollegePlacement.objects.filter(
                        college_id__in=college_ids, 
                        year=year,
                        intake_year=year-3,
                        stream_id=domain_id
                    )
                    .values(
                        'college_id',
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
                result_dict = {f"college_{i+1}": {} for i in range(len(college_ids))}

                for stats in placement_stats:
                    college_id = stats['college_id']
                    idx = college_order[college_id] + 1
                    college_key = f"college_{idx}"
                    domain = Domain.objects.filter(id=domain_id).first()
                    domain_name = DomainHelper.format_domain_name(domain.old_domain_name) if domain else None


                    result_dict[college_key] = {
                        "college_id": stats['college_id'],
                        "total_offers": stats['total_offers'] or 0,
                        "total_students_placed_in_domain": stats['no_placed'] or "N/A",
                        "highest_domestic_salary_lpa": stats['max_salary_dom'] or 0,
                        "highest_international_salary_cr": stats['max_salary_inter'] or 0,
                        "average_salary_lpa": format_fee(stats['avg_salary']),
                        "median_salary_lpa": format_fee(stats['median_salary']),
                        "domain_id":stats['stream_id'],
                        "domain_name":domain_name
                    }

                return result_dict

            except Exception as e:
                logger.error("Error fetching placement stats comparison data: %s", str(e))
                raise

        return cache.get_or_set(cache_key, fetch_data, 3600*24*365)

    @staticmethod
    def compare_placement_stats(stats_data: Dict) -> Dict:
        try:
            result_dict = {}
            for college_key, college_data in stats_data.items():
                result_dict[college_key] = {
                    "college_id": college_data.get("college_id"),
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
        """
        Generate a cache key using MD5 hashing.
        """
        key = '_'.join(map(str, args))
        return md5(key.encode()).hexdigest()

    @staticmethod
    def fetch_fees_details(course_ids: List[int], college_ids: List[int], intake_year: int) -> Dict:
        """
        Fetch fee details for a list of courses and colleges.
        """
        try:
            
            course_ids = [int(course_id) for course_id in course_ids if isinstance(course_id, (int, str))]
            college_ids = [int(college_id) for college_id in college_ids if isinstance(college_id, (int, str))]
        except (ValueError, TypeError):
            logger.error("Invalid course_ids or college_ids provided: course_ids=%s, college_ids=%s", course_ids, college_ids)
            raise ValueError("course_ids and college_ids must be flat lists of integers or strings.")

        logger.debug(f"Fetching fees details with course_ids: {course_ids}, college_ids: {college_ids}, intake_year: {intake_year}")

      
        cache_key = FeesHelper.get_cache_key('fees_detail', '-'.join(map(str, course_ids)), intake_year)

        
        def fetch_data():
            try:
               
                fee_details = (
                    Course.objects.filter(id__in=course_ids, college_id__in=college_ids)
                    .annotate(
                        gn_fees=Coalesce(Sum(Case(
                            When(fees__category='GN', then=F('fees__total_fees')),
                            default=Value(0),
                            output_field=DecimalField() 
                        )), Value(0, output_field=DecimalField())),
                        obc_fees=Coalesce(Sum(Case(
                            When(fees__category='OBC', then=F('fees__total_fees')),
                            default=Value(0),
                            output_field=DecimalField()
                        )), Value(0, output_field=DecimalField())),
                        sc_fees=Coalesce(Sum(Case(
                            When(fees__category='SC', then=F('fees__total_fees')),
                            default=Value(0),
                            output_field=DecimalField()
                        )), Value(0, output_field=DecimalField())),
                        nq_fees=Coalesce(Sum(Case(
                            When(fees__category='NQ', then=F('fees__total_fees')),
                            default=Value(0),
                            output_field=DecimalField()
                        )), Value(0, output_field=DecimalField()))
                    )
                    .values('college_id', 'gn_fees', 'obc_fees', 'sc_fees', 'nq_fees')
                )

               
                scholarships_data = (
                    CollegePlacement.objects.filter(college_id__in=college_ids, intake_year=intake_year)
                    .values('college_id')
                    .annotate(
                        total_gov=Coalesce(Sum('reimbursement_gov', output_field=DecimalField()), Value(0, output_field=DecimalField())),
                        total_institution=Coalesce(Sum('reimbursement_institution', output_field=DecimalField()), Value(0, output_field=DecimalField())),
                        total_private=Coalesce(Sum('reimbursement_private_bodies', output_field=DecimalField()), Value(0, output_field=DecimalField()))
                    )
                )

                
                scholarships_map = {
                    data['college_id']: {
                        'total_gov': data['total_gov'],
                        'total_institution': data['total_institution'],
                        'total_private': data['total_private'],
                        'high_scholarship_authority': FeesHelper.get_high_scholarship_authority(
                            data['total_gov'], data['total_institution'], data['total_private']
                        )
                    }
                    for data in scholarships_data
                }

               
                result_dict = {}
                for idx, fee_detail in enumerate(fee_details, start=1):
                    college_id = fee_detail['college_id']
                    scholarship_data = scholarships_map.get(college_id, {})
                    total_scholarship = (
                        scholarship_data.get('total_gov', 0) +
                        scholarship_data.get('total_institution', 0) +
                        scholarship_data.get('total_private', 0)
                    )

                    result_dict[f"college_{idx}"] = {
                        "college_id": college_id,
                        "gn_fees": format_fee(fee_detail['gn_fees']),
                        "obc_fees": format_fee(fee_detail['obc_fees']),
                        "sc_fees": format_fee(fee_detail['sc_fees']),
                        "nq_fees": format_fee(fee_detail['nq_fees']),
                        "total_scholarship_given": "NA" if total_scholarship == 0 else int(total_scholarship),
                        "high_scholarship_authority": scholarship_data.get('high_scholarship_authority', 'NA')
                    }

                return result_dict
            except Exception as e:
                logger.error("Error fetching fee details: %s", traceback.format_exc())
                raise

        return cache.get_or_set(cache_key, fetch_data, 3600*24*365)

    @staticmethod
    def get_high_scholarship_authority(total_gov, total_institution, total_private) -> str:
        """
        Determines the authority with the highest scholarship amount.
        """
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
            'student_faculty_ratio', '-'.join(map(str, college_ids)), year, intake_year, level
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
            'student_demographics', '-'.join(map(str, college_ids)), year, intake_year, level
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
            'gender_diversity', '-'.join(map(str, college_ids)), year, intake_year, level
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
        college_names = list(
            College.objects.filter(id__in=college_ids)
            .order_by('id')
            .values_list('name', flat=True)
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
            "college_names": college_names
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
    





class CollegeReviewsHelper:
    @staticmethod
    def get_cache_key(*args) -> str:
        key = '_'.join(str(arg) for arg in args)
        return md5(key.encode()).hexdigest()

    @staticmethod
    def get_college_reviews_summary(college_ids: List[int], grad_year: int) -> Dict:
        """
        Get aggregated reviews summary for colleges with caching.

        Args:
            college_ids (List[int]): List of college IDs to filter.
            grad_year (int): Graduation year to filter reviews.

        Returns:
            Dict: Reviews summary data for each college.
        """
       
        college_ids = [item for sublist in college_ids for item in (sublist if isinstance(sublist, list) else [sublist])]
        
      
        logger.debug(f"Fetching review summaries for college_ids: {college_ids}")

        cache_key = CollegeReviewsHelper.get_cache_key(
            'College_Reviews_Summary_V1',
            '-'.join(map(str, sorted(college_ids))),
            grad_year
        )

        def fetch_summary():
            try:
               
                results = (
                    CollegeReviews.objects.filter(
                        college_id__in=college_ids,
                        graduation_year__year=grad_year,
                        status=True
                    )
                    .distinct()
                    .values('college_id')
                    .annotate(
                        grad_year=ExtractYear('graduation_year'),
                      
                        infra_rating=Coalesce(Round(Avg(F('infra_rating') / 20), 1), Value(0.0, output_field=FloatField())),
                        campus_life_ratings=Coalesce(Round(Avg(F('college_life_rating') / 20), 1), Value(0.0, output_field=FloatField())),
                        academics_ratings=Coalesce(Round(Avg(F('overall_rating') / 20), 1), Value(0.0, output_field=FloatField())),
                        value_for_money_ratings=Coalesce(Round(Avg(F('affordability_rating') / 20), 1), Value(0.0, output_field=FloatField())),
                        placement_rating=Coalesce(Round(Avg(F('placement_rating') / 20), 1), Value(0.0, output_field=FloatField())),
                        faculty_rating=Coalesce(Round(Avg(F('faculty_rating') / 20), 1), Value(0.0, output_field=FloatField())),
                        review_count=Count('id')
                    )
                )

              
                reviews_text = (
                    CollegeReviews.objects.filter(
                        college_id__in=college_ids,
                        graduation_year__year=grad_year,
                        status=True
                    )
                    .values('college_id', 'title', 'campus_life', 'college_infra', 
                           'academics', 'placements', 'value_for_money')
                )

               
                text_data = {}
                for review in reviews_text:
                    college_id = review['college_id']
                    if college_id not in text_data:
                        text_data[college_id] = {
                            'keywords': [],
                            'reviews': []
                        }
                    
                    if review['title']:
                        text_data[college_id]['keywords'].append(review['title'])
                    
                    review_text = ' '.join(filter(None, [
                        review['campus_life'],
                        review['college_infra'],
                        review['academics'],
                        review['placements'],
                        review['value_for_money']
                    ]))
                    if review_text:
                        text_data[college_id]['reviews'].append(review_text)

                reviews_data = {}
                for result in results:
                    college_id = result['college_id']
                    college_text = text_data.get(college_id, {'keywords': [], 'reviews': []})
                    
                    reviews_data[college_id] = {
                        **result,
                        'all_keywords': ' '.join(college_text['keywords']) or 'NA',
                        'all_reviews': ' '.join(college_text['reviews']) or 'NA',
                        'college_id': college_id
                    }

             
                result_dict = {}
                for i, college_id in enumerate(college_ids, 1):
                    key = f"college_{i}"
                    result_dict[key] = reviews_data.get(college_id, {
                        'grad_year': grad_year,
                        'infra_rating': 0.0,
                        'campus_life_ratings': 0.0,
                        'academics_ratings': 0.0,
                        'value_for_money_ratings': 0.0,
                        'placement_rating': 0.0,
                        'faculty_rating': 0.0,
                        'review_count': 0,
                        'all_keywords': 'NA',
                        'all_reviews': 'NA',
                        'college_id': college_id
                    })

                return result_dict

            except Exception as e:
                logger.error(f"Error fetching reviews summary: {e}")
                raise

        return cache.get_or_set(cache_key, fetch_summary, 3600)

    @staticmethod
    def get_recent_reviews(college_ids: List[int], limit: int = 3) -> Dict:
        """
        Get recent reviews for colleges with caching.

        Args:
            college_ids (List[int]): List of college IDs to filter.
            limit (int, optional): Maximum number of reviews per college. Defaults to 3.

        Returns:
            Dict: Recent reviews for each college.
        """
      
        college_ids = [item for sublist in college_ids for item in (sublist if isinstance(sublist, list) else [sublist])]
        
       
        logger.debug(f"Fetching recent reviews for college_ids: {college_ids}")

        cache_key = CollegeReviewsHelper.get_cache_key(
            'Recent_Reviews',
            '-'.join(map(str, sorted(college_ids))),
            limit
        )

        def fetch_recent():
            try:
            
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

        return cache.get_or_set(cache_key, fetch_recent, 1800*48) 
    


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