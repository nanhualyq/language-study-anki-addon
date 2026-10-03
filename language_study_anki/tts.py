"""Line-level TTS via Anki's built-in engine (spec: tts-audio; decision D5).

`TTSTag` + `av_player` drive `aqt.tts.TTSProcessPlayer` (SAPI on Windows),
which handles voice selection and content-hash caching. Playback is async and
non-blocking; a new speak interrupts the current one (spec: Non-blocking
playback during practice).
"""

from __future__ import annotations

import traceback

DEFAULT_LANG = "en_US"


def speak(text: str, lang: str = DEFAULT_LANG) -> None:
    """Speak ``text`` asynchronously; interrupts any current playback."""
    if not text or not text.strip():
        return
    from aqt.sound import av_player
    from aqt.tts import TTSTag

    # Spike-verified signature (Anki 26.8.1):
    # TTSTag(field_text, lang, voices: list, speed: float, other_args: list)
    try:
        tag = TTSTag(text, lang, [], 1.0, [])
    except TypeError:
        tag = TTSTag(text=text, lang=lang)
    # New playback stops the current one (rapid successive clicks).
    try:
        av_player.clear_queue_and_maybe_interrupt()
    except Exception:
        try:
            av_player.stop_and_clear_queue()
        except Exception:
            pass
    av_player.play_tags([tag])


def stop() -> None:
    from aqt.sound import av_player

    try:
        av_player.stop_and_clear_queue()
    except Exception:
        print("language_study_anki: tts stop failed:\n" + traceback.format_exc())
