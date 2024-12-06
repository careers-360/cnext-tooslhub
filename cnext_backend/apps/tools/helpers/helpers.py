from django.utils.timezone import localtime
from tools.models import CPProductCampaign
from rest_framework.pagination import PageNumberPagination

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

    def get_manage_predictor_tools_filter(self):
        id =  self.request.query_params.get('name')
        consumption_type = self.request.query_params.get('consumption_type')
        published_status_web_wap = self.request.query_params.get('status')
        published_status_app = self.request.query_params.get('app_status')

        filter_data = dict()
        if id:
            filter_data['id'] = id
        if consumption_type:
            filter_data['consume_type'] = consumption_type
        if published_status_app:
            filter_data['app_status'] = published_status_app
        if published_status_web_wap:
            filter_data['status'] = published_status_web_wap

        return filter_data
    
    def get_predictor_tool_list(self,filter_value):

        itemsOnPage = self.request.query_params.get('page_size',10)
        queryset = CPProductCampaign.objects.only(
            'id', 'name', 'price', 'offer_price', 'status', 'app_status', 'created', 'updated'
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
                "web_wap_status":"published" if tool.status else "unpublished",
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
