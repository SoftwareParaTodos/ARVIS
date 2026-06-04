COLORS = {
    "background": "#050B14",
    "panel": "rgba(10, 19, 34, 224)",
    "panel_strong": "rgba(10, 19, 34, 240)",
    "panel_soft": "rgba(15, 23, 42, 188)",
    "accent": "#38BDF8",
    "accent_soft": "rgba(56, 189, 248, 110)",
    "accent_hover": "rgba(14, 165, 233, 120)",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "text": "#E5F6FF",
    "muted": "#8FB3C8",
    "disabled": "#64748B",
}

FONTS = {
    "ui": "Segoe UI",
    "technical": "Consolas",
}

BORDERS = {
    "panel": f"1px solid {COLORS['accent_soft']}",
    "control": "1px solid rgba(56, 189, 248, 90)",
}


ARVIS_STYLE = f"""
QMainWindow {{
    background-color: {COLORS["background"]};
}}

QWidget {{
    background-color: {COLORS["background"]};
    color: {COLORS["text"]};
    font-family: "{FONTS["ui"]}";
    font-size: 10pt;
}}

QFrame#HudPanel {{
    background-color: {COLORS["panel"]};
    border: {BORDERS["panel"]};
    border-radius: 14px;
}}

QFrame#ChatPanel {{
    background-color: {COLORS["panel_strong"]};
    border: 1px solid rgba(56, 189, 248, 95);
    border-radius: 16px;
}}

QLabel#TitleLabel {{
    color: {COLORS["accent"]};
    font-size: 18pt;
    font-weight: 700;
    letter-spacing: 1px;
}}

QLabel#SubTitleLabel {{
    color: {COLORS["muted"]};
    font-size: 10pt;
}}

QLabel#PanelTitle {{
    color: {COLORS["accent"]};
    font-size: 10pt;
    font-weight: 700;
    letter-spacing: 1px;
}}

QLabel#StatusGreen {{
    color: {COLORS["success"]};
    font-weight: 700;
}}

QLabel#StatusYellow {{
    color: {COLORS["warning"]};
    font-weight: 700;
}}

QLabel#StatusRed {{
    color: {COLORS["danger"]};
    font-weight: 700;
}}

QTextEdit {{
    background-color: rgba(5, 11, 20, 218);
    border: {BORDERS["control"]};
    border-radius: 10px;
    color: {COLORS["text"]};
    padding: 9px;
    selection-background-color: #0EA5E9;
}}

QTextEdit#LogView {{
    font-family: "{FONTS["technical"]}";
    font-size: 9pt;
}}

QTextEdit#ChatInput {{
    min-height: 40px;
    max-height: 76px;
}}

QLineEdit {{
    background-color: rgba(5, 11, 20, 230);
    border: {BORDERS["control"]};
    border-radius: 10px;
    padding: 9px;
    color: {COLORS["text"]};
}}

QPushButton {{
    background-color: rgba(14, 165, 233, 70);
    border: 1px solid rgba(56, 189, 248, 145);
    border-radius: 10px;
    color: {COLORS["text"]};
    padding: 8px 12px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {COLORS["accent_hover"]};
    border: 1px solid rgba(125, 211, 252, 210);
}}

QPushButton:pressed {{
    background-color: rgba(14, 165, 233, 180);
}}

QPushButton:disabled {{
    background-color: rgba(30, 41, 59, 120);
    border: 1px solid rgba(71, 85, 105, 120);
    color: {COLORS["disabled"]};
}}

QComboBox {{
    background-color: rgba(5, 11, 20, 230);
    border: {BORDERS["control"]};
    border-radius: 10px;
    padding: 7px;
    color: {COLORS["text"]};
}}

QCheckBox {{
    color: {COLORS["text"]};
}}

QListWidget {{
    background-color: rgba(5, 11, 20, 214);
    border: {BORDERS["control"]};
    border-radius: 10px;
    color: {COLORS["text"]};
    padding: 6px;
}}

QListWidget::item {{
    padding: 4px;
}}

QListWidget::item:selected {{
    background-color: rgba(14, 165, 233, 120);
}}

QScrollArea {{
    border: none;
}}

QScrollBar:vertical {{
    background: {COLORS["background"]};
    width: 10px;
}}

QScrollBar:horizontal {{
    background: {COLORS["background"]};
    height: 10px;
}}

QScrollBar::handle:vertical,
QScrollBar::handle:horizontal {{
    background: rgba(56, 189, 248, 120);
    border-radius: 5px;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    height: 0;
    width: 0;
}}
"""
