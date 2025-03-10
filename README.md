# IPA Backend

Django 기반 백엔드 시스템 프로젝트입니다.

## 기술 스택

- Python 3.9+
- Django 5.0.2
- Django REST Framework 3.14.0
- MySQL Database
- JWT 인증

## 프로젝트 구조

```
ipa_back/
├── ipa_back/             # 프로젝트 설정
│   ├── settings.py       # 설정 파일
│   ├── urls.py           # URL 라우팅
│   ├── wsgi.py           # WSGI 설정
│   └── asgi.py           # ASGI 설정
├── users/                # 사용자 앱
│   ├── models.py         # 사용자 모델
│   ├── serializers.py    # 시리얼라이저
│   ├── views.py          # 뷰
│   └── urls.py           # URL 설정
├── posts/                # 게시물 앱
│   ├── models.py         # 게시물 모델
│   ├── serializers.py    # 시리얼라이저
│   ├── views.py          # 뷰
│   └── urls.py           # URL 설정
├── manage.py             # Django 관리 스크립트
└── requirements.txt      # 의존성 목록
```

## 시작하기

### 필수 조건

- Python 3.9 이상
- MySQL 5.7 이상

### 설치 및 설정

1. 가상 환경 생성 및 활성화
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 데이터베이스 마이그레이션
```bash
python manage.py makemigrations
python manage.py migrate
```

4. 개발 서버 실행
```bash
python manage.py runserver
```

## API 엔드포인트

### 인증 API

- `POST /api/users/login/` - 로그인
- `POST /api/users/` - 회원가입
- `GET /api/users/me/` - 현재 사용자 정보 조회
- `POST /api/users/logout/` - 로그아웃

### 사용자 API

- `GET /api/users/` - 모든 사용자 조회
- `GET /api/users/{id}/` - ID로 사용자 조회
- `PUT /api/users/{id}/` - 사용자 정보 업데이트
- `DELETE /api/users/{id}/` - 사용자 삭제

### 게시물 API

- `POST /api/posts/` - 새 게시물 생성
- `GET /api/posts/` - 모든 게시물 조회 (페이징)
- `GET /api/posts/{id}/` - ID로 게시물 조회
- `PUT /api/posts/{id}/` - 게시물 업데이트
- `DELETE /api/posts/{id}/` - 게시물 삭제
- `GET /api/posts/search/?q=검색어` - 게시물 검색
- `GET /api/posts/user-posts/?user_id={id}` - 특정 사용자의 게시물 조회
- `GET /api/posts/bookmarked/` - 북마크한 게시물 조회
- `GET /api/posts/top/` - 인기 게시물 조회
- `POST /api/posts/{id}/like/` - 게시물 좋아요
- `POST /api/posts/{id}/bookmark/` - 게시물 북마크
- `POST /api/posts/{id}/remove-bookmark/` - 게시물 북마크 제거

### 태그 API

- `GET /api/posts/tags/` - 모든 태그 조회
- `GET /api/posts/tags/{id}/` - ID로 태그 조회 