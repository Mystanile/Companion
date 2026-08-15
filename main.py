from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

import keyboard
import yaml
from dotenv import load_dotenv
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from companion.agent import CompanionAgent
from companion.app_paths import app_root
from companion.overlay import OverlayWindow
from companion.tools import set_allowed_roots
from companion.voice import VoicePipeline


def resolve_config_path() -> Path:
    root = app_root()
    external = root / "config.yaml"
    if external.exists():
        return external
    if getattr(sys, "frozen", False):
        bundled = Path(sys._MEIPASS) / "config.yaml"
        if bundled.exists():
            return bundled
    return root / "config.yaml"


def load_env() -> None:
    load_dotenv(app_root() / ".env")


def tray_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(99, 102, 241))
    painter.setPen(QColor(255, 255, 255, 180))
    painter.drawEllipse(8, 8, 48, 48)
    painter.end()
    return QIcon(pixmap)


class CompanionController(QObject):
    state_changed = pyqtSignal(str, str)
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        voice: VoicePipeline,
        agent: CompanionAgent,
    ) -> None:
        super().__init__()
        self.voice = voice
        self.agent = agent
        self._busy = False

    def start_listening(self) -> None:
        if self._busy:
            return
        self._busy = True
        self.state_changed.emit("listening", "Release key when done")
        self.voice.start_recording()

    def stop_and_process(self) -> None:
        if not self._busy:
            return

        wav_path = self.voice.stop_recording()
        if wav_path is None:
            self._busy = False
            self.state_changed.emit("error", "Didn't catch any speech.")
            self.failed.emit("Didn't catch any speech.")
            return

        threading.Thread(target=self._process, args=(wav_path,), daemon=True).start()

    def _process(self, wav_path: Path) -> None:
        try:
            self.state_changed.emit("thinking", "Transcribing…")
            transcript = self.voice.transcribe(wav_path)
            self.state_changed.emit("thinking", transcript)
            reply = self.agent.handle(transcript)
            self.state_changed.emit("speaking", reply)
            self.voice.speak(reply)
            self.finished.emit(reply)
        except Exception as exc:  # noqa: BLE001
            message = str(exc) or "Unknown error"
            self.failed.emit(message)
        finally:
            self._busy = False


def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def main() -> int:
    load_env()
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        app = QApplication(sys.argv)
        env_path = app_root() / ".env"
        QMessageBox.critical(
            None,
            "Companion",
            f"Missing GROQ_API_KEY.\n\nAdd your key to:\n{env_path}",
        )
        return 1

    config = load_config(resolve_config_path())

    hotkey = config.get("hotkey", "`")
    overlay_cfg = config.get("overlay", {})
    voice_cfg = config.get("voice", {})
    path_cfg = config.get("paths", {})

    set_allowed_roots(path_cfg.get("allowed_roots", ["~"]))

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Companion")

    overlay = OverlayWindow(
        size=int(overlay_cfg.get("size", 72)),
        orb_size=int(overlay_cfg.get("orb_size", 56)),
        left_margin=int(overlay_cfg.get("left_margin", 28)),
        bottom_margin=int(overlay_cfg.get("bottom_margin", 28)),
    )
    overlay.set_state("idle")

    voice = VoicePipeline(
        groq_api_key=api_key,
        stt_model=voice_cfg.get("stt_model", "whisper-large-v3-turbo"),
        tts_voice=voice_cfg.get("tts_voice", "en-US-AriaNeural"),
    )
    agent = CompanionAgent(
        groq_api_key=api_key,
        model=voice_cfg.get("llm_model", "llama-3.3-70b-versatile"),
    )
    controller = CompanionController(voice, agent)

    tray = QSystemTrayIcon(tray_icon(), app)
    menu = QMenu()
    quit_action = QAction("Quit Companion")
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)
    tray.setContextMenu(menu)
    tray.setToolTip(f"Companion — hold [{hotkey}] to talk")
    tray.show()

    def on_state(state: str, detail: str) -> None:
        overlay.set_state(state, detail)

    def on_finished(_: str) -> None:
        overlay.set_state("idle")

    def on_failed(_message: str) -> None:
        overlay.set_state("error")
        QTimer.singleShot(2500, lambda: overlay.set_state("idle"))

    controller.state_changed.connect(on_state)
    controller.finished.connect(on_finished)
    controller.failed.connect(on_failed)

    holding = {"active": False}

    def on_press(_event) -> None:  # noqa: ANN001
        if holding["active"]:
            return
        holding["active"] = True
        controller.start_listening()

    def on_release(_event) -> None:  # noqa: ANN001
        if not holding["active"]:
            return
        holding["active"] = False
        controller.stop_and_process()

    keyboard.on_press_key(hotkey, on_press, suppress=False)
    keyboard.on_release_key(hotkey, on_release, suppress=False)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
