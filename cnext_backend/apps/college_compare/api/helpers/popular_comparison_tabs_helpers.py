from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from django.db.models import QuerySet, Count, Q, Prefetch, F
from django.core.cache import cache
import hashlib
from college_compare.models import Domain, CollegeCompareData, Course, College
from .landing_page_helpers import CollegeDataHelper, DomainHelper
from django.db import connection, connections
import hashlib
import logging
import time
import cProfile
import io
import pstats
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
logger = logging.getLogger(__name__)



class CacheHelper:
    """Helper class to manage caching."""

    @staticmethod
    def get_cache_key(*args: Any) -> str:
        key = '_'.join(str(arg) for arg in args)
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




# class BaseComparisonHelper:
#     """Base class for comparison helpers."""
    
#     @staticmethod
#     def _get_base_comparison_query_raw(filter_condition: Q, cache_burst: int = 0, **kwargs) -> List[Dict]:
#         """Get base comparison query results. Added **kwargs to handle extra parameters."""
#         cache_key = CacheHelper.get_cache_key("base_comparison_query", str(filter_condition))

#         def compute_query():
#             sql, params = CollegeCompareData.objects.filter(filter_condition).values(
#                 'course_1', 'course_2'
#             ).annotate(
#                 compare_count=Count('id'),
#                 course_1_college_id=F('course_1__college_id'),
#                 course_2_college_id=F('course_2__college_id'),
#             ).order_by('-compare_count')[:20].query.sql_with_params()
#             with connections['default'].cursor() as cursor:
#                 cursor.execute(sql, params)
#                 columns = [col[0] for col in cursor.description]
#                 return [dict(zip(columns, row)) for row in cursor.fetchall()]

#         return CacheHelper.get_or_set(key=cache_key, callback=compute_query, timeout=3600*24*7, cache_burst=cache_burst)

#     @staticmethod
#     def _get_course_data(course: Course, cache_burst: int = 0) -> Dict[str, Any]:
#         cache_key = CacheHelper.get_cache_key("course_data", course.id)

#         def compute_data():
#             return {
#                 "name": course.college.name,
#                 "logo": CollegeDataHelper.get_college_logo(course.college.id),
#                 "location": CollegeDataHelper.get_location_string(course.college.location),
#                 "course_name": course.course_name,
#                 "college_id": course.college.id,
#                 "course_id": course.id,
#                 "short_name": course.college.short_name or 'NA',
#                 "degree_id": course.degree_id,
#                 "degree_name": getattr(course.degree, 'name', None),
#                 "level": course.level,
#                 "domain_id": course.degree_domain.id if hasattr(course, 'degree_domain') and course.degree_domain else None,
#                 "branch_id": course.branch_id
#             }
#         return CacheHelper.get_or_set(cache_key, compute_data,timeout=3600*24*7)

#     @staticmethod
#     def _prepare_course_data_bulk(courses: QuerySet, cache_burst: int = 0) -> Dict[int, Dict[str, Any]]:
#         """Prepares course data in bulk."""
#         course_data = {}
#         for course in courses:
#             course_data[course.id] = BaseComparisonHelper._get_course_data(course)
#         return course_data

#     @staticmethod
#     def _get_courses_by_ids(course_ids: Set[int], cache_burst: int = 0) -> Dict[int, Course]:
#         cache_key = CacheHelper.get_cache_key("courses_by_ids_optimized", "_".join(map(str, sorted(course_ids))))

#         def fetch_courses():
#             courses = Course.objects.filter(id__in=course_ids).select_related(
#                 'degree', 'branch', 'college', 'college__location', 'degree_domain'
#             ).only(
#                 'id', 'course_name', 'degree_id', 'branch_id', 'level', 'degree__name', 'branch__name',
#                 'college__name', 'college__short_name', 'college__id', 'college__location', 'degree_domain__id', 'degree_domain__name'
#             )
#             return {course.id: course for course in courses}

#         return CacheHelper.get_or_set(cache_key, fetch_courses, timeout=3600*24*7)

