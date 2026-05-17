#!/usr/bin/env python3
"""Generate core VoiceHealth course audio for the WeChat mini program."""

from course_audio_pipeline import common_parser, run_core_generation


def main() -> None:
    parser = common_parser(
        "Generate VoiceHealth core lesson MP3 files with YunyangNeural, slow rate, low pitch, and ffmpeg loudness normalization."
    )
    args = parser.parse_args()
    run_core_generation(args)


if __name__ == "__main__":
    main()
