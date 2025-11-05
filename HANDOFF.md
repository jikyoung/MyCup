# 🔄 MyCup 프로젝트 인계 문서

**마지막 업데이트:** 2024-11-04  
**현재 상태:** MVP 95% 완료, 배포 준비 단계

---

## ✅ 완료된 작업 (지금까지)

### 🔐 1. 인증 시스템 (100%)

**구현된 기능:**
- ✅ 일반 회원가입/로그인 (JWT)
- ✅ Google OAuth 로그인
- ✅ Kakao OAuth 로그인
- ✅ 비밀번호 암호화 (bcrypt)

**주요 파일:**
```
app/api/routes/auth.py          # 인증 API 엔드포인트
app/services/oauth_service.py   # OAuth 서비스 (Google, Kakao)
app/models/user.py              # User 모델 (provider, provider_id 포함)
```

**OAuth 플로우:**
```
1. GET /api/v1/auth/google      → Google 로그인 페이지
2. Google 인증 완료             → callback으로 리다이렉트
3. 사용자 정보 저장/업데이트      → JWT 토큰 발급
4. 프론트엔드로 리다이렉트        → http://localhost:3000/auth/callback?token=...
```

---

### 📸 2. 사진 관리 (100%)

**구현된 기능:**
- ✅ 사진 업로드 (최대 16장, 파일당 20MB)
- ✅ 사진 목록 조회 (페이지네이션)
- ✅ 사진 삭제
- ✅ 파일 보안 (확장자, MIME 타입, 크기 검증)

**주요 파일:**
```
app/api/routes/photos.py        # 사진 API
app/models/photo.py             # Photo 모델
app/core/file_security.py       # 파일 보안 검증
```

**보안 규칙:**
- 허용 포맷: jpg, jpeg, png, webp
- 파일당 최대: 20MB
- 요청당 최대: 320MB (16장)

---

### 🏆 3. 월드컵 시스템 (100%)

**구현된 기능:**
- ✅ 월드컵 생성 (4/8/16강)
- ✅ 토너먼트 브라켓 자동 생성
- ✅ 매치 선택 (승자 선택)
- ✅ 다음 라운드 자동 진행
- ✅ 우승자 판정
- ✅ 결과 조회 (순위 TOP 4)

**주요 파일:**
```
app/api/routes/worldcup.py      # 월드컵 API
app/models/worldcup.py          # Worldcup 모델
app/models/match.py             # Match 모델
app/services/worldcup_service.py # 토너먼트 로직
```

**API 플로우:**
```
1. POST /api/v1/worldcup                    → 월드컵 생성
2. POST /api/v1/worldcup/{id}/matches/{id}/select → 승자 선택 (반복)
3. GET /api/v1/worldcup/{id}/result         → 결과 조회
```

---

### 🤖 4. AI 분석 & 인사이트 (100%)

**구현된 기능:**
- ✅ GPT-4 Vision으로 사진 분석 (키워드, 감정, 설명)
- ✅ 배치 처리 (여러 장 동시)
- ✅ 인사이트 스토리텔링
- ✅ 월드컵 완료 시 자동 분석
- ✅ DB 캐싱 (60초 → 1초 단축)
- ✅ 에러 핸들링 (재시도 3회)

**주요 파일:**
```
app/services/ai_service.py      # OpenAI API 연동
app/models/worldcup.py          # analysis_result 필드 (JSON 캐시)
```

**분석 내용:**
- `keywords`: 사진 키워드 3개 (예: "바다", "가족", "행복")
- `emotion`: 감정 (happy/peaceful/excited/nostalgic)
- `description`: 한 줄 설명
- `insight_story`: AI 생성 스토리텔링

**비용 최적화:**
- 동일 월드컵 재조회 시 캐시 사용 (API 호출 없음)
- 월드컵 완료 시 자동 분석 → DB 저장

---

### 🎨 5. 카드뉴스 생성 (90%)

**구현된 기능:**
- ✅ Pillow로 이미지 생성
- ✅ 기본 템플릿 (표지 + 순위 3장)
- ✅ 한글 폰트 지원 (AppleSDGothicNeo)
- ✅ 카드뉴스 생성 API

**주요 파일:**
```
app/services/cardnews_service.py # 카드뉴스 생성
app/api/routes/worldcup.py       # POST /api/v1/worldcup/{id}/cardnews
uploads/cardnews/                # 생성된 카드 저장
```

**미완성:**
- ❌ 워터마크 (무료/프리미엄 구분)
- ❌ 다운로드 API (현재는 URL만 제공)
- ❌ 고급 템플릿 2-3개 추가

---

### 🔗 6. 공유 기능 (80%)

**구현된 기능:**
- ✅ 공유 링크 생성 (짧은 ID)
- ✅ 인증 없이 조회 가능
- ✅ 만료 기간 설정
- ✅ 공개/비공개 설정

