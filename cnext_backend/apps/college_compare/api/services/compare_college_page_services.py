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
    def get_colleges_dropdown(search_input: str = None, country_id: int = 1, uid: int = None, college_ids: List[int] = None) -> List[Dict]:
        print(f"DropdownService Input: search_input={search_input}, country_id={country_id}, uid={uid}, college_ids={college_ids}")

        if college_ids is not None and not isinstance(college_ids, list):
            raise ValueError("college_ids must be a list of integers.")
        
        def fetch_data():
            queryset = College.objects.filter(
                DropdownService.PUBLISHED_FILTER,
                country_id=country_id
            ).only('id', 'name', 'short_name')

            if uid and search_input and college_ids:
                search_lower = search_input.lower()
                queryset = queryset.filter(name__icontains=search_lower).exclude(id__in=college_ids).order_by('id')
                return list(queryset.values('id', 'name', 'short_name')[:10])

            if uid and search_input:
                search_lower = search_input.lower()
                queryset = queryset.filter(name__icontains=search_lower)
                return list(queryset.values('id', 'name', 'short_name')[:10])

            if uid and college_ids:
                return UserContextHelper.get_top_comparison_on_college(college_ids)

            if search_input and college_ids:
                search_lower = search_input.lower()
                queryset = queryset.filter(name__icontains=search_lower).exclude(id__in=college_ids).order_by('id')
              
                return list(queryset.values('id', 'name', 'short_name')[:10])

            if search_input:
                search_lower = search_input.lower()
                queryset = queryset.filter(name__icontains=search_lower)
                return list(queryset.values('id', 'name', 'short_name')[:10])

            if uid:
                user_context = UserContextHelper.get_user_context(uid)
                domain_id = user_context.get('domain_id')
                education_level = user_context.get('education_level')
                return UserContextHelper.get_top_compared_colleges(domain_id, education_level)

            if college_ids:
                return UserContextHelper.get_top_comparison_on_college(college_ids)

            return UserContextHelper.get_top_compared_colleges(1, 1)

       
        prefix = "DropDown_Default_" 
        if search_input and uid and college_ids:
            prefix = f"Dropdown_search_{search_input}_Exclude__{'_'.join(map(str, college_ids))}"
        elif search_input and uid:
            prefix = f"DropDown_Search_{search_input}_User_{uid}"
        elif uid and college_ids:
            prefix = f"DropDown_User__{uid}_Colleges_{'_'.join(map(str, college_ids))}"
        elif search_input:
            prefix = f"DropDown_Search_{search_input}"
        elif uid:
            prefix = f"DropDown_User_{uid}"
        elif college_ids:
            prefix = f"DropDown_Colleges_{'_'.join(map(str, college_ids))}"

        cache_key = CacheHelper.get_cache_key("colleges__v1__", country_id, prefix=prefix)
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
        """
        Retrieve a dropdown list of courses with relevant details.

        Args:
            college_id (int): ID of the college.
            degree_id (int): ID of the degree.

        Returns:
            List[Dict]: A list of dictionaries containing course details.
        """
        cache_key = CacheHelper.get_cache_key("courses", college_id, degree_id, prefix="dropdown")

        def fetch_data():
           
            return list(Course.objects.filter(
                college_id=college_id,
                degree_id=degree_id,
                status=True
            ).only('id', 'course_name', 'branch_id', 'level', 'degree_domain')
            .values('id', 'course_name', 'branch_id', 'level', 'degree_domain')
            )

       
        courses = CacheHelper.get_or_set(cache_key, fetch_data, timeout=86400)
        for course in courses:
            course['domain_id'] = course.pop('degree_domain')  
        return courses


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
        cache_key = CacheHelper.get_cache_key("Summary_v4", college_ids, course_ids)

        def fetch_data():
            results = list(Course.objects.filter(
                college_id__in=college_ids,
                id__in=course_ids,
                status=True
            ).select_related(
                'college__data'
            ).values(
                'id',
                'course_name',
                college_name=F('college__name'),
                rating=F('college__data__rating'),
                total_reviews=F('college__data__total_review'),
                college_id_alias=F('college_id')
            ))

            college_data = {
                college.get('college_id_alias'): {
                    "course_name": college.get('course_name', 'NA'),
                    "rating": college.get('rating', 'NA'),
                    "total_reviews": college.get('total_reviews', 'NA'),
                    "college_name": college.get('college_name', 'NA'),
                    "course_id": college.get('id', 'NA'),
                    "college_id": college.get('college_id_alias', 'NA')
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
                        "course_name": "NA",
                        "rating": "NA",
                        "total_reviews": "NA",
                        "college_name": "NA",
                        "course_id": "NA",
                        "college_id": college_id
                    }

            return result_dict

        return CacheHelper.get_or_set(cache_key, fetch_data, timeout=86400)





class QuickFactsService:
    @staticmethod
    def get_quick_facts(college_ids: List[int], course_ids: List[int]) -> Dict[str, Dict]:
        cache_key = CacheHelper.get_cache_key("quick_facts_v2", college_ids, course_ids)

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
                ).values('college_id', 'degree_id').annotate(count=Count('id'))
                for count in counts:
                    key = (count['college_id'], count['degree_id'])
                    course_counts[key] = count['count']

                
                results = {}
                for idx, college_id in enumerate(college_ids, start=1):
                
                    matching_course = next(
                        (course for course in courses if course.college_id == college_id), None
                    )
                    key = f"college_{idx}"
                    if matching_course:
                        college = matching_course.college
                        count_key = (college.id, matching_course.degree_id)
                        results[key] = {
                            'college_id': college.id,
                            'college_name': college.name,
                            'course_name': matching_course.course_name,
                            'course_id': matching_course.id,
                            'location': college.location.loc_string if college.location else 'NA',
                            'ownership': college.ownership_display(),
                            'parent_institute': college.parent_institute(),
                            'type_of_institute': college.type_of_institute(),
                            'college_type': dict(College.ENTITY_TYPE_CHOICES).get(college.type_of_entity, '-'),
                            'establishment_year': college.year_of_establishment or '',
                            'campus_size': college.campus_size_in_acres(),
                            'total_courses_offered': course_counts.get(count_key, 0)
                        }
                    else:
                       
                        results[key] = {
                            'college_id': college_id,
                            'college_name': 'NA',
                            'course_name': 'NA',
                            'course_id': 'NA',
                            'location': 'NA',
                            'ownership': 'NA',
                            'parent_institute': 'NA',
                            'type_of_institute': 'NA',
                            'college_type': 'NA',
                            'establishment_year': '',
                            'campus_size': 'NA',
                            'total_courses_offered': 0
                        }
                return results

            except Exception as e:
                print(f"Error in fetching quick facts: {e}")
                return {}

        return CacheHelper.get_or_set(cache_key, fetch_data, timeout=3600)