#     @classmethod
#     def _transform_comparison_data(cls, comparison: Dict, course_map: Dict[int, Course],
#                                     course_data_map: Dict[int, Dict[str, Any]],
#                                     extra_data: Optional[Dict[str, Any]] = None,
#                                     college_id: Optional[int] = None,
#                                     cache_burst: int = 0) -> Optional[Dict[str, Any]]:
#         cache_key = CacheHelper.get_cache_key(
#             "comparison_data",
#             comparison['course_1'],
#             comparison['course_2'],
#             str(extra_data) if extra_data else "",
#             str(college_id) if college_id else ""
#         )

#         def compute_data():
#             course_1 = course_map.get(comparison['course_1'])
#             course_2 = course_map.get(comparison['course_2'])
#             if not (course_1 and course_2):
#                 return None
#             college_data_1 = course_data_map.get(course_1.id)
#             college_data_2 = course_data_map.get(course_2.id)

#             if college_id:
#                 if course_1.college.id != college_id:
#                     college_data_1, college_data_2 = college_data_2, college_data_1
#                     course_1, course_2 = course_2, course_1

#                 elif course_2.college.id == college_id:
#                     college_data_2, college_data_1 = college_data_1, college_data_2
#                     course_2, course_1 = course_1, course_2

#             result = {
#                 "college_1": college_data_1,
#                 "college_2": college_data_2,
#                 "compare_count": comparison['compare_count'],
#                 "college_ids": f"{course_1.college.id},{course_2.college.id}",
#                 "course_ids": f"{course_1.id},{course_2.id}"
#             }
#             if extra_data:
#                 result.update(extra_data)
#             return result

#         return CacheHelper.get_or_set(cache_key, compute_data, timeout=3600*24*7)


# class ComparisonHelper(BaseComparisonHelper):
#     COMPARISON_TYPES = {
#         'degree_branch': 'degree_branch_comparisons',
#         'degree': 'degree_comparisons',
#         'domain': 'domain_comparisons',
#         'college': 'college_comparisons'
#     }


#     @lru_cache(maxsize=1028)
        
#     def _filter_condition(self, comparison_type: str, **kwargs) -> Q:
#         if comparison_type == 'degree_branch':
#             exact_course_condition = Q(course_1__id=kwargs['course_id'])

#             # Count exact matches
#             exact_match_count = CollegeCompareData.objects.filter(exact_course_condition).count()

#             # If exact matches are sufficient, return only the exact condition
#             if exact_match_count >= 10:
#                 return exact_course_condition

#             # Otherwise, include the fallback condition
#             fallback_condition = (
#                 Q(course_1__id=kwargs['course_id']) |  # Either match the exact course
#                 (
#                     Q(course_1__degree__id=kwargs['degree_id']) & 
#                     Q(course_2__degree__id=kwargs['degree_id']) &
#                     Q(course_1__branch__id=kwargs['branch_id']) &
#                     Q(course_2__branch__id=kwargs['branch_id'])
#                 )
#             )
#             return fallback_condition

#         elif comparison_type == 'domain':
#             return (Q(course_1__degree_domain__id=kwargs['domain_id']) &
#                     Q(course_2__degree_domain__id=kwargs['domain_id']) &
#                     ~Q(course_1__degree__id=kwargs.get('degree_id', 0)) &
#                     ~Q(course_2__degree__id=kwargs.get('degree_id', 0)))

#         elif comparison_type == 'degree':
#             return Q(course_1__degree__id=kwargs['degree_id']) & Q(course_2__degree__id=kwargs['degree_id']) & \
#                 ~Q(course_1__branch__id=kwargs.get('branch_id', 0)) & ~Q(course_2__branch__id=kwargs.get('branch_id', 0))

#         elif comparison_type == 'college':
#             return Q(course_1__college_id=kwargs['college_id']) | Q(course_2__college_id=kwargs['college_id'])

#         return Q()

  

#     @lru_cache(maxsize=1028)
#     def _get_extra_data(self, comparison_type: str, course: Course, **kwargs) -> Dict[str, Any]:

#         if comparison_type == 'degree_branch':
#             return {
#                 "degree_name": course.degree.name if hasattr(course, 'degree') else None,
#                 "degree_id": kwargs['degree_id'],
#                 "branch_id": kwargs['branch_id'],
#                 "branch_name": course.branch.name if hasattr(course, 'branch') else None,
#                 "course_name": course.course_name if hasattr(course, 'course_name') else None,
#             }

