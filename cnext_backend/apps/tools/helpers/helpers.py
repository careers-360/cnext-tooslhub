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
    
    def get_predictor_tool_list(self):

        itemsOnPage = self.request.query_params.get('page_size',10)
        queryset = CPProductCampaign.objects.only(
            'id', 'name', 'price', 'offer_price', 'status', 'app_status', 'created', 'updated'
        ).order_by('-updated')
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
                "web/wap_status":"published" if tool.status else "unpublished",
                "app_status": tool.app_status,
                "created_date":self.get_humanize_date_format(tool.created),
                "updated_date":self.get_humanize_date_format(tool.updated)  
            })
            
        return paginator.get_paginated_response(tools_data)
    
    @staticmethod
    def get_humanize_date_format(date):
        if date:
            return localtime(date).strftime('%b %d, %Y %I:%M %p')
        return None
