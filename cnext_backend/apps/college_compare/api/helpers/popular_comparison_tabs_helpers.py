

from typing import Any, Callable, Dict, List, Optional, Set
from django.db.models import QuerySet, Count, Q
from django.core.cache import cache
import hashlib
from college_compare.models import (
    Domain, CollegeCompareData, Course
)
from .landing_page_helpers import CollegeDataHelper, DomainHelper



class CacheHelper:
    """
    Helper class for managing cache operations with consistent key generation and error handling.
    """
    
    @staticmethod
    def get_cache_key(*args: Any) -> str:
        """
        Generate a consistent cache key from variable arguments.
        
        Args:
            *args: Variable number of arguments to include in the cache key.
            
        Returns:
            str: MD5 hash of the concatenated arguments.
        """
        key = '_'.join(str(arg) for arg in args)
        return hashlib.md5(key.encode()).hexdigest()

    @staticmethod
    def get_or_set(key: str, callback: Callable[[], Any], timeout: int = 3600) -> Any:
        """
        Get value from cache or compute and store it if not present.
        
        Args:
            key: Cache key to look up
            callback: Function to call if cache miss occurs
            timeout: Cache timeout in seconds (default: 1 hour)
            
        Returns:
            Cached value or computed result from callback
        """
        try:
            result = cache.get(key)
            if result is None:
                result = callback()
                if result is not None:
                    cache.set(key, result, timeout)
            return result
        except Exception as e:
            return callback()




class BaseComparisonHelper:
    """
    Base class providing common functionality for comparison helpers, with caching integrated.
    """

    @staticmethod
    def _get_base_comparison_query(filter_condition: Q) -> QuerySet:
        """
        Get base comparison query with common annotations, with caching.

        Args:
            filter_condition: Q object containing filter conditions

        Returns:
            QuerySet with comparison data
        """
        cache_key = CacheHelper.get_cache_key("base_comparison_query", str(filter_condition))

        def compute_query():
            return CollegeCompareData.objects.filter(filter_condition).values(
                'course_1__college', 'course_2__college', 'course_1', 'course_2'
            ).annotate(
                compare_count=Count('id')
            ).order_by('-compare_count')[:10]

        return CacheHelper.get_or_set(cache_key, compute_query)

    @staticmethod
    def _prepare_course_data(course: Course) -> Dict[str, Any]:
        """
        Prepare standardized course data dictionary, with caching for optimized logo and location fetches.

        Args:
            course: Course instance to prepare data for

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
            }

        return CacheHelper.get_or_set(cache_key, compute_data)

    @staticmethod
    def _get_courses_by_ids(course_ids: Set[int]) -> Dict[int, Course]:
        """
        Fetch courses with related data efficiently, with caching.

        Args:
            course_ids: Set of course IDs to fetch

        Returns:
            Dictionary mapping course IDs to Course instances
        """
        cache_key = CacheHelper.get_cache_key("courses_by_ids", "_".join(map(str, sorted(course_ids))))

        def fetch_courses():
            courses = Course.objects.filter(id__in=course_ids).select_related(
                'degree', 'branch', 'college', 'college__location'
            )
            return {course.id: course for course in courses}

        return CacheHelper.get_or_set(cache_key, fetch_courses)

    @classmethod
    def _transform_comparison_data(cls, comparison: Dict, course_map: Dict[int, Course], 
                                   extra_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Transform comparison data into standardized format, ensuring unique ordering for deduplication,
        with caching for optimization.

        Args:
            comparison: Raw comparison data
            course_map: Mapping of course IDs to Course instances
            extra_data: Additional data to include in result

        Returns:
            Transformed comparison data dictionary or None if invalid
        """
        cache_key = CacheHelper.get_cache_key(
            "comparison_data",
            comparison['course_1'],
            comparison['course_2']
        )

        def compute_data():
            course_1 = course_map.get(comparison['course_1'])
            course_2 = course_map.get(comparison['course_2'])

            if not (course_1 and course_2):
                return None

         
            college_data_1 = cls._prepare_course_data(course_1)
            college_data_2 = cls._prepare_course_data(course_2)

            if college_data_1["name"] > college_data_2["name"]:
                college_data_1, college_data_2 = college_data_2, college_data_1

            result = {
                "college_1": college_data_1,
                "college_2": college_data_2,
                "compare_count": comparison['compare_count'],
                "college_ids": f"{course_1.college.id},{course_2.college.id}",
                "course_ids": f"{course_1.id},{course_2.id}",
            }

            if extra_data:
                result.update(extra_data)

            return result

        return CacheHelper.get_or_set(cache_key, compute_data)


class PopularDegreeBranchComparisonHelper(BaseComparisonHelper):
    """
    Helper for fetching popular comparisons filtered by degree and branch.
    """
    
    @staticmethod
    def get_popular_courses(degree_id: int, branch_id: int) -> List[Dict[str, Any]]:
        """
        Get popular course comparisons for a specific degree and branch.
        
        Args:
            degree_id: ID of the degree to filter by
            branch_id: ID of the branch to filter by
            
        Returns:
            List of comparison data dictionaries
        """
        cache_key = CacheHelper.get_cache_key('degree_branches', degree_id, branch_id)
        
        def fetch_courses():
            filter_condition = Q(course_1__degree__id=degree_id) & Q(course_1__branch__id=branch_id  ) & Q(course_2__branch__id=branch_id  )
            compare_data = PopularDegreeBranchComparisonHelper._get_base_comparison_query(filter_condition)
            
            course_ids = {comp['course_1'] for comp in compare_data} | {comp['course_2'] for comp in compare_data}
            course_map = PopularDegreeBranchComparisonHelper._get_courses_by_ids(course_ids)
            
            results = []
            processed_pairs = set()
            for comparison in compare_data:
                pair_key = tuple(sorted((comparison['course_1'], comparison['course_2'])))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                course = course_map.get(comparison['course_1'])
                if not course:
                    continue

                extra_data = {
                    "degree_name": course.degree.name if course.degree else None,
                    "degree_id": degree_id,
                    "branch_id": branch_id,
                    "branch_name": course.branch.name if course.branch else None,
                }
                result = PopularDegreeBranchComparisonHelper._transform_comparison_data(
                    comparison, course_map, extra_data
                )
                if result:
                    results.append(result)
                    
            return results

        return CacheHelper.get_or_set(cache_key, fetch_courses, 1800)


