from __future__ import annotations

import re
from html import escape
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QEvent, QObject, Qt, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import (
    QAction,
    QColor,
    QDesktopServices,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSystemTrayIcon,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services.desktop_settings import (
    DESKTOP_VERSION,
    PROJECT_DIR,
    SETTINGS_PATH as DESKTOP_CONFIG_PATH,
    load_desktop_settings,
    save_desktop_settings,
)
from services.api_client import ApiClient
from services.diagnostics import build_diagnostic_report
from ui.hud_core import HudCore
from ui.panels import HudPanel, LocalPanel, SecurityPanel, SystemPanel, ToolsPanel
from ui.theme import ARVIS_STYLE


STORAGE_DIR = PROJECT_DIR / "backend" / "storage"


class ApiWorker(QObject):
    finished = Signal(str, object)

    def __init__(self, kind: str, func: Callable[..., dict[str, Any]], *args, **kwargs):
        super().__init__()
        self.kind = kind
        self.func = func
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self) -> None:
        try:
            result = self.func(*self.args, **self.kwargs)
        except Exception as error:
            result = {"ok": False, "data": {}, "error": str(error)}
        self.finished.emit(self.kind, result)


class ChatInput(QTextEdit):
    submitted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ChatInput")
        self.setAcceptRichText(False)
        self.setPlaceholderText("Escribi una orden... Ej: info del sistema")

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)
                return
            self.submitted.emit()
            return
        super().keyPressEvent(event)

    def text_value(self) -> str:
        return self.toPlainText().strip()


