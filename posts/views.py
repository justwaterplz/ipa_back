from django.shortcuts import render
from rest_framework import viewsets, status, generics, serializers, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import F
from .models import Post, Tag, PostTag, Bookmark
from .serializers import PostSerializer, TagSerializer, PostCreateSerializer
import uuid
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your views here.

class PostViewSet(viewsets.ModelViewSet):
    """게시물 CRUD API"""
    permission_classes = [AllowAny]  # 개발 중 테스트를 위해 임시로 변경
    serializer_class = PostSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_queryset(self):
        queryset = Post.objects.all()
        tag = self.request.query_params.get('tag', None)
        if tag:
            queryset = queryset.filter(tags__name=tag)
        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateSerializer
        return PostSerializer

    def perform_create(self, serializer):
        # 인증된 사용자가 있으면 해당 사용자를 작성자로 설정
        if self.request.user.is_authenticated:
            serializer.save(author=self.request.user)
        else:
            # 테스트를 위해 임시로 첫 번째 사용자를 작성자로 설정
            user = User.objects.first()
            if user:
                serializer.save(author=user)
            else:
                raise serializers.ValidationError("게시물을 생성하려면 최소한 한 명의 사용자가 필요합니다.")

    @action(detail=True, methods=['post'])
    def bookmark(self, request, pk=None):
        """게시물 북마크"""
        post = self.get_object()
        
        # 인증된 사용자가 있으면 해당 사용자로 북마크 처리
        if request.user.is_authenticated:
            user = request.user
        else:
            # 테스트를 위해 임시로 첫 번째 사용자 사용
            user = User.objects.first()
            if not user:
                return Response({"error": "북마크를 추가하려면 최소한 한 명의 사용자가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        bookmark, created = Bookmark.objects.get_or_create(
            user=user,
            post=post
        )
        if not created:
            bookmark.delete()
            return Response({'status': '북마크가 제거되었습니다.'})
        return Response({'status': '북마크가 추가되었습니다.'})

class TagListView(generics.ListAPIView):
    """태그 목록 API"""
    permission_classes = [AllowAny]  # 개발 중 테스트를 위해 임시로 변경
    serializer_class = TagSerializer

    def get_queryset(self):
        queryset = Tag.objects.all()
        language = self.request.query_params.get('language', 'ko')
        queryset = queryset.filter(language=language)
        return queryset.order_by('name')

class UserPostsView(generics.ListAPIView):
    """사용자의 게시물 목록 API"""
    permission_classes = [AllowAny]  # 개발 중 테스트를 위해 임시로 변경
    serializer_class = PostSerializer

    def get_queryset(self):
        # 인증된 사용자가 있으면 해당 사용자의 게시물 반환
        if self.request.user.is_authenticated:
            return Post.objects.filter(author=self.request.user).order_by('-created_at')
        else:
            # 테스트를 위해 임시로 첫 번째 사용자의 게시물 반환
            user = User.objects.first()
            if user:
                return Post.objects.filter(author=user).order_by('-created_at')
            return Post.objects.none()

class UserBookmarksView(generics.ListAPIView):
    """사용자의 북마크 목록 API"""
    permission_classes = [AllowAny]  # 개발 중 테스트를 위해 임시로 변경
    serializer_class = PostSerializer

    def get_queryset(self):
        # 인증된 사용자가 있으면 해당 사용자의 북마크 반환
        if self.request.user.is_authenticated:
            return Post.objects.filter(bookmark__user=self.request.user).order_by('-created_at')
        else:
            # 테스트를 위해 임시로 첫 번째 사용자의 북마크 반환
            user = User.objects.first()
            if user:
                return Post.objects.filter(bookmark__user=user).order_by('-created_at')
            return Post.objects.none()