class CardDisplayService:
    @staticmethod
    def get_card_display_details(college_ids: List[int], course_ids: List[int]) -> Dict[str, Dict]:
        cache_key = CacheHelper.get_cache_key("cards_display_v1", college_ids, course_ids)

        def fetch_logo(college_id):
            """Fetch logo for a single college."""
            return {
                college_id: SocialMediaGallery.objects.filter(
                    college_id=college_id
                ).values_list('logo', flat=True).first()
            }

        def fetch_data():
            # Fetch logos in parallel
            tasks = [lambda cid=cid: fetch_logo(cid) for cid in college_ids]
            logos = ParallelService.execute_parallel_tasks(tasks)
            logo_dict = {k: v for d in logos for k, v in d.items()}

            # Fetch courses
            courses = Course.objects.filter(
                college_id__in=college_ids,
                id__in=course_ids,
                status=True
            ).values(
                'id', 'course_name', 'college_id', 'college__name'
            )

            # Prepare results in the order of college_ids
            results = {}
            for idx, college_id in enumerate(college_ids, start=1):
                key = f"college_{idx}"
                matching_course = next(
                    (course for course in courses if course['college_id'] == college_id), None
                )
                if matching_course:
                    logo_url = logo_dict.get(matching_course['college_id'], '')
                    results[key] = {
                        'id': matching_course['id'],
                        'course_name': matching_course['course_name'],
                        'college_id': matching_course['college_id'],
                        'college_name': matching_course['college__name'],
                        'logo': f"https://cache.careers360.mobi/media/{logo_url}" if logo_url else ''
                    }
                else:
                    # Default values for missing colleges
                    results[key] = {
                        'id': 'NA',
                        'course_name': 'NA',
                        'college_id': college_id,
                        'college_name': 'NA',
                        'logo': ''
                    }
            return results

        return CacheHelper.get_or_set(cache_key, fetch_data, timeout=3600)
