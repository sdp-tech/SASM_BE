from django.urls import path
from .views import PostListApi, PostDetailApi, PostCreateApi, PostUpdateApi, PostDeleteApi, PostLikeApi, PostCommentView, PostReportView, PostCommentReportView, PostHashtagListApi

urlpatterns = [
    path('posts/',
         PostListApi.as_view(), name='post_list'),
    path('posts/<int:post_id>/',
         PostDetailApi.as_view(), name='post_detail'),
    path('posts/create/', PostCreateApi.as_view(), name='post_create'),
    path('posts/<int:post_id>/update/',
         PostUpdateApi.as_view(), name='post_update'),
    path('posts/<int:post_id>/delete/',
         PostDeleteApi.as_view(), name='post_delete'),
    path('posts/<int:post_id>/like/',
         PostLikeApi.as_view(), name='post_like'),
    path('post_hashtags/',
         PostHashtagListApi.as_view(), name='post_hashtag_list'),
    path('post_comments/',
         PostCommentView.as_view({'get': 'list', 'post': 'create'}), name='post_comments'),
    path('post_comments/<int:pk>/',
         PostCommentView.as_view({'get': 'retrieve', 'patch': 'update', 'delete': 'destroy'}), name='post_comment'),
    path('report/post/',
         PostReportView.as_view({'post': 'create'}), name='post_report'),
    path('report/post_comment/',
         PostCommentReportView.as_view({'post': 'create'}), name='post_comment_report'),
]
