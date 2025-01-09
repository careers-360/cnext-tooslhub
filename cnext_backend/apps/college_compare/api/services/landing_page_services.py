
#landing_page_services.py

from django.db.models import (
    Q, Count, F, Case, When, Value, IntegerField, Avg, Window, Prefetch, 
    FloatField, CharField, Sum, OuterRef, Subquery
)
from django.db.models.functions import Coalesce, RowNumber
from django.db.models.functions import Coalesce, RowNumber, Concat, Upper, Lower, Substr
from college_compare.models import College, Course, Domain, CollegeCompareData, CollegeDomain
from django.shortcuts import render
from college_compare.api.helpers.landing_page_helpers import *
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import List, Dict, Tuple
from collections import defaultdict
from functools import partial
from django.template.base import VariableDoesNotExist


logger = logging.getLogger(__name__)

from django.contrib.postgres.aggregates import ArrayAgg


from multiprocessing import Pool,cpu_count


class PeerComparisonService:
    @classmethod
    def get_peer_comparisons(cls, uid=None):
        user_context = UserContextHelper.get_user_context(uid)
        cache_key = CacheHelper.get_cache_key(
            "Peers_Comparison", user_context.get('domain_id'), user_context.get('education_level')
        )
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        result = {"Undergraduate": {}, "Postgraduate": {}}
        try:
            valid_domains = DomainHelper.get_valid_domains()
            user_domain_id = user_context.get('domain_id')
            ordered_domains = sorted(valid_domains, key=lambda domain: domain.id != user_domain_id)

            valid_course_ids = CacheHelper.get_or_set(
                "valid_course_ids", lambda: CollegeDomain.objects.filter(
                    status=True, domain__in=valid_domains
                ).values_list('college_course_id', flat=True).distinct(), timeout=3600 * 24 * 31
            )

            domain_level_combinations = CacheHelper.get_or_set(
                "domain_level_combinations",
                lambda: CollegeCompareData.objects.filter(
                    college_1__isnull=False, college_2__isnull=False,
                    course_1__in=valid_course_ids, course_2__in=valid_course_ids
                ).annotate(
                    level=Case(
                        When(Q(course_1__level=1) | Q(course_2__level=1), then=Value(1)),
                        When(Q(course_1__level=2) | Q(course_2__level=2), then=Value(2)),
                        default=Value(1),
                        output_field=IntegerField()
                    ),
                    domain_id=F('course_1__collegedomain_course__domain')
                ).values('domain_id', 'level').distinct(), timeout=3600 * 24 * 31
            )

            num_processes = min(cpu_count(), len(domain_level_combinations))
            with Pool(processes=num_processes) as pool:
                all_comparisons = pool.map(
                    partial(cls._fetch_comparisons_for_domain_level, valid_course_ids=valid_course_ids),
                    domain_level_combinations
                )

            all_comparisons = [comp for sublist in all_comparisons for comp in sublist]

            college_ids = {comp['college_id_1'] for comp in all_comparisons}
            college_ids.update(comp['college_id_2'] for comp in all_comparisons)

            colleges = College.objects.filter(id__in=college_ids, published='published').select_related('location')
            colleges_dict = {college.id: college for college in colleges}

            domain_names = {
                domain.id: DomainHelper.format_domain_name(domain.old_domain_name)
                for domain in ordered_domains
            }

            for level in ["Undergraduate", "Postgraduate"]:
                for domain in domain_names.values():
                    result[level][domain] = []

            for comparison in all_comparisons:
                domain_name = domain_names.get(comparison['domain_id'])
                if not domain_name:
                    continue
                level_str = "Undergraduate" if comparison['level'] == 1 else "Postgraduate"
                college_1 = colleges_dict.get(comparison['college_id_1'])
                college_2 = colleges_dict.get(comparison['college_id_2'])
                if not (college_1 and college_2):
                    continue
                comparison_obj = {
                    "college_1": {
                        "name": college_1.name,
                        "short_name": college_1.short_name,
                        "logo": CollegeDataHelper.get_college_logo(college_1.id),
                        "location": CollegeDataHelper.get_location_string(college_1.location),
                        'college_id': comparison['college_id_1']
                    },
                    "college_2": {
                        "name": college_2.name,
                        "short_name": college_2.short_name,
                        "logo": CollegeDataHelper.get_college_logo(college_2.id),
                        "location": CollegeDataHelper.get_location_string(college_2.location),
                        "college_id": comparison['college_id_2']
                    },
                    "compare_count": comparison['compare_count'],
                    "college_ids": f"{comparison['college_id_1']},{comparison['college_id_2']}"
                }
                if domain_name in result[level_str] and len(result[level_str][domain_name]) < 10:
                    if not any(c['college_ids'] == comparison_obj['college_ids'] for c in result[level_str][domain_name]):
                        result[level_str][domain_name].append(comparison_obj)

            for level in ["Undergraduate", "Postgraduate"]:
                result[level] = {domain: comparisons for domain, comparisons in result[level].items() if comparisons}

            prioritized_result = {
                "Postgraduate": result["Postgraduate"],
                "Undergraduate": result["Undergraduate"]
            } if user_context.get('education_level') == 2 else result

            cache.set(cache_key, prioritized_result, timeout=3600 * 24 * 7)
            return prioritized_result

        except Exception as e:
            logger.error(f"Error occurred: {str(e)}", exc_info=True)
            return {
                "error": {
                    "message": "An unexpected error occurred while processing your request.",
                    "exception_type": str(type(e).__name__)
                }
            }

    @staticmethod
    def _fetch_comparisons_for_domain_level(combo, valid_course_ids):
        domain_id = combo['domain_id']
        level = combo['level']
        cache_key = f"domain_level_comparisons_{domain_id}_{level}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        comparisons = list(
            CollegeCompareData.objects.filter(
                college_1__isnull=False, college_2__isnull=False,
                course_1__in=valid_course_ids, course_2__in=valid_course_ids,
                course_1__collegedomain_course__domain=domain_id,
                course_2__collegedomain_course__domain=domain_id,
                course_1__level=level, course_2__level=level
            )
            .annotate(
                college_id_1=Case(
                    When(college_1__lt=F('college_2'), then=F('college_1')),
                    default=F('college_2'),
                    output_field=IntegerField()
                ),
                college_id_2=Case(
                    When(college_1__gt=F('college_2'), then=F('college_1')),
                    default=F('college_2'),
                    output_field=IntegerField()
                ),
                domain_id=F('course_1__collegedomain_course__domain'),
                level=Value(level, output_field=IntegerField())
            )
            .filter(college_id_1__lt=F('college_id_2'))
            .values('college_id_1', 'college_id_2', 'domain_id', 'level')
            .annotate(compare_count=Count('id'))
            .order_by('-compare_count')[:10]
        )

        cache.set(cache_key, comparisons, timeout=3600 * 24 * 31)
        return comparisons



