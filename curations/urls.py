from django.urls import path
from .views import RepCurationListApi, AdminCurationListApi, VerifiedUserCurationListApi, CuratedStoryDetailApi, CurationDetailApi, CurationCreateApi, CurationUpdateApi, CurationDeleteApi, CurationListApi

urlpatterns = [
    path('rep_curations/', RepCurationListApi.as_view(), name="rep_curations"),
    path('admin_curations/', AdminCurationListApi.as_view(), name="admin_curations"),
    path('verified_user_curations/', VerifiedUserCurationListApi.as_view(),
         name="verified_user_curations"),
    path('curation_search/', CurationListApi.as_view(), name="curation_search"),
    path('curation_detail/<int:curation_id>/',
         CurationDetailApi.as_view(), name='curation_detail'),
    path('curated_story_detail/<int:curation_id>/',
         CuratedStoryDetailApi.as_view(), name='curated_story_detail'),
    path('curation_create/',
         CurationCreateApi.as_view(), name='curation_create'),
    path('curation_update/<int:curation_id>/',
         CurationUpdateApi.as_view(), name='curation_update'),
    path('curation_delete/<int:curation_id>/',
         CurationDeleteApi.as_view(), name='curation_delete'),
]
