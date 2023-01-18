from django.urls import path
from .views import PostDetailView, PostCommentView, PostReportView, PostCommentReportView, PostLikeView

urlpatterns = [
    path('post_comments/',
        PostCommentView.as_view({'get': 'list', 'post': 'create'}), name='post_comments'),
    path('post_comments/<int:pk>/',
        PostCommentView.as_view({'get': 'retrieve', 'patch': 'update', 'delete': 'destroy'}), name='post_comment'),
    path('report/post/',
        PostReportView.as_view({'post': 'create'}), name='post_report'),
    path('report/post_comment/',
        PostCommentReportView.as_view({'post': 'create'}), name='post_comment_report'),
    path('post_new/', PostDetailView.as_view({'post': 'create'}), name='post_new'),
    path('post_detail/<int:pk>/',
        PostDetailView.as_view({'put': 'update', 'get': 'retrieve', 'delete': 'destroy'}), name='post_detail'),
    path('post_like/<int:pk>/',
        PostLikeView.as_view({'get': 'get'}), name='post_like_list'),
    path('post_like_user/', PostLikeView.as_view({'post': 'post'}), name='post_like_user'),
]