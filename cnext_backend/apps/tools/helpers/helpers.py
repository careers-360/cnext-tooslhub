from django.utils.timezone import localtime
import re, time, os
import threading
from datetime import datetime as t
from django.db.models import F, Q
from cnext_backend import settings
from rank_predictor.models import RpContentSection, RpSmartRegistration
from tools.api.serializers import ToolBasicDetailSerializer
from tools.models import CPProductCampaign, UrlAlias, UrlMetaPatterns
from rest_framework.pagination import PageNumberPagination
from django.utils.text import slugify
from utils.helpers.response import SuccessResponse,ErrorResponse
from rest_framework import status
from utils.helpers.choices import FIELD_TYPE, TOOL_TYPE_INTEGER
import json

class UrlAliasCreation():

    def __init__(self):
        self.current_timestamp = int(time.mktime(t.strptime(t.today().strftime('%d/%m/%Y, %I:%M:%S'), "%d/%m/%Y, %I:%M:%S").timetuple()))

    def url_length_check(self, alias_type=None):
        url_length = 1000 
        return url_length

    def pathauto_is_alias_reserved(self, alias, pid):
        if pid:
            data = UrlAlias.objects.filter(Q(alias=alias) & ~Q(id=pid))
        else:
            data = UrlAlias.objects.filter(alias=alias)
        pid = data.count()
        if pid > 0:
            return True
        return False

    def check_duplicate_alias(self, alias, pid, alias_type=None):
        actual_alias = alias
        url_length = self.url_length_check(alias_type)
        alias = (alias[:url_length]) if len(alias) > url_length else alias
        alias_status = self.pathauto_is_alias_reserved(alias, pid)
        if alias_status == False:
            return alias
        else:
            seperator = 1
            while (alias_status):
                alias = actual_alias
                alias = alias + '-' + str(seperator)
                status = self.pathauto_is_alias_reserved(alias, False)
                if status == False:
                    return alias
                else:
                    seperator += 1
                    continue

    def update_or_create_alias(self, source, alias, pattern_id, pid=None):
        if pid:
            alias_instance = UrlAlias.objects.get(id=pid)
            if alias_instance.alias != alias:
                alias_instance.source = source
                alias_instance.alias = alias
                alias_instance.url_meta_pattern_id = pattern_id
                alias_instance.save()
        else:
            new_alias = UrlAlias(
                url_meta_pattern_id=pattern_id,
                source=source, 
                alias=alias,
                created=self.current_timestamp,
                updated=self.current_timestamp,
                created_by=1,
                updated_by=1,
                status=1
            )
            new_alias.save()

    def seo_url_alias_creation(self, url_alias=None, instance=None, **kwargs):
        if kwargs.get('type'):
            url_meta_type = kwargs.get('type')

        alias_meta_type = 'rppredictorfieldsmapping'
        source = f'{url_meta_type}/{instance.id}'
        source_result = f'{url_meta_type}/result/{instance.id}'
        aliases = UrlAlias.objects.filter(Q(source=source) | Q(source=source_result))
        alias_dict = {alias.source: alias.id for alias in aliases}
        pid = alias_dict.get(source)
        pid_result = alias_dict.get(source_result)
        pattern_id = UrlMetaPatterns.objects.filter(type=alias_meta_type).first().id
        result_pattern_id = UrlMetaPatterns.objects.filter(type=alias_meta_type).last().id

        alias = f'{url_alias}'
        alias_result = f'{url_alias}/result'
        alias = self.check_duplicate_alias(alias, pid)
        alias_result = self.check_duplicate_alias(alias_result, pid_result)
        self.update_or_create_alias(source, alias, pattern_id, pid)
        self.update_or_create_alias(source_result, alias_result, result_pattern_id, pid_result)

