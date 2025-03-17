from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from users.views import ImageUploadView, CustomTokenObtainPairView

schema_view = get_schema_view(
    openapi.Info(
        title="IPA API",
        default_version='v1',
        description="IPA 프로젝트의 API 문서",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # 루트 URL을 Swagger 문서로 리다이렉트
    path('', RedirectView.as_view(url='/swagger/', permanent=False), name='index'),
    
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/posts/', include('posts.urls')),
    
    # 이미지 업로드 API
    path('api/images/upload/', ImageUploadView.as_view(), name='image-upload'),
    
    # JWT 토큰 관련 URL
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # 기존 토큰 엔드포인트도 유지 (호환성을 위해)
    path('api/token/username/', TokenObtainPairView.as_view(), name='token_obtain_pair_username'),
    
    # Swagger 문서화 URL (drf-yasg)
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Spectacular 문서화 URL (drf-spectacular)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# 개발 환경에서 미디어 파일 제공
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 