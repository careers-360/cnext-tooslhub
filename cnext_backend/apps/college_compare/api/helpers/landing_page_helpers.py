#landind_page_helpers.py ----


from college_compare.models import (
    College, Course, Domain, User, SocialMediaGallery, Location, 
    CollegeReviews, RankingUploadList, CollegeCompareData
)


from django.db.models import Avg, Min, Count, Q,Subquery,F
from django.core.cache import cache
from django.db.models import Prefetch
from functools import lru_cache
import hashlib


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


class CollegeDataHelper:
    @staticmethod
    @lru_cache(maxsize=1000)
    def get_college_logo(college_id):
        cache_key = f'college_logos_{college_id}'
        
        def fetch_logo():
            try:
                logo = SocialMediaGallery.objects.filter(college=college_id).values_list('logo', flat=True).first()
                return f"https://cache.careers360.mobi/media/{logo or 'default_logo.jpg'}"
            except Exception:
                return 'https://cache.careers360.mobi/media/default_logo.jpg'
        
        return CacheHelper.get_or_set(cache_key, fetch_logo, 86400)  

    @staticmethod
    def get_college_details(college_ids):
        cache_key = f'college_details_{"-".join(map(str, sorted(college_ids)))}'
        
        def fetch_colleges():
            return list(College.objects.filter(
                id__in=college_ids, 
                published='published'
            ).select_related('location').values('id', 'name', 'location__loc_string'))
        
        return CacheHelper.get_or_set(cache_key, fetch_colleges, 3600)

    @staticmethod
    def get_location_string(location):
        if not location:
            return "Location not available"
        return location.loc_string or "Location not available"
    
    @staticmethod
    def get_nirf_rank(college_id):
        nirf_ranking = RankingUploadList.objects.filter(
            college_id=college_id,
            ranking__ranking_authority='NIRF',
            ranking__ranking_entity__in=['Overall', 'Stream Wise Colleges']
        ).aggregate(min_rank=Min('overall_rank'))

        return nirf_ranking['min_rank'] or "NA"

    @staticmethod
    def get_avg_rating(college_id):
        avg_rating = CollegeReviews.objects.filter(
            college_id=college_id
        ).aggregate(avg_rating=Avg('overall_rating') / 20.0)

        return round(avg_rating['avg_rating'] or 0.0, 1)


class DomainHelper:
    @staticmethod
    @lru_cache(maxsize=1000)
    def format_domain_name(old_domain_name):
        if not old_domain_name:
            return 'Unknown'
        parts = old_domain_name.split('.')
        return parts[0].split()[0].capitalize()

    @staticmethod
    def get_valid_domains():
        cache_key = 'valid_Domains'
        
        def fetch_domains():
            return Domain.objects.filter(is_stream=True)
        
        return CacheHelper.get_or_set(cache_key, fetch_domains, 3600)

    @staticmethod
    def get_domain_names(domain_ids):
        cache_key = f'domain_names_{"-".join(map(str, sorted(domain_ids)))}'
        
        def fetch_domain_names():
            domains = Domain.objects.filter(
                id__in=domain_ids, 
                is_stream=True
            ).values('id', 'old_domain_name')
            return {
                domain['id']: DomainHelper.format_domain_name(domain['old_domain_name'])
                for domain in domains
            }
        
        return CacheHelper.get_or_set(cache_key, fetch_domain_names, 3600)
    
    @staticmethod
    def annotate_domain_name(queryset, domain_field: str = 'ranking__nirf_stream') -> Subquery:
        """
        Creates a Subquery annotation for fetching the `old_domain_name`
        corresponding to the specified domain field in a queryset.

        Args:
            queryset: The queryset to annotate.
            domain_field: The field in the queryset to match against `Domain.name`.

        Returns:
            A Subquery that fetches the formatted `old_domain_name`.
        """
        return Subquery(
            Domain.objects.filter(name=F(domain_field))
            .values('old_domain_name')[:1]
        )


class UserContextHelper:
    @staticmethod
    def get_user_context(uid):
        if not uid:
            return {'domain_id': 1, 'education_level': 1}

        cache_key = f'user_context_{uid}'
        
        def fetch_user_context():
            try:
                user = User.objects.select_related('domain').get(uid=uid)
                return {
                    'domain_id': user.domain.id if user.domain and user.domain.is_stream else 1,
                    'education_level': user.get_education_level_mark() or 1
                }
            except User.DoesNotExist:
                return {'domain_id': 1, 'education_level': 1}
            except Exception as e:
                return {'domain_id': 1, 'education_level': 1, 'error': str(e)}
        
        return CacheHelper.get_or_set(cache_key, fetch_user_context, 3600*24)

    @staticmethod
    def get_top_compared_colleges(domain_id, education_level):
       
        cache_key = f"Top_compared_{domain_id}_{education_level}"
        
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

       
        compare_data_query = CollegeCompareData.objects.filter(
            Q(course_1__college__domains__id=domain_id),
            Q(course_1__level=education_level)
        ).values('college_1').annotate(
            total_comparisons=Count('college_1')
        ).order_by('-total_comparisons')[:5]
        
        college_ids = [entry['college_1'] for entry in compare_data_query]

      
        colleges = College.objects.filter(id__in=college_ids, published='published').only('id', 'name', 'short_name')

       
        result = [
            {
                'id': college.id,
                'name': college.name,
                'short_name': college.short_name,
            }
            for college in colleges
        ]

        cache.set(cache_key, result, timeout=1800)  
        return result
    
    @staticmethod
    def get_top_comparison_on_college(college_ids):
        cache_key = f"Top___compared__{college_ids}"

        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        compare_data_query = (
            CollegeCompareData.objects.filter(
                Q(college_1__in=college_ids) |
                Q(college_2__in=college_ids) |
                Q(college_3__in=college_ids) |
                Q(college_4__in=college_ids)
            )
            .values('college_1', 'college_2', 'college_3', 'college_4')
        )

        comparison_counts = {}
        for row in compare_data_query:
            for field in ['college_1', 'college_2', 'college_3', 'college_4']:
                college_id = row[field]
                if college_id not in college_ids:
                    comparison_counts[college_id] = comparison_counts.get(college_id, 0) + 1

        top_colleges = sorted(
            comparison_counts.items(), key=lambda x: x[1], reverse=True
        )[:6]
        top_college_ids = [college_id for college_id, _ in top_colleges]

        colleges = College.objects.filter(
            id__in=top_college_ids, published='published'
        ).only('id', 'name', 'short_name')

        result = [
            {
                'id': college.id,
                'name': college.name,
                'short_name': college.short_name,
                'comparison_count': comparison_counts[college.id],
            }
            for college in colleges
            if college.id in comparison_counts
        ]

        result_sorted = sorted(result, key=lambda x: x['comparison_count'], reverse=True)

        cache.set(cache_key, result_sorted, timeout=1800)

        return result_sorted