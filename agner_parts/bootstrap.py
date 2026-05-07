
import sys, os, json, re, sqlite3, datetime, base64, html, zipfile
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from collections import deque  # Para o histórico de abas fechadas
import traceback  # Importar traceback para depuração
import weakref  # Para weak references em callbacks, se necessário (PyQt já faz para QObject methods)

# PyQt6 com imports seguros
from PyQt6.QtCore import (
    QObject, pyqtSignal, pyqtSlot, QUrl, QTimer, QSize, QPoint, QByteArray,
    Qt, QSettings, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTabBar, QStackedWidget, QStatusBar, QLabel, QProgressBar,
    QDialog, QDialogButtonBox, QMenu, QInputDialog, QMessageBox,
    QComboBox, QCheckBox, QFormLayout, QTextBrowser, QTabWidget, QSpinBox,
    QToolButton, QListWidget, QListWidgetItem, QListView, QFrame, QScrollArea, QGridLayout, QFileDialog,
    QSizePolicy, QCompleter # Adicionado QSizePolicy
)
from PyQt6.QtGui import QIcon, QKeySequence, QPixmap, QPainter, QColor, QShortcut, QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView

from PyQt6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo,
    QWebEngineProfile, QWebEngineSettings, QWebEngineScript,
)
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest as QWebEngineDownloadItem
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtSvg import QSvgRenderer

# Cripto
try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("WARNING: cryptography library not found. Password management will be disabled.")

# ================= UI/ (MainWindow, dialogs, widgets) =================

# --- Ícones e Tema Moderno ---
class SafeIconProvider:
    """Provider de ícones com cache seguro e fallbacks"""
    _cache: Dict[tuple, QIcon] = {}
    _renderer: Optional[QSvgRenderer] = None

    @staticmethod
    def get_icon(svg_data: str, color: str = "#ffffff", size: int = 24) -> QIcon:
        key = (svg_data, color, size)
        if key in SafeIconProvider._cache:
            return SafeIconProvider._cache[key]

        try:
            if SafeIconProvider._renderer is None:
                SafeIconProvider._renderer = QSvgRenderer()

            # Simplificado: Assume que o SVG usa 'currentColor' e o substitui.
            modified_svg = svg_data.replace('currentColor', color)

            data = QByteArray(modified_svg.encode('utf-8'))

            if not SafeIconProvider._renderer.load(data):
                print(f"Failed to load SVG data: {modified_svg[:50]}...")  # Debug
                return QIcon()

            pix = QPixmap(size, size)
            pix.fill(Qt.GlobalColor.transparent)  # Garante fundo transparente

            painter = QPainter(pix)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # Melhor renderização
            SafeIconProvider._renderer.render(painter)
            painter.end()

            icon = QIcon(pix)
            SafeIconProvider._cache[key] = icon
            return icon

        except Exception as e:
            print(f"Erro criando ícone: {e}")
            return QIcon()


