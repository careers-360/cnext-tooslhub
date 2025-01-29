from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task(name='college_compare.tasks.generate_url_aliases')
def generate_url_aliases():
    try:
        logger.info("Starting URL alias generation task")
        call_command('url_alias')
        logger.info("Successfully completed URL alias generation")
        return "URL aliases generated successfully"
    except Exception as exc:
        logger.error(f"Error generating URL aliases: {exc}")
        raise