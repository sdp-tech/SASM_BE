from .models import Story
from users.models import User

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def story_like(request, id):
    story = get_object_or_404(Story, id=id)
    user = request.user
    profile = User.objects.get(email=user)
    check_like = story.story_likeuser_set.filter(id=profile.id)

    if check_like.exists():
        story.story_likeuser_set.remove(profile)
        story.story_like_cnt -= 1
        story.save()
        return JsonResponse({'msg': 'cancel'})
    else:
        story.story_likeuser_set.add(profile)
        story.story_like_cnt += 1
        story.save()
        return JsonResponse({'msg': 'click'})