class TopCollegesCoursesService:
    BATCH_SIZE = 5000
    CACHE_TIMEOUT = 3600 * 168
    MAX_WORKERS = 8

    @classmethod
    def get_top_colleges_courses(cls, uid: int = None) -> Dict:
        """Get top colleges and courses with optimized batch processing using multiprocessing."""
        try:
            user_context = UserContextHelper.get_user_context(uid)
            cache_key = f"top_colleges_courses_v5_{user_context.get('domain_id')}"

            if cached := cache.get(cache_key):
                return cached

            
            with Pool(processes=cls.MAX_WORKERS) as pool:
                colleges_future = pool.apply_async(partial(cls._get_top_colleges, user_context))
                courses_future = pool.apply_async(partial(cls._get_top_courses, user_context))

                result = {
                    'colleges': colleges_future.get(),
                    'courses': courses_future.get()
                }

            # Cache the result
            cache.set(cache_key, result, cls.CACHE_TIMEOUT)
            return result

        except Exception as e:
            logger.error(f"Error in get_top_colleges_courses: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    @classmethod
    def _get_top_colleges(cls, user_context: Dict) -> List[Dict]:
        """Get top colleges using batch processing with caching."""
        try:
            domain_id = user_context.get('domain_id')
            
        
            cache_key = f"top_colleges_v5_{domain_id}"

            if cached := cache.get(cache_key):
                return cached

         
            comparison_counts_1 = CollegeCompareData.objects.filter(
                college_1=OuterRef('id')
            ).values('college_1').annotate(
                count=Count('*')
            ).values('count')

            comparison_counts_2 = CollegeCompareData.objects.filter(
                college_2=OuterRef('id')
            ).values('college_2').annotate(
                count=Count('*')
            ).values('count')

       
            colleges = College.objects.filter(
                published='published'
            ).annotate(
                comparisons_as_college_1=Coalesce(Subquery(comparison_counts_1), 0),
                comparisons_as_college_2=Coalesce(Subquery(comparison_counts_2), 0),
   
                total_comparisons=(
                    F('comparisons_as_college_1') +
                    F('comparisons_as_college_2') 
                  
                )
            ).select_related('location')

            if domain_id:
                colleges = colleges.filter(
                    collegedomain__domain_id=domain_id,
                    collegedomain__status=True
                ).distinct()

            colleges = colleges.order_by('-total_comparisons')[:10]
            result = [cls._process_college(college) for college in colleges]

            # Cache the result
            cache.set(cache_key, result, cls.CACHE_TIMEOUT)
            return result

        except Exception as e:
            logger.error(f"Error in _get_top_colleges: {str(e)}", exc_info=True)
            return []

    
    @classmethod
    def _get_top_courses(cls, user_context: Dict) -> List[Dict]:
        """Get top courses using batch processing with caching."""
        try:
            domain_id = user_context.get('domain_id')
            education_level = user_context.get('education_level')
            cache_key = f"top_courses_v6_{domain_id}"

            if cached := cache.get(cache_key):
                return cached

          
            comparison_counts_1 = CollegeCompareData.objects.filter(
                course_1=OuterRef('id')
            ).values('course_1').annotate(
                count=Count('*')
            ).values('count')

            comparison_counts_2 = CollegeCompareData.objects.filter(
                course_2=OuterRef('id')
            ).values('course_2').annotate(
                count=Count('*')
            ).values('count')

           

            courses = Course.objects.filter(
                status=True
            ).annotate(
                comparisons_as_course_1=Coalesce(Subquery(comparison_counts_1), 0),
                comparisons_as_course_2=Coalesce(Subquery(comparison_counts_2), 0),
                total_comparisons=(
                    F('comparisons_as_course_1') +
                    F('comparisons_as_course_2') 
                  
                )
            ).select_related(
                'college', 'degree'
            )

            if domain_id:
                courses = courses.filter(
                    collegedomain_course__domain_id=domain_id,
                    collegedomain_course__status=True
                ).distinct()

            courses = courses.order_by('-total_comparisons')[:10]
            result = [cls._process_course(course) for course in courses]

            cache.set(cache_key, result, cls.CACHE_TIMEOUT)
            return result

        except Exception as e:
            logger.error(f"Error in _get_top_courses: {str(e)}", exc_info=True)
            return []


    @staticmethod
    def _process_college(college: College) -> Dict:
        """ """
        try:
            return {
                'college_short_name': college.short_name or 'NA',
                'college_full_name': college.name,
                'college_id': college.id,
                'location': college.location.loc_string if college.location else "N/A",
                'ownership': college.get_ownership_display(),
                'nirf_rank': CollegeDataHelper.get_nirf_rank(college.id),
                'college_logo':  CollegeDataHelper.get_college_logo(college.id),
                'total_comparisons': college.total_comparisons,
                'avg_review_rating': CollegeDataHelper.get_avg_rating(college.id)
            }
        except Exception as e:
            logger.error(f"Error processing college {college.id}: {str(e)}")
            return {}

    @staticmethod
    def _process_course(course: Course) -> Dict:
        """"""
        try:
            return {
                'course_name': course.course_name,
                'college_short_name': course.college.short_name or 'NA',
                'college_full_name': course.college.name,
                'course_id': course.id,
                'college_id': course.college.id,
                'ownership': course.college.get_ownership_display(),
                'nirf_rank': CollegeDataHelper.get_nirf_rank(course.college.id),
                'college_logo':  CollegeDataHelper.get_college_logo(course.college.id),
                'total_comparisons': course.total_comparisons,
                'degree_name': course.degree.name if course.degree else 'NA',
                'degree_id': course.degree.id if course.degree else None
            }
        except Exception as e:
            logger.error(f"Error processing course {course.id}: {str(e)}")
            return {}




