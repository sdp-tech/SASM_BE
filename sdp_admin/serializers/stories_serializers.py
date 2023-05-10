import time
from django.shortcuts import get_object_or_404

from rest_framework import serializers

from stories.models import Story, StoryPhoto
from places.models import Place


class StorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Story
        ordering = ['-id']
        fields = [
            'id',
            'title',
            'story_review',
            'place',
            'tag',
            'preview',
            'rep_pic',
            'html_content',
        ]

    def change_rep_pic_name(self, story, validated_data):
        place_id = validated_data['place'].id
        ext = story.rep_pic.name.split(".")[-1]
        story.rep_pic.name = '{}/{}.{}'.format(place_id,
                                               'rep' + str(int(time.time())), ext)

    def create(self, validated_data):
        # validated_data 내 rep_pic의 이름 변경이 원활하게 되지 않아 DRY한 방법으로 구현
        story = Story(**validated_data)

        self.change_rep_pic_name(story, validated_data)
        story.save()

        return story

    def update(self, instance, validated_data):
        # validated_data 내 rep_pic의 이름 변경이 원활하게 되지 않아 DRY한 방법으로 구현
        print(validated_data)
        fields = instance._meta.fields
        for field in fields:
            field = field.name.split('.')[-1]  # to get coulmn name
            # rep_pic이 업데이트되지 않았을 경우 skip
            if field == 'rep_pic' and 'rep_pic' not in validated_data:
                continue
            exec("instance.%s = validated_data.get(field, instance.%s)" %
                 (field, field))

        # rep_pic이 업데이트되었을 때 실행
        if 'rep_pic' in validated_data:
            self.change_rep_pic_name(instance, validated_data)
        instance.save()
        return instance


class StoryPhotoSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = StoryPhoto
        fields = [
            'caption',
            'image',
        ]
