from rest_framework import serializers
from sdp_admin.models import Voc

class VocSerializer(serializers.ModelSerializer):

    class Meta:
        model = Voc
        fields = [
            'content',
        ]
    
    def create(self, validated_data):
        voc = Voc.objects.create(**validated_data)
        return voc
    
