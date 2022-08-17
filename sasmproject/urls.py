from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path,include
from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

urlpatterns = [
    path('admin/', admin.site.urls),
    path('stories/',include('stories.urls')),
    path('users/',include('users.urls')),
    path('users/', include('dj_rest_auth.urls')),
    path('users/', include('allauth.urls')),
    path('places/', include('places.urls')),
]
# API 문서에 작성될 소개 내용
schema_view = get_schema_view(
    openapi.Info(
        title='API 문서 제목',
        default_version='API 버전',
        description=
        '''
        API 문서 설명

        작성자 : ...
        ''',
        terms_of_service='',
        contact=openapi.Contact(name='이름', email='이메일'),
        license=openapi.License(name='API 문서 이름')
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=urlpatterns,
)

# API 작성에 필요한 url 경로
urlpatterns += [
    path('swagger<str:format>', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('docs/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]