

from functools import lru_cache
from college_compare.models import College, Degree, Course, Branch, SocialMediaGallery,Domain
from college_compare.api.helpers.landing_page_helpers  import UserContextHelper
from django.db.models import Q, F, Count, Value, CharField
from django.db.models.functions import Concat
from django.core.cache import cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from typing import List, Dict, Any, Callable,Optional
from ..helpers.landing_page_helpers import DomainHelper


class CacheHelper:
    CACHE_VERSION = 1

    @staticmethod
    def get_cache_key(*args: Any, prefix: str = "") -> str:
        """Optimized cache key generation with versioning"""
        key = f"{prefix}_v{CacheHelper.CACHE_VERSION}_" + '_'.join(str(arg) for arg in args)
        return hashlib.md5(key.encode()).hexdigest()

    @staticmethod
    def get_or_set(key: str, callback: Callable[[], Any], timeout: int = 3600, cache_burst: int = 0) -> Any:
        """Get or set cached value."""
        try:
            if cache_burst == 1:
                cache.delete(key)
                result = callback()
                if result is not None:
                    cache.set(key, result, timeout)
                return result

            result = cache.get(key)
            if result is None:
                result = callback()
                if result is not None:
                    cache.set(key, result, timeout)
            return result
        except Exception:
            return callback()


class DropdownService:
    PUBLISHED_FILTER = Q(published='published', status=True)

    @staticmethod
    def get_colleges_dropdown(search_input: str = None, country_id: int = 1, uid: int = None, college_ids: List[int] = None, cache_burst: int = 0) -> List[Dict]:
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
                queryset = queryset.filter(name__icontains=search_lower).order_by('id')
                return list(queryset.values('id', 'name', 'short_name')[:10])

            if uid and college_ids:
                return UserContextHelper.get_top_comparison_on_college(college_ids)

            if search_input and college_ids:
                search_lower = search_input.lower()
                queryset = queryset.filter(name__icontains=search_lower).exclude(id__in=college_ids).order_by('id')
              
                return list(queryset.values('id', 'name', 'short_name')[:10])

            if search_input:
                search_lower = search_input.lower()
                queryset = queryset.filter(name__icontains=search_lower).order_by('id')
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
        return CacheHelper.get_or_set(cache_key, fetch_data, timeout=86400, cache_burst=cache_burst)
   

    @staticmethod
    def get_degrees_dropdown(college_id: int, country_id: int = 1, cache_burst: int = 0) -> List[Dict]:
        """Fetch degrees for dropdown with caching."""
        cache_key = CacheHelper.get_cache_key("degree", college_id, country_id, prefix="dropdown")

        def fetch_data():
            return list(Degree.objects.filter(
                course__college_id=college_id,
                course__status=True,
                published='published'  
            ).distinct().only('id', 'name').values('id', 'name'))

        return CacheHelper.get_or_set(cache_key, fetch_data, timeout=86400, cache_burst=cache_burst)

    @staticmethod
    def get_courses_dropdown(college_id: int, degree_id: int, cache_burst: int = 0) -> List[Dict]:
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

        courses = CacheHelper.get_or_set(cache_key, fetch_data, timeout=86400, cache_burst=cache_burst)
        
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


class NoDataAvailableError(Exception):
    """Custom exception to indicate no data is available."""
    pass


