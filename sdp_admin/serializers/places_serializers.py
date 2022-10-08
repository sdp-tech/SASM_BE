from rest_framework import serializers
from places.models import SNSType

class SNSTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SNSType
        fields = [
            'id',
            'name',
        ]