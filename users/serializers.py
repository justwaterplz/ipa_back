from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'profile_image', 'is_admin', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'profile_image')
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        if 'profile_image' in validated_data:
            user.profile_image = validated_data['profile_image']
            user.save()
            
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'profile_image')
        
    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.profile_image = validated_data.get('profile_image', instance.profile_image)
        instance.save()
        return instance

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128, write_only=True, style={'input_type': 'password'})
    
    def validate(self, data):
        email = data.get('email', None)
        password = data.get('password', None)
        
        if not email or not password:
            raise serializers.ValidationError("이메일과 비밀번호를 모두 입력해주세요.")
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("해당 이메일로 등록된 사용자가 없습니다.")
        
        user = authenticate(username=user.username, password=password)
        
        if not user:
            raise serializers.ValidationError("이메일 또는 비밀번호가 올바르지 않습니다.")
        
        if not user.is_active:
            raise serializers.ValidationError("비활성화된 계정입니다.")
        
        return {
            'user': user
        } 