


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
 


class BaseComparisonHelper:
    """Base class for comparison helpers."""
    @staticmethod
    def _get_base_comparison_query_raw(filter_condition: Q, cache_burst: int = 0) -> List[Dict]:
        cache_key = CacheHelper.get_cache_key("base_comparison_query", str(filter_condition))

        def compute_query():
            sql, params = CollegeCompareData.objects.filter(filter_condition).values(
                'course_1', 'course_2'
            ).annotate(
                compare_count=Count('id'),
                course_1_college_id=F('course_1__college_id'),
                course_2_college_id=F('course_2__college_id'),
            ).order_by('-compare_count')[:200].query.sql_with_params()
            with connections['default'].cursor() as cursor:
                cursor.execute(sql, params)
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        return CacheHelper.get_or_set(key=cache_key, callback=compute_query, timeout=3600*24*7, cache_burst=cache_burst)
    @staticmethod
    def _get_course_data(course: Course, cache_burst: int = 0) -> Dict[str, Any]:
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
                "degree_name": course.degree.name,
                "level": course.level,
                "domain_id": course.degree_domain.id if hasattr(course, 'degree_domain') and course.degree_domain else None,
                "branch_id": course.branch_id
            }
        return CacheHelper.get_or_set(cache_key, compute_data, cache_burst=cache_burst)
    @staticmethod
    def _prepare_course_data_bulk(courses: QuerySet, cache_burst: int = 0) -> Dict[int, Dict[str, Any]]:
        """Prepares course data in bulk."""
        course_data = {}
        for course in courses:
            course_data[course.id] = BaseComparisonHelper._get_course_data(course, cache_burst)
        return course_data
    @staticmethod
    def _get_courses_by_ids(course_ids: Set[int], cache_burst: int = 0) -> Dict[int, Course]:
        cache_key = CacheHelper.get_cache_key("courses_by_ids_optimized", "_".join(map(str, sorted(course_ids))))
        def fetch_courses():
            courses = Course.objects.filter(id__in=course_ids).select_related(
                'degree', 'branch', 'college', 'college__location', 'degree_domain'
            ).only(
                'id', 'course_name', 'degree_id', 'branch_id', 'level', 'degree__name', 'branch__name',
                'college__name', 'college__short_name', 'college__id', 'college__location', 'degree_domain__id', 'degree_domain__name'
            )
            return {course.id: course for course in courses}
        return CacheHelper.get_or_set(cache_key, fetch_courses, cache_burst=cache_burst, timeout=300)
    @classmethod
    def _transform_comparison_data(cls, comparison: Dict, course_map: Dict[int, Course],
                                    course_data_map: Dict[int, Dict[str, Any]],
                                    extra_data: Optional[Dict[str, Any]] = None,
                                    college_id: Optional[int] = None,
                                    cache_burst: int = 0) -> Optional[Dict[str, Any]]:
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
        return CacheHelper.get_or_set(cache_key, compute_data, cache_burst=cache_burst, timeout=3600*24*7)

class ComparisonHelper(BaseComparisonHelper):
    COMPARISON_TYPES = {
        'degree_branch': 'degree_branch_comparisons',
        'degree': 'degree_comparisons',
        'domain': 'domain_comparisons',
        'college': 'college_comparisons'
    }
    def _filter_condition(self, comparison_type: str, **kwargs) -> Q:
        if comparison_type == 'degree_branch':
            return (
                Q(course_1__degree__id=kwargs['degree_id']) &
                    Q(course_1__branch__id=kwargs['branch_id']) &
                    Q(course_2__branch__id=kwargs['branch_id']) & Q(course_1__id=kwargs['course_id'])  )
        elif comparison_type == 'domain':
            return (Q(course_1__degree_domain__id=kwargs['domain_id']) &
                    Q(course_2__degree_domain__id=kwargs['domain_id']) &
                    ~Q(course_1__degree__id=kwargs.get('degree_id', 0)) &
                    ~Q(course_2__degree__id=kwargs.get('degree_id', 0)))
        elif comparison_type == 'degree':
            return Q(course_1__degree__id=kwargs['degree_id']) & Q(course_2__degree__id=kwargs['degree_id']) & \
                   ~Q(course_1__branch__id=kwargs.get('branch_id', 0)) & ~Q(course_2__branch__id=kwargs.get('branch_id', 0))
        elif comparison_type == 'college':
            return Q(course_1__college_id=kwargs['college_id']) | Q(course_2__college_id=kwargs['college_id'])
        return Q()
    def _get_extra_data(self, comparison_type: str, course: Course, **kwargs) -> Dict[str, Any]:
        if comparison_type == 'degree_branch':
            return {
                "degree_name": course.degree.name if hasattr(course, 'degree') else None,
                "degree_id": kwargs['degree_id'],
                "branch_id": kwargs['branch_id'],
                "branch_name": course.branch.name if hasattr(course, 'branch') else None,
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
            return {
                "college_name": course.college.name,
            }
        return {}
    def _process_comparison(self, comparison: Dict, course_map: Dict[int, Course],
                                    course_data_map: Dict[int, Dict[str, Any]],
                                    extra_data: Optional[Dict[str, Any]] = None,
                                    college_id: Optional[int] = None,
                                    cache_burst: int = 0) -> Optional[Dict[str, Any]]:
        """Helper function to process a single comparison."""
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
            # Attempt to get the cached result first
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"get_popular_comparisons - Cache hit for key: {cache_key}")
                return cached_result
            filter_condition = self._filter_condition(comparison_type, **kwargs)
            compare_data = self._get_base_comparison_query_raw(filter_condition, cache_burst=cache_burst, **kwargs)
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
            max_workers = min(32, num_comparisons or 1)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                processed_results = list(executor.map(lambda args: self._process_comparison(*args), comparison_args))
            
            for result in processed_results:
                if result:
                    results.append(result)
                if len(results) >= 10:
                    break
            end_time = time.time()
            logger.info(f"get_popular_comparisons - Total time: {end_time - start_time:.4f} seconds")
            # Cache the entire result
            cache.set(cache_key, results, timeout=300)
            logger.info(f"get_popular_comparisons - Cached result for key: {cache_key}")
            pr.disable()
            s = io.StringIO()
            sortby = pstats.SortKey.CUMULATIVE
            ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
            ps.print_stats()
            logger.info(f"Profiling Results:\n{s.getvalue()}")
            return results
        return CacheHelper.get_or_set(cache_key, fetch_comparisons, timeout=3600 * 24, cache_burst=cache_burst)

