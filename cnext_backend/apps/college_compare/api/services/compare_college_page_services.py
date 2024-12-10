from functools import lru_cache
from college_compare.models import College, Degree, Course, Branch, SocialMediaGallery
from college_compare.api.helpers.landing_page_helpers  import UserContextHelper
from django.db.models import Q, F, Count, Value, CharField
from django.db.models.functions import Concat
from django.core.cache import cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from typing import List, Dict, Any


class CacheHelper:
    CACHE_VERSION = 1

    @staticmethod
    def get_cache_key(*args, prefix=""):
        """Optimized cache key generation with versioning"""
        key = f"{prefix}_v{CacheHelper.CACHE_VERSION}_" + '_'.join(str(arg) for arg in args)
        return hashlib.md5(key.encode()).hexdigest()

    @staticmethod
    @lru_cache(maxsize=100)
    def get_or_set(key: str, callback, timeout=3600):
        result = cache.get(key)
        if result is None:
            result = callback()
            cache.set(key, result, timeout)
        return result


class DropdownService:
    PUBLISHED_FILTER = Q(published='published', status=True)

    @staticmethod
    def get_colleges_dropdown(search_input: str = None, country_id: int = 1, uid: int = None) -> List[Dict]:
        """Fetch colleges for dropdown with caching"""
        def fetch_data():
            queryset = College.objects.filter(
                DropdownService.PUBLISHED_FILTER,
                country_id=country_id
            ).only('id', 'name', 'short_name')

            if search_input:
                print(search_input)
                search_lower = search_input.lower()
                queryset = queryset.filter(name__icontains=search_lower)
                return list(queryset.values('id', 'name', 'short_name')[:10])

            elif uid:
                print("----------")
                user_context = UserContextHelper.get_user_context(uid)
                domain_id = user_context.get('domain_id')
                education_level = user_context.get('education_level')
                return UserContextHelper.get_top_compared_colleges(domain_id, education_level)

            return UserContextHelper.get_top_compared_colleges(1, 1)
        
    
        if search_input:
            Prefix = f"DropDown_{search_input}"
        elif uid:
            user_context = UserContextHelper.get_user_context(uid)
            domain_id = user_context.get('domain_id')
            Prefix = f"DropDown_{domain_id}"
        else:
            Prefix = "DropDown_default"
        cache_key = CacheHelper.get_cache_key("Colleges", country_id, prefix=Prefix)

    
        return CacheHelper.get_or_set(cache_key, fetch_data, timeout=86400)

   

    @staticmethod
    def get_degrees_dropdown(college_id: int, country_id: int = 1) -> List[Dict]:
        """Fetch degrees for dropdown with caching."""
        cache_key = CacheHelper.get_cache_key("degree", college_id, country_id, prefix="dropdown")

        def fetch_data():
            return list(Degree.objects.filter(
                course__college_id=college_id,
                course__status=True,
                published='published'  
            ).distinct().only('id', 'name').values('id', 'name'))

        return CacheHelper.get_or_set(cache_key, fetch_data, timeout=86400)

    @staticmethod
    def get_courses_dropdown(college_id: int, degree_id: int) -> List[Dict]:
        cache_key = CacheHelper.get_cache_key("courses", college_id, degree_id, prefix="dropdown")

        def fetch_data():
            return list(Course.objects.filter(
                college_id=college_id,
                degree_id=degree_id,
                status=True
            ).only('id', 'course_name', 'branch_id').values('id', 'course_name', 'branch_id'))

        return CacheHelper.get_or_set(cache_key, fetch_data, timeout=86400)


class ParallelService:
    """Service for running tasks in parallel."""
    @staticmethod
    def execute_parallel_tasks(tasks: List[callable]) -> List[Any]:
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_task = {executor.submit(task): task for task in tasks}
            for future in as_completed(future_to_task):
                try:
                    results.append(future.result())
                except Exception as e:
                 
                    print(f"Error in parallel execution: {e}")
        return results



