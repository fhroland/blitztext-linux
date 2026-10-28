"""Exercise the installed decoder, including faster-whisper/PyAV compatibility."""
import io
import wave

import pytest


def test_installed_decoder_reads_pcm_wav():
    pytest.importorskip("av")
    audio = pytest.importorskip("faster_whisper.audio")
    wav_data = io.BytesIO()
    with wave.open(wav_data, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x10" * 1600)
    wav_data.seek(0)
    samples = audio.decode_audio(wav_data)
    assert samples.shape == (1600,)
    assert float(samples.mean()) == pytest.approx(0.125)