**주요 파일:**
```
app/api/routes/share.py         # 공유 API
app/models/share.py             # Share 모델
```

**API:**
```
POST /api/v1/share/worldcup/{id}  → 공유 링크 생성
GET /api/v1/share/{share_id}      → 공유된 월드컵 조회 (인증 불필요)
```

**미완성:**
- ❌ 커뮤니티 투표 기능 (다른 사람이 투표)

---

### ⚡ 7. 성능 & 보안 (100%)

**구현된 기능:**
- ✅ Rate Limiting
  - 무료: 평생 5회
  - 프리미엄: 월 50회
- ✅ CORS 설정 (localhost:3000, 8081)
- ✅ 파일 업로드 보안 (확장자, MIME, 크기)
- ✅ DB 인덱스 (성능 개선)
- ✅ 로깅 시스템 (loguru)
  - `logs/mycup.log` (전체)
  - `logs/error.log` (에러만)

**주요 파일:**
```
app/services/rate_limit_service.py   # Rate Limiting
app/core/file_security.py            # 파일 보안
app/core/logger.py                   # 로깅 설정
app/core/logging_middleware.py      # 로깅 미들웨어
main.py                              # CORS, 미들웨어
```

---

## ❌ 남은 작업 (배포 전 필수)

### 🎯 Priority 1: 커뮤니티 투표 (2-3시간)

**목표:** 다른 사람의 월드컵에 투표하고 비교

**구현할 API:**
```python
# 1. 공개 월드컵 목록 조회
GET /api/v1/worldcup/public?page=1&limit=20

Response:
{
  "worldcups": [
    {
      "id": "...",
      "username": "철수",
      "round_type": 4,
      "created_at": "...",
      "vote_count": 52
    }
  ]
}

# 2. 공개 월드컵 투표
POST /api/v1/worldcup/{id}/vote

Request:
{
  "rankings": [
    {"photo_id": "...", "rank": 1},
    {"photo_id": "...", "rank": 2},
    ...
  ]
}

Response:
{
  "my_result": [...],
  "original_result": [...],
  "comparison": "일치율 75%"
}

# 3. 투표 결과 조회
GET /api/v1/worldcup/{id}/votes

Response:
{
  "total_votes": 123,
  "photo_stats": [
    {
      "photo_id": "...",
      "rank_1_count": 45,
      "rank_2_count": 30,
      ...
    }
  ]
}
```

**구현 가이드:**
```python
# app/models/vote.py (새 파일)
class Vote(Base):
    __tablename__ = "votes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    worldcup_id = Column(String, ForeignKey("worldcups.id"))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # 로그인 안 해도 가능
    ip_address = Column(String)  # 중복 투표 방지
    rankings = Column(JSON)  # [{"photo_id": "...", "rank": 1}, ...]
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# app/api/routes/worldcup.py에 추가
@router.get("/public")
def get_public_worldcups(...):
    # Worldcup 조회 (Share에서 is_public=True인 것들)
    # 페이지네이션
    # 투표 수 포함
    pass

@router.post("/{worldcup_id}/vote")
def vote_worldcup(...):
    # IP 중복 체크
    # Vote 저장
    # 원본 결과 vs 내 결과 비교
    pass
```

---

### 🎯 Priority 2: 카드뉴스 개선 (1시간)

**1) 워터마크 추가**
```python
# app/services/cardnews_service.py 수정

def create_cover_card(insight_story, overall_keywords, is_premium=False):
    # ... 기존 코드 ...
    
    # 무료 유저 워터마크
    if not is_premium:
        watermark_font = ImageFont.truetype(FONT_PATH, 30)
        draw.text(
            (540, 1850), 
            "Made with MyCup", 
            font=watermark_font, 
            fill=(200, 200, 200), 
            anchor="mm"
        )
```

**2) 다운로드 API**
```python
# app/api/routes/worldcup.py 추가

@router.get("/{worldcup_id}/cardnews/download")
def download_cardnews(worldcup_id: str, ...):
    # 카드뉴스 이미지들을 ZIP으로 압축
    # 다운로드 링크 반환
    pass
```

---

### 🎯 Priority 3: 프로필 API (1시간)
```python
# app/api/routes/users.py (새 파일)

@router.get("/me")
def get_my_profile(...):
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "profile_image": user.profile_image,
        "tier": "premium" if user.is_premium else "free",
        "stats": {
            "total_worldcups": ...,
            "total_photos": ...,
            "worldcup_remaining": ...
        }
    }

@router.patch("/me")
def update_profile(...):
    # username, profile_image 수정
    pass
```

---

### 🎯 Priority 4: 환경변수 검증 (30분)
```python
# app/config.py 수정

class Settings(BaseSettings):
    # ... 기존 설정 ...
    
    @validator('*', pre=True, always=True)
    def check_required_fields(cls, v, field):
        if v is None or v == "":
            raise ValueError(f"{field.name} 필수 환경변수가 설정되지 않았습니다")
        return v
```

