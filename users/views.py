from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from datetime import datetime, timedelta
import jwt
import uuid
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from django.conf import settings
from .models import User, Session
from .serializers import UserSerializer, UserCreateSerializer, UserUpdateSerializer, LoginSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        # 개발 중 테스트를 위해 모든 액션에 대해 인증 없이 접근 가능하도록 설정
        return [AllowAny()]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate JWT token using rest_framework_simplejwt
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        return Response({
            'refresh': str(refresh),
            'access': access_token,
            'token': access_token,
            'user': UserSerializer(user).data
        })
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        # 테스트를 위해 인증 요구사항 제거
        # 인증된 사용자가 있으면 해당 사용자 반환, 없으면 첫 번째 사용자 반환
        if request.user.is_authenticated:
            return Response(UserSerializer(request.user).data)
        else:
            # 첫 번째 사용자 반환
            user = User.objects.first()
            if user:
                return Response(UserSerializer(user).data)
            return Response({'detail': '사용자가 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            Session.objects.filter(token=token).delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserCreateView(generics.CreateAPIView):
    """회원가입 API"""
    permission_classes = [AllowAny]
    serializer_class = UserCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # JWT 토큰 생성
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    """로그인 API"""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({
                'error': 'username과 password를 모두 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return Response({
                'error': '잘못된 인증 정보입니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """사용자 프로필 조회/수정 API"""
    permission_classes = [AllowAny]  # 개발 중 테스트를 위해 임시로 변경
    serializer_class = UserSerializer

    def get_object(self):
        # 인증된 사용자가 있으면 해당 사용자 반환
        if self.request.user.is_authenticated:
            return self.request.user
        else:
            # 테스트를 위해 임시로 첫 번째 사용자 반환
            return User.objects.first()

class UserLogoutView(APIView):
    """로그아웃 API"""
    permission_classes = [AllowAny]  # 개발 중 테스트를 위해 임시로 변경

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': '로그아웃되었습니다.'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST) 