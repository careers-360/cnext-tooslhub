

from typing import Any, Callable, Dict, List, Optional, Set,Tuple
from django.db.models import QuerySet, Count, Q
from django.core.cache import cache
import hashlib
from college_compare.models import (
    Domain, CollegeCompareData, Course
)
from .landing_page_helpers import CollegeDataHelper, DomainHelper
import time



class CacheHelper:
    """
    """
    
    @staticmethod
    def get_cache_key(*args: Any) -> str:
        key = '_'.join(str(arg) for arg in args)
        return hashlib.md5(key.encode()).hexdigest()

    @staticmethod
    def get_or_set(key: str, callback: Callable[[], Any], timeout: int = 3600) -> Any:
        """
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
        """
        cache_key = CacheHelper.get_cache_key("base_comparison_query", str(filter_condition))

        def compute_query():
            return CollegeCompareData.objects.filter(filter_condition).values(
                'course_1__college', 'course_2__college', 'course_1', 'course_2'
            ).annotate(
                compare_count=Count('id')
            ).order_by('-compare_count')  # Removed limit here to fetch all matching data

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
                                extra_data: Optional[Dict[str, Any]] = None, 
                                college_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        
        Args:
            comparison: Raw comparison data
            course_map: Mapping of course IDs to Course instances
            extra_data: Additional data to include in result
            college_id: ID of the college that should always be 'college_1' (optional)
        
        Returns:
            comparison data dictionary or None if invalid
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

            
            if college_id and course_1.college.id != college_id:
                college_data_1, college_data_2 = college_data_2, college_data_1
                course_1, course_2 = course_2, course_1

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


class ComparisonHelper(BaseComparisonHelper):
    """
    """
    
    COMPARISON_TYPES = {
        'degree_branch': 'degree_branch_comparisons',
        'degree': 'degree_comparisons',
        'domain': 'domain_comparisons',
        'college': 'college_comparisons'
    }

    def __init__(self):
        self._processed_pairs = set()

    def _is_comparison_processed(self, pair_key: Tuple[int, int]) -> bool:
        """
        Check if a comparison has been processed.
        
        Args:
            pair_key: Tuple of course IDs being compared
            
        Returns:
            bool indicating if comparison has been processed
        """
        if pair_key in self._processed_pairs:
            return True
                
        self._processed_pairs.add(pair_key)
        return False

    def _filter_condition(self, comparison_type: str, **kwargs) -> Q:
        """
        """
        if comparison_type == 'degree_branch':
            return (Q(course_1__degree__id=kwargs['degree_id']) & 
                   Q(course_1__branch__id=kwargs['branch_id']) &
                   Q(course_2__branch__id=kwargs['branch_id']))
        
        elif comparison_type == 'domain':
            return (Q(course_1__degree_domain__id=kwargs['domain_id']) &
                   Q(course_2__degree_domain__id=kwargs['domain_id']) &
                   ~Q(course_1__degree__id=kwargs['degree_id']) &
                   ~Q(course_2__degree__id=kwargs['degree_id']))
        
        elif comparison_type == 'degree':
            return Q(course_1__degree__id=kwargs['degree_id']) & Q(course_2__degree__id=kwargs['degree_id'])  & ~Q(course_1__branch__id=kwargs['branch_id']) & ~Q(course_2__branch__id=kwargs['branch_id'])
        
        elif comparison_type == 'college':
            return Q(course_1__college_id=kwargs['college_id']) | Q(course_2__college_id=kwargs['college_id'])
        
        return Q()

    def _get_extra_data(self, comparison_type: str, course: Course, **kwargs) -> Dict[str, Any]:
        """
       
        Args:
            comparison_type: Type of comparison
            course: Course instance to extract data from
            **kwargs: Additional parameters
            
        Returns:
            Dictionary of additional data
        """
        if comparison_type == 'degree_branch':
            return {
                "degree_name": course.degree.name,
                "degree_id": kwargs['degree_id'],
                "branch_id": kwargs['branch_id'],
                "branch_name": course.branch.name,
            }
        
        elif comparison_type == 'domain':
            domain = Domain.objects.filter(id=kwargs['domain_id']).first()
            return {
                "domain_id": kwargs['domain_id'],
                "domain_name": DomainHelper.format_domain_name(domain.old_domain_name) if domain else None,
            }
        
        elif comparison_type == 'degree':
            return {
                "degree_name": course.degree.name,
                "degree_id": kwargs['degree_id'],
            }
            
        return {}


    def get_popular_comparisons(self, comparison_type: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Get popular comparisons based on type and parameters.
        
        Args:
            comparison_type: Type of comparison to fetch ('degree_branch', 'degree', 'domain', 'college')
            **kwargs: Parameters for filtering comparisons
            
        Returns:
            List of comparison data dictionaries
        """
        if comparison_type not in self.COMPARISON_TYPES:
            return []

       
        cache_key = CacheHelper.get_cache_key(
            self.COMPARISON_TYPES[comparison_type],
            *[str(value) for value in kwargs.values()],
            
            
        )

        def fetch_comparisons():
          
            filter_condition = self._filter_condition(comparison_type, **kwargs)
            compare_data = self._get_base_comparison_query(filter_condition)

            
            compare_data = compare_data[:200]  
            course_ids = {comp['course_1'] for comp in compare_data} | {comp['course_2'] for comp in compare_data}
            course_map = self._get_courses_by_ids(course_ids)

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

               
                extra_data = self._get_extra_data(comparison_type, course, **kwargs)

                
                result = self._transform_comparison_data(comparison, course_map, extra_data, college_id=kwargs.get('college_id'))

                if result:
                    results.append(result)

               
                if len(results) >= 10:
                    break

            return results

        
        return CacheHelper.get_or_set(cache_key, fetch_comparisons, 86400 * 7)