---

### 🎯 Priority 5: README 작성 (1시간)
```markdown
# MyCup

## 설치

\`\`\`bash
# 1. 레포 클론
git clone https://github.com/jikyoung/MyCup.git
cd MyCup

# 2. 가상환경 생성 (uv)
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 의존성 설치
uv sync

# 4. 환경변수 설정
cp .env.example .env
# .env 파일 편집

# 5. DB 마이그레이션
uv run alembic upgrade head

# 6. 서버 실행
uv run uvicorn main:app --reload
\`\`\`

## API 문서
http://localhost:8000/docs

## 환경변수
- DATABASE_URL
- OPENAI_API_KEY
- GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
- KAKAO_CLIENT_ID
...
```

---

## 📂 주요 파일 구조
```
mycup/
├── app/
│   ├── api/routes/
│   │   ├── auth.py           # 인증 (OAuth 포함)
│   │   ├── photos.py         # 사진 관리
│   │   ├── worldcup.py       # 월드컵 (핵심)
│   │   └── share.py          # 공유
│   ├── models/
│   │   ├── user.py           # User (OAuth 필드 포함)
│   │   ├── photo.py
│   │   ├── worldcup.py       # analysis_result 캐시
│   │   ├── match.py
│   │   └── share.py
│   ├── services/
│   │   ├── ai_service.py     # OpenAI (핵심!)
│   │   ├── cardnews_service.py
│   │   ├── worldcup_service.py
│   │   ├── oauth_service.py  # OAuth
│   │   └── rate_limit_service.py
│   ├── core/
│   │   ├── logger.py         # 로깅 설정
│   │   ├── logging_middleware.py
│   │   └── file_security.py
│   └── config.py             # 환경변수
├── logs/                     # 로그 파일
├── uploads/                  # 업로드 파일
├── .env                      # 환경변수
├── main.py                   # FastAPI 앱
└── PROGRESS.md              # 진행 상황
```

---

## 🔧 다음 개발자가 알아야 할 것

### 1. 가상환경 관리: UV
```bash
uv add <package>    # 패키지 설치
uv run <command>    # 명령 실행
```

### 2. DB 마이그레이션
```bash
uv run alembic revision --autogenerate -m "메시지"
uv run alembic upgrade head
```

### 3. 환경변수 (.env)
```
DATABASE_URL=postgresql://mycup_user:password@localhost:5432/mycup
SECRET_KEY=...
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...
KAKAO_CLIENT_ID=...
```

### 4. OpenAI API 비용
- 사진 1장 분석: ~$0.01
- 월드컵 1개 (4장): ~$0.05
- **캐싱 중요!** (analysis_result 필드)

### 5. Rate Limiting
- User 모델의 `worldcup_count`, `monthly_worldcup_count` 필드
- 월드컵 생성 시 자동 증가
- 제한 초과 시 429 에러

---

## 🐛 알려진 이슈

1. **8강/16강 미테스트**
   - 4강만 테스트 완료
   - 프론트 연동 후 테스트 필요

2. **S3 미연동**
   - 현재 로컬 스토리지 사용 (`uploads/` 폴더)
   - 배포 시 S3 연동 필요

3. **Redis 미연동**
   - DB 캐싱만 구현
   - Redis 추가하면 더 빠름

---

## 🚀 배포 체크리스트

- [ ] 커뮤니티 투표 구현
- [ ] 카드뉴스 워터마크
- [ ] 프로필 API
- [ ] 환경변수 검증
- [ ] README 작성
- [ ] 8강/16강 테스트
- [ ] S3 연동
- [ ] 프로덕션 DB 세팅
- [ ] 도메인 연결
- [ ] HTTPS 설정

---

## 💡 GPT/Perplexity로 계속할 때 프롬프트

\`\`\`
나는 MyCup이라는 FastAPI 프로젝트를 개발 중이야.

현재 완료된 것:
- 인증 (일반 + OAuth)
- 사진 관리
- 월드컵 시스템
- AI 분석 (GPT-4 Vision)
- 카드뉴스 생성
- 공유 기능
- Rate Limiting, CORS, 로깅

다음 구현할 것:
1. 커뮤니티 투표 기능
   - 공개 월드컵 목록 API
   - 다른 사람 월드컵 투표 API
   - Vote 모델 생성

[HANDOFF.md 파일 내용 복사]

커뮤니티 투표 기능부터 구현 도와줘.
\`\`\`

---

## ✅ 마지막 커밋

\`\`\`bash
git add .
git commit -m "feat: OAuth 로그인 완성 (Google, Kakao)

- Google OAuth 연동
- Kakao OAuth 연동
- User 모델에 provider, provider_id, profile_image 필드 추가
- 세션 미들웨어 추가
- OAuth 콜백 → JWT 토큰 발급 → 프론트 리다이렉트
- 테스트 완료"

git push origin dev
\`\`\`

---

**행운을 빕니다! 🚀**