class SummaryComparisonService:
    @staticmethod
    def get_summary_comparison(college_ids: List[int], course_ids: List[int]) -> List[Dict]:
        cache_key = CacheHelper.get_cache_key("Summary", college_ids, course_ids)

        def fetch_data():
            return list(Course.objects.filter(
                college_id__in=college_ids,
                id__in=course_ids,
                status=True
            ).select_related(
                'college__data'
            ).values(
                'course_name',
                rating=F('college__data__rating'),
                total_reviews=F('college__data__total_review'),
                college_name=F('college__name')
            ))

        return CacheHelper.get_or_set(cache_key, fetch_data, timeout=3600)



class QuickFactsService:
    @staticmethod
    def get_quick_facts(college_ids: List[int], course_ids: List[int]) -> List[Dict]:
        cache_key = CacheHelper.get_cache_key("quick_facts", college_ids, course_ids)

        def fetch_data():
            try:
              
                courses = Course.objects.filter(
                    college_id__in=college_ids,
                    id__in=course_ids,
                    status=True
                ).select_related(
                    'college',
                    'college__location',
                    'college__entity_reference',
                    'degree'
                ).only(
                    'id', 'course_name', 'college_id', 'degree_id',
                    'college__name', 'college__ownership',
                    'college__institute_type_1', 'college__type_of_entity',
                    'college__year_of_establishment', 'college__campus_size',
                    'college__location__loc_string',
                    'college__entity_reference__short_name'
                )

                
                course_counts = {}
                counts = Course.objects.filter(
                    college_id__in=college_ids,
                    status=True
                ).values('college_id', 'degree_id').annotate(
                    count=Count('id')
                )
                for count in counts:
                    key = (count['college_id'], count['degree_id'])
                    course_counts[key] = count['count']

                
                result = []
                for course in courses:
                    college = course.college
                    count_key = (college.id, course.degree_id)
                    result.append({
                        'college_id': college.id,
                        'college_name': college.name,
                        'course_name': course.course_name,
                        'course_id': course.id,
                        'location': college.location.loc_string if college.location else 'NA',
                        'ownership': college.ownership_display(),
                        'parent_institute': college.parent_institute(),
                        'type_of_institute': college.type_of_institute(),
                        'college_type': dict(College.ENTITY_TYPE_CHOICES).get(college.type_of_entity, '-'),
                        'establishment_year': college.year_of_establishment or '',
                        'campus_size': college.campus_size_in_acres(),
                        'total_courses_offered': course_counts.get(count_key, 0)
                    })

                return result

            except Exception as e:
               
                print(f"Error in fetching quick facts: {e}")
                return []

        return CacheHelper.get_or_set(cache_key, fetch_data, timeout=3600)

class CardDisplayService:
    @staticmethod
    def get_card_display_details(college_ids: List[int], course_ids: List[int]) -> List[Dict]:
        cache_key = CacheHelper.get_cache_key("cards", college_ids, course_ids)

        def fetch_logo(college_id):
            """Fetch logo for a single college."""
            return {
                college_id: SocialMediaGallery.objects.filter(
                    college_id=college_id
                ).values_list('logo', flat=True).first()
            }

        def fetch_data():
            tasks = [lambda cid=cid: fetch_logo(cid) for cid in college_ids]
            logos = ParallelService.execute_parallel_tasks(tasks)
            logo_dict = {k: v for d in logos for k, v in d.items()}

            courses = Course.objects.filter(
                college_id__in=college_ids,
                id__in=course_ids,
                status=True
            ).values(
                'id', 'course_name', 'college_id', 'college__name'
            )

            return [{
                'id': course['id'],
                'course_name': course['course_name'],
                'college_id': course['college_id'],
                'college_name': course['college__name'],
                'logo': f"https://cache.careers360.mobi/media/{logo_dict.get(course['college_id'], '')}"
            } for course in courses]

        return CacheHelper.get_or_set(cache_key, fetch_data, timeout=3600)
