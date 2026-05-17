# VoiceHealth 课程音频生成规范

本规范用于健康学院核心课、书目课和后续健康教育课程。目标是让课程在网页和微信小程序里听起来像老师讲课，而不是把长文直接机器朗读。

## 四层链路

1. **课程化口播稿**
   - 每节课先生成 150-230 字左右的自然口播稿。
   - 不直接朗读完整正文。
   - 文案保持健康管理参考定位，不写诊断、治疗承诺。

2. **神经 TTS**
   - 默认音色：`zh-CN-YunyangNeural`
   - 默认语速：`-7%`
   - 默认音高：`-2Hz`
   - 可通过环境变量覆盖：
     - `VOICEHEALTH_TTS_VOICE`
     - `VOICEHEALTH_TTS_RATE`
     - `VOICEHEALTH_TTS_PITCH`
     - `VOICEHEALTH_TTS_BITRATE`

3. **ffmpeg 统一后期**
   - 响度：`loudnorm=I=-16:TP=-1.5:LRA=9`
   - 采样率：`24000Hz`
   - 声道：单声道
   - 格式：MP3
   - 码率：`48k`，需要更高音质时可用 `64k`

4. **小程序播放体验**
   - 小程序使用 `wx.createInnerAudioContext()`。
   - 课程卡片支持播放、暂停、加载态、错误提示、进度显示和拖动 seek。
   - 本地课程音频放在 `voiceHealth-miniprogram-v2/miniprogram/audio/courses/`。

## 关键文件

- `data/courses/voicehealth_core_courses.json`：核心课程数据和口播稿。
- `scripts/course_audio_pipeline.py`：通用 TTS + ffmpeg 处理链路。
- `scripts/generate_core_audio_neural.py`：生成核心课音频。
- `scripts/generate_book_audio_neural.py`：生成书目课或扩展课程音频。
- `scripts/enhance_book_courses_deepseek.py`：用 DeepSeek 生成或增强口播稿。
- `scripts/audit_lesson1_benchmark.py`：审计 MP3 规格。
- `voiceHealth-miniprogram-v2/miniprogram/pages/articles/`：健康学院页面和播放器。

## 生成核心课音频

```bash
cd /Users/apple/Desktop/OPC/voiceHealth
source venv/bin/activate
pip install -r requirements.txt

python scripts/generate_core_audio_neural.py --overwrite
```

仅生成指定课程：

```bash
python scripts/generate_core_audio_neural.py --ids vh-01,vh-02 --overwrite
```

使用 64kbps：

```bash
python scripts/generate_core_audio_neural.py --bitrate 64k --overwrite
```

## 一键生成全部可用课程

当 `data/courses/` 下存在多个课程 JSON 时，可直接运行：

```bash
python scripts/generate_all_audio.py
```

脚本会：

- 扫描所有包含 `courses` 数组的课程 JSON。
- 核心课默认输出到 `voiceHealth-miniprogram-v2/miniprogram/audio/courses/`。
- 文件名包含 `book` 的书目课默认输出到 `voiceHealth-miniprogram-v2/miniprogram/audio/books/`。
- 已存在的 MP3 默认跳过，避免重复合成；需要重做时加 `--overwrite`。
- 写入汇总审计：`docs/all-course-audio-audit.json`。

## 用 DeepSeek 增强口播稿

```bash
export DEEPSEEK_API_KEY="..."
python scripts/enhance_book_courses_deepseek.py \
  --input data/courses/voicehealth_core_courses.json \
  --output data/courses/voicehealth_core_courses.json \
  --force
```

没有 `DEEPSEEK_API_KEY` 时，脚本会使用本地保守压缩逻辑，方便离线开发。

## 审计音频

```bash
python scripts/audit_lesson1_benchmark.py \
  --audio-dir voiceHealth-miniprogram-v2/miniprogram/audio/courses \
  --expect-count 12
```

审计输出：

- `docs/course-audio-audit.json`
- 每条音频的时长、采样率、声道、码率和等级。

核心课达到 A 级的基本标准：

- 20-75 秒。
- 24000Hz。
- 单声道。
- MP3 码率不高于 70kbps。
- 文件可被 `ffprobe` 正常解析。

## 网页和小程序接入

网页端可直接使用：

```html
<audio controls>
  <source src="audio/courses/vh-07.mp3" type="audio/mpeg">
</audio>
```

小程序端课程页已内置：

```js
const audio = wx.createInnerAudioContext()
audio.src = '/audio/courses/vh-07.mp3'
audio.play()
```

后续扩展课程时，先补充课程 JSON，再运行生成和审计脚本，最后把 MP3 随小程序包发布。