class CustomPaginator(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return {
            'lastPage': self.page.paginator.num_pages,
            'itemsOnPage': self.page_size,
            'current': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'totalRows': self.page.paginator.count,
            'results': data
        }


class ToolsHelper():

    def __init__(self, request=None, **kwargs):
        self.request = request
        self.current_timestamp = int(time.mktime(t.strptime(t.today().strftime('%d/%m/%Y, %I:%M:%S'), "%d/%m/%Y, %I:%M:%S").timetuple()))

    def get_manage_predictor_tools_filter(self):
        id =  self.request.query_params.get('name')
        domain = self.request.query_params.get('domain')
        tool_type = self.request.query_params.get('tool_type') 
        consumption_type = self.request.query_params.get('consumption_type')
        published_status_app = self.request.query_params.get('published_status_app')
        published_status_web_wap = self.request.query_params.get('published_status_web_wap')

        filter_data = dict()
        if id:
            filter_data['id'] = id
        if domain:
            filter_data['domain'] = domain
        if tool_type:
            filter_data['type'] = tool_type
        if consumption_type:
            filter_data['consume_type'] = consumption_type
        if published_status_app:
            filter_data['app_status'] = published_status_app
        if published_status_web_wap:
            filter_data['for_web'] = published_status_web_wap

        return filter_data
    
    def get_predictor_tool_list(self,filter_value):

        itemsOnPage = self.request.query_params.get('page_size',10)
        queryset = CPProductCampaign.objects.only(
            'id', 'name', 'price', 'offer_price', 'for_web', 'app_status', 'created', 'updated'
        ).order_by('-updated')
        
        if filter_value:
            queryset = queryset.filter(**filter_value)

        published_result_predictor = queryset.filter(type='result_predictor').count()
        paginator = CustomPaginator()
        paginator.page_size = itemsOnPage
        tools = paginator.paginate_queryset(queryset, self.request)
        tools_data = []
        for tool in tools:
            tools_data.append({
                "id": tool.id,
                "name": tool.name,
                "list_price":tool.price,
                "offer_price":tool.offer_price,
                "web_wap_status":"published" if tool.for_web else "unpublished",
                "app_status": tool.app_status,
                "created_date":self.get_humanize_date_format(tool.created),
                "updated_date":self.get_humanize_date_format(tool.updated),
            })
            
        return {"total_published_result_predictor":published_result_predictor,"tools_list":paginator.get_paginated_response(tools_data)}
    
    @staticmethod
    def get_humanize_date_format(date):
        if date:
            return localtime(date).strftime('%b %d, %Y %I:%M %p')
        return None

    def get_basic_detail_data(self,pk):
        try:
            seo_data = {}
            data = CPProductCampaign.objects.filter(pk=pk).values('id','type','exam','name','usage_count_matrix'\
                    ,'positive_feedback_percentage','app_status','for_web','display_preference','gif','youtube',\
                        'image','secondary_image','smart_registration',\
                            'promotion_banner_wap').first()
            if data:
                structured_data = {
                    "id":data.get("id"),
                    "basic_detail": {
                        "type": data.get("type"),
                        "exam": data.get("exam"),
                        "name": data.get("name"),
                        "usage_count_matrix": data.get("usage_count_matrix"),
                        "positive_feedback_percentage": data.get("positive_feedback_percentage"),
                        "app_status": data.get("app_status"),
                        "for_web": data.get("for_web"),
                    },
                    "input_page_media": {
                        "display_preference": data.get("display_preference"),
                        "gif": data.get("gif"),
                        "youtube": data.get("youtube"),
                        "image": f"{settings.CAREERS_BASE_IMAGES_URL}{data.get('image')}" if data.get('image') else None,
                        "secondary_image": f"{settings.CAREERS_BASE_IMAGES_URL}{data.get('secondary_image')}" if data.get("secondary_image") else None,
                        "smart_registration": data.get("smart_registration"),
                        "promotion_banner_wap": data.get("promotion_banner_wap"),
                    },
                }
                url_alias_data = UrlAlias.objects.filter(source = f'result-predictor/{pk}').values('alias','url_meta_pattern_id').first()
                if url_alias_data:
                    seo_data = UrlMetaPatterns.objects.filter(id = url_alias_data.get('url_meta_pattern_id')).values('page_title','meta_keywords', 'meta_desc').first()
                structured_data['seo_detail'] = {
                        "page_title": seo_data.get("page_title") if seo_data else None,
                        "meta_description": seo_data.get("meta_desc",None) if seo_data else None,
                        "keywords": seo_data.get("meta_keywords",None) if seo_data else None,
                        "url_alias": url_alias_data.get("alias",None )if url_alias_data else None,
                    }
                smart_registration_instance = RpSmartRegistration.objects.filter(product_id = pk).values('field', 'peak_season', 'non_peak_season')
                prepared_data = [
                    {
                        'id': data['field'],
                        'name': FIELD_TYPE.get(data['field'], 'Unknown'),
                        'peak_season': data['peak_season'],
                        'non_peak_season': data['non_peak_season']
                    }
                    for data in smart_registration_instance
                ]
                structured_data['smart_registration_flow'] = prepared_data
            return structured_data
        except Exception as e:
            return str(e)
        
    def add_edit_basic_detail(self, *args,**kwargs):
        bulk_create_data = []
        bulk_update_data = []
        request_data = kwargs.get('request_data')
        smart_registration = kwargs.get('smart_registration')
        instance = kwargs.get('instance')

        # Updating request data to handle created_by in update case
        if instance:
            request_data['created_by'] = instance.created_by
            image_fields = ['image', 'secondary_image','gif']
            for field in image_fields:
                if request_data.get(field):
                    field_data = request_data.get(field)
                    if field_data:
                        if isinstance(field_data, str):# Check if the field data contains url and replace it with image field
                            request_data[field] = getattr(instance, field)
                    else:                              # Check if the field data is None (explicitly removing the image)
                        request_data[field] = None

        serializer = ToolBasicDetailSerializer(instance=instance, data=request_data) if instance else ToolBasicDetailSerializer(data=request_data)
        if serializer.is_valid():
            obj = serializer.save()
            if smart_registration:
                product_id = obj.id
                created_by = obj.created_by
                updated_by = obj.updated_by

                existing_records = RpSmartRegistration.objects.filter(product_id=product_id)
                existing_lookup = {record.field: record for record in existing_records}

                for data in smart_registration:
                    field = data.get('id')
                    peak_season = data.get('peak_season')
                    non_peak_season = data.get('non_peak_season')

                    if field in existing_lookup:
                        # Prepare for bulk update
                        existing_record = existing_lookup[field]
                        existing_record.peak_season = peak_season
                        existing_record.non_peak_season = non_peak_season
                        existing_record.updated_by = updated_by
                        bulk_update_data.append(existing_record)
                    else:
                        # Prepare for bulk creation
                        bulk_create_data.append(RpSmartRegistration(
                            field=field,
                            peak_season=peak_season,
                            non_peak_season=non_peak_season,
                            product_id=product_id,
                            created_by=created_by,
                            updated_by=updated_by
                        ))

                if bulk_update_data:
                    RpSmartRegistration.objects.bulk_update(bulk_update_data, ['peak_season', 'non_peak_season', 'updated_by'])

                if bulk_create_data:
                    RpSmartRegistration.objects.bulk_create(bulk_create_data)

            thread = threading.Thread(target=self.prepare_meta_data, args=(request_data, obj))
            thread.start()
            return True, {'product_id':product_id}
        else:
            return False, serializer.errors
    
    def prepare_meta_data(self, request_data, instance, **kwargs):
        url_alias = request_data.get('url_alias')
        tool_type = request_data.get('type')
        page_title = request_data.get('page_title')
        meta_keywords = request_data.get('meta_keywords')
        meta_desc = request_data.get('meta_description')
        kwargs['type'] = 'result-predictor'

        old_url_alias = UrlAlias.objects.filter(source=f'result-predictor/{instance.id}').values_list('alias', flat=True).first()

        if old_url_alias != url_alias:
            als = UrlAliasCreation()
            als.seo_url_alias_creation(url_alias=url_alias, instance=instance, **kwargs)

        meta_pattern = UrlMetaPatterns.objects.filter(type='rppredictorfieldsmapping').first()
        if meta_pattern:
            if (
                meta_pattern.meta_desc != meta_desc or
                meta_pattern.meta_keywords != meta_keywords or
                meta_pattern.page_title != page_title
            ):
                meta_pattern.meta_desc = meta_desc
                meta_pattern.meta_keywords = meta_keywords
                meta_pattern.page_title = page_title
                meta_pattern.updated = self.current_timestamp
                meta_pattern.save()

    def get_input_page_detail_data(self, pk):
        data = CPProductCampaign.objects.filter(pk=pk).values(
            'id', 'display_name_type', 'custom_exam_name', 'custom_flow_type', 
            'custom_year', 'listing_desc','exam_other_content', 'header_section','alias'
        ).first()
        
        if data:
            header_section = data.get('header_section')
            if header_section:
                try:
                    if isinstance(header_section, str):
                        header_section = json.loads(header_section)
                except json.JSONDecodeError:
                    header_section = []
                header_section = [item['value'] for item in header_section if isinstance(item, dict) and 'value' in item]
            data['header_section'] = header_section
        return data
    
    def edit_input_page_detail(self, *args, **kwargs):
        request_data = kwargs.get('request_data')
        instance = kwargs.get('instance')

        update_data = {}
        update_data['listing_desc'] = request_data.get('listing_description')
        update_data['exam_other_content'] = request_data.get('exam_other_content')
        if request_data.get('display_name_type') == 2:
            update_data['alias'] = request_data.get('alias')
        else:
            custom_exam_name = request_data.get('custom_exam_name')
            custom_flow_type = request_data.get('custom_flow_type')
            custom_year = request_data.get('custom_year')
            update_by = request_data.get('updated_by')
            update_data.update({
                'alias': f"{custom_exam_name} {custom_flow_type} {custom_year}",
                'custom_exam_name': custom_exam_name,
                'custom_flow_type': custom_flow_type,
                'custom_year': custom_year,
                'updated_by': update_by
            })

        incoming_header_section = request_data.get('header_section', [])
        
        if isinstance(incoming_header_section, str):
            incoming_header_section = json.loads(incoming_header_section)

        formatted_incoming_header_section = [{"value": item} if isinstance(item, str) else item for item in incoming_header_section]
        update_data['header_section'] = formatted_incoming_header_section
        CPProductCampaign.objects.filter(id=instance.id).update(**update_data)
        return "Ok"
    
    def get_tool_content_data(self, pk):
        image_url = os.getenv('CAREERS_BASE_IMAGES_URL')
        data = RpContentSection.objects.filter(product_id = pk).values('id','heading','content','image_web','image_wap')
        return [
                {
                    'id': item['id'],
                    'heading': item['heading'],
                    'content': item['content'],
                    'image_web': f"{image_url}{item['image_web']}" if item['image_web'] else None,
                    'image_wap': f"{image_url}{item['image_wap']}" if item['image_wap'] else None
                }
                for item in data
            ]

    def edit_tool_content(self, *args, **kwargs):
        request_data = kwargs.get('request_data')
        instance = kwargs.get('instance')
        img_data = kwargs.get('img_data')
        product_id = instance.id
        try:
            existing_sections = RpContentSection.objects.filter(product_id=product_id)
            existing_ids = set(existing_sections.values_list('id', flat=True))
            incoming_ids = set()
            updated_sections = []

            for index, item in enumerate(request_data):
                section_id = item.get('id')
                incoming_ids.add(section_id)

                image_web = img_data.get(f'image_web_{index}')
                image_wap = img_data.get(f'image_wap_{index}')

                if isinstance(image_web, list) and image_web:
                    image_web = image_web[0]
                if isinstance(image_wap, list) and image_wap:
                    image_wap = image_wap[0]

                if section_id:
                    try:
                        content_section = RpContentSection.objects.get(id=section_id)
                        # to handle the case when the request has image in url format
                        if isinstance(image_web, str):
                            image_web = content_section.image_web
                        if isinstance(image_wap, str):
                            image_wap = content_section.image_wap

                        # Handle `null` explicitly passed in the request data
                        if image_web is None:
                            image_web = None
                        if image_wap is None:
                            image_wap = None

                        content_section.heading = item.get('heading', content_section.heading)
                        content_section.content = item.get('content', content_section.content)
                        content_section.updated_by = item.get('updated_by', content_section.updated_by)
                        content_section.image_web = image_web
                        content_section.image_wap = image_wap
                        content_section.save()

                        updated_sections.append({
                            "id": content_section.id,
                            "heading": content_section.heading,
                            "content": content_section.content,
                            "image_web": content_section.image_web.url if content_section.image_web else None,
                            "image_wap": content_section.image_wap.url if content_section.image_wap else None
                        })
                    except RpContentSection.DoesNotExist:
                        return {"message": f"Content section with ID {section_id} does not exist"}

                else:
                    content_section = RpContentSection.objects.create(
                        product_id=product_id,
                        heading=item.get('heading'),
                        content=item.get('content'),
                        image_web=image_web,
                        image_wap=image_wap,
                        created_by= item.get('created_by'),
                        updated_by= item.get('updated_by'),

                    )

            ids_to_delete = existing_ids - incoming_ids
            RpContentSection.objects.filter(id__in=ids_to_delete).delete()

            return {"message": "OK"}

        except Exception as e:
            return {"message": "An error occurred", "error": str(e)}