class PopularDegreeComparisonHelper(BaseComparisonHelper):
    """
    Helper for fetching popular comparisons filtered by degree.
    """
    
    @staticmethod
    def get_popular_courses(degree_id: int) -> List[Dict[str, Any]]:
        """
        Get popular course comparisons for a specific degree.
        
        Args:
            degree_id: ID of the degree to filter by
            
        Returns:
            List of comparison data dictionaries
        """
        cache_key = CacheHelper.get_cache_key('degree', degree_id)
        
        def fetch_courses():
            filter_condition = Q(course_1__degree__id=degree_id) &  Q(course_2__degree__id=degree_id) 
            compare_data = PopularDegreeComparisonHelper._get_base_comparison_query(filter_condition)
            
            course_ids = {comp['course_1'] for comp in compare_data} | {comp['course_2'] for comp in compare_data}
            course_map = PopularDegreeComparisonHelper._get_courses_by_ids(course_ids)
            
            results = []
            processed_pairs = set()
            for comparison in compare_data:
                pair_key = tuple(sorted((comparison['course_1'], comparison['course_2'])))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                course = course_map.get(comparison['course_1'])
                if not course:
                    continue

                extra_data = {
                    "degree_name": course.degree.name if course.degree else None,
                    "degree_id": degree_id,
                }
                result = PopularDegreeComparisonHelper._transform_comparison_data(
                    comparison, course_map, extra_data
                )
                if result:
                    results.append(result)
                    
            return results

        return CacheHelper.get_or_set(cache_key, fetch_courses, 1800)


class PopularDomainComparisonHelper(BaseComparisonHelper):
    """
    Helper for fetching popular comparisons filtered by domain.
    """
    
    @staticmethod
    def get_popular_courses(domain_id: int,degree_id: int,) -> List[Dict[str, Any]]:
        """
        Get popular course comparisons for a specific domain.
        
        Args:
            domain_id: ID of the domain to filter by
            degree_id: ID of the degree to filter by
            
        Returns:
            List of comparison data dictionaries
        """
        cache_key = CacheHelper.get_cache_key('Domaincomparisons_v1', domain_id,degree_id)
        
        def fetch_courses():
            filter_condition =   (
            Q(course_1__degree_domain__id=domain_id) &
            Q(course_2__degree_domain__id=domain_id) &
            ~Q(course_1__degree__id=degree_id) & 
            ~Q(course_2__degree__id=degree_id)
            
        )
            
            compare_data = PopularDomainComparisonHelper._get_base_comparison_query(filter_condition)

            print(compare_data,"------------")
            
            course_ids = {comp['course_1'] for comp in compare_data} | {comp['course_2'] for comp in compare_data}
            print(course_ids)
            course_map = PopularDomainComparisonHelper._get_courses_by_ids(course_ids)
            print(course_map,"----------")
            
            domain = Domain.objects.filter(id=domain_id).first()
            domain_name = DomainHelper.format_domain_name(domain.old_domain_name) if domain else None
            
            results = []
            processed_pairs = set()
            for comparison in compare_data:
                pair_key = tuple(sorted((comparison['course_1'], comparison['course_2'])))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                extra_data = {
                    "domain_id": domain_id,
                    "domain_name": domain_name,
                }
                result = PopularDomainComparisonHelper._transform_comparison_data(
                    comparison, course_map, extra_data
                )
                if result:
                    results.append(result)
                    
            return results

        return CacheHelper.get_or_set(cache_key, fetch_courses, 1800)


class PopularComparisonOnCollegeHelper(BaseComparisonHelper):
    """
    Helper for fetching popular comparisons for a specific college.
    """
    
    @staticmethod
    def fetch_popular_comparisons(college_id: int) -> List[Dict[str, Any]]:
        """
        Fetch popular comparisons for a specific college.
        
        Args:
            college_id: ID of the college to fetch comparisons for
            
        Returns:
            List of comparison data dictionaries
        """
        cache_key = CacheHelper.get_cache_key('colleges_comparisons', college_id)
        
        def fetch_data():
            comparisons = CollegeCompareData.objects.filter(
                Q(course_1__college_id=college_id) | Q(course_2__college_id=college_id)
            ).values(
                'course_1', 'course_2'
            ).annotate(
                compare_count=Count('id')
            ).order_by('-compare_count')[:10]

            course_ids = {comp['course_1'] for comp in comparisons} | {comp['course_2'] for comp in comparisons}
            course_map = PopularComparisonOnCollegeHelper._get_courses_by_ids(course_ids)
            
            results = []
            processed_pairs = set()
            for comparison in comparisons:
                pair_key = tuple(sorted((comparison['course_1'], comparison['course_2'])))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                result = PopularComparisonOnCollegeHelper._transform_comparison_data(comparison, course_map)
                if result:
                    results.append(result)
            
            return results
        
        return CacheHelper.get_or_set(cache_key, fetch_data, 1800)