class SummaryComparisonService:
    @staticmethod
    def get_summary_comparison(college_ids: List[int], course_ids: List[int], cache_burst: int = 0) -> Dict:
        cache_key = CacheHelper.get_cache_key("summary__h1_tag", college_ids, course_ids)
        print(cache_burst)

        def fetch_data():
            results = list(Course.objects.filter(
                college_id__in=college_ids,
                id__in=course_ids,
                status=True
            ).select_related(
                'college__data',
                'college',
                'degree',
                "degree_domain"
            ).values(
                'id',
                'course_name',
                'college__name',
                'college__data__rating',
                'college__data__total_review',
                'college_id',
                'college__short_name',
                'degree__name',
                'degree_domain__name'
            ))

            if not results:
                raise NoDataAvailableError("No data available for the provided college IDs and course IDs.")

            college_data = {
                college['college_id']: {
                    "course_name": college.get('course_name', 'NA'),
                    "rating": college.get('college__data__rating', 'NA').split("/")[0].strip() if college.get('college__data__rating', 'NA') != 'NA' else 'NA',
                    "total_reviews": college.get('college__data__total_review', 'NA').split("Reviews")[0].strip() if college.get('college__data__total_review', 'NA') != 'NA' else 'NA',
                    "college_name": college.get('college__name', 'NA'),
                    "course_id": college.get('id', 'NA'),
                    "college_id": college.get('college_id', 'NA'),
                    "college_short_name": college.get('college__short_name', 'NA'),
                    "degree_name": college.get('degree__name', 'NA'),
                    "domain_name": DomainHelper.format_domain_name(college.get('degree_domain__name', 'NA'))
                }
                for college in results
            }

            result_dict = {
                f"college_{i}": college_data.get(college_id, {
                    "course_name": "NA",
                    "rating": "NA",
                    "total_reviews": "NA",
                    "college_name": "NA",
                    "course_id": "NA",
                    "college_id": college_id,
                    "college_short_name": "NA",
                    "degree_name": "NA",
                    "domain_name": "NA"
                })
                for i, college_id in enumerate(college_ids, 1)
            }

            college_count = len(college_ids)
            h1_tag = "NA"
            comparison_string = "NA"

            if college_count >= 2:
                college1 = result_dict.get("college_1", {})
                college2 = result_dict.get("college_2", {})
                college3 = result_dict.get("college_3", {})

                if college_count == 2 and college1 and college2:
                    h1_tag = (
                        f"Compare {college1.get('college_short_name', 'NA')} {college1.get('course_name', 'NA')} and "
                        f"{college2.get('college_short_name', 'NA')} {college2.get('course_name', 'NA')} on the basis of their Fees, "
                        f"Placements, Cut Off, Reviews, Seats, Courses, and other details. {college1.get('college_short_name', 'NA')} "
                        f"{college1.get('course_name', 'NA')} is rated {college1.get('rating', 'NA')} out of 5 by "
                        f"{college1.get('total_reviews', 'NA')} genuine verified students while {college2.get('college_short_name', 'NA')} "
                        f"{college2.get('course_name', 'NA')} is rated {college2.get('rating', 'NA')} out of 5 by "
                        f"{college2.get('total_reviews', 'NA')} students at Careers360. Explore Careers360 for detailed comparison on all "
                        f"course parameters and download free information on  Admission details, Placement report, Eligibility criteria, etc."
                    )
                    comparison_string = f"{college1.get('college_short_name', 'NA')} vs {college2.get('college_short_name', 'NA')}"

                elif college_count == 3 and college1 and college2 and college3:
                    h1_tag = (
                        f"Compare {college1.get('college_short_name', 'NA')} {college1.get('course_name', 'NA')}, "
                        f"{college2.get('college_short_name', 'NA')} {college2.get('course_name', 'NA')} and "
                        f"{college3.get('college_short_name', 'NA')} {college3.get('course_name', 'NA')} on the basis of their Fees, "
                        f"Placements, Cut Off, Reviews, Seats, Courses, and other details. {college1.get('college_short_name', 'NA')} "
                        f"{college1.get('course_name', 'NA')} is rated {college1.get('rating', 'NA')} out of 5 by "
                        f"{college1.get('total_reviews', 'NA')} genuine verified students, {college2.get('college_short_name', 'NA')} "
                        f"{college2.get('course_name', 'NA')} is rated {college2.get('rating', 'NA')} out of 5 by "
                        f"{college2.get('total_reviews', 'NA')} students and {college3.get('college_short_name', 'NA')} "
                        f"{college3.get('course_name', 'NA')} is rated {college3.get('rating', 'NA')} out of 5 by "
                        f"{college3.get('total_reviews', 'NA')} students at Careers360. Explore Careers360 for detailed comparison on all "
                        f"course parameters and download free information on Admission details, Placement report, Eligibility criteria, etc."
                    )
                    comparison_string = f"{college1.get('college_short_name', 'NA')} vs {college2.get('college_short_name', 'NA')} vs {college3.get('college_short_name', 'NA')}"

            elif college_count == 1:
                college1 = result_dict.get("college_1", {})
                if college1:
                    h1_tag = f"{college1.get('college_name', 'NA')} {college1.get('course_name', 'NA')} details"
                    comparison_string = f"{college1.get('college_short_name', 'NA')}"

            return {
                "h1_tag": h1_tag,
                "comparison_string": comparison_string,
            }

        return CacheHelper.get_or_set(cache_key, fetch_data, timeout=86400 * 7, cache_burst=cache_burst)




