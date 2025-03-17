from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, AdminRequestViewSet

# 라우터 등록 방식 변경
router = DefaultRouter()
# 빈 문자열 대신 구체적인 베이스 경로 사용
router.register(r'base', UserViewSet, basename='user')

admin_router = DefaultRouter()
admin_router.register(r'requests', AdminRequestViewSet, basename='admin-requests')

urlpatterns = [
    # 기본 CRUD 작업을 위한 라우터 URL
    path('', UserViewSet.as_view({'get': 'list', 'post': 'create'}), name='user-list'),
    path('<uuid:pk>/', UserViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='user-detail'),
    
    # 기존 URL 패턴 유지
    path('me/', UserViewSet.as_view({'get': 'me'}), name='me'),
    path('logout/', UserViewSet.as_view({'post': 'logout'}), name='logout'),
    
    # 프로필 이미지 URL - 명시적으로 모든 메서드 허용
    path('<uuid:pk>/profile-image/', UserViewSet.as_view({
        'get': 'get_profile_image',
        'post': 'upload_profile_image',
        'delete': 'delete_profile_image',
        'options': 'options'
    }), name='profile-image'),
    
    # 관리자 요청 관련 URL
    path('admin-request/', AdminRequestViewSet.as_view({'post': 'admin_request', 'options': 'options'}), name='admin-request'),
    # 권한 신청 URL - 명시적으로 OPTIONS 메서드 추가
    path('permission-request/', AdminRequestViewSet.as_view({'post': 'permission_request', 'options': 'options'}), name='permission-request'),
    path('my-requests/', AdminRequestViewSet.as_view({'get': 'my_requests', 'options': 'options'}), name='my-requests'),
    
    # 관리자 전용 URL
    path('admin/requests/', AdminRequestViewSet.as_view({'get': 'list_all', 'options': 'options'}), name='admin-requests-list'),
    path('admin/requests/<uuid:pk>/', AdminRequestViewSet.as_view({'get': 'retrieve', 'options': 'options'}), name='admin-request-detail'),
    path('admin/requests/<uuid:pk>/approve/', AdminRequestViewSet.as_view({'post': 'approve', 'options': 'options'}), name='admin-request-approve'),
    path('admin/requests/<uuid:pk>/reject/', AdminRequestViewSet.as_view({'post': 'reject', 'options': 'options'}), name='admin-request-reject'),
] 