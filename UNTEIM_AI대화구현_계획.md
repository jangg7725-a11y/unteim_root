# 운트임 대화형 AI 구현 계획
> 목표: 사용자 자기이해·정서지원을 위한 텍스트 + 음성 대화 AI
> 작성일: 2026-05-11

---

## 현재 상태 vs 목표

```
현재: 사주 분석 → 리포트 출력 (단방향)
목표: 사주 분석 → AI와 텍스트+음성 대화 (양방향)
```

---

## 전체 아키텍처

```
┌─────────────────────────────────────────────────┐
│                  프론트엔드                        │
│  텍스트 입력 ──┐                                   │
│  음성 입력 ───┼──► AI 대화 인터페이스              │
│  음성 출력 ◄──┘                                   │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────▼─────────┐
        │   백엔드 라우터      │
        │  (티어 분기)         │
        └────┬──────────┬───┘
             │          │
    ┌────────▼───┐  ┌───▼──────────────┐
    │  일반 티어   │  │   프리미엄 티어    │
    │ 자체 AI     │  │  GPT-4o / Claude │
    │ (Ollama)   │  │  (API 과금)       │
    └────────────┘  └──────────────────┘
```

---

## 1. 2티어 AI 구조

| 구분 | 일반 티어 | 프리미엄 티어 |
|------|-----------|--------------|
| AI 엔진 | Ollama (자체 서버) | GPT-4o / Claude API |
| STT (음성→텍스트) | Whisper 자체 호스팅 | OpenAI Whisper API |
| TTS (텍스트→음성) | Coqui TTS 자체 호스팅 | OpenAI TTS API |
| 비용 구조 | 서버비 고정 (월 $50~150) | 사용량 과금 ($0.01~0.03/회) |
| 동시 처리 | 서버 스펙에 따라 10~30명 | 무제한 (API 한도 내) |

---

## 2. 자체 AI (일반 티어) — Ollama

### 설치

```bash
# Linux/Mac 서버에 Ollama 설치
curl -fsSL https://ollama.ai/install.sh | sh

# 한국어 지원 모델 선택
ollama pull EEVE-Korean-10.8B    # 한국어 성능 최고 (VRAM 8GB 필요)
ollama pull llama3.1:8b          # 균형형 (VRAM 6GB)
ollama pull mistral              # 가볍고 빠름 (VRAM 5GB)
```

### 모델 비교

| 모델 | VRAM | 한국어 수준 | 응답 속도 |
|------|------|------------|----------|
| EEVE-Korean-10.8B | 8GB | ★★★★★ | 중간 |
| Llama3.1:8b | 6GB | ★★★☆☆ | 빠름 |
| Mistral:7b | 5GB | ★★★☆☆ | 가장 빠름 |

### 백엔드 AI 라우터 (engine/ai_router.py 신규 생성)

```python
# engine/ai_router.py

class AITier:
    STANDARD = "standard"   # Ollama 자체 AI
    PREMIUM  = "premium"    # OpenAI / Claude

def route_ai_request(user_tier: str, messages: list, saju_context: str):
    if user_tier == AITier.PREMIUM:
        return _call_openai(messages, saju_context)
    return _call_ollama(messages, saju_context)

def _call_ollama(messages, saju_context):
    import httpx
    payload = {
        "model": "EEVE-Korean-10.8B",
        "messages": [
            {"role": "system", "content": saju_context},
            *messages
        ],
        "stream": True
    }
    return httpx.post("http://localhost:11434/api/chat", json=payload, timeout=60)

def _call_openai(messages, saju_context):
    # 기존 counsel_service.py 로직 재사용
    ...
```

---

## 3. 음성 구현

### 3-1. STT (음성 → 텍스트)

**옵션 A: Whisper 자체 호스팅 (일반 티어, 무료)**

```python
import whisper
model = whisper.load_model("small")   # 한국어 지원, 경량
result = model.transcribe(audio_file, language="ko")
text = result["text"]
```

**옵션 B: OpenAI Whisper API (프리미엄 티어, $0.006/분)**

```python
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file,
    language="ko"
)
text = transcript.text
```

**옵션 C: 브라우저 Web Speech API (무료, 즉시 사용 가능)**

```typescript
// 설치 불필요 — 브라우저 내장
const recognition = new webkitSpeechRecognition();
recognition.lang = 'ko-KR';
recognition.onresult = (e) => setText(e.results[0][0].transcript);
recognition.start();
```
> ⚠️ Chrome 전용, 오프라인 불가. 프로토타입 단계에 권장.

---

### 3-2. TTS (텍스트 → 음성)

**옵션 A: Coqui TTS (일반 티어, 완전 무료)**

```bash
pip install TTS
```

```python
from TTS.api import TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
tts.tts_to_file(
    text="안녕하세요, 당신의 사주를 살펴볼게요.",
    language="ko",
    file_path="output.wav"
)
```

**옵션 B: OpenAI TTS API (프리미엄 티어, $0.015/1000자)**

```python
response = client.audio.speech.create(
    model="tts-1",
    voice="nova",          # 여성 목소리 (shimmer, alloy 등 선택)
    input="안녕하세요"
)
response.stream_to_file("output.mp3")
```

**옵션 C: 브라우저 Web Speech API (무료, 즉시 사용 가능)**

```typescript
// VoicePlayer.tsx 확장
const utterance = new SpeechSynthesisUtterance(text);
utterance.lang = 'ko-KR';
utterance.rate = 0.95;    // 속도
utterance.pitch = 1.0;    // 음높이
speechSynthesis.speak(utterance);
```

---

## 4. 백엔드 신규 API 엔드포인트

> `scripts/run_api_server_v1.py` 에 추가