class QuickFactsService:
    @staticmethod
    def get_quick_facts(college_ids: List[int], course_ids: List[int] = None, cache_burst: int = 0) -> Dict[str, Dict]:
        # Create a cache key that accounts for optional course_ids
        cache_key = CacheHelper.get_cache_key("quick_facts", college_ids, course_ids or [])

        def fetch_data():
            try:
                # Base query for courses
                courses_query = Course.objects.filter(
                    college_id__in=college_ids,
                    status=True
                )

                # Apply course_ids filter only if provided
                if course_ids:
                    courses_query = courses_query.filter(id__in=course_ids)

                # Fetch courses and related data
                courses = courses_query.select_related(
                    'college',
                    'college__location',
                    'college__entity_reference',

                ).only(
                    'college_id',
                    'college__name', 'college__ownership',
                    'college__institute_type_1', 'college__institute_type_2', 'college__type_of_entity',
                    'college__year_of_establishment', 'college__campus_size', 'college__associate_hospital',
                    'college__number_of_bed',
                    'college__location__loc_string',
                    'college__entity_reference__short_name'
                )

                total_courses_per_college = courses.values('college_id').annotate(total_courses=Count('id'))
                total_courses_map = {item['college_id']: item['total_courses'] for item in total_courses_per_college}

                # Create a dictionary for faster lookups
                course_map = {course.college_id: course for course in courses}

                results = {}
                all_na = True

                for idx, college_id in enumerate(college_ids, start=1):
                    key = f"college_{idx}"
                    matching_course = course_map.get(college_id)

                    if matching_course:
                        all_na = False
                        college = matching_course.college

                        results[key] = {
                            'college_id': college.id,
                            'college_name': college.name,
                            'location': college.location.loc_string if college.location else 'NA',
                            'ownership': college.ownership_display(),
                            'parent_institute': college.parent_institute(),

                            'type_of_institute': College.type_of_institute(
                                college.institute_type_1, college.institute_type_2
                            ),
                            'college_type': dict(College.ENTITY_TYPE_CHOICES).get(college.type_of_entity, 'NA'),
                            'establishment_year': college.year_of_establishment or '',
                            'campus_size': college.campus_size_in_acres(),
                            'total_courses_offered': total_courses_map.get(college_id, 0),
                            "is_hospital": bool(
                                dict(College.ENTITY_TYPE_CHOICES).get(college.type_of_entity, 'NA') == 'Hospital'),
                            "associate_hospital": college.associate_hospital or 'NA',
                            "number_of_bed": college.number_of_bed

                        }
                    else:
                        results[key] = {
                            'college_id': college_id,
                            'college_name': 'NA',
                            'location': 'NA',
                            'ownership': 'NA',
                            'parent_institute': 'NA',
                            'type_of_institute': 'NA',
                            'college_type': 'NA',
                            'establishment_year': '',
                            'campus_size': 'NA',
                            'total_courses_offered': 0,
                            "number_of_bed": 'NA',
                            "associate_hospital": 'NA'
                        }

                if all_na:
                    raise NoDataAvailableError("No data available for the provided college IDs.")

                return results

            except NoDataAvailableError as e:
                print(f"Error: {e}")
                raise

            except Exception as e:
                print(f"Error in fetching quick facts: {e}")
                return {}

        return CacheHelper.get_or_set(cache_key, fetch_data, timeout=3600 * 24 * 7, cache_burst=cache_burst)

    


class CardDisplayService:
    @staticmethod
    def get_card_display_details(college_ids: List[int], course_ids: Optional[List[int]] = None, cache_burst: int = 0) -> Dict[str, Dict]:
        cache_key = CacheHelper.get_cache_key("cards_display_v4", college_ids, course_ids)

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

            # Fetch college details (name & short name)
            college_details = {
                college["id"]: {"college_name": college["name"], "college_short_name": college["short_name"]}
                for college in College.objects.filter(id__in=college_ids).values("id", "name", "short_name")
            }

            # Fetch courses only if course_ids are provided
            courses = []
            if course_ids:
                courses = Course.objects.filter(
                    college_id__in=college_ids,
                    id__in=course_ids,
                    status=True
                ).values(
                    'id', 'course_name', 'college_id'
                )

            # Prepare results
            results = {}
            for idx, college_id in enumerate(college_ids, start=1):
                key = f"college_{idx}"
                matching_course = next(
                    (course for course in courses if course['college_id'] == college_id), None
                )

                logo_url = logo_dict.get(college_id, '')
                college_info = college_details.get(college_id, {"college_name": "NA", "college_short_name": "NA"})

                results[key] = {
                    'id': matching_course['id'] if matching_course else 'NA',
                    'course_name': matching_course['course_name'] if matching_course else 'NA',
                    'college_id': college_id,
                    'college_name': college_info["college_name"],
                    'logo': f"https://cache.careers360.mobi/media/{logo_url}" if logo_url else '',
                    "college_short_name": college_info["college_short_name"],
                }

            return results

        return CacheHelper.get_or_set(cache_key, fetch_data, timeout=3600, cache_burst=cache_burst)
