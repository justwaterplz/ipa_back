from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from .models import Post, Tag, PostTag, Bookmark

User = get_user_model()

class PostAPITestCase(APITestCase):
    def setUp(self):
        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 테스트용 태그 생성
        self.tag = Tag.objects.create(name='test_tag', language='ko')
        
        # 테스트용 게시물 생성
        self.post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            author=self.user
        )
        PostTag.objects.create(post=self.post, tag=self.tag)

    def test_create_post(self):
        """게시물 생성 테스트"""
        url = reverse('post-list')
        data = {
            'title': 'New Post',
            'content': 'New Content',
            'tag_names': ['new_tag']
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(Tag.objects.count(), 2)

    def test_list_posts(self):
        """게시물 목록 조회 테스트"""
        url = reverse('post-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("게시물 목록:", response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_post(self):
        """게시물 상세 조회 테스트"""
        url = reverse('post-detail', kwargs={'pk': self.post.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Post')

    def test_update_post(self):
        """게시물 수정 테스트"""
        url = reverse('post-detail', kwargs={'pk': self.post.pk})
        data = {
            'title': 'Updated Post',
            'content': 'Updated Content'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Post')

    def test_delete_post(self):
        """게시물 삭제 테스트"""
        url = reverse('post-detail', kwargs={'pk': self.post.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)

    def test_bookmark_post(self):
        """게시물 북마크 테스트"""
        url = reverse('post-bookmark', kwargs={'pk': self.post.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Bookmark.objects.filter(user=self.user, post=self.post).exists())

    def test_list_tags(self):
        """태그 목록 조회 테스트"""
        url = reverse('tag-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("태그 목록:", response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_user_posts(self):
        """사용자의 게시물 목록 조회 테스트"""
        url = reverse('user-posts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("사용자의 게시물 목록:", response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_user_bookmarks(self):
        """사용자의 북마크 목록 조회 테스트"""
        # 먼저 북마크 생성
        Bookmark.objects.create(user=self.user, post=self.post)
        
        url = reverse('user-bookmarks')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("사용자의 북마크 목록:", response.data)
        self.assertEqual(len(response.data['results']), 1)
