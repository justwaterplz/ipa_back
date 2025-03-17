from rest_framework import viewsets, status, generics, parsers, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from datetime import datetime, timedelta
import jwt
import uuid
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.http import FileResponse, HttpResponse
import os
from django.conf import settings
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from django.conf import settings
from .models import User, Session, AdminRequest
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer, LoginSerializer,
    AdminRequestSerializer, AdminRequestCreateSerializer, AdminRequestUpdateSerializer,
    CustomTokenObtainPairSerializer
)

# 커스텀 토큰 뷰 - 이메일로 로그인
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.request.method == 'OPTIONS':
            return [AllowAny()]
        elif self.action == 'create':
            return [AllowAny()]
        elif self.action in ['update_status', 'make_admin']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
    
    def options(self, request, *args, **kwargs):
        """OPTIONS 요청을 처리합니다."""
        response = Response()
        if '/profile-image/' in request.path:
            response['Allow'] = 'GET, POST, DELETE, OPTIONS'
        elif self.action == 'update' or self.action == 'partial_update':
            response['Allow'] = 'PUT, PATCH, OPTIONS'
        else:
            response['Allow'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        return response
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        return Response(UserSerializer(request.user).data)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            Session.objects.filter(token=token).delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """사용자의 승인 상태를 업데이트합니다. 관리자만 사용 가능합니다."""
        user = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in [choice[0] for choice in User.STATUS_CHOICES]:
            return Response({'error': '유효하지 않은 상태입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.status = new_status
        user.save()
        
        return Response(UserSerializer(user).data)
    
    @action(detail=True, methods=['post'])
    def make_admin(self, request, pk=None):
        """사용자에게 관리자 권한을 부여하거나 해제합니다. 슈퍼유저만 사용 가능합니다."""
        if not request.user.is_superuser:
            return Response({'error': '슈퍼유저만 이 작업을 수행할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        user = self.get_object()
        is_admin = request.data.get('is_admin', False)
        
        user.is_admin = is_admin
        user.save()
        
        return Response(UserSerializer(user).data)
    
    @action(detail=False, methods=['post'])
    def request_approval(self, request):
        """사용자가 승인을 요청합니다."""
        user = request.user
        
        if user.status != 'not_requested':
            return Response({'error': '이미 승인을 요청했거나 승인된 상태입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.status = 'pending'
        user.save()
        
        return Response(UserSerializer(user).data)

    @action(detail=True, methods=['get'], url_path='profile-image')
    def get_profile_image(self, request, pk=None):
        """사용자의 프로필 이미지를 조회합니다."""
        user = self.get_object()
        
        if not user.profile_image:
            return Response({'error': '프로필 이미지가 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 이미지 파일 경로
        image_path = os.path.join(settings.MEDIA_ROOT, str(user.profile_image))
        
        # 파일이 존재하는지 확인
        if not os.path.exists(image_path):
            return Response({'error': '이미지 파일을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 이미지 파일 반환
        return FileResponse(open(image_path, 'rb'), content_type='image/jpeg')
    
    @action(detail=True, methods=['post'], url_path='profile-image')
    def upload_profile_image(self, request, pk=None):
        """사용자의 프로필 이미지를 업로드/변경합니다."""
        print(f"프로필 이미지 업로드 요청 받음: 메서드={request.method}, 경로={request.path}")
        print(f"요청 헤더: {request.headers}")
        print(f"요청 데이터 타입: {type(request.data)}")
        print(f"요청 데이터 키: {request.data.keys() if hasattr(request.data, 'keys') else 'No keys'}")
        print(f"요청 FILES 키: {request.FILES.keys() if hasattr(request.FILES, 'keys') else 'No keys'}")
        
        try:
            user = self.get_object()
            
            # 자신의 프로필 이미지만 변경 가능
            if str(user.id) != str(request.user.id) and not request.user.is_staff:
                print(f"권한 오류: 요청 사용자 ID={request.user.id}, 대상 사용자 ID={user.id}")
                return Response({'error': '다른 사용자의 프로필 이미지를 변경할 권한이 없습니다.'}, 
                               status=status.HTTP_403_FORBIDDEN)
            
            # 이미지 파일 확인
            image_file = None
            
            # 먼저 request.FILES에서 이미지 찾기
            if 'image' in request.FILES:
                image_file = request.FILES['image']
                print(f"request.FILES['image'] 발견: {image_file.name}, 크기: {image_file.size}")
            elif 'profile_image' in request.FILES:
                image_file = request.FILES['profile_image']
                print(f"request.FILES['profile_image'] 발견: {image_file.name}, 크기: {image_file.size}")
            # 그 다음 request.data에서 이미지 찾기
            elif 'image' in request.data:
                image_file = request.data['image']
                print(f"request.data['image'] 발견: 타입: {type(image_file)}")
            elif 'profile_image' in request.data:
                image_file = request.data['profile_image']
                print(f"request.data['profile_image'] 발견: 타입: {type(image_file)}")
            
            if not image_file:
                return Response({'error': '이미지 파일이 제공되지 않았습니다.'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # 이미지 파일 타입 확인
            print(f"이미지 파일 타입: {type(image_file)}")
            if hasattr(image_file, 'name'):
                print(f"이미지 파일 이름: {image_file.name}")
            if hasattr(image_file, 'size'):
                print(f"이미지 파일 크기: {image_file.size}")
            
            # 기존 이미지가 있으면 삭제
            if user.profile_image:
                old_image_path = os.path.join(settings.MEDIA_ROOT, str(user.profile_image))
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # 새 이미지 저장 - 직접 파일 저장 방식으로 변경
            file_ext = os.path.splitext(image_file.name)[1] if hasattr(image_file, 'name') else '.jpg'
            filename = f"profile_{user.id}{file_ext}"
            upload_path = os.path.join('profile_images', filename)
            full_path = os.path.join(settings.MEDIA_ROOT, upload_path)
            
            # 디렉토리 확인
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 파일 저장
            with open(full_path, 'wb+') as destination:
                if hasattr(image_file, 'chunks'):
                    for chunk in image_file.chunks():
                        destination.write(chunk)
                else:
                    destination.write(image_file.read())
            
            # 사용자 모델 업데이트
            user.profile_image = upload_path
            user.save()
            
            # 이미지 URL 생성
            image_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{upload_path}")
            print(f"생성된 이미지 URL: {image_url}")
            
            return Response({
                'message': '프로필 이미지가 업데이트되었습니다.',
                'profile_image': image_url
            })
        except Exception as e:
            print(f"프로필 이미지 업로드 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'프로필 이미지 업로드 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], url_path='profile-image')
    def delete_profile_image(self, request, pk=None):
        """사용자의 프로필 이미지를 삭제합니다."""
        user = self.get_object()
        
        # 자신의 프로필 이미지만 삭제 가능
        if str(user.id) != str(request.user.id) and not request.user.is_staff:
            return Response({'error': '다른 사용자의 프로필 이미지를 삭제할 권한이 없습니다.'}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        # 이미지가 없는 경우
        if not user.profile_image:
            return Response({'error': '삭제할 프로필 이미지가 없습니다.'}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        # 이미지 파일 삭제
        image_path = os.path.join(settings.MEDIA_ROOT, str(user.profile_image))
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # 이미지 필드 초기화
        user.profile_image = None
        user.save()
        
        return Response({'message': '프로필 이미지가 삭제되었습니다.'})

class UserCreateView(generics.CreateAPIView):
    """회원가입 API"""
    permission_classes = [AllowAny]
    serializer_class = UserCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """사용자 프로필 조회/수정 API"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class UserLogoutView(APIView):
    """로그아웃 API"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': '로그아웃되었습니다.'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ImageUploadView(APIView):
    """이미지 업로드 API"""
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def post(self, request):
        if 'image' not in request.data:
            return Response({'error': '이미지 파일이 제공되지 않았습니다.'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        image = request.data['image']
        
        # 이미지 저장 경로 설정 (media/uploads/)
        upload_path = os.path.join('uploads', f"{uuid.uuid4()}{os.path.splitext(image.name)[1]}")
        
        # 이미지 저장
        with open(os.path.join(settings.MEDIA_ROOT, upload_path), 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)
        
        # 이미지 URL 반환
        image_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{upload_path}")
        
        return Response({
            'image_url': image_url
        }, status=status.HTTP_201_CREATED)

class AdminRequestViewSet(viewsets.ModelViewSet):
    """관리자 요청 관련 API"""
    serializer_class = AdminRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'request_type']
    search_fields = ['message', 'user__username', 'user__email']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    queryset = AdminRequest.objects.all()
    
    def options(self, request, *args, **kwargs):
        """OPTIONS 요청을 처리합니다."""
        response = Response()
        if request.path.endswith('/permission-request/'):
            response['Allow'] = 'POST, OPTIONS'
        elif request.path.endswith('/admin-request/'):
            response['Allow'] = 'POST, OPTIONS'
        elif request.path.endswith('/my-requests/'):
            response['Allow'] = 'GET, OPTIONS'
        elif '/approve/' in request.path or '/reject/' in request.path:
            response['Allow'] = 'POST, OPTIONS'
        else:
            response['Allow'] = 'GET, OPTIONS'
        return response
    
    def get_queryset(self):
        # 관리자는 모든 요청을 볼 수 있고, 일반 사용자는 자신의 요청만 볼 수 있음
        if self.request.user.is_staff or self.request.user.is_superuser or self.request.user.is_admin:
            return AdminRequest.objects.all()
        return AdminRequest.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AdminRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AdminRequestUpdateSerializer
        return AdminRequestSerializer
    
    def get_permissions(self):
        if self.request.method == 'OPTIONS':
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy', 'list_all']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def admin_request(self, request):
        """일반 관리자 요청을 생성합니다."""
        serializer = AdminRequestCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        admin_request = serializer.save(request_type='general_request')
        
        return Response({
            'success': True,
            'message': '요청이 성공적으로 전송되었습니다.',
            'request': AdminRequestSerializer(admin_request).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def permission_request(self, request):
        """권한 신청 요청을 생성합니다."""
        print(f"권한 신청 요청 받음: {request.data}")  # 디버깅용 로그
        
        try:
            serializer = AdminRequestCreateSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            admin_request = serializer.save(request_type='permission_request')
            
            # 사용자 상태를 'pending'으로 변경
            user = request.user
            user.status = 'pending'
            user.save()
            
            return Response({
                'success': True,
                'message': '권한 신청이 성공적으로 전송되었습니다.',
                'request': AdminRequestSerializer(admin_request).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"권한 신청 처리 중 오류 발생: {str(e)}")  # 디버깅용 로그
            return Response({
                'success': False,
                'message': f'권한 신청 처리 중 오류가 발생했습니다: {str(e)}',
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """관리자 요청을 승인합니다."""
        admin_request = self.get_object()
        
        # 관리자 권한 확인
        if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin):
            return Response({'error': '관리자 권한이 필요합니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # 이미 처리된 요청인지 확인
        if admin_request.status != 'pending':
            return Response({'error': '이미 처리된 요청입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 요청 상태 업데이트
        admin_request.status = 'approved'
        admin_request.admin_note = request.data.get('admin_note', '')
        admin_request.save()
        
        # 권한 신청인 경우 사용자 상태도 업데이트
        if admin_request.request_type == 'permission_request':
            user = admin_request.user
            user.status = 'approved'
            user.save()
        
        return Response({
            'success': True,
            'message': '요청이 성공적으로 승인되었습니다.',
            'request': AdminRequestSerializer(admin_request).data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """관리자 요청을 거부합니다."""
        admin_request = self.get_object()
        
        # 관리자 권한 확인
        if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin):
            return Response({'error': '관리자 권한이 필요합니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # 이미 처리된 요청인지 확인
        if admin_request.status != 'pending':
            return Response({'error': '이미 처리된 요청입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 요청 상태 업데이트
        admin_request.status = 'rejected'
        admin_request.admin_note = request.data.get('admin_note', '')
        admin_request.save()
        
        # 권한 신청인 경우 사용자 상태도 업데이트
        if admin_request.request_type == 'permission_request':
            user = admin_request.user
            user.status = 'rejected'
            user.save()
        
        return Response({
            'success': True,
            'message': '요청이 성공적으로 거부되었습니다.',
            'request': AdminRequestSerializer(admin_request).data
        })
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """현재 사용자의 요청 목록을 조회합니다."""
        queryset = AdminRequest.objects.filter(user=request.user)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def list_all(self, request):
        """모든 요청 목록을 조회합니다. (관리자 전용)"""
        queryset = AdminRequest.objects.all()
        
        # 필터링
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 검색
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(message__icontains=search)
            )
        
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data) 