from tools.models import CPProductCampaign
from rest_framework import serializers

class ToolBasicDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = CPProductCampaign
        fields = ('__all__') #TODO include exclude need to added 