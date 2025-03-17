from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, AdminRequest
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    user_status = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'profile_image', 'is_admin', 'status', 'user_status', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'user_status')

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

class AdminRequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AdminRequest
        fields = ('id', 'user', 'request_type', 'message', 'status', 'admin_note', 'created_at', 'updated_at', 'name', 'department')
        read_only_fields = ('id', 'created_at', 'updated_at')

class AdminRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminRequest
        fields = ('request_type', 'message', 'name', 'department')
        
    def create(self, validated_data):
        user = self.context['request'].user
        admin_request = AdminRequest.objects.create(user=user, **validated_data)
        return admin_request

class AdminRequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminRequest
        fields = ('status', 'admin_note')
        
    def validate_status(self, value):
        if value not in ['approved', 'rejected']:
            raise serializers.ValidationError("상태는 'approved' 또는 'rejected'만 가능합니다.")
        return value

# 커스텀 JWT 토큰 시리얼라이저 - 이메일로 로그인
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    # 인증 성공
                    refresh = self.get_token(user)
                    data = {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'user': UserSerializer(user).data
                    }
                    return data
                else:
                    raise serializers.ValidationError('비밀번호가 일치하지 않습니다.')
            except User.DoesNotExist:
                raise serializers.ValidationError('해당 이메일로 등록된 사용자가 없습니다.')
        else:
            raise serializers.ValidationError('이메일과 비밀번호를 모두 입력해주세요.') 