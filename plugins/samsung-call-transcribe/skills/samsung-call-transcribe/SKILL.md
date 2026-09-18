---
name: samsung-call-transcribe
description: Pull call recordings from a Samsung Galaxy (Android) phone over USB debugging (adb) and transcribe them locally using Whisper (whisper-cli). Use when transcribing phone calls, reviewing discussion contents, or creating meeting notes from call audio.
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

# Samsung Call Recording Transcription (`samsung-call-transcribe`)

Pull call recording audio files (`/sdcard/Recordings/Call/`) from a Samsung Galaxy phone via adb and transcribe them locally using Whisper.

---

## 1. Core Principles & Privacy

- **Read-only access**: Never modify or delete original recording files on the phone.
- **Local temporary workspace**: Always pull files to a temporary directory such as `/tmp/call-transcribe`, never inside the git repository.
- **No media commits**: Do not commit raw audio files (M4A/WAV) or verbatim transcripts to git repositories unless explicitly requested by the user.
- **Summarize and clean up**: Record only key decisions, dates, and action items in persistent project notes, and delete temporary audio files once finished.

---

## 2. Procedure

### (1) Connect device and list recordings

```bash
# 1. Verify device connection
adb devices -l

# 2. List recent call recordings
adb shell ls -l "/sdcard/Recordings/Call/" | tail -n 20

# 3. Filter by date or contact name (e.g. 20260901)
adb shell ls "/sdcard/Recordings/Call/*20260901*"
```

### (2) Copy file to temporary workspace (`adb pull`)

```bash
work_dir="/tmp/call-transcribe"
mkdir -p "$work_dir"

# Copy target recording
adb pull "/sdcard/Recordings/Call/<recording_filename>.m4a" "$work_dir/recording.m4a"
```

### (3) Convert audio and transcribe with Whisper

Set the Whisper ggml model path (defaults to `$HOME/models/whisper/ggml-large-v3-turbo.bin` or configure via `WHISPER_MODEL_PATH`):

```bash
work_dir="/tmp/call-transcribe"
model_path="${WHISPER_MODEL_PATH:-$HOME/models/whisper/ggml-large-v3-turbo.bin}"

# 1. Convert to 16kHz mono PCM WAV
ffmpeg -hide_banner -loglevel error -y \
  -i "$work_dir/recording.m4a" -ar 16000 -ac 1 -c:a pcm_s16le \
  "$work_dir/call.wav"

# 2. Run Whisper transcription (add domain keywords to --prompt if needed)
whisper-cli \
  -m "$model_path" -l ko -otxt -osrt \
  -of "$work_dir/call" \
  --prompt "Meeting, discussion, schedule, estimate" \
  "$work_dir/call.wav"
```

Outputs:
- `$work_dir/call.txt`: Plain text transcript
- `$work_dir/call.srt`: Timestamped subtitle file (useful for verifying unclear sections)

---

## 3. Verification & Cleanup Tips

- Automatic transcription may mishear proper nouns or numbers. For critical or doubtful details, check the timestamp in the `.srt` file.
- Cross-reference with written communications (e.g. messenger chats or emails) following the call.
- Remove temporary large audio files after transcription is completed:
  ```bash
  rm -f "$work_dir/call.wav" "$work_dir/recording.m4a"
  ```
