from django.db.models import (
    Q, Count, F, Case, When, Value, IntegerField, Avg, Subquery, Window, Prefetch, FloatField, CharField, Sum
)
from django.db.models.functions import Coalesce, RowNumber, Concat, Upper, Lower, Substr
from college_compare.models import College, Course, Domain, CollegeCompareData, CollegeDomain
from django.shortcuts import render
from college_compare.api.helpers.landing_page_helpers import *
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import List, Dict
from collections import defaultdict
from django.template.base import VariableDoesNotExist
import concurrent.futures

logger = logging.getLogger(__name__)


class PeerComparisonService:
    @classmethod
    def get_peer_comparisons(cls, uid=None):
        user_context = UserContextHelper.get_user_context(uid)
        cache_key = CacheHelper.get_cache_key(
            "Peer_Comparisons", user_context.get('domain_id'), user_context.get('education_level')
        )
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        result = {"Undergraduate": {}, "Postgraduate": {}}
        try:
            # Cache domains and courses for reuse
            valid_domains = DomainHelper.get_valid_domains()
            user_domain_id = user_context.get('domain_id')
            ordered_domains = sorted(valid_domains, key=lambda domain: domain.id != user_domain_id)
            
            valid_course_ids = CacheHelper.get_or_set(
                "valid_course_ids", lambda: CollegeDomain.objects.filter(
                    status=True, domain__in=valid_domains
                ).values_list('college_course_id', flat=True).distinct(), timeout=3600*24*7
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
                ).values('domain_id', 'level').distinct(), timeout=3600*24*7
            )

           
            all_comparisons = []
            with ThreadPoolExecutor(max_workers=8) as executor:
                for combo in domain_level_combinations:
                    domain_id, level = combo['domain_id'], combo['level']
                    comparisons_future = executor.submit(
                        cls._fetch_comparisons_for_domain_level, domain_id, level, valid_course_ids
                    )
                    all_comparisons.extend(comparisons_future.result())

            # Collect college ids
            college_ids = {comp['college_id_1'] for comp in all_comparisons}
            college_ids.update(comp['college_id_2'] for comp in all_comparisons)

           
            
            colleges_dict = {
                college.id: college for college in College.objects.filter(
                    id__in=college_ids, published='published'
                ).select_related('location')
            }

           
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
                        "logo": CollegeDataHelper.get_college_logo(college_1.id),
                        "location": CollegeDataHelper.get_location_string(college_1.location)
                    },
                    "college_2": {
                        "name": college_2.name,
                        "logo": CollegeDataHelper.get_college_logo(college_2.id),
                        "location": CollegeDataHelper.get_location_string(college_2.location)
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

        
            cache.set(cache_key, prioritized_result, timeout=3600 * 24)
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
    def _fetch_comparisons_for_domain_level(domain_id, level, valid_course_ids):
        cache_key = f"domain_level_comparisons_{domain_id}_{level}"

        
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

    
        comparisons = (
            CollegeCompareData.objects.filter(
                college_1__isnull=False, college_2__isnull=False,
                course_1__in=valid_course_ids, course_2__in=valid_course_ids,
                course_1__collegedomain_course__domain=domain_id,
                course_2__collegedomain_course__domain=domain_id,
                course_1__level=level, course_2__level=level
            ).annotate(
                college_id_1=Case(
                    When(college_1__lt=F('college_2'), then=F('college_1')),
                    default=F('college_2')
                ),
                college_id_2=Case(
                    When(college_1__gt=F('college_2'), then=F('college_1')),
                    default=F('college_2')
                ),
                domain_id=F('course_1__collegedomain_course__domain'),
                level=Case(
                    When(course_1__level=1, then=Value(1)),
                    When(course_1__level=2, then=Value(2)),
                    default=Value(1),
                    output_field=IntegerField()
                )
            ).filter(college_id_1__lt=F('college_id_2'))
            .values('college_id_1', 'college_id_2', 'domain_id', 'level')
            .annotate(compare_count=Count('id'))
            .order_by('-compare_count')[:10]
        )

       
        cache.set(cache_key, comparisons, timeout=3600 * 24)  

        return comparisons








class TopCollegesCoursesService:
    CACHE_TIMEOUT = 3600 * 24 
    TOP_N = 10  
    @classmethod
    def get_top_colleges_courses(cls, uid: int = None) -> Dict:
        """
        Get top 10 most compared colleges and courses, with user context consideration.
        Optimized version using parallel processing and efficient querying.
        """
        try:
           
            user_context = UserContextHelper.get_user_context(uid)
           
            cache_key = CacheHelper.get_cache_key(
                "top_colleges_courses",
                user_context.get('domain_id'),
                user_context.get('education_level')
            )
            
           
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result

           
            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
                colleges_future = executor.submit(cls._get_top_colleges, user_context)
                courses_future = executor.submit(cls._get_top_courses, user_context)
                
                result = {
                    'colleges': colleges_future.result(),
                    'courses': courses_future.result()
                }

            
            cache.set(cache_key, result, cls.CACHE_TIMEOUT)
            return result

        except Exception as e:
            logger.error(f"Error in get_top_colleges_courses: {str(e)}", exc_info=True)
            return {
                "error": {
                    "message": "An unexpected error occurred while processing your request.",
                    "exception_type": str(type(e).__name__)
                }
            }

    @classmethod
    def _get_top_colleges(cls, user_context: Dict) -> List[Dict]:
        """
        Get top colleges using MySQL-compatible queries with caching based on domain_id.
        """
        domain_id = user_context.get('domain_id')

        
        cache_key = CacheHelper.get_cache_key("TopColleges", domain_id)

      
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        
        comparison_query = CollegeCompareData.objects.values('college_1').annotate(
            total_count=Count('id')
        ).filter(college_1__isnull=False)

       
        for field_num in range(2, 5):
            field_counts = CollegeCompareData.objects.values(
                f'college_{field_num}'
            ).annotate(
                count=Count('id')
            ).filter(**{f'college_{field_num}__isnull': False})

            additional_counts = {
                item[f'college_{field_num}']: item['count']
                for item in field_counts
            }

            for item in comparison_query:
                college_id = item['college_1']
                item['total_count'] += additional_counts.get(college_id, 0)

        

        if domain_id:
            valid_college_ids = set(
                CollegeDomain.objects.filter(
                    domain_id=domain_id,
                    status=True
                ).values_list('college_id', flat=True)
            )
            comparison_query = [
                item for item in comparison_query
                if item['college_1'] in valid_college_ids
            ]

        top_colleges_data = sorted(
            comparison_query,
            key=lambda x: x['total_count'],
            reverse=True
        )[:cls.TOP_N]

        top_college_ids = [item['college_1'] for item in top_colleges_data]
        count_lookup = {item['college_1']: item['total_count'] for item in top_colleges_data}

        colleges = College.objects.filter(
            id__in=top_college_ids,
            published='published'
        ).select_related('location')

        result = []
        for college in colleges:
            try:
                college_logo = CollegeDataHelper.get_college_logo(college.id)
            except Exception as e:
                logger.error(f"Error fetching logo for college {college.id}: {str(e)}")
                college_logo = 'https://cache.careers360.mobi/media/default_logo.jpg'

            result.append({
                'college_short_name': college.short_name or 'NA',
                'college_full_name': college.name,
                'college_id': college.id,
                'location': CollegeDataHelper.get_location_string(college.location),
                'ownership': college.get_ownership_display(),
                'nirf_rank': CollegeDataHelper.get_nirf_rank(college.id),
                'college_logo': college_logo,
                'total_comparisons': count_lookup.get(college.id, 0),
                'avg_review_rating': round(CollegeDataHelper.get_avg_rating(college.id), 1)
            })

        result.sort(key=lambda x: x['total_comparisons'], reverse=True)

       
        cache.set(cache_key, result, cls.CACHE_TIMEOUT)

        return result

    @classmethod
    def _get_top_courses(cls, user_context: Dict) -> List[Dict]:
        """
        Get top courses using caching based on domain_id and education_level.
        """
        domain_id = user_context.get('domain_id')
        

        
        cache_key = CacheHelper.get_cache_key("topCourses", domain_id)

       
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        comparison_query = CollegeCompareData.objects.values('course_1').annotate(
            total_count=Count('id')
        ).filter(course_1__isnull=False)

        for field_num in range(2, 5):
            field_counts = CollegeCompareData.objects.values(
                f'course_{field_num}'
            ).annotate(
                count=Count('id')
            ).filter(**{f'course_{field_num}__isnull': False})

            additional_counts = {
                item[f'course_{field_num}']: item['count']
                for item in field_counts
            }

            for item in comparison_query:
                course_id = item['course_1']
                item['total_count'] += additional_counts.get(course_id, 0)

        if domain_id:
            valid_course_ids = set(
                CollegeDomain.objects.filter(
                    domain_id=domain_id,
                    status=True
                ).values_list('college_course_id', flat=True)
            )
            comparison_query = [
                item for item in comparison_query
                if item['course_1'] in valid_course_ids
            ]

        top_courses_data = sorted(
            comparison_query,
            key=lambda x: x['total_count'],
            reverse=True
        )[:cls.TOP_N]

        top_course_ids = [item['course_1'] for item in top_courses_data]
        count_lookup = {item['course_1']: item['total_count'] for item in top_courses_data}

        top_courses = Course.objects.filter(
            id__in=top_course_ids,
            status=True
        ).select_related('college', 'degree')

        domain_mapping = {}
        if domain_id:
            domain_records = CollegeDomain.objects.filter(
                college_course_id__in=top_course_ids,
                domain_id=domain_id,
                status=True
            ).select_related('domain')
            domain_mapping = {
                record.college_course_id: record.domain.name
                for record in domain_records
            }

        result = []
        for course in top_courses:
            try:
                college_logo = CollegeDataHelper.get_college_logo(course.college.id)
            except Exception as e:
                logger.error(f"Error fetching logo for college {course.college.id}: {str(e)}")
                college_logo = 'https://cache.careers360.mobi/media/default_logo.jpg'

            result.append({
                'course_name': course.course_name,
                'college_short_name': course.college.short_name or 'NA',
                'college_full_name': course.college.name,
                'course_id': course.id,
                'college_id': course.college.id,
                'ownership': course.college.get_ownership_display(),
                'nirf_rank': CollegeDataHelper.get_nirf_rank(course.college.id),
                'avg_review_rating': CollegeDataHelper.get_avg_rating(course.college.id),
                'college_logo': college_logo,
                'total_comparisons': count_lookup.get(course.id, 0),
                'degree_name': course.degree.name if course.degree else 'NA',
                'degree_id': course.degree.id if course.degree else None
            })

        result.sort(key=lambda x: x['total_comparisons'], reverse=True)

        
        cache.set(cache_key, result, cls.CACHE_TIMEOUT)

        return result

