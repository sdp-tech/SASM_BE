from django.urls import path
from .views import PostCommentView, PostReportView, PostCommentReportView

urlpatterns = [
    path('post_comments/',
        PostCommentView.as_view({'get': 'list', 'post': 'create'}), name='post_comments'),
    path('post_comments/<int:pk>/',
        PostCommentView.as_view({'get': 'retrieve', 'patch': 'update', 'delete': 'destroy'}), name='post_comment'),
    path('report/post/',
        PostReportView.as_view({'post': 'create'}), name='post_report'),
    path('report/post_comment/',
        PostCommentReportView.as_view({'post': 'create'}), name='post_comment_report'),
]