```python
from fastapi.responses import StreamingResponse, EventSourceResponse

# ── STT: 음성 → 텍스트 ──────────────────────────────
@app.post("/api/counsel/voice-input")
async def voice_to_text(audio: UploadFile, tier: str = "standard"):
    audio_bytes = await audio.read()
    if tier == "premium":
        text = openai_whisper(audio_bytes)
    else:
        text = local_whisper(audio_bytes)       # 자체 Whisper
    return {"text": text}


# ── TTS: 텍스트 → 음성 ──────────────────────────────
@app.post("/api/counsel/voice-output")
async def text_to_voice(req: TTSRequest):
    if req.tier == "premium":
        audio = openai_tts(req.text)
    else:
        audio = coqui_tts(req.text)             # 자체 Coqui
    return StreamingResponse(audio, media_type="audio/wav")


# ── 스트리밍 AI 응답 (텍스트) ─────────────────────────
@app.post("/api/counsel/stream")
async def counsel_stream(req: CounselRequest):
    saju_context = build_saju_context(req.birth_str, req.profile)

    async def generate():
        async for chunk in ai_router.stream(req.tier, req.messages, saju_context):
            yield f"data: {chunk}\n\n"

    return EventSourceResponse(generate())
```

---

## 5. 프론트엔드 대화 UI

> `frontend/src/counsel/CounselCorner.tsx` 확장

```typescript
interface ConversationState {
  isRecording: boolean;    // 마이크 녹음 중
  isSpeaking: boolean;     // AI 음성 출력 중
  isStreaming: boolean;    // AI 텍스트 스트리밍 중
  tier: 'standard' | 'premium';
}

// 전체 음성 대화 흐름
const handleVoiceInput = async () => {
  setIsRecording(true);
  const audioBlob = await recordMicrophone();      // 1. 마이크 녹음
  setIsRecording(false);

  const { text } = await sttAPI(audioBlob);        // 2. STT 변환
  addMessage({ role: 'user', text });

  setIsStreaming(true);
  const response = await streamAI(text);           // 3. AI 스트리밍
  setIsStreaming(false);

  setIsSpeaking(true);
  await ttsPlay(response);                         // 4. 음성 출력
  setIsSpeaking(false);
};

// SSE 스트리밍 수신
const streamAI = async (userText: string) => {
  const es = new EventSource('/api/counsel/stream');
  let fullText = '';
  es.onmessage = (e) => {
    fullText += e.data;
    setStreamingText(fullText);    // 실시간 타이핑 효과
  };
  return fullText;
};
```

---

## 6. 서버 인프라

### 권장 GPU 서버 (자체 AI 운영용)

| 서비스 | 스펙 | 예상 비용 | 특징 |
|--------|------|----------|------|
| RunPod | RTX 3090 24GB | $0.4/시간 | 유연한 온/오프 |
| Vast.ai | RTX 4090 24GB | $0.3/시간 | 저렴 |
| AWS g4dn.xlarge | T4 16GB | $0.5/시간 | 안정적 |
| 국내 IDC | A10 24GB | 월 $100~200 | 고정비, 안정 |

> **추천**: 초기에는 RunPod 온디맨드로 테스트 → 사용자 증가 후 월 고정 서버로 전환

### 구성도

```
[GPU 서버]
  ├── Ollama (LLM)        : 포트 11434
  ├── Whisper (STT)       : FastAPI 내장
  ├── Coqui TTS           : FastAPI 내장
  └── 운트임 백엔드 API    : 포트 8000

[일반 CDN/웹서버]
  └── 프론트엔드 (React)
```

---

## 7. 구현 로드맵

```
[ Week 1 ] 프로토타입 — 브라우저 내장 음성 (비용 0)
  ✔ Web Speech API로 STT/TTS 연결
  ✔ 기존 counsel_service.py 스트리밍 전환
  ✔ CounselCorner.tsx 대화 UI 업그레이드

[ Week 2~3 ] 백엔드 AI 라우터 구축
  ✔ engine/ai_router.py 작성
  ✔ Ollama 로컬 연동 테스트
  ✔ /api/counsel/stream 엔드포인트 추가

[ Week 4 ] 스트리밍 UI 완성
  ✔ SSE EventSource 연결
  ✔ 실시간 타이핑 효과
  ✔ 음성 재생 상태 UI

[ Week 5~6 ] 자체 음성 서버 구축
  ✔ Whisper 자체 STT 서버
  ✔ Coqui TTS 서버
  ✔ GPU 서버 배포

[ Week 7+ ] 티어 분리 + 결제 연동
  ✔ 일반/프리미엄 분기 로직
  ✔ 결제 시스템 연동 (Stripe 등)
  ✔ 사용량 트래킹
```

---

## 8. 우선순위 결정 기준

| 빠른 시작 원한다면 | 품질 원한다면 |
|--------------------|--------------|
| Web Speech API (즉시) | Whisper + Coqui TTS |
| OpenAI API 그대로 유지 | EEVE-Korean Ollama |
| 기존 CounselCorner 확장 | 신규 VoiceChat 컴포넌트 설계 |

---

## 관련 현재 파일

| 파일 | 역할 | 확장 방향 |
|------|------|-----------|
| `engine/counsel_service.py` | AI 상담 서비스 | AI 라우터 분기 추가 |
| `engine/counsel_intent.py` | 의도 분류 | 음성 의도 분류 추가 |
| `scripts/run_api_server_v1.py` | API 서버 | STT/TTS/스트림 엔드포인트 추가 |
| `frontend/src/counsel/CounselCorner.tsx` | 상담 UI | 음성 대화 UI 확장 |
| `frontend/src/components/counsel/VoicePlayer.tsx` | 음성 재생 | TTS 연동 확장 |

---

*이 문서는 구현 착수 전 검토용입니다. 단계별로 우선순위를 정해 진행하세요.*
