from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.PostViewSet, basename='post')

urlpatterns = [
    path('', include(router.urls)),
    path('tags/', views.TagListView.as_view(), name='tag-list'),
    path('user/posts/', views.UserPostsView.as_view(), name='user-posts'),
    path('user/bookmarks/', views.UserBookmarksView.as_view(), name='user-bookmarks'),
] 