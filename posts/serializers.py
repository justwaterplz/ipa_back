from rest_framework import serializers
from .models import Post, Tag, PostTag, Bookmark
from users.serializers import UserSerializer

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'language']

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'tags', 'file', 'image', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class PostCreateSerializer(serializers.ModelSerializer):
    tag_names = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'tag_names', 'file', 'image']
    
    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        post = Post.objects.create(**validated_data)
        
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            PostTag.objects.create(post=post, tag=tag)
        
        return post 