from django.shortcuts import render
from rest_framework import viewsets, status, generics, serializers, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import F, Q
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
        
        # 기본 검색 (프롬프트: 제목 및 내용)
        prompt = self.request.query_params.get('prompt', None)
        if prompt:
            queryset = queryset.filter(
                Q(title__icontains=prompt) | 
                Q(content__icontains=prompt)
            )
        
        # 일반 검색어 (제목, 내용, 작성자 이름 등 전체 검색)
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(content__icontains=search) |
                Q(author__username__icontains=search) |
                Q(used_model__icontains=search) |
                Q(model_version__icontains=search) |
                Q(tags__name__icontains=search)
            ).distinct()
        
        # 태그로 필터링
        tag = self.request.query_params.get('tag', None)
        if tag:
            queryset = queryset.filter(tags__name__icontains=tag)
        
        # 여러 태그로 필터링 (쉼표로 구분된 태그 목록)
        tags = self.request.query_params.get('tags', None)
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            tag_query = Q()
            for tag_name in tag_list:
                tag_query |= Q(tags__name__icontains=tag_name)
            queryset = queryset.filter(tag_query).distinct()
        
        # AI 모델로 필터링
        model = self.request.query_params.get('model', None)
        if model:
            queryset = queryset.filter(used_model__icontains=model)
        
        # 모델 버전으로 필터링
        version = self.request.query_params.get('version', None)
        if version:
            queryset = queryset.filter(model_version__icontains=version)
        
        # 작성자로 필터링
        author = self.request.query_params.get('author', None)
        if author:
            queryset = queryset.filter(author__username__icontains=author)
        
        # 작성일 범위로 필터링
        created_after = self.request.query_params.get('created_after', None)
        if created_after:
            queryset = queryset.filter(created_at__gte=created_after)
        
        created_before = self.request.query_params.get('created_before', None)
        if created_before:
            queryset = queryset.filter(created_at__lte=created_before)
        
        # 색상으로 필터링 (추후 구현 예정)
        # color = self.request.query_params.get('color', None)
        # if color:
        #     # 색상 필드가 추가되면 구현
        #     pass
        
        # 정렬 방식
        ordering = self.request.query_params.get('ordering', '-created_at')
        valid_orderings = ['created_at', '-created_at', 'title', '-title', 'author__username', '-author__username']
        if ordering not in valid_orderings:
            ordering = '-created_at'
        
        return queryset.order_by(ordering)

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