class SettingsDialog(QDialog):
    def __init__(self, parent=None, animations_enabled: bool = True, settings=None):
        super().__init__(parent)

        self.setWindowTitle("Configuracion de ARVIS")
        self.setMinimumWidth(480)
        self.settings = settings or {}

        layout = QFormLayout(self)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Facil", "Avanzado"])

        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["Configurable", "Masculina", "Femenina", "Sistema"])

        self.backend_url_input = QLineEdit(
            self.settings.get("backend_base_url", "http://127.0.0.1:8000")
        )

        self.timeout_input = QLineEdit(str(self.settings.get("request_timeout_seconds", 5)))
        self.refresh_input = QLineEdit(
            str(self.settings.get("auto_refresh_interval_seconds", 15))
        )

        self.animations_check = QCheckBox("Activar animaciones")
        self.animations_check.setChecked(animations_enabled)

        self.auto_refresh_check = QCheckBox("Actualizar estados automaticamente")
        self.auto_refresh_check.setChecked(
            bool(self.settings.get("auto_refresh_status", True))
        )

        self.compact_check = QCheckBox("Iniciar en modo compacto")
        self.compact_check.setChecked(bool(self.settings.get("compact_mode_enabled", False)))

        self.top_check = QCheckBox("Siempre visible")
        self.top_check.setChecked(bool(self.settings.get("always_on_top", False)))

        self.tray_check = QCheckBox("Minimizar a bandeja")
        self.tray_check.setChecked(bool(self.settings.get("minimize_to_tray", True)))

        self.ui_mode_combo = QComboBox()
        self.ui_mode_combo.addItems(["easy", "advanced"])
        self.ui_mode_combo.setCurrentText(self.settings.get("ui_mode", "easy"))

        layout.addRow("Modo:", self.mode_combo)
        layout.addRow("Voz:", self.voice_combo)
        layout.addRow("Backend URL:", self.backend_url_input)
        layout.addRow("Timeout HTTP:", self.timeout_input)
        layout.addRow("Intervalo estado:", self.refresh_input)
        layout.addRow("Animaciones:", self.animations_check)
        layout.addRow("Auto refresh:", self.auto_refresh_check)
        layout.addRow("Compacto:", self.compact_check)
        layout.addRow("Siempre visible:", self.top_check)
        layout.addRow("Bandeja:", self.tray_check)
        layout.addRow("UI mode:", self.ui_mode_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def desktop_settings(self) -> dict[str, Any]:
        return {
            "backend_base_url": self.backend_url_input.text().strip(),
            "request_timeout_seconds": _safe_int(self.timeout_input.text(), 5),
            "auto_refresh_status": self.auto_refresh_check.isChecked(),
            "auto_refresh_interval_seconds": _safe_int(self.refresh_input.text(), 15),
            "compact_mode_enabled": self.compact_check.isChecked(),
            "always_on_top": self.top_check.isChecked(),
            "minimize_to_tray": self.tray_check.isChecked(),
            "ui_mode": self.ui_mode_combo.currentText(),
        }


class DiagnosticsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        self.setWindowTitle("Configuracion y diagnostico")
        self.setMinimumSize(780, 620)

        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.action_buttons: list[QPushButton] = []
        root.addWidget(self.tabs, stretch=1)

        self.summary_view = self._read_only_text()
        self.tabs.addTab(self._tab_with_buttons(self.summary_view, [
            ("Actualizar", self.window.refresh_status),
            ("Cargar completo", self.window.refresh_full_diagnostics),
            ("Copiar diagnostico", self.window.copy_diagnostic_report),
            ("Copiar estado backend", self.window.copy_backend_status),
        ]), "Resumen")

        self._build_desktop_tab()
        self._build_backend_settings_tab()
        self._build_ai_tab()
        self._build_voice_tab()
        self._build_mic_tab()
        self._build_pending_tab()
        self._build_paths_tab()
        self._build_logs_tab()

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.refresh_from_window()

    def _build_desktop_tab(self) -> None:
        widget = QWidget()
        layout = QFormLayout(widget)

        self.desktop_backend_url = QLineEdit()
        self.desktop_timeout = QSpinBox()
        self.desktop_timeout.setRange(1, 60)
        self.desktop_auto_refresh = QCheckBox("Actualizar automaticamente")
        self.desktop_refresh_interval = QSpinBox()
        self.desktop_refresh_interval.setRange(3, 300)
        self.desktop_ui_mode = QComboBox()
        self.desktop_ui_mode.addItems(["easy", "advanced"])
        self.desktop_compact = QCheckBox("Modo compacto")
        self.desktop_top = QCheckBox("Siempre visible")
        self.desktop_tray = QCheckBox("Minimizar a bandeja")

        save_btn = QPushButton("Guardar configuracion desktop")
        save_btn.clicked.connect(lambda: self.window.save_desktop_settings_from_dialog(self))

        layout.addRow("Backend URL:", self.desktop_backend_url)
        layout.addRow("Timeout:", self.desktop_timeout)
        layout.addRow("Auto refresh:", self.desktop_auto_refresh)
        layout.addRow("Intervalo:", self.desktop_refresh_interval)
        layout.addRow("UI mode:", self.desktop_ui_mode)
        layout.addRow("Compacto:", self.desktop_compact)
        layout.addRow("Siempre visible:", self.desktop_top)
        layout.addRow("Bandeja:", self.desktop_tray)
        layout.addRow(save_btn)

        self.tabs.addTab(widget, "Desktop")

    def _build_backend_settings_tab(self) -> None:
        widget = QWidget()
        layout = QFormLayout(widget)

        self.backend_ollama_enabled = QCheckBox("Ollama activo")
        self.backend_ollama_model = QLineEdit()
        self.backend_ollama_timeout = QSpinBox()
        self.backend_ollama_timeout.setRange(1, 300)
        self.backend_history_enabled = QCheckBox("Historial conversacional")
        self.backend_history_limit = QSpinBox()
        self.backend_history_limit.setRange(1, 50)
        self.backend_voice_enabled = QCheckBox("Voz activa")
        self.backend_stt_enabled = QCheckBox("STT activo")
        self.backend_tts_enabled = QCheckBox("TTS activo")
        self.backend_mic_enabled = QCheckBox("Microfono activo")
        self.backend_mic_default = QSpinBox()
        self.backend_mic_default.setRange(1, 60)
        self.backend_pending_expiration = QSpinBox()
        self.backend_pending_expiration.setRange(1, 240)

        save_btn = QPushButton("Guardar settings backend")
        save_btn.clicked.connect(lambda: self.window.save_backend_settings_from_dialog(self))

        layout.addRow("IA local:", self.backend_ollama_enabled)
        layout.addRow("Modelo Ollama:", self.backend_ollama_model)
        layout.addRow("Timeout Ollama:", self.backend_ollama_timeout)
        layout.addRow("Historial:", self.backend_history_enabled)
        layout.addRow("Limite historial:", self.backend_history_limit)
        layout.addRow("Voz:", self.backend_voice_enabled)
        layout.addRow("STT:", self.backend_stt_enabled)
        layout.addRow("TTS:", self.backend_tts_enabled)
        layout.addRow("Mic:", self.backend_mic_enabled)
        layout.addRow("Duracion mic:", self.backend_mic_default)
        layout.addRow("Expiracion pendientes:", self.backend_pending_expiration)
        layout.addRow(save_btn)

        self.tabs.addTab(widget, "Backend settings")

    def _build_ai_tab(self) -> None:
        self.ai_view = self._read_only_text()
        self.tabs.addTab(self._tab_with_buttons(self.ai_view, [
            ("Actualizar modelos", self.window.request_ai_models_for_dialog),
            ("Cambiar modelo", lambda: self.window.set_ai_model_from_dialog(self)),
        ]), "IA local")

    def _build_voice_tab(self) -> None:
        self.voice_view = self._read_only_text()
        self.tabs.addTab(self._tab_with_buttons(self.voice_view, [
            ("Estado voz", self.window.refresh_voice_status),
            ("Probar TTS", self.window.test_tts_from_dialog),
        ]), "Voz")

    def _build_mic_tab(self) -> None:
        self.mic_view = self._read_only_text()
        self.tabs.addTab(self._tab_with_buttons(self.mic_view, [
            ("Estado microfono", self.window.refresh_mic_status),
            ("Listar dispositivos", self.window.request_mic_devices_for_dialog),
        ]), "Microfono")

    def _build_pending_tab(self) -> None:
        self.pending_view = self._read_only_text()
        self.tabs.addTab(self._tab_with_buttons(self.pending_view, [
            ("Ver pendientes", self.window.refresh_pending_actions),
            ("Confirmar seleccionado", self.window.confirm_selected_action),
            ("Cancelar seleccionado", self.window.cancel_selected_action),
        ]), "Pendientes")

    def _build_paths_tab(self) -> None:
        self.paths_view = self._read_only_text()
        self.tabs.addTab(self._tab_with_buttons(self.paths_view, [
            ("Abrir proyecto", self.window.open_project_folder),
            ("Abrir storage", self.window.open_storage_folder),
        ]), "Rutas")

    def _build_logs_tab(self) -> None:
        self.logs_view = self._read_only_text()
        self.tabs.addTab(self._tab_with_buttons(self.logs_view, [
            ("Copiar diagnostico", self.window.copy_diagnostic_report),
            ("Limpiar logs visuales", self.window.clear_visual_logs),
        ]), "Logs")

    def _tab_with_buttons(self, view: QTextEdit, buttons: list[tuple[str, Callable]]) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(view, stretch=1)
        row = QHBoxLayout()
        row.addStretch()
        for text, callback in buttons:
            button = QPushButton(text)
            button.clicked.connect(callback)
            self.action_buttons.append(button)
            row.addWidget(button)
        layout.addLayout(row)
        return widget

    def _read_only_text(self) -> QTextEdit:
        view = QTextEdit()
        view.setReadOnly(True)
        view.setMinimumHeight(180)
        return view

    def refresh_from_window(self) -> None:
        self._load_desktop_fields()
        self._load_backend_fields()
        self.summary_view.setPlainText(self.window.build_diagnostic_report_text())
        self.ai_view.setPlainText(self.window.build_ai_diagnostic_text())
        self.voice_view.setPlainText(self.window.build_voice_diagnostic_text())
        self.mic_view.setPlainText(self.window.build_mic_diagnostic_text())
        self.pending_view.setPlainText(self.window.build_pending_diagnostic_text())
        self.paths_view.setPlainText(self.window.build_paths_diagnostic_text())
        self.logs_view.setPlainText(self.window.build_logs_diagnostic_text())

    def _load_desktop_fields(self) -> None:
        settings = self.window.desktop_settings
        self.desktop_backend_url.setText(str(settings.get("backend_base_url", "")))
        self.desktop_timeout.setValue(int(settings.get("request_timeout_seconds", 5)))
        self.desktop_auto_refresh.setChecked(bool(settings.get("auto_refresh_status", True)))
        self.desktop_refresh_interval.setValue(
            int(settings.get("auto_refresh_interval_seconds", 15))
        )
        self.desktop_ui_mode.setCurrentText(str(settings.get("ui_mode", "easy")))
        self.desktop_compact.setChecked(bool(settings.get("compact_mode_enabled", False)))
        self.desktop_top.setChecked(bool(settings.get("always_on_top", False)))
        self.desktop_tray.setChecked(bool(settings.get("minimize_to_tray", True)))

    def _load_backend_fields(self) -> None:
        settings = self.window.last_backend_settings or {}
        self.backend_ollama_enabled.setChecked(bool(settings.get("ollama_enabled", False)))
        self.backend_ollama_model.setText(str(settings.get("ollama_model", "")))
        self.backend_ollama_timeout.setValue(int(settings.get("ollama_timeout_seconds", 30)))
        self.backend_history_enabled.setChecked(
            bool(settings.get("conversation_history_enabled", False))
        )
        self.backend_history_limit.setValue(
            int(settings.get("conversation_history_limit", 6))
        )
        self.backend_voice_enabled.setChecked(bool(settings.get("voice_enabled", False)))
        self.backend_stt_enabled.setChecked(bool(settings.get("stt_enabled", False)))
        self.backend_tts_enabled.setChecked(bool(settings.get("tts_enabled", False)))
        self.backend_mic_enabled.setChecked(bool(settings.get("mic_enabled", False)))
        self.backend_mic_default.setValue(int(settings.get("mic_default_record_seconds", 5)))
        self.backend_pending_expiration.setValue(
            int(settings.get("pending_action_expiration_minutes", 10))
        )

    def desktop_payload(self) -> dict[str, Any]:
        return {
            "backend_base_url": self.desktop_backend_url.text().strip(),
            "request_timeout_seconds": self.desktop_timeout.value(),
            "auto_refresh_status": self.desktop_auto_refresh.isChecked(),
            "auto_refresh_interval_seconds": self.desktop_refresh_interval.value(),
            "ui_mode": self.desktop_ui_mode.currentText(),
            "compact_mode_enabled": self.desktop_compact.isChecked(),
            "always_on_top": self.desktop_top.isChecked(),
            "minimize_to_tray": self.desktop_tray.isChecked(),
        }

    def backend_payload(self) -> dict[str, Any]:
        return {
            "ollama_enabled": self.backend_ollama_enabled.isChecked(),
            "ollama_model": self.backend_ollama_model.text().strip() or "llama3.2",
            "ollama_timeout_seconds": self.backend_ollama_timeout.value(),
            "conversation_history_enabled": self.backend_history_enabled.isChecked(),
            "conversation_history_limit": self.backend_history_limit.value(),
            "voice_enabled": self.backend_voice_enabled.isChecked(),
            "stt_enabled": self.backend_stt_enabled.isChecked(),
            "tts_enabled": self.backend_tts_enabled.isChecked(),
            "mic_enabled": self.backend_mic_enabled.isChecked(),
            "mic_default_record_seconds": self.backend_mic_default.value(),
            "pending_action_expiration_minutes": self.backend_pending_expiration.value(),
        }

    def set_loading(self, loading: bool) -> None:
        for button in self.action_buttons:
            button.setEnabled(not loading)


class ArvisWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.desktop_settings = load_desktop_settings()
        self.api = ApiClient(
            self.desktop_settings["backend_base_url"],
            self.desktop_settings["request_timeout_seconds"],
        )

        self.setWindowTitle(f"ARVIS - Centro de comando v{DESKTOP_VERSION}")
        self.setMinimumSize(980, 640)
        self.setStyleSheet(ARVIS_STYLE)

        self.animations_enabled = True
        self.backend_online = False
        self.compact_mode = bool(self.desktop_settings.get("compact_mode_enabled", False))
        self.always_on_top = bool(self.desktop_settings.get("always_on_top", False))
        self.minimize_to_tray = bool(self.desktop_settings.get("minimize_to_tray", True))
        self.ui_mode = self.desktop_settings.get("ui_mode", "easy")
        self._force_exit = False
        self._normal_geometry = None
        self._last_backend_online: bool | None = None
        self.last_response_text = ""
        self.last_error: str | None = None
        self.last_health: dict[str, Any] = {}
        self.last_backend_settings: dict[str, Any] = {}
        self.last_ai_status: dict[str, Any] = {}
        self.last_voice_status: dict[str, Any] = {}
        self.last_mic_status: dict[str, Any] = {}
        self.last_pending_actions: list[dict[str, Any]] = []
        self.diagnostics_dialog: DiagnosticsDialog | None = None
        self._log_entries: list[str] = []
        self._workers: list[tuple[QThread, ApiWorker]] = []
        self._active_api_kinds: set[str] = set()
        self._refresh_in_progress = False
        self._pending_actions_by_id: dict[int, dict[str, Any]] = {}

        self._build_ui()
        self._setup_tray()
        self._setup_timer()
        self.set_always_on_top(self.always_on_top, persist=False)
        self.apply_ui_mode(self.ui_mode, persist=False)
        if self.compact_mode:
            QTimer.singleShot(0, lambda: self.set_compact_mode(True, persist=False))

        QTimer.singleShot(250, self.refresh_status)
        QTimer.singleShot(450, lambda: self.add_chat("ARVIS", "ARVIS en linea."))

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)

        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title = QLabel("ARVIS")
        title.setObjectName("TitleLabel")

        subtitle = QLabel(f"Centro operativo inteligente - Desktop v{DESKTOP_VERSION}")
        subtitle.setObjectName("SubTitleLabel")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.backend_status = QLabel("Backend: verificando")
        self.backend_status.setObjectName("StatusYellow")

        self.ai_status = QLabel("IA LOCAL: verificando")
        self.ai_status.setObjectName("StatusYellow")

        self.mic_status = QLabel("MIC: verificando")
        self.mic_status.setObjectName("StatusYellow")

        header.addLayout(title_box)
        header.addStretch()
        header.addWidget(self.backend_status)
        header.addSpacing(18)
        header.addWidget(self.ai_status)
        header.addSpacing(18)
        header.addWidget(self.mic_status)
        main_layout.addLayout(header)

        body_container = QWidget()
        body_container.setObjectName("BodyContainer")
        body = QHBoxLayout(body_container)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(16)

        self.left_widget = QWidget()
        left_col = QVBoxLayout(self.left_widget)
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(14)

        self.system_panel = SystemPanel()
        self.local_panel = LocalPanel()
        self.backend_panel = self._build_backend_panel()
        self.log_panel = self._build_log_panel()

        left_col.addWidget(self.system_panel)
        left_col.addWidget(self.local_panel)
        left_col.addWidget(self.backend_panel)
        left_col.addWidget(self.log_panel, stretch=1)

        self.center_widget = QWidget()
        center_col = QVBoxLayout(self.center_widget)
        center_col.setContentsMargins(0, 0, 0, 0)
        center_col.setSpacing(12)

        self.hud = HudCore()
        center_col.addWidget(self.hud, stretch=1)

        self.status_text = QLabel("Esperando orden...")
        self.status_text.setAlignment(Qt.AlignCenter)
        self.status_text.setObjectName("SubTitleLabel")
        center_col.addWidget(self.status_text)

        self.compact_bar = self._build_compact_bar()
        center_col.addWidget(self.compact_bar)
        self.compact_bar.setVisible(False)

        self.chat_panel = self._build_chat_panel()
        center_col.addWidget(self.chat_panel, stretch=0)

        self.right_widget = QWidget()
        right_col = QVBoxLayout(self.right_widget)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(14)

        self.tools_panel = ToolsPanel()
        self.status_panel = self._build_status_panel()
        self.pending_panel = self._build_pending_panel()
        self.ai_panel = self._build_ai_panel()
        self.voice_panel = self._build_voice_panel()
        self.security_panel = SecurityPanel()

        right_col.addWidget(self.tools_panel)
        right_col.addWidget(self.status_panel)
        right_col.addWidget(self.pending_panel)
        right_col.addWidget(self.ai_panel)
        right_col.addWidget(self.voice_panel)
        right_col.addWidget(self.security_panel)
        right_col.addStretch()

        body.addWidget(self.left_widget, stretch=1)
        body.addWidget(self.center_widget, stretch=3)
        body.addWidget(self.right_widget, stretch=1)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(body_container)
        main_layout.addWidget(scroll_area, stretch=1)

        footer = self._build_footer()
        main_layout.addLayout(footer)

    def _build_compact_bar(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("ChatPanel")

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        self.compact_status_label = QLabel("ARVIS compacto")
        self.compact_status_label.setObjectName("PanelTitle")

        normal_btn = QPushButton("Normal")
        normal_btn.clicked.connect(lambda: self.set_compact_mode(False))

        top_btn = QPushButton("Siempre visible")
        top_btn.clicked.connect(self.toggle_always_on_top)

        tray_btn = QPushButton("Bandeja")
        tray_btn.clicked.connect(self.minimize_to_system_tray)

        layout.addWidget(self.compact_status_label, stretch=1)
        layout.addWidget(normal_btn)
        layout.addWidget(top_btn)
        layout.addWidget(tray_btn)
        return panel

    def _build_backend_panel(self) -> HudPanel:
        panel = HudPanel("BACKEND")
        self.backend_url_label = panel.add_line(f"URL: {self.api.base_url}")
        self.backend_version_label = panel.add_line("Version: --")
        self.backend_message_label = panel.add_line("Estado: verificando...", "StatusYellow")

        retry_btn = QPushButton("Reintentar conexion")
        retry_btn.clicked.connect(self.refresh_status)

        swagger_btn = QPushButton("Abrir Swagger")
        swagger_btn.clicked.connect(self.open_swagger)

        panel.layout.addWidget(retry_btn)
        panel.layout.addWidget(swagger_btn)
        return panel

    def _build_status_panel(self) -> HudPanel:
        panel = HudPanel("ESTADOS")
        self.backend_line = panel.add_line("Backend: --", "StatusYellow")
        self.ai_line = panel.add_line("IA: --", "StatusYellow")
        self.model_line = panel.add_line("Modelo: --")
        self.stt_line = panel.add_line("STT: --", "StatusYellow")
        self.tts_line = panel.add_line("TTS: --", "StatusYellow")
        self.mic_line = panel.add_line("Microfono: --", "StatusYellow")
        self.pending_line = panel.add_line("Pendientes: --")
        return panel

    def _build_pending_panel(self) -> HudPanel:
        panel = HudPanel("ACCIONES PENDIENTES")
        self.pending_list = QListWidget()
        self.pending_list.setMinimumHeight(88)
        self.pending_list.setMaximumHeight(150)

        buttons = QHBoxLayout()
        self.confirm_btn = QPushButton("Confirmar")
        self.cancel_btn = QPushButton("Cancelar")
        self.pending_refresh_btn = QPushButton("Actualizar")

        self.confirm_btn.clicked.connect(self.confirm_selected_action)
        self.cancel_btn.clicked.connect(self.cancel_selected_action)
        self.pending_refresh_btn.clicked.connect(self.refresh_pending_actions)

        buttons.addWidget(self.confirm_btn)
        buttons.addWidget(self.cancel_btn)
        buttons.addWidget(self.pending_refresh_btn)

        panel.layout.addWidget(self.pending_list)
        panel.layout.addLayout(buttons)
        return panel

    def _build_ai_panel(self) -> HudPanel:
        panel = HudPanel("IA LOCAL")
        self.ollama_label = panel.add_line("Ollama: --", "StatusYellow")
        self.current_model_label = panel.add_line("Modelo actual: --")
        self.ollama_enabled_check = QCheckBox("IA local activa")
        self.ollama_enabled_check.setEnabled(False)
        self.ollama_enabled_check.stateChanged.connect(self.update_ollama_enabled)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("modelo, ej: llama3.2")

        ai_buttons = QHBoxLayout()
        self.models_btn = QPushButton("Listar modelos")
        self.set_model_btn = QPushButton("Cambiar modelo")
        self.models_btn.clicked.connect(self.list_ai_models)
        self.set_model_btn.clicked.connect(self.set_ai_model)
        ai_buttons.addWidget(self.models_btn)
        ai_buttons.addWidget(self.set_model_btn)

        panel.layout.addWidget(self.ollama_enabled_check)
        panel.layout.addWidget(self.model_input)
        panel.layout.addLayout(ai_buttons)
        return panel

    def _build_voice_panel(self) -> HudPanel:
        panel = HudPanel("VOZ")
        self.voice_line = panel.add_line("Voz: --", "StatusYellow")
        self.voice_stt_line = panel.add_line("STT: --", "StatusYellow")
        self.voice_tts_line = panel.add_line("TTS: --", "StatusYellow")
        self.voice_mic_line = panel.add_line("Microfono: --", "StatusYellow")

        voice_buttons = QHBoxLayout()
        self.voice_status_btn = QPushButton("Estado voz")
        self.mic_status_btn = QPushButton("Estado mic")
        self.record_btn = QPushButton("Grabar 5s")

        self.voice_status_btn.clicked.connect(self.refresh_voice_status)
        self.mic_status_btn.clicked.connect(self.refresh_mic_status)
        self.record_btn.clicked.connect(self.record_voice_chat)

        voice_buttons.addWidget(self.voice_status_btn)
        voice_buttons.addWidget(self.mic_status_btn)
        voice_buttons.addWidget(self.record_btn)
        panel.layout.addLayout(voice_buttons)
        return panel

    def _build_log_panel(self) -> HudPanel:
        panel = HudPanel("LOG")
        self.log_view = QTextEdit()
        self.log_view.setObjectName("LogView")
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(130)
        panel.layout.addWidget(self.log_view)
        return panel

    def _build_chat_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("ChatPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        chat_title = QLabel("CHAT / ULTIMA ORDEN")
        chat_title.setObjectName("PanelTitle")

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setMinimumHeight(150)
        self.chat.setMaximumHeight(230)

        self.chat_status_label = QLabel("Listo")
        self.chat_status_label.setObjectName("SubTitleLabel")

        input_row = QHBoxLayout()

        self.input = ChatInput()
        self.input.submitted.connect(self.send_message)

        self.send_btn = QPushButton("Enviar")
        self.send_btn.clicked.connect(self.send_message)

        self.listen_btn = QPushButton("Simular escucha")
        self.listen_btn.clicked.connect(self.simulate_listening)

        input_row.addWidget(self.input, stretch=1)
        input_row.addWidget(self.listen_btn)
        input_row.addWidget(self.send_btn)

        utility_row = QHBoxLayout()
        self.clear_chat_btn = QPushButton("Limpiar chat")
        self.copy_last_btn = QPushButton("Copiar ultima respuesta")
        self.clear_chat_btn.clicked.connect(self.clear_chat_view)
        self.copy_last_btn.clicked.connect(self.copy_last_response)
        utility_row.addStretch()
        utility_row.addWidget(self.clear_chat_btn)
        utility_row.addWidget(self.copy_last_btn)

        layout.addWidget(chat_title)
        layout.addWidget(self.chat)
        layout.addWidget(self.chat_status_label)
        layout.addLayout(input_row)
        layout.addLayout(utility_row)
        return panel

    def _build_footer(self) -> QHBoxLayout:
        footer = QHBoxLayout()

        self.mode_label = QLabel("Modo: Facil")
        self.anim_label = QLabel("Animaciones: ON")
        self.voice_label = QLabel("Voz: Configurable")

        self.refresh_btn = QPushButton("Actualizar estados")
        self.refresh_btn.clicked.connect(self.refresh_status)

        project_btn = QPushButton("Abrir proyecto")
        project_btn.clicked.connect(self.open_project_folder)

        storage_btn = QPushButton("Abrir storage")
        storage_btn.clicked.connect(self.open_storage_folder)

        fullscreen_btn = QPushButton("Pantalla completa")
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)

        self.compact_btn = QPushButton("Modo compacto")
        self.compact_btn.clicked.connect(lambda: self.set_compact_mode(not self.compact_mode))

        self.top_btn = QPushButton("Siempre visible")
        self.top_btn.clicked.connect(self.toggle_always_on_top)

        tray_btn = QPushButton("Bandeja")
        tray_btn.clicked.connect(self.minimize_to_system_tray)

        config_btn = QPushButton("Configuracion")
        config_btn.clicked.connect(self.open_settings)

        footer.addWidget(self.mode_label)
        footer.addSpacing(14)
        footer.addWidget(self.anim_label)
        footer.addSpacing(14)
        footer.addWidget(self.voice_label)
        footer.addStretch()
        footer.addWidget(self.refresh_btn)
        footer.addWidget(project_btn)
        footer.addWidget(storage_btn)
        footer.addWidget(fullscreen_btn)
        footer.addWidget(self.compact_btn)
        footer.addWidget(self.top_btn)
        footer.addWidget(tray_btn)
        footer.addWidget(config_btn)
        return footer

    def _setup_timer(self) -> None:
        self.backend_timer = QTimer(self)
        self.backend_timer.timeout.connect(self.refresh_status)
        interval = int(self.desktop_settings.get("auto_refresh_interval_seconds", 15))
        self.backend_timer.setInterval(max(interval, 15) * 1000)
        if self.desktop_settings.get("auto_refresh_status", True):
            self.backend_timer.start()

    def _setup_tray(self) -> None:
        self.tray = None

        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self._build_tray_icon())
        self.tray.setToolTip("ARVIS")
        self.tray.activated.connect(self._handle_tray_activated)

        menu = QMenu()

        show_action = QAction("Mostrar ARVIS", self)
        show_action.triggered.connect(self.show_from_tray)

        compact_action = QAction("Modo compacto", self)
        compact_action.triggered.connect(lambda: self.set_compact_mode(not self.compact_mode))

        refresh_action = QAction("Actualizar estados", self)
        refresh_action.triggered.connect(self.refresh_status)

        swagger_action = QAction("Abrir Swagger", self)
        swagger_action.triggered.connect(self.open_swagger)

        hide_action = QAction("Minimizar a bandeja", self)
        hide_action.triggered.connect(self.minimize_to_system_tray)

        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.exit_application)

        menu.addAction(show_action)
        menu.addAction(compact_action)
        menu.addAction(refresh_action)
        menu.addAction(swagger_action)
        menu.addAction(hide_action)
        menu.addSeparator()
        menu.addAction(exit_action)

        self.tray.setContextMenu(menu)
        self.tray.show()

    def show_from_tray(self) -> None:
        self.show()
        if self.isMinimized():
            self.showNormal()
        self.raise_()
        self.activateWindow()

    def _handle_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_from_tray()

    def _build_tray_icon(self) -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("#050B14"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#38BDF8"), 4))
        painter.setBrush(QColor(14, 165, 233, 70))
        painter.drawEllipse(8, 8, 48, 48)
        painter.setPen(QColor("#E5F6FF"))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "A")
        painter.end()
        return QIcon(pixmap)

    def add_chat(self, sender: str, message: str, status: str | None = None) -> None:
        color = {
            "blocked": "#EF4444",
            "confirmation_required": "#F59E0B",
            "executed": "#38BDF8",
            "error": "#EF4444",
            "response": "#E5F6FF",
        }.get(status or "response", "#E5F6FF")
        badge = f" <span style='color:{color}'>[{escape(status)}]</span>" if status else ""
        safe_sender = escape(sender)
        safe_message = escape(message).replace("\n", "<br>")
        self.chat.append(f"<b>{safe_sender}:</b>{badge} {safe_message}")
        self._scroll_text_to_end(self.chat)

        if sender == "ARVIS" and message:
            self.last_response_text = message

        if status:
            visible_status = _status_label(status)
            self.chat_status_label.setText(visible_status)
            self.chat_status_label.setObjectName(_status_object_name(status))
            self._refresh_label(self.chat_status_label)

    def log_event(self, event_type: str, message: str, status: str = "info") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "ok": "#22C55E",
            "success": "#22C55E",
            "info": "#38BDF8",
            "warning": "#FACC15",
            "error": "#EF4444",
            "blocked": "#EF4444",
            "pending": "#F59E0B",
        }.get(status, "#E5F6FF")
        entry = (
            f"<span style='color:#8FB3C8'>{timestamp}</span> "
            f"<b>{escape(event_type)}</b> "
            f"<span style='color:{color}'>{escape(message)}</span>"
        )
        self._log_entries.append(entry)
        self._log_entries = self._log_entries[-200:]
        log_view = getattr(self, "log_view", None)
        if log_view is None:
            return
        try:
            log_view.setHtml("<br>".join(self._log_entries))
            self._scroll_text_to_end(log_view)
        except Exception:
            return

    def set_state(self, state: str, text: str) -> None:
        self.hud.set_state(state)
        self.status_text.setText(text)

    def simulate_listening(self) -> None:
        self.set_state("listening", "Escuchando...")
        QTimer.singleShot(1700, lambda: self.set_state("online", "Esperando orden..."))

    def send_message(self) -> None:
        text = self.input.text_value()
        if not text:
            return

        if not self.backend_online:
            message = (
                "Backend de ARVIS no disponible. Inicia run_backend.bat "
                "o revisa la conexion local."
            )
            self.add_chat("ARVIS", message, "error")
            self.log_event("chat", "mensaje no enviado: backend desconectado", "warning")
            return

        self.input.clear()
        self.add_chat("Usuario", text)
        self.log_event("chat", f"enviado: {text[:80]}", "info")
        self.set_state("processing", "Procesando...")
        self.chat_status_label.setText("Procesando...")
        self.chat_status_label.setObjectName("StatusYellow")
        self._refresh_label(self.chat_status_label)
        self._set_chat_enabled(False)
        self._run_api("chat", self.api.send_chat_message, text)

    def refresh_status(self) -> None:
        if self._refresh_in_progress:
            self.log_event("estado", "refresh ignorado: ya hay uno en curso", "info")
            return
        self._refresh_in_progress = True
        self.refresh_btn.setEnabled(False)
        self.log_event("estado", "inicio refresh liviano", "info")
        self._run_api("status_snapshot", self._fetch_status_snapshot)

    def refresh_full_diagnostics(self) -> None:
        if "full_diagnostics" in self._active_api_kinds:
            self.log_event("diagnostico", "carga completa ya en curso", "info")
            return
        self.log_event("diagnostico", "inicio diagnostico completo", "info")
        self._set_diagnostics_loading(True)
        self._run_api("full_diagnostics", self._fetch_full_diagnostics)

    def refresh_pending_actions(self) -> None:
        self._run_api("pending_actions", self.api.get_pending_actions)

    def refresh_voice_status(self) -> None:
        self._run_api("voice_status", self.api.get_voice_status)

    def refresh_mic_status(self) -> None:
        self._run_api("mic_status", self.api.get_mic_status)

    def list_ai_models(self) -> None:
        self._run_api("ai_models", self.api.get_ai_models)

    def set_ai_model(self) -> None:
        model = self.model_input.text().strip()
        if not model:
            self.log_event("ia", "modelo vacio", "warning")
            return
        self._run_api("set_ai_model", self.api.set_ai_model, model)

    def update_ollama_enabled(self) -> None:
        if not self.backend_online or not self.ollama_enabled_check.isEnabled():
            return
        enabled = self.ollama_enabled_check.isChecked()
        self._run_api("settings_update", self.api.update_settings, {"ollama_enabled": enabled})

    def record_voice_chat(self) -> None:
        if not self.backend_online:
            self.add_chat("ARVIS", "Backend no disponible para voz.", "error")
            return
        self.set_state("listening", "Grabando 5 segundos...")
        self.record_btn.setEnabled(False)
        self._run_api("voice_mic_chat", self.api.record_mic_chat, 5, False)

    def confirm_selected_action(self) -> None:
        action_id = self._selected_pending_action_id()
        if action_id is None:
            self.log_event("pendientes", "no hay accion seleccionada", "warning")
            return
        self._run_api("confirm_action", self.api.confirm_action, action_id)

    def cancel_selected_action(self) -> None:
        action_id = self._selected_pending_action_id()
        if action_id is None:
            self.log_event("pendientes", "no hay accion seleccionada", "warning")
            return
        self._run_api("cancel_action", self.api.cancel_action, action_id)

    def _fetch_status_snapshot(self) -> dict[str, Any]:
        health = self.api.get_health()
        data: dict[str, Any] = {"health": health}
        if not health["ok"]:
            return {"ok": False, "data": data, "error": health["error"]}

        data["ai"] = self.api.get_ai_status()
        data["voice"] = self.api.get_voice_status()
        data["pending"] = self.api.get_pending_actions()
        return {"ok": True, "data": data, "error": None}

    def _fetch_full_diagnostics(self) -> dict[str, Any]:
        health = self.api.get_health()
        data: dict[str, Any] = {"health": health}
        if not health["ok"]:
            return {"ok": False, "data": data, "error": health["error"]}

        data["settings"] = self.api.get_settings()
        data["ai"] = self.api.get_ai_status()
        data["ai_models"] = self.api.get_ai_models()
        data["voice"] = self.api.get_voice_status()
        data["mic"] = self.api.get_mic_status()
        data["mic_devices"] = self.api.get_mic_devices()
        data["pending"] = self.api.get_pending_actions()
        return {"ok": True, "data": data, "error": None}

    def _run_api(self, kind: str, func: Callable[..., dict[str, Any]], *args, **kwargs) -> None:
        if kind in self._active_api_kinds:
            self.log_event("api", f"{kind} ignorado: ya esta en curso", "info")
            return
        self._active_api_kinds.add(kind)
        thread = QThread(self)
        worker = ApiWorker(kind, func, *args, **kwargs)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._handle_api_result)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._cleanup_worker(thread))

        self._workers.append((thread, worker))
        thread.start()

    def _cleanup_worker(self, thread: QThread) -> None:
        self._workers = [item for item in self._workers if item[0] is not thread]

    @Slot(str, object)
    def _handle_api_result(self, kind: str, result: dict[str, Any]) -> None:
        self._active_api_kinds.discard(kind)
        if kind == "status_snapshot":
            self._refresh_in_progress = False
            self.refresh_btn.setEnabled(True)
            self._apply_status_snapshot(result)
        elif kind == "full_diagnostics":
            self._handle_full_diagnostics(result)
        elif kind == "chat":
            self._handle_chat_response(result)
        elif kind == "pending_actions":
            self._apply_pending_actions(result)
        elif kind == "voice_status":
            self._apply_voice_status(result)
        elif kind == "mic_status":
            self._apply_mic_status(result)
        elif kind == "voice_mic_chat":
            self._handle_voice_chat_response(result)
        elif kind == "ai_models":
            self._handle_ai_models(result)
        elif kind == "set_ai_model":
            self._handle_set_ai_model(result)
        elif kind == "settings_update":
            self._handle_settings_update(result)
        elif kind == "diagnostic_ai_models":
            self._handle_diagnostic_ai_models(result)
        elif kind == "diagnostic_mic_devices":
            self._handle_diagnostic_mic_devices(result)
        elif kind == "diagnostic_tts":
            self._handle_diagnostic_tts(result)
        elif kind == "diagnostic_backend_settings_update":
            self._handle_diagnostic_backend_settings_update(result)
        elif kind in {"confirm_action", "cancel_action"}:
            self._handle_action_resolution(kind, result)

    def _apply_status_snapshot(self, result: dict[str, Any]) -> None:
        if not result["ok"]:
            self.last_error = str(result.get("error") or "Backend no disponible.")
            self._set_backend_connected(False, result.get("error"))
            self.log_event("backend", "desconectado", "warning")
            self._refresh_diagnostics_dialog()
            return

        data = result["data"]
        self.last_error = None
        self._set_backend_connected(True, None)
        self._apply_health(data["health"])
        self._apply_ai_status(data.get("ai", {}))
        self._apply_voice_status(data.get("voice", {}))
        self._apply_pending_actions(data.get("pending", {}))
        self.log_event("estado", "refresh liviano finalizado", "ok")
        self._refresh_diagnostics_dialog()

    def _handle_full_diagnostics(self, result: dict[str, Any]) -> None:
        self._set_diagnostics_loading(False)
        if not result["ok"]:
            self.last_error = str(result.get("error") or "Backend no disponible.")
            self._set_backend_connected(False, result.get("error"))
            self.log_event("diagnostico", "diagnostico completo fallo", "warning")
            self._refresh_diagnostics_dialog()
            return

        data = result.get("data", {})
        self.last_error = None
        self._set_backend_connected(True, None)
        self._apply_health(data.get("health", {}))
        self._apply_settings(data.get("settings", {}))
        self._apply_ai_status(data.get("ai", {}))
        self._apply_voice_status(data.get("voice", {}))
        self._apply_mic_status(data.get("mic", {}))
        self._apply_pending_actions(data.get("pending", {}))

        ai_models = data.get("ai_models", {})
        ai_models_list = []
        if ai_models.get("ok"):
            ai_models_list = ai_models.get("data", {}).get("models", [])
        else:
            self.last_error = str(ai_models.get("error") or "Ollama no disponible.")

        mic_devices = data.get("mic_devices", {})
        mic_devices_list = []
        if mic_devices.get("ok"):
            mic_devices_list = mic_devices.get("data", {}).get("devices", [])
        else:
            self.last_error = str(mic_devices.get("error") or "Microfono no disponible.")

        self.log_event("diagnostico", "diagnostico completo finalizado", "success")
        self._refresh_diagnostics_dialog()
        if self.diagnostics_dialog:
            self.diagnostics_dialog.ai_view.setPlainText(
                self.build_ai_diagnostic_text(models=ai_models_list)
            )
            self.diagnostics_dialog.mic_view.setPlainText(
                self.build_mic_diagnostic_text(devices=mic_devices_list)
            )

    def _apply_health(self, wrapped: dict[str, Any]) -> None:
        data = wrapped.get("data", {}) if wrapped.get("ok") else {}
        if data:
            self.last_health = data
        version = data.get("version", "--")
        self.backend_version_label.setText(f"Version: {version}")
        self.model_line.setText(f"Modelo: {data.get('ai_model', '--')}")
        self.pending_line.setText(f"{data.get('pending_actions_count', '--')} pendientes")
        self._set_label_state(
            self.ai_line,
            f"IA {_availability(data.get('ai_available'))}",
            bool(data.get("ai_available")),
        )
        self._set_label_state(
            self.stt_line,
            f"Voz {_availability(data.get('stt_available'))}",
            bool(data.get("stt_available")),
        )
        self._set_label_state(
            self.tts_line,
            f"TTS {_availability(data.get('tts_available'))}",
            bool(data.get("tts_available")),
        )
        self._set_label_state(
            self.mic_line,
            f"Mic {_availability(data.get('mic_available'))}",
            bool(data.get("mic_available")),
        )

    def _apply_settings(self, wrapped: dict[str, Any]) -> None:
        if not wrapped.get("ok"):
            return
        settings = wrapped.get("data", {})
        self.last_backend_settings = settings
        self.ollama_enabled_check.blockSignals(True)
        self.ollama_enabled_check.setEnabled(True)
        self.ollama_enabled_check.setChecked(bool(settings.get("ollama_enabled", False)))
        self.ollama_enabled_check.blockSignals(False)

    def _apply_ai_status(self, wrapped: dict[str, Any]) -> None:
        if not wrapped.get("ok"):
            self.last_error = str(wrapped.get("error") or "Ollama no disponible.")
            self._set_label_state(self.ollama_label, "Ollama: no disponible", False)
            self.ai_status.setText("IA LOCAL: error")
            self.ai_status.setObjectName("StatusYellow")
            self._refresh_label(self.ai_status)
            return

        data = wrapped.get("data", {})
        self.last_ai_status = data
        available = bool(data.get("available"))
        model = data.get("model", "--")
        enabled = bool(data.get("enabled", True))

        self._set_label_state(
            self.ollama_label,
            "Ollama: disponible" if available else "Ollama: no disponible",
            available,
        )
        self.current_model_label.setText(f"Modelo actual: {model}")
        self.model_line.setText(f"Modelo: {model}")
        self.ai_status.setText("IA LOCAL: disponible" if available else "IA LOCAL: sin Ollama")
        self.ai_status.setObjectName("StatusGreen" if available else "StatusYellow")
        self._refresh_label(self.ai_status)

        self.ollama_enabled_check.blockSignals(True)
        self.ollama_enabled_check.setEnabled(True)
        self.ollama_enabled_check.setChecked(enabled)
        self.ollama_enabled_check.blockSignals(False)

    def _apply_voice_status(self, wrapped: dict[str, Any]) -> None:
        if not wrapped.get("ok"):
            self.last_error = str(wrapped.get("error") or "Voz no configurada.")
            self._set_label_state(self.voice_line, "Voz: error", False)
            return

        data = wrapped.get("data", {})
        self.last_voice_status = data
        enabled = bool(data.get("voice_enabled", False))
        stt_available = bool(data.get("stt", {}).get("available"))
        tts_available = bool(data.get("tts", {}).get("available"))
        self._set_label_state(
            self.voice_line,
            "Voz lista" if enabled else "Voz no configurada",
            enabled,
        )
        self._set_label_state(
            self.voice_stt_line,
            f"STT {_availability(stt_available)}",
            stt_available,
        )
        self._set_label_state(
            self.voice_tts_line,
            f"TTS {_availability(tts_available)}",
            tts_available,
        )
        self._set_label_state(
            self.stt_line,
            f"Voz {_availability(stt_available)}",
            stt_available,
        )
        self._set_label_state(
            self.tts_line,
            f"TTS {_availability(tts_available)}",
            tts_available,
        )

    def _apply_mic_status(self, wrapped: dict[str, Any]) -> None:
        if not wrapped.get("ok"):
            self.last_error = str(wrapped.get("error") or "Microfono no disponible.")
            self._set_label_state(self.voice_mic_line, "Microfono: error", False)
            self.mic_status.setText("MIC: error")
            self.mic_status.setObjectName("StatusYellow")
            self._refresh_label(self.mic_status)
            return

        data = wrapped.get("data", {})
        self.last_mic_status = data
        available = bool(data.get("available"))
        self._set_label_state(
            self.voice_mic_line,
            f"Microfono {_availability(available)}",
            available,
        )
        self._set_label_state(
            self.mic_line,
            f"Mic {_availability(available)}",
            available,
        )
        self.mic_status.setText("MIC: disponible" if available else "MIC: no disponible")
        self.mic_status.setObjectName("StatusGreen" if available else "StatusYellow")
        self._refresh_label(self.mic_status)

    def _apply_pending_actions(self, wrapped: dict[str, Any]) -> None:
        if not wrapped.get("ok"):
            self.last_error = str(wrapped.get("error") or "No se pudieron leer pendientes.")
            self.pending_list.clear()
            self.pending_line.setText("Pendientes: error")
            return

        data = wrapped.get("data", {})
        actions = data.get("actions", [])
        if not isinstance(actions, list):
            actions = []
        self.last_pending_actions = actions

        self._pending_actions_by_id = {}
        self.pending_list.clear()

        for action in actions:
            try:
                action_id = int(action.get("id"))
            except (TypeError, ValueError):
                continue
            self._pending_actions_by_id[action_id] = action
            created_at = _short_datetime(action.get("created_at"))
            label = (
                f"#{action_id} | {action.get('detected_intent', '--')} | "
                f"{action.get('risk_level', '--')} | {created_at}"
            )
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, action_id)
            self.pending_list.addItem(item)

        self.pending_line.setText(f"{len(actions)} pendientes")
        self.confirm_btn.setEnabled(self.backend_online and bool(actions))
        self.cancel_btn.setEnabled(self.backend_online and bool(actions))

    def _handle_chat_response(self, result: dict[str, Any]) -> None:
        self._set_chat_enabled(True)
        self.set_state("responding", "Respondiendo...")

        if not result["ok"]:
            self.add_chat("ARVIS", result["error"], "error")
            self.log_event("chat", result["error"], "error")
            self._set_backend_connected(False, result["error"])
        else:
            data = result.get("data", {})
            status = str(data.get("status", "response"))
            message = str(data.get("message", "Respuesta recibida del backend."))
            self.add_chat("ARVIS", message, status)
            self.log_event("respuesta", f"{status}: {message[:90]}", _status_to_log(status))
            if status == "confirmation_required":
                self.refresh_pending_actions()

        QTimer.singleShot(900, lambda: self.set_state("online", "Esperando orden..."))

    def _handle_voice_chat_response(self, result: dict[str, Any]) -> None:
        self.record_btn.setEnabled(self.backend_online)
        if not result["ok"]:
            self.add_chat("ARVIS", result["error"], "error")
            self.log_event("voz", result["error"], "error")
        else:
            data = result.get("data", {})
            text = data.get("transcription", {}).get("text")
            assistant_response = data.get("assistant_response", {})
            if text:
                self.add_chat("Voz", str(text))
            self.add_chat(
                "ARVIS",
                str(assistant_response.get("message", data.get("message", "Voz procesada."))),
                str(data.get("status", assistant_response.get("status", "response"))),
            )
            self.log_event("voz", "grabacion procesada", "ok")
        QTimer.singleShot(900, lambda: self.set_state("online", "Esperando orden..."))

    def _handle_ai_models(self, result: dict[str, Any]) -> None:
        if not result["ok"]:
            self.log_event("ia", result["error"], "warning")
            self.add_chat("ARVIS", "Ollama no disponible o no responde.", "error")
            return
        data = result.get("data", {})
        models = data.get("models", [])
        if models:
            self.add_chat("ARVIS", "Modelos instalados: " + ", ".join(map(str, models)))
            self.log_event("ia", f"{len(models)} modelos detectados", "ok")
        else:
            self.add_chat("ARVIS", "No hay modelos instalados o Ollama no esta disponible.")
            self.log_event("ia", "sin modelos disponibles", "warning")

    def _handle_set_ai_model(self, result: dict[str, Any]) -> None:
        if not result["ok"]:
            self.log_event("ia", result["error"], "error")
            return
        data = result.get("data", {})
        model = data.get("model") or data.get("settings", {}).get("ollama_model")
        self.current_model_label.setText(f"Modelo actual: {model or '--'}")
        self.model_line.setText(f"Modelo: {model or '--'}")
        self.log_event("ia", f"modelo guardado: {model or '--'}", "ok")
        self.refresh_status()
        self._refresh_diagnostics_dialog()

    def _handle_settings_update(self, result: dict[str, Any]) -> None:
        if result["ok"]:
            self.log_event("settings", "configuracion backend actualizada", "ok")
            self._refresh_diagnostics_dialog()
        else:
            self.last_error = str(result["error"])
            self.log_event("settings", result["error"], "error")
            self._refresh_diagnostics_dialog()

    def _handle_diagnostic_ai_models(self, result: dict[str, Any]) -> None:
        self._set_diagnostics_loading(False)
        if result["ok"]:
            data = result.get("data", {})
            models = data.get("models", [])
            if self.diagnostics_dialog:
                self.diagnostics_dialog.ai_view.setPlainText(
                    self.build_ai_diagnostic_text(models=models)
                )
            self.log_event("ia", f"modelos actualizados: {len(models)}", "success")
        else:
            self.last_error = str(result.get("error"))
            self.log_event("ia", result["error"], "warning")
            self._refresh_diagnostics_dialog()

    def _handle_diagnostic_mic_devices(self, result: dict[str, Any]) -> None:
        self._set_diagnostics_loading(False)
        if result["ok"]:
            devices = result.get("data", {}).get("devices", [])
            if self.diagnostics_dialog:
                self.diagnostics_dialog.mic_view.setPlainText(
                    self.build_mic_diagnostic_text(devices=devices)
                )
            self.log_event("mic", f"dispositivos detectados: {len(devices)}", "success")
        else:
            self.last_error = str(result.get("error"))
            self.log_event("mic", result["error"], "warning")
            self._refresh_diagnostics_dialog()

    def _handle_diagnostic_tts(self, result: dict[str, Any]) -> None:
        self._set_diagnostics_loading(False)
        if result["ok"]:
            self.log_event("voz", "prueba TTS solicitada", "success")
        else:
            self.last_error = str(result.get("error"))
            self.log_event("voz", result["error"], "warning")
        self._refresh_diagnostics_dialog()

    def _handle_diagnostic_backend_settings_update(self, result: dict[str, Any]) -> None:
        self._set_diagnostics_loading(False)
        if result["ok"]:
            self.last_backend_settings = result.get("data", {})
            self.log_event("settings", "settings backend guardados", "success")
            self.refresh_status()
        else:
            self.last_error = str(result.get("error"))
            self.log_event("settings", result["error"], "error")
            self._refresh_diagnostics_dialog()

    def _handle_action_resolution(self, kind: str, result: dict[str, Any]) -> None:
        label = "confirmada" if kind == "confirm_action" else "cancelada"
        if not result["ok"]:
            self.add_chat("ARVIS", result["error"], "error")
            self.log_event("pendientes", result["error"], "error")
        else:
            data = result.get("data", {})
            status = str(data.get("status", "response"))
            message = str(data.get("message", f"Accion {label}."))
            self.add_chat("ARVIS", message, status)
            self.log_event("pendientes", f"accion {label}: {status}", _status_to_log(status))
        self.refresh_pending_actions()

    def _set_backend_connected(self, online: bool, error: str | None = None) -> None:
        previous = self._last_backend_online
        self._last_backend_online = online
        self.backend_online = online
        self.system_panel.set_backend_status(online)
        self.backend_status.setText("Backend OK" if online else "Backend desconectado")
        self.backend_status.setObjectName("StatusGreen" if online else "StatusRed")
        self.backend_line.setText("Backend OK" if online else "Backend desconectado")
        self.backend_line.setObjectName("StatusGreen" if online else "StatusRed")

        if online:
            self.backend_message_label.setText("Estado: conectado")
            self.backend_message_label.setObjectName("StatusGreen")
            self.compact_status_label.setText("ARVIS en linea")
            self.set_state("online", "Esperando orden...")
            if previous is not True:
                self.log_event("backend", "conectado", "success")
        else:
            self.backend_message_label.setText(
                "Backend de ARVIS no disponible. Inicia run_backend.bat."
            )
            self.backend_message_label.setObjectName("StatusRed")
            self.backend_version_label.setText("Version: --")
            self.compact_status_label.setText("Backend no disponible")
            self.set_state("offline", "Backend desconectado")
            if error:
                self.status_text.setText("Backend no disponible. Reintenta conexion local.")
            if previous is not False:
                self.log_event("backend", "desconectado", "warning")

        self._refresh_label(self.backend_status)
        self._refresh_label(self.backend_line)
        self._refresh_label(self.backend_message_label)
        self._set_backend_dependent_actions(online)

    def _set_backend_dependent_actions(self, enabled: bool) -> None:
        self.input.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        self.confirm_btn.setEnabled(enabled and self.pending_list.count() > 0)
        self.cancel_btn.setEnabled(enabled and self.pending_list.count() > 0)
        self.models_btn.setEnabled(enabled)
        self.set_model_btn.setEnabled(enabled)
        self.voice_status_btn.setEnabled(enabled)
        self.mic_status_btn.setEnabled(enabled)
        self.record_btn.setEnabled(enabled)

    def _set_chat_enabled(self, enabled: bool) -> None:
        self.input.setEnabled(enabled and self.backend_online)
        self.send_btn.setEnabled(enabled and self.backend_online)

    def _set_label_state(self, label: QLabel, text: str, ok: bool) -> None:
        label.setText(text)
        label.setObjectName("StatusGreen" if ok else "StatusYellow")
        self._refresh_label(label)

    @staticmethod
    def _refresh_label(label: QLabel) -> None:
        label.style().unpolish(label)
        label.style().polish(label)

    def _selected_pending_action_id(self) -> int | None:
        item = self.pending_list.currentItem()
        if item is None and self.pending_list.count() > 0:
            item = self.pending_list.item(0)
        if item is None:
            return None
        return int(item.data(Qt.UserRole))

    def open_swagger(self) -> None:
        QDesktopServices.openUrl(QUrl(f"{self.api.base_url}/docs"))
        self.log_event("ui", "Swagger abierto", "info")

    def open_project_folder(self) -> None:
        self._open_local_path(PROJECT_DIR)

    def open_storage_folder(self) -> None:
        self._open_local_path(STORAGE_DIR)

    def _open_local_path(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        self.log_event("ui", f"carpeta abierta: {path}", "info")

    def build_diagnostic_report_text(self) -> str:
        return build_diagnostic_report(
            desktop_version=DESKTOP_VERSION,
            backend_url=self.api.base_url,
            backend_online=self.backend_online,
            health=self.last_health,
            ai_status=self.last_ai_status,
            voice_status=self.last_voice_status,
            mic_status=self.last_mic_status,
            pending_count=len(self.last_pending_actions),
            project_dir=PROJECT_DIR,
            storage_dir=STORAGE_DIR,
            desktop_config_path=DESKTOP_CONFIG_PATH,
            log_entries=self._log_entries,
            last_error=self.last_error,
        )

    def build_ai_diagnostic_text(self, models: list[Any] | None = None) -> str:
        settings = self.last_backend_settings
        status = self.last_ai_status
        model_lines = "\n".join(f"- {model}" for model in (models or [])) or "- sin datos"
        return "\n".join(
            [
                f"IA activada: {settings.get('ollama_enabled', '--')}",
                f"Ollama disponible: {status.get('available', '--')}",
                f"URL Ollama: {status.get('base_url', settings.get('ollama_base_url', '--'))}",
                f"Modelo actual: {status.get('model', settings.get('ollama_model', '--'))}",
                f"Timeout: {settings.get('ollama_timeout_seconds', '--')}",
                "Modelos instalados:",
                model_lines,
                "Nota: ARVIS no descarga modelos automaticamente.",
            ]
        )

    def build_voice_diagnostic_text(self) -> str:
        settings = self.last_backend_settings
        voice = self.last_voice_status
        stt = voice.get("stt", {}) if isinstance(voice.get("stt"), dict) else {}
        tts = voice.get("tts", {}) if isinstance(voice.get("tts"), dict) else {}
        return "\n".join(
            [
                f"voice_enabled: {settings.get('voice_enabled', voice.get('voice_enabled', '--'))}",
                f"STT disponible: {stt.get('available', '--')}",
                f"Motor STT: {settings.get('stt_engine', '--')}",
                f"Modelo STT: {settings.get('stt_model', '--')}",
                f"TTS disponible: {tts.get('available', '--')}",
                f"Motor TTS: {settings.get('tts_engine', '--')}",
                f"Error STT: {stt.get('error', '--')}",
                f"Error TTS: {tts.get('error', '--')}",
            ]
        )

    def build_mic_diagnostic_text(self, devices: list[Any] | None = None) -> str:
        settings = self.last_backend_settings
        mic = self.last_mic_status
        device_lines = "\n".join(f"- {device}" for device in (devices or [])) or "- sin datos"
        return "\n".join(
            [
                f"mic_enabled: {settings.get('mic_enabled', '--')}",
                f"Microfono disponible: {mic.get('available', '--')}",
                f"Motor: {settings.get('mic_engine', '--')}",
                f"Duracion por defecto: {settings.get('mic_default_record_seconds', '--')}",
                f"Error: {mic.get('error', '--')}",
                "Dispositivos:",
                device_lines,
            ]
        )

    def build_pending_diagnostic_text(self) -> str:
        lines = [f"Pendientes: {len(self.last_pending_actions)}"]
        for action in self.last_pending_actions:
            lines.append(
                f"#{action.get('id')} | {action.get('detected_intent')} | "
                f"{action.get('risk_level')} | {action.get('created_at')}"
            )
        return "\n".join(lines)

    def build_paths_diagnostic_text(self) -> str:
        return "\n".join(
            [
                f"Proyecto: {PROJECT_DIR}",
                f"Storage backend: {STORAGE_DIR}",
                f"Config desktop: {DESKTOP_CONFIG_PATH}",
                "No se permiten rutas arbitrarias desde esta pantalla.",
            ]
        )

    def build_logs_diagnostic_text(self) -> str:
        if not self._log_entries:
            return "Sin eventos visuales."
        return "\n".join(_plain_log_entry(entry) for entry in self._log_entries[-50:])

    def copy_diagnostic_report(self) -> None:
        QApplication.clipboard().setText(self.build_diagnostic_report_text())
        self.log_event("diagnostico", "diagnostico copiado", "success")
        self._refresh_diagnostics_dialog()

    def copy_backend_status(self) -> None:
        text = "\n".join(
            [
                f"Backend URL: {self.api.base_url}",
                f"Backend estado: {'conectado' if self.backend_online else 'desconectado'}",
                f"Version: {self.last_health.get('version', '--')}",
                f"Storage: {self.last_health.get('storage_path', '--')}",
                f"Database: {self.last_health.get('database_exists', '--')}",
            ]
        )
        QApplication.clipboard().setText(text)
        self.log_event("diagnostico", "estado backend copiado", "success")

    def save_desktop_settings_from_dialog(self, dialog: DiagnosticsDialog) -> None:
        payload = dialog.desktop_payload()
        if not payload["backend_base_url"]:
            self.log_event("settings", "backend_base_url vacio", "error")
            return
        self.desktop_settings = save_desktop_settings(payload)
        self.api = ApiClient(
            self.desktop_settings["backend_base_url"],
            self.desktop_settings["request_timeout_seconds"],
        )
        self.backend_url_label.setText(f"URL: {self.api.base_url}")
        self.minimize_to_tray = bool(self.desktop_settings["minimize_to_tray"])
        self.set_always_on_top(bool(self.desktop_settings["always_on_top"]), persist=False)
        self.apply_ui_mode(str(self.desktop_settings["ui_mode"]), persist=False)
        self.set_compact_mode(bool(self.desktop_settings["compact_mode_enabled"]), persist=False)
        self.backend_timer.stop()
        self._setup_timer()
        self.log_event("settings", "configuracion desktop guardada", "success")
        self.refresh_status()
        self._refresh_diagnostics_dialog()

    def save_backend_settings_from_dialog(self, dialog: DiagnosticsDialog) -> None:
        if not self.backend_online:
            self.log_event("settings", "backend no disponible", "error")
            return
        if "diagnostic_backend_settings_update" in self._active_api_kinds:
            self.log_event("settings", "guardado backend ya en curso", "info")
            return
        payload = dialog.backend_payload()
        self._set_diagnostics_loading(True)
        self._run_api("diagnostic_backend_settings_update", self.api.update_settings, payload)

    def request_ai_models_for_dialog(self) -> None:
        if "diagnostic_ai_models" in self._active_api_kinds:
            self.log_event("ia", "modelos ya se estan consultando", "info")
            return
        self._set_diagnostics_loading(True)
        self._run_api("diagnostic_ai_models", self.api.get_ai_models)

    def request_mic_devices_for_dialog(self) -> None:
        if "diagnostic_mic_devices" in self._active_api_kinds:
            self.log_event("mic", "dispositivos ya se estan consultando", "info")
            return
        self._set_diagnostics_loading(True)
        self._run_api("diagnostic_mic_devices", self.api.get_mic_devices)

    def test_tts_from_dialog(self) -> None:
        if not self.backend_online:
            self.log_event("voz", "backend no disponible para TTS", "error")
            return
        if "diagnostic_tts" in self._active_api_kinds:
            self.log_event("voz", "prueba TTS ya en curso", "info")
            return
        self._set_diagnostics_loading(True)
        self._run_api("diagnostic_tts", self.api.generate_tts, "Hola, soy ARVIS.", False)

    def set_ai_model_from_dialog(self, dialog: DiagnosticsDialog) -> None:
        model = dialog.backend_ollama_model.text().strip()
        if not model:
            self.log_event("ia", "modelo vacio", "warning")
            return
        self._run_api("set_ai_model", self.api.set_ai_model, model)

    def clear_visual_logs(self) -> None:
        self._log_entries.clear()
        log_view = getattr(self, "log_view", None)
        if log_view is not None:
            log_view.clear()
        self.log_event("logs", "logs visuales limpiados", "info")
        self._refresh_diagnostics_dialog()

    def _refresh_diagnostics_dialog(self) -> None:
        if self.diagnostics_dialog is not None and self.diagnostics_dialog.isVisible():
            try:
                self.diagnostics_dialog.refresh_from_window()
            except Exception:
                return

    def _set_diagnostics_loading(self, loading: bool) -> None:
        if self.diagnostics_dialog is not None:
            self.diagnostics_dialog.set_loading(loading)

    def clear_chat_view(self) -> None:
        self.chat.clear()
        self.chat_status_label.setText("Chat visual limpio")
        self.chat_status_label.setObjectName("SubTitleLabel")
        self._refresh_label(self.chat_status_label)
        self.log_event("chat", "vista limpia", "info")

    def copy_last_response(self) -> None:
        if not self.last_response_text:
            self.log_event("chat", "no hay respuesta para copiar", "warning")
            return
        QApplication.clipboard().setText(self.last_response_text)
        self.log_event("chat", "ultima respuesta copiada", "success")

    def set_compact_mode(self, enabled: bool, persist: bool = True) -> None:
        if enabled == self.compact_mode and persist:
            return

        if enabled:
            if not self.compact_mode:
                self._normal_geometry = self.geometry()
            self.compact_mode = True
            self.left_widget.hide()
            self.right_widget.hide()
            self.local_panel.hide()
            self.chat.setMaximumHeight(150)
            self.compact_bar.setVisible(True)
            self.compact_btn.setText("Modo normal")
            self.resize(560, 420)
            self.setMinimumSize(460, 360)
            self.log_event("ui", "modo compacto activado", "info")
        else:
            self.compact_mode = False
            self.left_widget.show()
            self.right_widget.show()
            self.local_panel.show()
            self.chat.setMaximumHeight(230)
            self.compact_bar.setVisible(False)
            self.compact_btn.setText("Modo compacto")
            self.setMinimumSize(980, 640)
            if self._normal_geometry is not None:
                self.setGeometry(self._normal_geometry)
            self.log_event("ui", "modo normal activado", "info")

        if persist:
            self._update_desktop_setting("compact_mode_enabled", self.compact_mode)

    def toggle_always_on_top(self) -> None:
        self.set_always_on_top(not self.always_on_top)

    def set_always_on_top(self, enabled: bool, persist: bool = True) -> None:
        self.always_on_top = enabled
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowStaysOnTopHint
            self.top_btn.setText("No fijar")
        else:
            flags &= ~Qt.WindowStaysOnTopHint
            self.top_btn.setText("Siempre visible")
        self.setWindowFlags(flags)
        if self.isVisible():
            self.show()
        if persist:
            self._update_desktop_setting("always_on_top", enabled)
        self.log_event("ui", "siempre visible ON" if enabled else "siempre visible OFF", "info")

    def toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showMaximized()
            self.log_event("ui", "pantalla restaurada", "info")
        else:
            self.showFullScreen()
            self.log_event("ui", "pantalla completa", "info")

    def minimize_to_system_tray(self) -> None:
        if self.tray and self.minimize_to_tray:
            self.hide()
            self.tray.showMessage(
                "ARVIS",
                "ARVIS sigue activo en la bandeja.",
                QSystemTrayIcon.Information,
                1800,
            )
            self.log_event("ui", "minimizado a bandeja", "info")
            return
        self.showMinimized()

    def exit_application(self) -> None:
        self._force_exit = True
        self.close()

    def apply_ui_mode(self, mode: str, persist: bool = True) -> None:
        self.ui_mode = mode if mode in {"easy", "advanced"} else "easy"
        advanced = self.ui_mode == "advanced"
        self.tools_panel.setVisible(advanced)
        self.security_panel.setVisible(advanced)
        self.log_panel.setVisible(advanced)
        self.ai_panel.setVisible(advanced)
        self.voice_panel.setVisible(advanced)
        self.mode_label.setText("Modo: Avanzado" if advanced else "Modo: Facil")
        if persist:
            self._update_desktop_setting("ui_mode", self.ui_mode)

    def _update_desktop_setting(self, key: str, value: Any) -> None:
        self.desktop_settings[key] = value
        self.desktop_settings = save_desktop_settings(self.desktop_settings)

    @staticmethod
    def _scroll_text_to_end(widget: QTextEdit | None) -> None:
        if widget is None:
            return
        try:
            cursor = widget.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            widget.setTextCursor(cursor)
        except Exception:
            return

    def open_settings(self) -> None:
        if self.diagnostics_dialog is None:
            self.diagnostics_dialog = DiagnosticsDialog(self)
        self.diagnostics_dialog.refresh_from_window()
        self.diagnostics_dialog.show()
        self.diagnostics_dialog.raise_()
        self.diagnostics_dialog.activateWindow()

    def enter_compact_mode(self) -> None:
        self.set_compact_mode(not self.compact_mode)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
            return

        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showMaximized()
            return

        super().keyPressEvent(event)

    def changeEvent(self, event) -> None:
        if (
            event.type() == QEvent.WindowStateChange
            and self.isMinimized()
            and self.minimize_to_tray
            and self.tray
        ):
            QTimer.singleShot(0, self.minimize_to_system_tray)
        super().changeEvent(event)

    def closeEvent(self, event) -> None:
        if self.minimize_to_tray and self.tray and not self._force_exit:
            event.ignore()
            self.minimize_to_system_tray()
            return

        for thread, _worker in list(self._workers):
            thread.quit()
            thread.wait(800)
        event.accept()


def _safe_int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _availability(value: Any) -> str:
    if value is True:
        return "disponible"
    if value is False:
        return "no disponible"
    return "--"


def _status_label(status: str) -> str:
    labels = {
        "executed": "Ejecutado",
        "blocked": "Bloqueado por seguridad",
        "confirmation_required": "Requiere confirmacion",
        "response": "Respuesta",
        "error": "Error",
    }
    return labels.get(status, status)


def _status_object_name(status: str) -> str:
    if status in {"executed", "response"}:
        return "StatusGreen"
    if status == "confirmation_required":
        return "StatusYellow"
    if status in {"blocked", "error"}:
        return "StatusRed"
    return "SubTitleLabel"


def _short_datetime(value: Any) -> str:
    if not isinstance(value, str) or not value:
        return "--"
    return value.replace("T", " ")[:16]


def _plain_log_entry(entry: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", "", entry).split())


def _status_to_log(status: str) -> str:
    if status in {"executed", "response"}:
        return "success"
    if status == "blocked":
        return "blocked"
    if status == "confirmation_required":
        return "pending"
    return "info"
