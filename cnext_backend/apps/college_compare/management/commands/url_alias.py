import logging
from itertools import combinations
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db.models import Q
from college_compare.models import College, CollegeCompareData, BaseUrlAlias


logger = logging.getLogger(__name__)

def clean_college_name(college_name):
    """Clean the college name for URL and H1 tags."""
    return college_name.split('(')[0].strip().replace(" ", "-").replace(",", "")

def get_frequently_compared_colleges_with_batches(min_comparisons=10, batch_size=10000):
    """Fetch frequently compared college pairs in batches."""
    total_records = CollegeCompareData.objects.count()
    logger.info(f"Total records: {total_records}")
    
    processed_records = 0
    comparisons = {}

    while processed_records < total_records:
        batch = (
            CollegeCompareData.objects.values(
                'college_1', 'college_2', 'college_3', 'college_4'
            )
            .order_by('id')[processed_records:processed_records + batch_size]
        )

        for record in batch:
            colleges = [
                record['college_1'],
                record['college_2'],
                record['college_3'],
                record['college_4'],
            ]
            colleges = [college for college in colleges if college is not None]

            for pair in combinations(colleges, 2):
                pair = tuple(sorted(pair))  
                comparisons[pair] = comparisons.get(pair, 0) + 1

        processed_records += len(batch)
        logger.info(f"Processed records: {processed_records}/{total_records} ({(processed_records / total_records) * 100:.2f}%)")

    frequent_pairs = [
        {'college1_id': pair[0], 'college2_id': pair[1], 'count': count}
        for pair, count in comparisons.items() if count >= min_comparisons
    ]

    return frequent_pairs

def get_existing_aliases_and_sources(url_meta_pattern_id=102):
    """Fetch existing aliases and sources to avoid duplicate inserts."""
    existing_entries = BaseUrlAlias.objects.filter(url_meta_pattern_id=url_meta_pattern_id).values_list('alias', 'source', 'url_meta_pattern_id')
    return set(existing_entries)  

def generate_comparison_aliases(frequent_pairs):
    """Generate comparison aliases, sources, and H1 tags from frequent college pairs."""
   
    college_ids = {pair['college1_id'] for pair in frequent_pairs} | {pair['college2_id'] for pair in frequent_pairs}

    
    college_data = {
        college.id: {
            "clean_name": clean_college_name(college.name),
            "h1_name": college.short_name if college.short_name else college.name
        }
        for college in College.objects.filter(id__in=college_ids)
    }

    result = []
    for pair in frequent_pairs:
        college1_id, college2_id = pair['college1_id'], pair['college2_id']

        
        if college1_id == college2_id:
            continue

        college1_name = college_data.get(college1_id, {}).get("clean_name", "Unknown")
        college2_name = college_data.get(college2_id, {}).get("clean_name", "Unknown")

        college1_name_h1tag = college_data.get(college1_id, {}).get("h1_name", "Unknown")
        college2_name_h1tag = college_data.get(college2_id, {}).get("h1_name", "Unknown")

        alias = f"compare-colleges/{college1_name}-vs-{college2_name}"
        source = f"compare-colleges/{college1_id}/{college2_id}"
        h1tag = f"Compare {college1_name_h1tag} vs {college2_name_h1tag} on Ranking, Courses, Cut off, Fee, Placement"

        result.append({"alias": alias, "source": source, "type": "comparison", "h1tag": h1tag})

    return result


def print_comparison_analysis_with_batches(min_comparisons=10, batch_size=10000):
    
    """Perform college comparison analysis and update BaseUrlAlias."""
    
    pairs = get_frequently_compared_colleges_with_batches(min_comparisons, batch_size)
    current_time = timezone.now()
    url_meta_pattern = 102

    logger.info("\nCollege Comparison Analysis")
    logger.info("=" * 50)

    existing_aliases_sources = get_existing_aliases_and_sources(url_meta_pattern_id=url_meta_pattern)
    logger.info(f"Existing aliases and sources: {len(existing_aliases_sources)}")


    created_count = 0
    skipped_count = 0
    aliases_data = []

    for pair in generate_comparison_aliases(pairs):
        alias, source = pair['alias'], pair['source']

        # Avoid duplicate inserts
        if (existing_aliases_sources == set()) or ((alias, source, url_meta_pattern) not in existing_aliases_sources):
            aliases_data.append(BaseUrlAlias(
                alias=alias,
                source=source,
                url_meta_pattern_id=url_meta_pattern,
                h1_tag=pair['h1tag'],
                status=1,
                facet_flag=0,
                push_to_sitemap=1,
                status_code=200,
                created=current_time,
                updated=current_time,
                created_by=1,
                updated_by=1
            ))
            created_count += 1
        else:
            skipped_count += 1
            logger.info(f"Skipping existing comparison: {alias}")


    
    chunk_size = 1000
    if aliases_data:
        for i in range(0, len(aliases_data), chunk_size):
            BaseUrlAlias.objects.bulk_create(aliases_data[i:i + chunk_size], ignore_conflicts=True)

    logger.info(f"\nSummary:")
    logger.info(f"Total pairs processed: {len(pairs)}")
    logger.info(f"New entries created: {created_count}")
    logger.info(f"Existing entries skipped: {skipped_count}")

class Command(BaseCommand):
    help = "Runs the college comparison analysis and updates BaseUrlAlias"

    def handle(self, *args, **kwargs):
        print_comparison_analysis_with_batches()