#         elif comparison_type == 'degree':
#             return {
#                 "degree_name": course.degree.name if hasattr(course, 'degree') else None,
#                 "degree_id": kwargs['degree_id'],
#             }
#         elif comparison_type == 'domain':
#             return {
#                 "domain_name": DomainHelper.format_domain_name(course.degree_domain.name) if hasattr(course, 'degree_domain') and course.degree_domain else None,
#                 "domain_id": kwargs['domain_id'],
#             }
#         elif comparison_type == 'college':
#             if college_id := kwargs.get('college_id'):
#                 try:
#                     college_name = CollegeDataHelper.get_college_name(college_id)
#                     return {"college_name": college_name} if college_name else {}
#                 except College.DoesNotExist:
#                     logger.error(f"College with id {college_id} not found")
#                     return {"college_name": None}

#         return {}
#     def _process_comparison(self, comparison: Dict, course_map: Dict[int, Course],
#                                     course_data_map: Dict[int, Dict[str, Any]],
#                                     extra_data: Optional[Dict[str, Any]] = None,
#                                     college_id: Optional[int] = None,
#                                     cache_burst: int = 0) -> Optional[Dict[str, Any]]:
#         """Helper function to process a single comparison."""
#         course = course_map.get(comparison['course_1'])
#         if not course:
#             return None
#         return self._transform_comparison_data(comparison, course_map, course_data_map, extra_data,
#                                                 college_id=college_id, cache_burst=cache_burst)

