---
name: samsung-call-transcribe
description: 삼성 갤럭시(Android) 휴대폰에 녹음된 통화 녹음 파일을 USB 디버깅(adb)으로 가져와 Whisper(whisper-cli)로 텍스트로 자동 전사할 때 사용한다. 통화 내용 확인, 미팅/상담 요약이 필요할 때 호출한다.
version: 1.0.0
requires:
  binaries:
    - adb
    - ffmpeg
    - whisper-cli
tags:
  - audio
  - transcription
  - whisper
  - samsung
  - android
---

# 삼성 통화 녹음 전사 가이드 (`samsung-call-transcribe`)

삼성 갤럭시 휴대폰의 통화 녹음 파일(`/sdcard/Recordings/Call/`)을 adb로 가져와 Whisper로 로컬 전사하는 스킬입니다.

---

## 1. 기본 원칙 및 보안

- **읽기 전용 접근**: 휴대폰 내 원본 녹음 파일은 절대 수정하거나 삭제하지 않습니다.
- **로컬 임시 작업**: 파일은 Git 리포가 아닌 `/tmp` 디렉토리(예: `/tmp/call-transcribe`)로 pull하여 작업합니다.
- **저장소 커밋 금지**: 사용자가 명시적으로 원본 보관을 요청하지 않는 한, 음성 파일(M4A/WAV) 및 전체 전사 원문은 저장소에 커밋하지 않습니다.
- **문서 요약 후 정리**: 문서에는 관련 결정·일정·후속 조치만 요약하여 기록하고, 작업이 끝나면 임시 녹음 및 WAV 파일은 삭제합니다.

---

## 2. 작업 절차

### (1) 휴대폰 연결 및 녹음 파일 조회

```bash
# 1. 기기 연결 확인
adb devices -l

# 2. 최근 통화 녹음 목록 확인
adb shell ls -l "/sdcard/Recordings/Call/" | tail -n 20

# 3. 특정 날짜 또는 상대방 검색 (예: 20260901)
adb shell ls "/sdcard/Recordings/Call/*20260901*"
```

### (2) 임시 폴더로 파일 복사 (`adb pull`)

```bash
work_dir="/tmp/call-transcribe"
mkdir -p "$work_dir"

# 대상 파일 복사
adb pull "/sdcard/Recordings/Call/<녹음파일명>.m4a" "$work_dir/recording.m4a"
```

### (3) 오디오 변환 및 Whisper 전사

Whisper 모델은 **`/Users/al03230673/models/whisper/ggml-large-v3-turbo.bin`**을 우선 사용합니다.

```bash
work_dir="/tmp/call-transcribe"
model_path="/Users/al03230673/models/whisper/ggml-large-v3-turbo.bin"

# 1. 16kHz 모노 PCM WAV로 변환
ffmpeg -hide_banner -loglevel error -y \
  -i "$work_dir/recording.m4a" -ar 16000 -ac 1 -c:a pcm_s16le \
  "$work_dir/call.wav"

# 2. Whisper 전사 실행 (도메인 특화 키워드를 --prompt에 추가)
whisper-cli \
  -m "$model_path" -l ko -otxt -osrt \
  -of "$work_dir/call" \
  --prompt "인테리어, 시공, 견적, 일정, 학원, 상담" \
  "$work_dir/call.wav"
```

결과물:
- `$work_dir/call.txt`: 전체 텍스트 전사본
- `$work_dir/call.srt`: 타임스탬프가 포함된 자막 파일 (불명확한 구간 확인용)

---

## 3. 요약 및 검증 팁

- 자동 전사는 불명확한 고유명사나 숫자가 오인될 수 있으므로, 의심스러운 부분은 `.srt` 파일의 타임스탬프를 확인합니다.
- 통화 후 메신저(카카오톡 등)로 교환된 서면 내용이 있다면 교차 검증합니다.
- 작업 완료 후 불필요한 대용량 음성 파일은 정리합니다: `rm -f "$work_dir/call.wav" "$work_dir/recording.m4a"`
