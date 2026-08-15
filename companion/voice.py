from __future__ import annotations

import asyncio
import tempfile
import wave
from pathlib import Path

import edge_tts
import numpy as np
import pygame
import sounddevice as sd
from groq import Groq


SAMPLE_RATE = 16_000
CHANNELS = 1


class VoicePipeline:
    def __init__(
        self,
        groq_api_key: str,
        stt_model: str = "whisper-large-v3-turbo",
        tts_voice: str = "en-US-AriaNeural",
    ) -> None:
        self.client = Groq(api_key=groq_api_key)
        self.stt_model = stt_model
        self.tts_voice = tts_voice
        self._recording: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._mixer_ready = False

    def _callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:  # noqa: ANN001
        if status:
            print(status)
        self._recording.append(indata.copy())

    def start_recording(self) -> None:
        self._recording = []
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop_recording(self) -> Path | None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._recording:
            return None

        audio = np.concatenate(self._recording, axis=0)
        if audio.size < SAMPLE_RATE * 0.25:
            return None

        pcm = np.clip(audio[:, 0], -1.0, 1.0)
        pcm16 = (pcm * 32767).astype(np.int16)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = Path(temp_file.name)
        temp_file.close()

        with wave.open(str(temp_path), "wb") as handle:
            handle.setnchannels(CHANNELS)
            handle.setsampwidth(2)
            handle.setframerate(SAMPLE_RATE)
            handle.writeframes(pcm16.tobytes())

        return temp_path

    def transcribe(self, wav_path: Path) -> str:
        with wav_path.open("rb") as handle:
            result = self.client.audio.transcriptions.create(
                file=(wav_path.name, handle.read()),
                model=self.stt_model,
                response_format="text",
            )
        wav_path.unlink(missing_ok=True)
        text = str(result).strip()
        if not text:
            raise RuntimeError("No speech detected.")
        return text

    async def _synthesize(self, text: str, output_path: Path) -> None:
        communicate = edge_tts.Communicate(text, self.tts_voice)
        await communicate.save(str(output_path))

    def _ensure_mixer(self) -> None:
        if not self._mixer_ready:
            pygame.mixer.init()
            self._mixer_ready = True

    def speak(self, text: str) -> None:
        if not text.strip():
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            output_path = Path(temp_file.name)

        try:
            asyncio.run(self._synthesize(text, output_path))
            if output_path.stat().st_size == 0:
                raise RuntimeError("Speech synthesis produced an empty file.")

            self._ensure_mixer()
            pygame.mixer.music.load(str(output_path))
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
        finally:
            if self._mixer_ready:
                pygame.mixer.music.unload()
            output_path.unlink(missing_ok=True)