class BaseComparisonHelper:
    """
    Base class for comparison helpers that provides core functionality for comparing courses
    and colleges. Handles data fetching, caching, and transformation of comparison data.
    """
    
    @staticmethod
    def _get_course_details(course_id: int) -> Dict[str, int]:
        """
        Helper method to fetch degree_id, domain_id, and branch_id from a course.
        This method centralizes the fetching of course-related IDs that are needed
        throughout the comparison process.

        Args:
            course_id: The ID of the course to fetch details for

        Returns:
            Dictionary containing degree_id, domain_id, and branch_id
        """
        try:
            course = Course.objects.select_related(
                'degree', 'degree_domain', 'branch'
            ).get(id=course_id)
            
            return {
                'degree_id': course.degree_id,
                'domain_id': course.degree_domain.id if course.degree_domain else None,
                'branch_id': course.branch_id
            }
        except Course.DoesNotExist:
            logger.error(f"Course with id {course_id} not found")
            return {'degree_id': None, 'domain_id': None, 'branch_id': None}
    
    @staticmethod
    def _get_base_comparison_query_raw(filter_condition: Q, cache_burst: int = 0, **kwargs) -> List[Dict]:
        """
        Get base comparison query results using raw SQL for better performance.
        Results are cached to minimize database load.

        Args:
            filter_condition: Django Q object containing the filter conditions
            cache_burst: Optional parameter to force cache refresh
            kwargs: Additional parameters for query customization

        Returns:
            List of dictionaries containing comparison data
        """
        cache_key = CacheHelper.get_cache_key("base_comparison_query", str(filter_condition))

        def compute_query():
            sql, params = CollegeCompareData.objects.filter(filter_condition).values(
                'course_1', 'course_2'
            ).annotate(
                compare_count=Count('id'),
                course_1_college_id=F('course_1__college_id'),
                course_2_college_id=F('course_2__college_id'),
            ).order_by('-compare_count')[:20].query.sql_with_params()
            
            with connections['default'].cursor() as cursor:
                cursor.execute(sql, params)
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

        return CacheHelper.get_or_set(key=cache_key, callback=compute_query, timeout=3600*24*7, cache_burst=cache_burst)

    @staticmethod
    def _get_course_data(course: Course, cache_burst: int = 0) -> Dict[str, Any]:
        """
        Fetch and cache detailed data for a single course.

        Args:
            course: Course object to get data for
            cache_burst: Optional parameter to force cache refresh

        Returns:
            Dictionary containing formatted course data
        """
        cache_key = CacheHelper.get_cache_key("course_data", course.id)

        def compute_data():
            return {
                "name": course.college.name,
                "logo": CollegeDataHelper.get_college_logo(course.college.id),
                "location": CollegeDataHelper.get_location_string(course.college.location),
                "course_name": course.course_name,
                "college_id": course.college.id,
                "course_id": course.id,
                "short_name": course.college.short_name or 'NA',
                "degree_id": course.degree_id,
                "degree_name": getattr(course.degree, 'name', None),
                "level": course.level,
                "domain_id": course.degree_domain.id if hasattr(course, 'degree_domain') and course.degree_domain else None,
                "branch_id": course.branch_id
            }
        return CacheHelper.get_or_set(cache_key, compute_data, timeout=3600*24*7)

    @staticmethod
    def _prepare_course_data_bulk(courses: QuerySet, cache_burst: int = 0) -> Dict[int, Dict[str, Any]]:
        """
        Prepares course data in bulk for multiple courses.
        
        Args:
            courses: QuerySet of Course objects
            cache_burst: Optional parameter to force cache refresh

        Returns:
            Dictionary mapping course IDs to their detailed data
        """
        course_data = {}
        for course in courses:
            course_data[course.id] = BaseComparisonHelper._get_course_data(course)
        return course_data

    @staticmethod
    def _get_courses_by_ids(course_ids: Set[int], cache_burst: int = 0) -> Dict[int, Course]:
        """
        Fetch multiple courses by their IDs efficiently using select_related.
        
        Args:
            course_ids: Set of course IDs to fetch
            cache_burst: Optional parameter to force cache refresh

        Returns:
            Dictionary mapping course IDs to Course objects
        """
        cache_key = CacheHelper.get_cache_key("courses_by_ids_optimized", "_".join(map(str, sorted(course_ids))))

        def fetch_courses():
            courses = Course.objects.filter(id__in=course_ids).select_related(
                'degree', 'branch', 'college', 'college__location', 'degree_domain'
            ).only(
                'id', 'course_name', 'degree_id', 'branch_id', 'level', 'degree__name', 'branch__name',
                'college__name', 'college__short_name', 'college__id', 'college__location', 'degree_domain__id', 'degree_domain__name'
            )
            return {course.id: course for course in courses}

        return CacheHelper.get_or_set(cache_key, fetch_courses, timeout=3600*24*7)

    @classmethod
    def _transform_comparison_data(cls, comparison: Dict, course_map: Dict[int, Course],
                                 course_data_map: Dict[int, Dict[str, Any]],
                                 extra_data: Optional[Dict[str, Any]] = None,
                                 college_id: Optional[int] = None,
                                 cache_burst: int = 0) -> Optional[Dict[str, Any]]:
        """
        Transform raw comparison data into a structured format, handling college ordering
        and additional data integration.

        Args:
            comparison: Raw comparison data
            course_map: Mapping of course IDs to Course objects
            course_data_map: Mapping of course IDs to course data
            extra_data: Optional additional data to include
            college_id: Optional college ID for ordering
            cache_burst: Optional parameter to force cache refresh

        Returns:
            Transformed comparison data dictionary or None if invalid
        """
        cache_key = CacheHelper.get_cache_key(
            "comparison_data",
            comparison['course_1'],
            comparison['course_2'],
            str(extra_data) if extra_data else "",
            str(college_id) if college_id else ""
        )

        def compute_data():
            course_1 = course_map.get(comparison['course_1'])
            course_2 = course_map.get(comparison['course_2'])
            if not (course_1 and course_2):
                return None
                
            college_data_1 = course_data_map.get(course_1.id)
            college_data_2 = course_data_map.get(course_2.id)

            # Handle college ordering if college_id is provided
            if college_id:
                if course_1.college.id != college_id:
                    college_data_1, college_data_2 = college_data_2, college_data_1
                    course_1, course_2 = course_2, course_1
                elif course_2.college.id == college_id:
                    college_data_2, college_data_1 = college_data_1, college_data_2
                    course_2, course_1 = course_1, course_2

            result = {
                "college_1": college_data_1,
                "college_2": college_data_2,
                "compare_count": comparison['compare_count'],
                "college_ids": f"{course_1.college.id},{course_2.college.id}",
                "course_ids": f"{course_1.id},{course_2.id}"
            }
            
            if extra_data:
                result.update(extra_data)
            return result

        return CacheHelper.get_or_set(cache_key, compute_data, timeout=3600*24*7)


