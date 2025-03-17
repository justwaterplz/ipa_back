from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    STATUS_CHOICES = (
        ('not_requested', '신청 전'),
        ('pending', '승인 대기 중'),
        ('approved', '승인됨'),
        ('rejected', '거부됨'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_requested')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username
    
    @property
    def user_status(self):
        """사용자의 상태와 관리자 권한을 함께 반환합니다."""
        if self.is_superuser:
            return 'superuser'
        elif self.is_admin:
            return 'admin'
        else:
            return self.status

class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s session {self.id}"

class AdminRequest(models.Model):
    """관리자 요청 모델"""
    REQUEST_TYPE_CHOICES = (
        ('general_request', '일반 요청'),
        ('permission_request', '권한 신청'),
        ('feature_request', '기능 요청'),
        ('bug_report', '버그 신고'),
    )
    
    STATUS_CHOICES = (
        ('pending', '대기 중'),
        ('approved', '승인됨'),
        ('rejected', '거부됨'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_requests')
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPE_CHOICES)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 권한 신청 관련 추가 필드
    name = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s {self.request_type} request"
    
    class Meta:
        ordering = ['-created_at'] 