# NOVOS SVG Icons modernos (do Lucide Icons e Heroicons para um visual mais limpo e consistente)
SVG_ICONS = {
    # Navegação - visual mais fluido e moderno
    "back": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="m15 18-6-6 6-6"/>
        <circle cx="9" cy="12" r="1" fill="currentColor" opacity="0.3"/>
    </svg>''',

    "forward": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="m9 18 6-6-6-6"/>
        <circle cx="15" cy="12" r="1" fill="currentColor" opacity="0.3"/>
    </svg>''',

    "reload": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
        <path d="M21 3v5h-5"/>
        <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
        <path d="M3 21v-5h5"/>
        <circle cx="12" cy="12" r="2" fill="none" stroke="currentColor" opacity="0.3"/>
    </svg>''',

    "stop": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="9"/>
        <rect x="9" y="9" width="6" height="6" fill="currentColor" rx="1"/>
    </svg>''',

    "home": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
        <polyline points="9,22 9,12 15,12 15,22"/>
        <circle cx="12" cy="8" r="1" fill="currentColor" opacity="0.6"/>
    </svg>''',

    # Favoritos - com efeito de brilho
    "bookmark_outline": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m19 21-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
        <path d="M12 7v6" stroke="currentColor" opacity="0.3"/>
        <circle cx="12" cy="8" r="1" fill="currentColor" opacity="0.4"/>
    </svg>''',

    "bookmark_filled": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="none">
        <path d="m19 21-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
        <path d="M12 7v6" stroke="white" stroke-width="1" opacity="0.6"/>
        <circle cx="12" cy="8" r="1" fill="white" opacity="0.8"/>
    </svg>''',

    # Configurações - design mais sofisticado
    "settings": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1m15.5-3.5L19 9m-14.5.5L7 7M16.5 19.5L19 17M4.5 17l2.5-2.5"/>
        <circle cx="12" cy="12" r="1" fill="currentColor" opacity="0.6"/>
    </svg>''',

    # Estrelas - com gradiente visual
    "star": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <defs>
            <radialGradient id="starGrad" cx="50%" cy="30%">
                <stop offset="0%" stop-color="currentColor" stop-opacity="1"/>
                <stop offset="100%" stop-color="currentColor" stop-opacity="0.7"/>
            </radialGradient>
        </defs>
        <path d="m12 2 3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2Z" fill="url(#starGrad)"/>
        <circle cx="12" cy="8" r="1" fill="white" opacity="0.8"/>
    </svg>''',

    "star_outline": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m12 2 3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2Z"/>
        <circle cx="12" cy="10" r="1" fill="currentColor" opacity="0.5"/>
    </svg>''',

    # Funcionalidades - design limpo e moderno
    "menu": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <line x1="4" y1="6" x2="20" y2="6"/>
        <line x1="4" y1="12" x2="20" y2="12"/>
        <line x1="4" y1="18" x2="20" y2="18"/>
        <circle cx="3" cy="6" r="1" fill="currentColor"/>
        <circle cx="3" cy="12" r="1" fill="currentColor"/>
        <circle cx="3" cy="18" r="1" fill="currentColor"/>
    </svg>''',

    "send": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m22 2-7 20-4-9-9-4 20-7z"/>
        <path d="M22 2 11 13" opacity="0.5"/>
        <circle cx="18" cy="6" r="1" fill="currentColor" opacity="0.7"/>
    </svg>''',

    "close_tab": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="9" opacity="0.1" fill="currentColor"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
    </svg>''',

    "add": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="9" opacity="0.1" fill="currentColor"/>
        <line x1="12" y1="8" x2="12" y2="16"/>
        <line x1="8" y1="12" x2="16" y2="12"/>
    </svg>''',

    # Utilitários - com mais personalidade
    "delete": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m3 6 18 0"/>
        <path d="m19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
        <path d="m8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
        <line x1="10" y1="11" x2="10" y2="17"/>
        <line x1="14" y1="11" x2="14" y2="17"/>
    </svg>''',

    "history": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="9"/>
        <polyline points="12,7 12,12 16,14"/>
        <path d="m9 22-3-3 3-3"/>
        <circle cx="12" cy="12" r="1" fill="currentColor" opacity="0.6"/>
    </svg>''',

    "download": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7,10 12,15 17,10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
        <circle cx="12" cy="12" r="1" fill="currentColor" opacity="0.5"/>
    </svg>''',

    # Privacidade - visual mais discreto e elegante
    "incognito": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
        <circle cx="12" cy="12" r="3"/>
        <path d="M12 5V2"/>
        <path d="M19 10l2-2"/>
        <path d="M5 10L3 8"/>
        <circle cx="12" cy="12" r="1" fill="currentColor"/>
    </svg>''',

    "profile": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
        <circle cx="12" cy="7" r="1" fill="currentColor" opacity="0.6"/>
        <path d="M12 11c-2 0-4 1-4 3" opacity="0.3"/>
    </svg>''',

    "extensions": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20.5 16.9A9 9 0 1 1 7.7 3.4"/>
        <path d="m6.4 19.9 7-8"/>
        <circle cx="12" cy="12" r="2"/>
        <path d="M13.4 10.6 19 5"/>
        <circle cx="19" cy="5" r="1" fill="currentColor"/>
    </svg>''',

    "clear_data": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="9"/>
        <path d="M9 9l6 6"/>
        <path d="m15 9-6 6"/>
        <circle cx="12" cy="12" r="3" opacity="0.2" fill="currentColor"/>
    </svg>'''
}

# Temas do navegador
THEMES = {
    "chrome_clean": {
        "name": "Chrome Clean",
        "window_bg": "#dfe4ec",
        "navbar_bg": "rgba(255, 255, 255, 0.90)",
        "tab_bar_bg": "#dfe4ec",
        "tab_bg": "rgba(255, 255, 255, 0.48)",
        "tab_selected_bg": "rgba(255, 255, 255, 0.96)",
        "tab_text": "#4b5563",
        "tab_selected_text": "#1f2937",
        "accent": "#1a73e8",
        "accent_hover": "#155ec0",
        "primary_text": "#202124",
        "secondary_text": "#5f6368",
        "divider": "rgba(60, 64, 67, 0.14)",
        "button_hover": "rgba(60, 64, 67, 0.08)",
        "input_bg": "rgba(255, 255, 255, 0.72)",
        "card_bg": "rgba(255, 255, 255, 0.96)",
        "dialog_bg": "#f8fafd",
        "loading_color": "#1a73e8",
        "icon_color": "#5f6368",
        "success": "#188038",
        "error": "#d93025",
        "warning": "#f9ab00",
        "dialog_text": "#202124",
        "dialog_input_bg": "#ffffff",
        "dialog_button_bg": "#eef2f7",
        "dialog_button_hover": "#e5eaf1",
        "web_bg": "#ffffff",
        "incognito_tab_bg": "rgba(54, 58, 64, 0.88)",
        "incognito_tab_selected_bg": "#ffffff",
        "incognito_text": "#e8eaed"
    },
    "chrome_dark": {
        "name": "Chrome Dark",
        "window_bg": "#202124",
        "navbar_bg": "rgba(41, 42, 45, 0.94)",
        "tab_bar_bg": "#202124",
        "tab_bg": "rgba(60, 64, 67, 0.72)",
        "tab_selected_bg": "#2f3136",
        "tab_text": "#c9cdd3",
        "tab_selected_text": "#f1f3f4",
        "accent": "#8ab4f8",
        "accent_hover": "#aecbfa",
        "primary_text": "#f1f3f4",
        "secondary_text": "#bdc1c6",
        "divider": "rgba(232, 234, 237, 0.12)",
        "button_hover": "rgba(232, 234, 237, 0.10)",
        "input_bg": "rgba(232, 234, 237, 0.10)",
        "card_bg": "#2f3136",
        "dialog_bg": "#242528",
        "loading_color": "#8ab4f8",
        "icon_color": "#bdc1c6",
        "success": "#81c995",
        "error": "#f28b82",
        "warning": "#fdd663",
        "dialog_text": "#f1f3f4",
        "dialog_input_bg": "#303134",
        "dialog_button_bg": "#303134",
        "dialog_button_hover": "#3c4043",
        "web_bg": "#202124",
        "incognito_tab_bg": "#141518",
        "incognito_tab_selected_bg": "#303134",
        "incognito_text": "#e8eaed"
    },
    "gamer_glass": {
        "name": "Gamer Glass",
        "window_bg": "#dce3ee",
        "navbar_bg": "rgba(248, 250, 252, 0.88)",
        "tab_bar_bg": "#dce3ee",
        "tab_bg": "rgba(255, 255, 255, 0.42)",
        "tab_selected_bg": "rgba(255, 255, 255, 0.94)",
        "tab_text": "#46515f",
        "tab_selected_text": "#111827",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "primary_text": "#111827",
        "secondary_text": "#64748b",
        "divider": "rgba(15, 23, 42, 0.12)",
        "button_hover": "rgba(15, 23, 42, 0.07)",
        "input_bg": "rgba(255, 255, 255, 0.70)",
        "card_bg": "rgba(255, 255, 255, 0.92)",
        "dialog_bg": "#f8fafc",
        "loading_color": "#2563eb",
        "icon_color": "#526071",
        "success": "#16a34a",
        "error": "#dc2626",
        "warning": "#d97706",
        "dialog_text": "#111827",
        "dialog_input_bg": "#ffffff",
        "dialog_button_bg": "#eef2f7",
        "dialog_button_hover": "#e2e8f0",
        "web_bg": "#ffffff",
        "incognito_tab_bg": "rgba(15, 23, 42, 0.82)",
        "incognito_tab_selected_bg": "#ffffff",
        "incognito_text": "#e2e8f0"
    }
}
HTML_START_PAGE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AGNER Browser - Nova Aba</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --page: #eef2f7;
    --page-2: #f8fafc;
    --surface: rgba(255, 255, 255, 0.76);
    --surface-solid: #ffffff;
    --surface-soft: rgba(255, 255, 255, 0.56);
    --border: rgba(15, 23, 42, 0.10);
    --text: #111827;
    --muted: #64748b;
    --accent: #1a73e8;
    --accent-soft: rgba(26, 115, 232, 0.10);
    --shadow: 0 18px 60px rgba(15, 23, 42, 0.10);
}

[data-theme="chrome_dark"] {
    --page: #202124;
    --page-2: #2b2d31;
    --surface: rgba(47, 49, 54, 0.82);
    --surface-solid: #303134;
    --surface-soft: rgba(60, 64, 67, 0.56);
    --border: rgba(232, 234, 237, 0.12);
    --text: #f1f3f4;
    --muted: #bdc1c6;
    --accent: #8ab4f8;
    --accent-soft: rgba(138, 180, 248, 0.14);
    --shadow: 0 18px 60px rgba(0, 0, 0, 0.28);
}

[data-theme="gamer_glass"] {
    --page: #e4ebf5;
    --page-2: #f8fafc;
    --surface: rgba(255, 255, 255, 0.70);
    --surface-solid: #ffffff;
    --surface-soft: rgba(255, 255, 255, 0.52);
    --border: rgba(15, 23, 42, 0.12);
    --text: #111827;
    --muted: #64748b;
    --accent: #2563eb;
    --accent-soft: rgba(37, 99, 235, 0.11);
    --shadow: 0 20px 70px rgba(37, 99, 235, 0.10);
}

html, body { min-height: 100%; }

body {
    font-family: "Segoe UI", Arial, sans-serif;
    color: var(--text);
    background: linear-gradient(180deg, var(--page-2) 0%, var(--page) 100%);
    padding: 34px;
}

.shell {
    width: min(1120px, 100%);
    margin: 0 auto;
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 14px;
}

.panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    box-shadow: var(--shadow);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
}

.hero {
    grid-column: span 8;
    padding: 28px;
    min-height: 238px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.brand {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
}

.brand h1 {
    font-size: 44px;
    font-weight: 700;
    letter-spacing: 0;
    line-height: 1;
}

.pill {
    color: var(--accent);
    background: var(--accent-soft);
    border: 1px solid rgba(26, 115, 232, 0.18);
    border-radius: 999px;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 600;
}

.search {
    display: flex;
    align-items: center;
    min-height: 54px;
    margin-top: 28px;
    background: var(--surface-solid);
    border: 1px solid var(--border);
    border-radius: 999px;
    box-shadow: 0 6px 24px rgba(15, 23, 42, 0.08);
    overflow: hidden;
}

.search:focus-within {
    border-color: var(--accent);
    box-shadow: 0 8px 30px rgba(26, 115, 232, 0.16);
}

.search input {
    flex: 1;
    border: 0;
    outline: 0;
    background: transparent;
    color: var(--text);
    font-size: 16px;
    padding: 0 22px;
}

.search input::placeholder { color: var(--muted); }

.search button {
    border: 0;
    background: transparent;
    color: var(--accent);
    font-weight: 700;
    padding: 0 22px;
    height: 54px;
    cursor: pointer;
}

.search button:hover { background: var(--accent-soft); }

.side {
    grid-column: span 4;
    padding: 20px;
    min-height: 238px;
}

.section-title {
    font-size: 13px;
    color: var(--muted);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 14px;
}

.actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}

.action {
    border: 1px solid var(--border);
    background: var(--surface-soft);
    color: var(--text);
    border-radius: 14px;
    min-height: 72px;
    padding: 14px;
    cursor: pointer;
    text-align: left;
}

.action:hover {
    background: var(--surface-solid);
    border-color: rgba(26, 115, 232, 0.26);
}

.action strong {
    display: block;
    font-size: 15px;
    margin-bottom: 6px;
}

.action span {
    display: block;
    color: var(--muted);
    font-size: 13px;
}

.links-panel {
    grid-column: span 8;
    padding: 20px;
}

.quick-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(132px, 1fr));
    gap: 10px;
}

.quick {
    position: relative;
    min-height: 116px;
    border: 1px solid var(--border);
    background: var(--surface-soft);
    color: var(--text);
    border-radius: 16px;
    padding: 14px;
    cursor: pointer;
    overflow: hidden;
}

.quick:hover {
    background: var(--surface-solid);
    border-color: rgba(26, 115, 232, 0.22);
}

.avatar {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    display: grid;
    place-items: center;
    background: var(--accent-soft);
    color: var(--accent);
    font-weight: 800;
    margin-bottom: 14px;
}

.quick-name {
    font-weight: 700;
    font-size: 15px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.quick-url {
    color: var(--muted);
    font-size: 12px;
    margin-top: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.remove {
    position: absolute;
    top: 9px;
    right: 9px;
    width: 24px;
    height: 24px;
    border: 0;
    border-radius: 999px;
    background: rgba(15, 23, 42, 0.08);
    color: var(--muted);
    display: none;
    cursor: pointer;
}

.quick:hover .remove { display: block; }
.remove:hover { color: var(--text); background: rgba(15, 23, 42, 0.14); }

.add {
    border-style: dashed;
}

.bento {
    grid-column: span 4;
    display: grid;
    grid-template-columns: 1fr;
    gap: 14px;
}

.mini {
    min-height: 116px;
    padding: 20px;
}

.metric {
    font-size: 30px;
    font-weight: 750;
    line-height: 1;
}

.metric-label {
    margin-top: 8px;
    color: var(--muted);
    font-size: 13px;
}

@media (max-width: 900px) {
    body { padding: 18px; }
    .hero, .side, .links-panel, .bento { grid-column: span 12; }
}
</style>
</head>
<body>
<main class="shell">
    <section class="panel hero">
        <div class="brand">
            <h1>AGNER</h1>
            <div class="pill">Gamer Glass</div>
        </div>
        <form class="search" onsubmit="return doSearch()">
            <input id="q" placeholder="Pesquisar no Google ou digitar URL" autocomplete="off" autofocus>
            <button type="submit">IR</button>
        </form>
    </section>

    <aside class="panel side">
        <div class="section-title">Acesso rapido</div>
        <div class="actions">
            <button class="action" onclick="navigateTo('about:history')"><strong>Historico</strong><span>Hoje</span></button>
            <button class="action" onclick="navigateTo('about:downloads')"><strong>Downloads</strong><span>Arquivos</span></button>
            <button class="action" onclick="navigateTo('https://www.youtube.com')"><strong>YouTube</strong><span>Video</span></button>
            <button class="action" onclick="navigateTo('https://store.steampowered.com')"><strong>Steam</strong><span>Games</span></button>
        </div>
    </aside>

    <section class="panel links-panel">
        <div class="section-title">Favoritos</div>
        <div id="links" class="quick-grid"></div>
    </section>

    <section class="bento">
        <div class="panel mini">
            <div id="clock" class="metric">--:--</div>
            <div class="metric-label">Sao Paulo</div>
        </div>
        <div class="panel mini">
            <div id="linkCount" class="metric">0</div>
            <div class="metric-label">Favoritos fixados</div>
        </div>
    </section>
</main>

<script>
let quickLinksData = []; //DATA_PLACEHOLDER
const bridge = () => window.agnerBrowserBridge || {};

function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    }[char]));
}

function normalizeUrl(value) {
    const url = String(value || '').trim();
    if (!url) return 'about:home';
    if (url.startsWith('about:') || url.startsWith('file:///') || /^https?:\\/\\//i.test(url)) return url;
    return 'https://' + url;
}

function getDomain(value) {
    try {
        const url = normalizeUrl(value);
        if (url.startsWith('about:')) return url;
        return new URL(url).hostname.replace(/^www\\./, '');
    } catch(e) {
        return value;
    }
}

function initials(name) {
    const clean = String(name || '').trim();
    return (clean[0] || 'A').toUpperCase();
}

function navigateTo(url) {
    const finalUrl = normalizeUrl(url);
    if (bridge().navigate) bridge().navigate(finalUrl);
    else window.location.href = finalUrl;
}

function createCard(name, url, isAdd) {
    const card = document.createElement('div');
    card.className = 'quick' + (isAdd ? ' add' : '');
    if (isAdd) {
        card.innerHTML = '<div class="avatar">+</div><div class="quick-name">Adicionar</div><div class="quick-url">Novo favorito</div>';
        card.onclick = addNew;
        return card;
    }

    card.dataset.name = name;
    card.dataset.url = url;
    card.innerHTML = `
        <button class="remove" title="Remover" onclick="deleteCard(event, this)">x</button>
        <div class="avatar">${escapeHtml(initials(name))}</div>
        <div class="quick-name">${escapeHtml(name)}</div>
        <div class="quick-url">${escapeHtml(getDomain(url))}</div>
    `;
    card.onclick = (event) => {
        if (event.target.classList.contains('remove')) return;
        navigateTo(url);
    };
    return card;
}

function renderLinks() {
    const root = document.getElementById('links');
    root.innerHTML = '';
    const defaults = [
        { name: 'Google', url: 'https://www.google.com' },
        { name: 'YouTube', url: 'https://www.youtube.com' },
        { name: 'GitHub', url: 'https://github.com' },
        { name: 'Steam', url: 'https://store.steampowered.com' },
        { name: 'Twitch', url: 'https://www.twitch.tv' },
        { name: 'Reddit', url: 'https://www.reddit.com' }
    ];
    const links = Array.isArray(quickLinksData) && quickLinksData.length ? quickLinksData : defaults;
    links.forEach((item) => root.appendChild(createCard(item.name, item.url, false)));
    root.appendChild(createCard('', '', true));
    document.getElementById('linkCount').textContent = String(links.length);
}

function saveLinks() {
    const items = Array.from(document.querySelectorAll('.quick:not(.add)')).map((card) => ({
        name: card.dataset.name,
        url: card.dataset.url
    }));
    quickLinksData = items;
    if (bridge().saveQuickLinks) bridge().saveQuickLinks(JSON.stringify(items));
    document.getElementById('linkCount').textContent = String(items.length);
}

function deleteCard(event, button) {
    event.stopPropagation();
    button.closest('.quick').remove();
    saveLinks();
}

function addNew() {
    const name = prompt('Nome do site:');
    if (!name || !name.trim()) return;
    const url = prompt('URL do site:');
    if (!url || !url.trim()) return;
    quickLinksData = Array.from(document.querySelectorAll('.quick:not(.add)')).map((card) => ({
        name: card.dataset.name,
        url: card.dataset.url
    }));
    quickLinksData.push({ name: name.trim(), url: normalizeUrl(url.trim()) });
    renderLinks();
    saveLinks();
}

function doSearch() {
    const query = document.getElementById('q').value.trim();
    if (!query) return false;
    const looksLikeUrl = query.startsWith('about:') || query.startsWith('file:///') ||
        /^https?:\\/\\//i.test(query) || (query.includes('.') && !query.includes(' '));
    navigateTo(looksLikeUrl ? query : 'https://www.google.com/search?q=' + encodeURIComponent(query));
    return false;
}

function applyTheme(theme) {
    const validThemes = ['chrome_clean', 'chrome_dark', 'gamer_glass'];
    document.documentElement.setAttribute('data-theme', validThemes.includes(theme) ? theme : 'chrome_clean');
}

function detectTheme() {
    try {
        const api = bridge();
        if (api.getCurrentTheme) api.getCurrentTheme((theme) => applyTheme(theme));
        else applyTheme('chrome_clean');
    } catch(e) {
        applyTheme('chrome_clean');
    }
}

function setClock() {
    const now = new Date();
    document.getElementById('clock').textContent = now.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

document.addEventListener('DOMContentLoaded', () => {
    detectTheme();
    setClock();
    renderLinks();
});
</script>
</body>
</html>
"""


