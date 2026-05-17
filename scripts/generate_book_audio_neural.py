#!/usr/bin/env python3
"""Generate book/course-series audio using the same VoiceHealth neural TTS profile.

Input JSON should contain a `courses` array. Each item needs:
  - id
  - title
  - spokenScript
"""

from course_audio_pipeline import common_parser, run_core_generation


def main() -> None:
    parser = common_parser("Generate book course MP3 files with the VoiceHealth course audio profile.")
    parser.set_defaults(output_dir="voiceHealth-miniprogram-v2/miniprogram/audio/books")
    args = parser.parse_args()
    run_core_generation(args)


if __name__ == "__main__":
    main()
