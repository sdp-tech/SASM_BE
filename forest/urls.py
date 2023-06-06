from django.urls import path
from .views import ForestCreateApi, ForestUpdateApi, ForestPhotoCreateApi, ForestDeleteApi, ForestLikeApi, ForestDetailApi, ForestListApi, CategoryListApi, SemiCategoryListApi

urlpatterns = [
    path('create/', ForestCreateApi.as_view(), name="forest_create"),
    path('<int:forest_id>/update/',
         ForestUpdateApi.as_view(), name='forest_update'),
    path('photos/create/',
         ForestPhotoCreateApi.as_view(), name='forest_photo_create'),
    path('<int:forest_id>/delete/',
         ForestDeleteApi.as_view(), name='forest_delete'),
    path('<int:forest_id>/likes/',
         ForestLikeApi.as_view(), name='forest_like'),
    path('<int:forest_id>/',
         ForestDetailApi.as_view(), name='forest_detail'),
    path('',
         ForestListApi.as_view(), name='forest_list'),
    path('categories/',
         CategoryListApi.as_view(), name='category_list'),
    path('semi_categories/',
         SemiCategoryListApi.as_view(), name='semi_category_list'),
]
