from django.urls import path
from .views import PostCommentView, ReportListView, PostReportView, PostCommentReportView

urlpatterns = [
    path('comments/',
        PostCommentView.as_view({'get': 'list', 'post': 'create'}), name='post_comments'),
    path('comments/<int:pk>/',
        PostCommentView.as_view({'get': 'retrieve', 'patch': 'update', 'delete': 'destroy'}), name='post_comment'),
    path('reports/',
        ReportListView.as_view({'get': 'list', 'post': 'create'}), name='reports'),      
    path('postreport/<int:pk>',
        PostReportView.as_view({'delete': 'destroy'}), name='post_report'),
    path('postcommentreport/<int:pk>',
        PostCommentReportView.as_view({'delete': 'destroy'}), name='post_comment_report'),     
]