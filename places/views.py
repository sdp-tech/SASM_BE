from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .models import Place
from users.models import User

# Create your views here.

@login_required
def place_like(request, id):
    place = get_object_or_404(Place, id=id)
    user = request.user
    profile = User.objects.get(email=user)

    check_like = place.place_likeuser_set.filter(id=profile.id)

    if check_like.exists():
        place.place_likeuser_set.remove(profile)
        place.place_like_cnt -= 1
        place.save()
        return JsonResponse({'msg': 'cancel'})
    else:
        place.place_likeuser_set.add(profile)
        place.place_like_cnt += 1
        place.save()
        return JsonResponse({'msg': 'click'})