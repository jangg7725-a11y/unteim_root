# UNTEIM 웹 배포 · 실행 가이드

사주 입력, 분석 결과, AI 상담(및 선택 TTS)을 쓰려면 **프론트엔드(Vite)** 와 **백엔드(FastAPI)** 를 각각 준비합니다.

## 1. 저장소 구조 요약

| 경로 | 역할 |
|------|------|
| `frontend/` | React + Vite SPA |
| `scripts/run_api_server_v1.py` | FastAPI 엔트리 (`/api/counsel`, `/api/analyze`, …) |
| `engine/` | 사주 엔진 · 상담 로직 |
| 루트 `.env` | 백엔드용 (`OPENAI_API_KEY`, `BACKEND_HOST` 등) |
| `frontend/.env` | 프론트 빌드용 (`VITE_*`만 브라우저에 포함) |

## 2. 환경 변수

### 백엔드 (프로젝트 루트 `.env`)

`README`와 함께 제공되는 **`.env.example`** 을 복사해 `.env` 를 만듭니다.

- **필수(상담 사용 시)**: `OPENAI_API_KEY`
- **바인딩**: `BACKEND_HOST` (로컬 `127.0.0.1`, 서버 공개 시 `0.0.0.0`), `BACKEND_PORT` (기본 `8000`)
- **CORS**: 프론트가 다른 도메인이면 `CORS_ORIGINS=https://your-frontend.example.com` (쉼표로 여러 개)
- **프로덕션**: `UVICORN_RELOAD=0`

### 프론트엔드 (`frontend/.env`)

**`.env.example`** 을 복사해 `frontend/.env` 생성.

- **`VITE_API_BASE_URL`**: 배포 시 백엔드 공개 URL (끝 슬래시 없음), 예: `https://api.example.com`  
  - **비우면**: `npm run dev`에서 `/api/*`가 Vite 프록시로 로컬 백엔드에 전달됨.
- **`VITE_DEV_PROXY_TARGET`**: (선택) 개발 프록시 대상, 기본 `http://127.0.0.1:8000`
- **`VITE_TTS_API_URL`**: (선택) TTS 서버 베이스 URL. 없으면 브라우저 `speechSynthesis` 폴백.

> ⚠️ `VITE_*`는 빌드 시 문자열로 박히므로 **비밀키를 넣지 마세요**. API 키는 항상 서버 환경 변수만.

## 3. 로컬 실행 순서

### A. Python 의존성

```bash
cd /path/to/unteim_root
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### B. 백엔드

루트에 `.env` 설정 후:

```bash
python scripts/run_api_server_v1.py
```

- 기본: `http://127.0.0.1:8000`
- 헬스: `http://127.0.0.1:8000/api/health` → `{"ok":true,"service":"unteim-api"}`

### C. 프론트

```bash
cd frontend
copy .env.example .env
# VITE_API_BASE_URL 은 로컬 개발 시 비워둬도 됨 (프록시 사용)
npm install
npm run dev
```

브라우저: **http://localhost:5173**

## 4. 프로덕션 빌드

```bash
cd frontend
# 배포용 API URL 설정
set VITE_API_BASE_URL=https://your-api.example.com
npm run build
```

`frontend/dist/`를 정적 호스팅(Netlify, S3+CloudFront, Nginx 등)에 올립니다.

백엔드는 별도 프로세스/컨테이너에서 실행하고, 위 `VITE_API_BASE_URL`과 동일한 호스트로 `/api/*`가 열려 있어야 합니다.

### 프리뷰 (로컬에서 dist 확인)

```bash
cd frontend
npm run preview
```

## 5. 배포 순서 (권장)

1. 백엔드 서버에 Python 3.x, `requirements.txt` 설치, 루트 `.env`에 `OPENAI_API_KEY`, `BACKEND_HOST=0.0.0.0`, `CORS_ORIGINS` 설정  
2. `python scripts/run_api_server_v1.py` 또는 `uvicorn scripts.run_api_server_v1:app --host 0.0.0.0 --port 8000` (프로덕션은 `UVICORN_RELOAD=0`)  
3. HTTPS 리버스 프록시(Nginx/Caddy)로 API 노출  
4. `frontend`에서 `VITE_API_BASE_URL` 설정 후 `npm run build`, 정적 파일 배포  
5. 브라우저에서 앱 열기 → 사주 입력 → AI 상담까지 동작 확인  

## 6. 배포 후 테스트 체크리스트

- [ ] `GET {API}/api/health` → `ok: true`
- [ ] 사주 입력 저장 후 AI 상담 탭에서 메시지 전송 → 응답 수신
- [ ] `OPENAI_API_KEY` 미설정 시 상담 503 및 안내 문구
- [ ] (TTS 사용 시) `VITE_TTS_API_URL` 및 서버 `/tts` 동작

## 7. 개발 vs 배포 차이

| 항목 | 개발 (`npm run dev`) | 배포 (정적 빌드) |
|------|----------------------|------------------|
| API 호출 | `VITE_API_BASE_URL` 비움 → 상대 경로 `/api` → Vite proxy | `VITE_API_BASE_URL`에 실제 API 호스트 필수 |
| 프록시 | `vite.config`의 `VITE_DEV_PROXY_TARGET` | 사용 안 함 |
| 비밀 | 서버 `.env`만 | 동일 — 클라이언트에 API 키 금지 |

## 8. 트러블슈팅

- **상단 배너 “서버에 연결할 수 없습니다”**: 백엔드 미기동 또는 `VITE_API_BASE_URL` 오타/차단. 헬스 URL을 브라우저에서 직접 열어 확인.
- **CORS 오류**: `CORS_ORIGINS`에 프론트 정확한 origin 추가(스킴+호스트+포트).
- **상담 503**: 서버에 `OPENAI_API_KEY` 설정.

## 9. 보안 메모

- 저장소에 API 키 커밋 금지.
- `localStorage`는 브라우저별 사용자 기억용 — 민감 정보 저장 금지.