class ComparisonHelper(BaseComparisonHelper):
    """
    Main comparison helper class that implements specific comparison logic
    for different types of comparisons (degree_branch, degree, domain, college).
    """
    
    COMPARISON_TYPES = {
        'degree_branch': 'degree_branch_comparisons',
        'degree': 'degree_comparisons',
        'domain': 'domain_comparisons',
        'college': 'college_comparisons'
    }

    @lru_cache(maxsize=1028)
    def _filter_condition(self, comparison_type: str, **kwargs) -> Q:
        """
        Generate filter conditions for different comparison types.
        Now handles simplified kwargs with course_id and college_id.

        Args:
            comparison_type: Type of comparison to generate filters for
            kwargs: Dictionary containing course_id and/or college_id

        Returns:
            Django Q object containing the appropriate filter conditions
        """
        # First, get the course details if course_id is provided
        course_details = {}
        if course_id := kwargs.get('course_id'):
            course_details = self._get_course_details(course_id)
            # Update kwargs with the fetched details
            kwargs.update(course_details)

        if comparison_type == 'degree_branch':
            exact_course_condition = Q(course_1__id=kwargs['course_id'])
            exact_match_count = CollegeCompareData.objects.filter(exact_course_condition).count()

            if exact_match_count >= 10:
                return exact_course_condition

            return (
                Q(course_1__id=kwargs['course_id']) |
                (
                    Q(course_1__degree__id=kwargs['degree_id']) & 
                    Q(course_2__degree__id=kwargs['degree_id']) &
                    Q(course_1__branch__id=kwargs['branch_id']) &
                    Q(course_2__branch__id=kwargs['branch_id'])
                )
            )

        elif comparison_type == 'domain':
            return (Q(course_1__degree_domain__id=kwargs['domain_id']) &
                   Q(course_2__degree_domain__id=kwargs['domain_id']) &
                   ~Q(course_1__degree__id=kwargs['degree_id']) &
                   ~Q(course_2__degree__id=kwargs['degree_id']))

        elif comparison_type == 'degree':
            return (Q(course_1__degree__id=kwargs['degree_id']) & 
                   Q(course_2__degree__id=kwargs['degree_id']) & 
                   ~Q(course_1__branch__id=kwargs['branch_id']) & 
                   ~Q(course_2__branch__id=kwargs['branch_id']))

        elif comparison_type == 'college':
            return ( Q(course_1__college_id=kwargs['college_id']) &   ~Q(course_1__branch__id=kwargs['branch_id'])  | Q(course_2__college_id=kwargs['college_id']) &   ~Q(course_2__branch__id=kwargs['branch_id']) )

        return Q()

    @lru_cache(maxsize=1028)
    def _get_extra_data(self, comparison_type: str, course: Course, **kwargs) -> Dict[str, Any]:
        """
        Get additional data specific to each comparison type.
        Now handles simplified kwargs structure.

        Args:
            comparison_type: Type of comparison
            course: Course object to get extra data for
            kwargs: Dictionary containing course_id and/or college_id

        Returns:
            Dictionary containing type-specific extra data
        """
        # First, get the course details if course_id is provided
        course_details = {}
        if course_id := kwargs.get('course_id'):
            course_details = self._get_course_details(course_id)
            # Update kwargs with the fetched details
            kwargs.update(course_details)

        if comparison_type == 'degree_branch':
            return {
                "degree_name": course.degree.name if hasattr(course, 'degree') else None,
                "degree_id": kwargs['degree_id'],
                "branch_id": kwargs['branch_id'],
                "branch_name": course.branch.name if hasattr(course, 'branch') else None,
                "course_name": course.course_name if hasattr(course, 'course_name') else None,
            }
        elif comparison_type == 'degree':
            return {
                "degree_name": course.degree.name if hasattr(course, 'degree') else None,
                "degree_id": kwargs['degree_id'],
            }
        elif comparison_type == 'domain':
            return {
                "domain_name": DomainHelper.format_domain_name(course.degree_domain.name) if hasattr(course, 'degree_domain') and course.degree_domain else None,
                "domain_id": kwargs['domain_id'],
            }
        elif comparison_type == 'college':
            if college_id := kwargs.get('college_id'):
                try:
                    college_name = CollegeDataHelper.get_college_name(college_id)
                    return {"college_name": college_name} if college_name else {}
                except College.DoesNotExist:
                    logger.error(f"College with id {college_id} not found")
                    return {"college_name": None}
        return {}

    def _process_comparison(self, comparison: Dict, course_map: Dict[int, Course],
                          course_data_map: Dict[int, Dict[str, Any]],
                          extra_data: Optional[Dict[str, Any]] = None,
                          college_id: Optional[int] = None,
                          cache_burst: int = 0) -> Optional[Dict[str, Any]]:
        """
        Helper function to process a single comparison.

        Args:
            comparison: Raw comparison data
            course_map: Mapping of course IDs to Course objects
            course_data_map: Mapping of course IDs to course data
            extra_data: Optional additional data to include
            college_id: Optional college ID for ordering
            cache_burst: Optional parameter to force cache refresh

        Returns:
            Processed comparison data or None if invalid
        """
        course = course_map.get(comparison['course_1'])
        if not course:
            return None
        return self._transform_comparison_data(comparison, course_map, course_data_map, extra_data,
                                            college_id=college_id, cache_burst=cache_burst)

    def get_popular_comparisons(self, comparison_type: str, cache_burst: int = 0, **kwargs) -> List[Dict[str, Any]]:
        if comparison_type not in self.COMPARISON_TYPES:
            return []

        cache_key = CacheHelper.get_cache_key(
            self.COMPARISON_TYPES[comparison_type],
            *[str(value) for value in kwargs.values()]
        )

        def fetch_comparisons():
            pr = cProfile.Profile()
            pr.enable()
            start_time = time.time()

            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"get_popular_comparisons - Cache hit for key: {cache_key}")
                return cached_result

            filter_condition = self._filter_condition(comparison_type, **kwargs)

            query_kwargs = {'cache_burst': cache_burst}
            compare_data = self._get_base_comparison_query_raw(filter_condition, **query_kwargs)

            if not compare_data:
                logger.info(f"get_popular_comparisons - No compare data found.")
                return []


            course_ids = set()
            for comp in compare_data:
                course_ids.add(comp['course_1'])
                course_ids.add(comp['course_2'])

            course_map = self._get_courses_by_ids(course_ids, cache_burst=cache_burst)
            courses = [course for course_id, course in course_map.items()]
            course_data_map = self._prepare_course_data_bulk(courses, cache_burst=cache_burst)


            results = []
            processed_pairs = set()
            comparison_args = []

            for comparison in compare_data:
                pair_key = tuple(sorted((comparison['course_1'], comparison['course_2'])))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                extra_data = self._get_extra_data(comparison_type, course_map.get(comparison['course_1']), **kwargs)
                comparison_args.append((comparison, course_map, course_data_map, extra_data, kwargs.get('college_id'), cache_burst))


            num_comparisons = len(comparison_args)
            max_workers = min(32, num_comparisons or 8)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                processed_results = list(executor.map(lambda args: self._process_comparison(*args), comparison_args))

            results = [result for result in processed_results if result][:10]


            end_time = time.time()
            logger.info(f"get_popular_comparisons - Total time: {end_time - start_time:.4f} seconds")
            cache.set(cache_key, results, timeout=3600*24*7)
            logger.info(f"get_popular_comparisons - Cached result for key: {cache_key}")


            pr.disable()
            s = io.StringIO()
            sortby = pstats.SortKey.CUMULATIVE
            ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
            ps.print_stats()
            logger.info(f"Profiling Results:\n{s.getvalue()}")

            

            return results

        return CacheHelper.get_or_set(cache_key, fetch_comparisons, timeout=3600 * 24*7, cache_burst=cache_burst)
