from django.utils.timezone import localtime
import re, time, os
import threading
from datetime import datetime as t
from django.db.models import F, Q
from rank_predictor.models import RpSmartRegistration
from tools.api.serializers import ToolBasicDetailSerializer
from tools.models import CPProductCampaign, UrlAlias, UrlMetaPatterns
from rest_framework.pagination import PageNumberPagination
from django.utils.text import slugify
from utils.helpers.response import SuccessResponse,ErrorResponse
from rest_framework import status
from utils.helpers.choices import FIELD_TYPE, TOOL_TYPE_INTEGER

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
        print("hereeee")
        print(instance,"--------------->>>>>>>>>>>")
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
        data = CPProductCampaign.objects.filter(pk=pk).values('id','type','exam','name','usage_count_matrix'\
                ,'positive_feedback_percentage','app_status','published','display_preference','gif','youtube',\
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
                    "published": data.get("published"),
                },
                "input_page_media": {
                    "display_preference": data.get("display_preference"),
                    "gif": data.get("gif"),
                    "youtube": data.get("youtube"),
                    "image": data.get("image"),
                    "secondary_image": data.get("secondary_image"),
                    "smart_registration": data.get("smart_registration"),
                    "promotion_banner_wap": data.get("promotion_banner_wap"),
                },
            }
            url_alias_data = UrlAlias.objects.filter(source = f'result-predictor/{pk}').values('alias','url_meta_pattern_id').first()
            seo_data = UrlMetaPatterns.objects.filter(id = url_alias_data.get('url_meta_pattern_id')).values('page_title','meta_keywords', 'meta_desc').first()
            structured_data['seo_detail'] = {
                    "page_title": seo_data.get("page_title"),
                    "meta_description": seo_data.get("meta_desc"),
                    "keywords": seo_data.get("meta_keywords"),
                    "url_alias": url_alias_data.get("alias"),
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
    
    def add_edit_basic_detail(self, *args,**kwargs):
        bulk_create_data = []
        bulk_update_data = []
        request_data = kwargs.get('request_data')
        smart_registration = kwargs.get('smart_registration')
        instance = kwargs.get('instance')

        # Updating request data to handle created_by in update case
        if instance:
            request_data['created_by'] = instance.created_by

        serializer = ToolBasicDetailSerializer(instance=instance, data=request_data) if instance else ToolBasicDetailSerializer(data=request_data)
        if serializer.is_valid():
            obj = serializer.save()
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

            self.prepare_meta_data(request_data,obj)
            thread = threading.Thread(target=self.prepare_meta_data, args=(request_data, obj))
            thread.start()
            return "Ok"
        else:
            return serializer.errors
    
    def prepare_meta_data(self, request_data, instance, **kwargs):
        url_alias = request_data.get('url_alias')
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

