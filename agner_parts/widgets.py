# ================= WIDGETS/ (HistoryWidget, DownloadsWidget) =================


class HistoryWidget(QWidget):
    """Bento-style history page used as an internal browser tab."""

    def __init__(self, history_manager: HistoryManager, theme: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.theme = theme
        self.cards_grid: Optional[QGridLayout] = None
        self.count_label: Optional[QLabel] = None
        self._init_ui()

    def _init_ui(self) -> None:
        self.setObjectName("internalBentoPage")
        self._apply_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 24)
        layout.setSpacing(16)

        header = QFrame()
        header.setObjectName("bentoHero")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 20)
        header_layout.setSpacing(16)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("Historico")
        title.setObjectName("bentoTitle")
        subtitle = QLabel("Suas paginas recentes em cards limpos.")
        subtitle.setObjectName("bentoSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.count_label = QLabel("0 visitas")
        self.count_label.setObjectName("bentoBadge")

        clear_btn = QPushButton("Limpar historico")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_history)

        header_layout.addLayout(title_box, 1)
        header_layout.addWidget(self.count_label)
        header_layout.addWidget(clear_btn)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setObjectName("bentoScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("bentoGridHost")
        self.cards_grid = QGridLayout(content)
        self.cards_grid.setContentsMargins(0, 0, 0, 0)
        self.cards_grid.setHorizontalSpacing(14)
        self.cards_grid.setVerticalSpacing(14)

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        self._load_history()

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            QWidget#internalBentoPage {{
                background-color: {self.theme['web_bg']};
                color: {self.theme['primary_text']};
            }}
            QFrame#bentoHero, QFrame#bentoCard, QFrame#emptyCard {{
                background-color: {self.theme['card_bg']};
                border: 1px solid {self.theme['divider']};
                border-radius: 18px;
            }}
            QLabel#bentoTitle {{
                font-size: 28px;
                font-weight: 750;
                color: {self.theme['primary_text']};
            }}
            QLabel#bentoSubtitle, QLabel#cardUrl, QLabel#cardMeta, QLabel#emptyText {{
                color: {self.theme['secondary_text']};
            }}
            QLabel#bentoBadge {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['secondary_text']};
                border: 1px solid {self.theme['divider']};
                border-radius: 14px;
                padding: 8px 12px;
                font-weight: 600;
            }}
            QLabel#cardTitle {{
                color: {self.theme['primary_text']};
                font-size: 15px;
                font-weight: 700;
            }}
            QPushButton#primaryButton, QPushButton#dangerButton {{
                border-radius: 12px;
                padding: 9px 14px;
                font-weight: 650;
            }}
            QPushButton#primaryButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: 1px solid {self.theme['accent']};
            }}
            QPushButton#primaryButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
            QPushButton#dangerButton {{
                background-color: {self.theme['dialog_button_bg']};
                color: {self.theme['primary_text']};
                border: 1px solid {self.theme['divider']};
            }}
            QPushButton#dangerButton:hover {{
                background-color: {self.theme['dialog_button_hover']};
            }}
            QScrollArea#bentoScroll {{
                border: none;
                background: transparent;
            }}
            QWidget#bentoGridHost {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                width: 10px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.theme['divider']};
                border-radius: 5px;
                min-height: 32px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

    def _clear_cards(self) -> None:
        if not self.cards_grid:
            return
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _load_history(self) -> None:
        self._clear_cards()
        history_items = self.history_manager.get_all_history()
        if self.count_label:
            self.count_label.setText(f"{len(history_items)} visitas")

        if not history_items:
            self.cards_grid.addWidget(self._create_empty_card("Sem historico ainda", "As paginas visitadas aparecem aqui."), 0, 0, 1, 3)
            return

        for index, item_data in enumerate(history_items):
            self.cards_grid.addWidget(self._create_history_card(item_data), index // 3, index % 3)

        self.cards_grid.setRowStretch((len(history_items) + 2) // 3, 1)

    def _create_empty_card(self, title_text: str, subtitle_text: str) -> QFrame:
        card = QFrame()
        card.setObjectName("emptyCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 28, 24, 28)
        layout.setSpacing(8)
        title = QLabel(title_text)
        title.setObjectName("cardTitle")
        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("emptyText")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return card

    def _create_history_card(self, item_data: Any) -> QFrame:
        url = item_data["url"]
        title_text = item_data["title"] or url
        try:
            visit_time = datetime.datetime.fromisoformat(item_data["visit_time"]).strftime("%d/%m/%Y %H:%M")
        except Exception:
            visit_time = str(item_data["visit_time"])

        card = QFrame()
        card.setObjectName("bentoCard")
        card.setMinimumHeight(150)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        title = QLabel(title_text)
        title.setObjectName("cardTitle")
        title.setWordWrap(True)

        url_label = QLabel(url)
        url_label.setObjectName("cardUrl")
        url_label.setWordWrap(True)

        meta = QLabel(f"Visitado: {visit_time}")
        meta.setObjectName("cardMeta")

        open_btn = QPushButton("Abrir")
        open_btn.setObjectName("primaryButton")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(lambda _=False, u=url: self._open_url(u))

        layout.addWidget(title)
        layout.addWidget(url_label)
        layout.addStretch()
        layout.addWidget(meta)
        layout.addWidget(open_btn, 0, Qt.AlignmentFlag.AlignRight)
        return card

    def _clear_history(self) -> None:
        reply = QMessageBox.question(
            self,
            "Limpar historico",
            "Limpar todo o historico de navegacao?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.history_manager.clear_history():
                self._load_history()
            else:
                QMessageBox.warning(self, "Erro", "Nao foi possivel limpar o historico.")

    def _open_url(self, url: str) -> None:
        current_parent = self.parent()
        while current_parent is not None and not isinstance(current_parent, SafeMainWindow):
            current_parent = current_parent.parent()
        if isinstance(current_parent, SafeMainWindow):
            current_parent.navigate_to_url_direct(url)

    def _visit_history_item(self, list_item: QListWidgetItem) -> None:
        history_item = list_item.data(Qt.ItemDataRole.UserRole)
        if history_item:
            self._open_url(history_item["url"])


class DownloadsWidget(QWidget):
    """Bento-style downloads page used as an internal browser tab."""

    def __init__(self, download_manager: DownloadManager, theme: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.download_manager = download_manager
        self.theme = theme
        self.palette = _internal_page_palette(theme)
        self.selected_download: Optional[QWebEngineDownloadItem] = None
        self.cards_grid: Optional[QGridLayout] = None
        self.total_label: Optional[QLabel] = None
        self.done_label: Optional[QLabel] = None
        self.active_label: Optional[QLabel] = None
        self.download_cards: List[QFrame] = []
        self._init_ui()
        self.download_manager.download_updated.connect(self._load_downloads)

    def _init_ui(self) -> None:
        self.setObjectName("internalBentoPage")
        self._apply_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 24)
        layout.setSpacing(16)

        header = QFrame()
        header.setObjectName("bentoHero")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 20)
        header_layout.setSpacing(16)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("Downloads")
        title.setObjectName("bentoTitle")
        subtitle = QLabel("Arquivos baixados, progresso e atalhos rapidos.")
        subtitle.setObjectName("bentoSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.open_file_btn = QPushButton("Abrir arquivo")
        self.open_folder_btn = QPushButton("Abrir pasta")
        for btn in (self.open_file_btn, self.open_folder_btn):
            btn.setObjectName("primaryButton" if btn is self.open_file_btn else "ghostButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_file_btn.clicked.connect(self._open_download)
        self.open_folder_btn.clicked.connect(self._open_download_folder)

        header_layout.addLayout(title_box, 1)
        header_layout.addWidget(self.open_file_btn)
        header_layout.addWidget(self.open_folder_btn)
        layout.addWidget(header)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        self.total_label = self._create_stat_card("0", "Total")
        self.done_label = self._create_stat_card("0", "Concluidos")
        self.active_label = self._create_stat_card("0", "Ativos")
        stats_row.addWidget(self.total_label)
        stats_row.addWidget(self.done_label)
        stats_row.addWidget(self.active_label)
        layout.addLayout(stats_row)

        scroll = QScrollArea()
        scroll.setObjectName("bentoScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("bentoGridHost")
        self.cards_grid = QGridLayout(content)
        self.cards_grid.setContentsMargins(0, 0, 0, 0)
        self.cards_grid.setHorizontalSpacing(14)
        self.cards_grid.setVerticalSpacing(14)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        self._load_downloads()

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            QWidget#internalBentoPage {{
                background-color: {self.theme['web_bg']};
                color: {self.theme['primary_text']};
            }}
            QFrame#bentoHero, QFrame#downloadCard, QFrame#emptyCard, QLabel#statCard {{
                background-color: {self.theme['card_bg']};
                border: 1px solid {self.theme['divider']};
                border-radius: 18px;
            }}
            QFrame#downloadCard[selected="true"] {{
                border: 1px solid {self.theme['accent']};
                background-color: {self.theme['input_bg']};
            }}
            QLabel#bentoTitle {{
                font-size: 28px;
                font-weight: 750;
                color: {self.theme['primary_text']};
            }}
            QLabel#bentoSubtitle, QLabel#downloadMeta, QLabel#emptyText {{
                color: {self.theme['secondary_text']};
            }}
            QLabel#downloadTitle {{
                color: {self.theme['primary_text']};
                font-size: 15px;
                font-weight: 700;
            }}
            QLabel#statusDone {{
                color: {self.theme['success']};
                font-weight: 700;
            }}
            QLabel#statusActive, QLabel#statusWaiting {{
                color: {self.theme['warning']};
                font-weight: 700;
            }}
            QLabel#statusError {{
                color: {self.theme['error']};
                font-weight: 700;
            }}
            QLabel#statCard {{
                padding: 14px;
                font-size: 14px;
                color: {self.theme['secondary_text']};
            }}
            QLabel#statCard[metric="true"] {{
                font-size: 26px;
                font-weight: 750;
                color: {self.theme['primary_text']};
            }}
            QPushButton#primaryButton, QPushButton#ghostButton {{
                border-radius: 12px;
                padding: 9px 14px;
                font-weight: 650;
            }}
            QPushButton#primaryButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: 1px solid {self.theme['accent']};
            }}
            QPushButton#primaryButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
            QPushButton#primaryButton:disabled {{
                background-color: {self.theme['dialog_button_bg']};
                color: {self.theme['secondary_text']};
                border: 1px solid {self.theme['divider']};
            }}
            QPushButton#ghostButton {{
                background-color: {self.theme['dialog_button_bg']};
                color: {self.theme['primary_text']};
                border: 1px solid {self.theme['divider']};
            }}
            QPushButton#ghostButton:hover {{
                background-color: {self.theme['dialog_button_hover']};
            }}
            QFrame#progressTrack {{
                background-color: {self.theme['dialog_button_bg']};
                border-radius: 4px;
            }}
            QFrame#progressFill {{
                background-color: {self.theme['accent']};
                border-radius: 4px;
            }}
            QScrollArea#bentoScroll {{
                border: none;
                background: transparent;
            }}
            QWidget#bentoGridHost {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                width: 10px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.theme['divider']};
                border-radius: 5px;
                min-height: 32px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

    def _create_stat_card(self, value: str, label: str) -> QLabel:
        stat = QLabel(f"{value}\n{label}")
        stat.setObjectName("statCard")
        stat.setMinimumHeight(72)
        stat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return stat

    def _clear_cards(self) -> None:
        self.download_cards.clear()
        if not self.cards_grid:
            return
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _load_downloads(self) -> None:
        self._clear_cards()
        downloads = self.download_manager.get_all_downloads()

        total = len(downloads)
        done = len([d for d in downloads if d.state() == QWebEngineDownloadItem.DownloadState.DownloadFinished])
        active = len([d for d in downloads if d.state() == QWebEngineDownloadItem.DownloadState.DownloadInProgress])
        self.total_label.setText(f"{total}\nTotal")
        self.done_label.setText(f"{done}\nConcluidos")
        self.active_label.setText(f"{active}\nAtivos")

        if not downloads:
            self.selected_download = None
            self.open_file_btn.setEnabled(False)
            self.cards_grid.addWidget(self._create_empty_card(), 0, 0, 1, 3)
            return

        if self.selected_download not in downloads:
            self.selected_download = downloads[0]
        self.open_file_btn.setEnabled(self._is_finished(self.selected_download))

        for index, item in enumerate(downloads):
            self.cards_grid.addWidget(self._create_download_card(item), index // 3, index % 3)
        self.cards_grid.setRowStretch((len(downloads) + 2) // 3, 1)

    def _create_empty_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("emptyCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 28, 24, 28)
        title = QLabel("Nenhum download ainda")
        title.setObjectName("downloadTitle")
        subtitle = QLabel("Quando voce baixar arquivos, eles aparecem aqui em cards.")
        subtitle.setObjectName("emptyText")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return card

    def _create_download_card(self, item: QWebEngineDownloadItem) -> QFrame:
        card = QFrame()
        card.setObjectName("downloadCard")
        card.setProperty("selected", item == self.selected_download)
        card.setMinimumHeight(154)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.mousePressEvent = lambda event, download=item, frame=card: self._select_download(download, frame)
        self.download_cards.append(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        filename = os.path.basename(item.path()) or "download"
        title = QLabel(filename)
        title.setObjectName("downloadTitle")
        title.setWordWrap(True)

        meta = QLabel(self._format_file_size(item.totalBytes()) if item.totalBytes() > 0 else "Tamanho desconhecido")
        meta.setObjectName("downloadMeta")

        status = QLabel(self._status_text(item))
        status.setObjectName(self._status_object_name(item))

        layout.addWidget(title)
        layout.addWidget(meta)
        layout.addStretch()
        layout.addWidget(status)

        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadInProgress:
            layout.addWidget(self._create_progress_bar(item))

        return card

    def _create_progress_bar(self, item: QWebEngineDownloadItem) -> QWidget:
        container = QWidget()
        container.setFixedHeight(8)
        track = QFrame(container)
        track.setObjectName("progressTrack")
        track.setGeometry(0, 0, 220, 8)
        fill = QFrame(container)
        fill.setObjectName("progressFill")
        percent = 0
        if item.totalBytes() > 0:
            percent = max(0, min(100, int((item.receivedBytes() / item.totalBytes()) * 100)))
        fill.setGeometry(0, 0, int(220 * percent / 100), 8)
        return container

    def _select_download(self, item: QWebEngineDownloadItem, selected_card: QFrame) -> None:
        self.selected_download = item
        self.open_file_btn.setEnabled(self._is_finished(item))
        for card in self.download_cards:
            card.setProperty("selected", card is selected_card)
            card.style().unpolish(card)
            card.style().polish(card)

    def _is_finished(self, item: Optional[QWebEngineDownloadItem]) -> bool:
        return bool(item and item.state() == QWebEngineDownloadItem.DownloadState.DownloadFinished)

    def _status_text(self, item: QWebEngineDownloadItem) -> str:
        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadFinished:
            return "Concluido"
        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadInProgress:
            if item.totalBytes() > 0:
                percent = int((item.receivedBytes() / item.totalBytes()) * 100)
                return f"Baixando {percent}%"
            return "Baixando"
        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadInterrupted:
            return "Interrompido"
        return "Aguardando"

    def _status_object_name(self, item: QWebEngineDownloadItem) -> str:
        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadFinished:
            return "statusDone"
        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadInterrupted:
            return "statusError"
        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadInProgress:
            return "statusActive"
        return "statusWaiting"

    def _format_file_size(self, size: int) -> str:
        if size <= 0:
            return "0 B"
        value = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} PB"

    def _open_download(self) -> None:
        if not self.selected_download:
            self._show_notification("Selecione um download primeiro", error=True)
            return
        if not self._is_finished(self.selected_download):
            self._show_notification("Download ainda nao concluido", error=True)
            return
        try:
            os.startfile(self.selected_download.path())
        except Exception as e:
            self._show_notification(f"Nao foi possivel abrir: {e}", error=True)

    def _open_download_folder(self) -> None:
        try:
            folder = self.download_manager.download_path
            if self.selected_download:
                folder = os.path.dirname(self.selected_download.path())
            os.startfile(folder)
        except Exception as e:
            self._show_notification(f"Nao foi possivel abrir a pasta: {e}", error=True)

    def _show_notification(self, message: str, error: bool = False) -> None:
        notification = QLabel(message, self)
        notification.setObjectName("toast")
        notification.setStyleSheet(f"""
            QLabel#toast {{
                background-color: {self.theme['error'] if error else self.theme['success']};
                color: white;
                padding: 10px 16px;
                border-radius: 10px;
                font-weight: 650;
            }}
        """)
        notification.adjustSize()
        notification.move((self.width() - notification.width()) // 2, 24)
        notification.show()
        QTimer.singleShot(2400, notification.deleteLater)


def _internal_page_palette(theme: dict) -> dict:
    is_dark = "dark" in str(theme.get("name", "")).lower() or theme.get("web_bg") == "#202124"
    if is_dark:
        return {
            "page": theme.get("web_bg", "#202124"),
            "surface": theme.get("card_bg", "#2f3136"),
            "surface_soft": theme.get("dialog_button_bg", "#303134"),
            "text": theme.get("primary_text", "#f1f3f4"),
            "muted": theme.get("secondary_text", "#bdc1c6"),
            "border": theme.get("divider", "rgba(232, 234, 237, 0.12)"),
            "accent": theme.get("accent", "#8ab4f8"),
            "accent_hover": theme.get("accent_hover", "#aecbfa"),
            "input": theme.get("dialog_input_bg", "#303134"),
            "selection": theme.get("input_bg", "#303134"),
            "success": theme.get("success", "#81c995"),
            "error": theme.get("error", "#f28b82"),
        }
    return {
        "page": theme.get("web_bg", "#ffffff"),
        "surface": theme.get("card_bg", "#ffffff"),
        "surface_soft": theme.get("dialog_button_bg", "#f1f3f4"),
        "text": theme.get("primary_text", "#202124"),
        "muted": theme.get("secondary_text", "#5f6368"),
        "border": theme.get("divider", "rgba(60, 64, 67, 0.14)"),
        "accent": theme.get("accent", "#1a73e8"),
        "accent_hover": theme.get("accent_hover", "#155ec0"),
        "input": theme.get("dialog_input_bg", "#ffffff"),
        "selection": theme.get("input_bg", "#e8f0fe"),
        "success": theme.get("success", "#188038"),
        "error": theme.get("error", "#d93025"),
    }


class DownloadsWidget(QWidget):
    """Chrome-style downloads page that follows the active browser theme."""

    def __init__(self, download_manager: DownloadManager, theme: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.download_manager = download_manager
        self.theme = theme
        self.palette = _internal_page_palette(theme)
        self.selected_download: Optional[QWebEngineDownloadItem] = None
        self.list_layout: Optional[QVBoxLayout] = None
        self.rows: List[QFrame] = []
        self._init_ui()
        self.download_manager.download_updated.connect(self._load_downloads)
        self.download_manager.download_finished.connect(lambda _: self._load_downloads())

    def _init_ui(self) -> None:
        p = self.palette
        self.setObjectName("chromeDownloadsPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QWidget#chromeDownloadsPage {{
                background-color: {p['page']};
                color: {p['text']};
            }}
            QLabel#downloadsTitle {{
                color: {p['text']};
                font-size: 24px;
                font-weight: 800;
            }}
            QLabel#dateLabel {{
                color: {p['muted']};
                font-size: 13px;
                font-weight: 700;
            }}
            QLineEdit#downloadSearch {{
                background-color: {p['input']};
                color: {p['text']};
                border: 2px solid {p['accent']};
                border-radius: 20px;
                padding: 9px 18px;
                min-width: 520px;
            }}
            QPushButton#topAction, QPushButton#rowAction {{
                background-color: transparent;
                color: {p['accent']};
                border: 1px solid {p['accent']};
                border-radius: 16px;
                padding: 7px 14px;
                font-weight: 700;
            }}
            QPushButton#rowAction {{
                border-color: transparent;
                color: {p['muted']};
                min-width: 34px;
                padding: 6px 8px;
            }}
            QFrame#downloadRow {{
                background-color: {p['surface']};
                border: 1px solid {p['border']};
                border-radius: 8px;
            }}
            QFrame#downloadRow[selected="true"] {{
                border: 1px solid {p['accent']};
                background-color: {p['selection']};
            }}
            QLabel#fileIcon, QLabel#fileMeta, QLabel#emptyDownloads {{
                color: {p['muted']};
            }}
            QLabel#fileTitle {{
                color: {p['accent']};
                font-weight: 700;
            }}
            QProgressBar {{
                border: none;
                background-color: {p['surface_soft']};
                border-radius: 4px;
                max-height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {p['accent']};
                border-radius: 4px;
            }}
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                width: 10px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background-color: {p['muted']};
                border-radius: 5px;
                min-height: 34px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 0)
        root.setSpacing(18)

        header = QHBoxLayout()
        title = QLabel("Historico de transferencias")
        title.setObjectName("downloadsTitle")
        self.search = QLineEdit()
        self.search.setObjectName("downloadSearch")
        self.search.setPlaceholderText("Pesquise o historico de transferencias")
        self.search.textChanged.connect(self._load_downloads)
        clear_btn = QPushButton("Limpar tudo")
        clear_btn.setObjectName("topAction")
        clear_btn.clicked.connect(self._clear_downloads)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search)
        header.addStretch()
        header.addWidget(clear_btn)
        root.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        host = QWidget()
        host.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        host.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(host)
        self.list_layout.setContentsMargins(0, 0, 0, 30)
        self.list_layout.setSpacing(10)
        scroll.setWidget(host)
        root.addWidget(scroll, 1)
        self._load_downloads()

    def _clear_rows(self) -> None:
        self.rows.clear()
        if not self.list_layout:
            return
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _load_downloads(self, *_args) -> None:
        if not self.list_layout:
            return
        self.setUpdatesEnabled(False)
        try:
            self._clear_rows()
            query = self.search.text().strip().lower() if hasattr(self, "search") else ""
            downloads = [item for item in self.download_manager.get_all_downloads()
                         if not query or query in (os.path.basename(item.path()) or "").lower()]
            if not downloads:
                self.selected_download = None
                empty = QLabel("Nenhuma transferencia para mostrar.")
                empty.setObjectName("emptyDownloads")
                empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty.setMinimumHeight(360)
                self.list_layout.addWidget(empty)
                self.list_layout.addStretch()
                return
            day_label = QLabel("Recentes")
            day_label.setObjectName("dateLabel")
            day_label.setMaximumWidth(720)
            self.list_layout.addWidget(day_label, 0, Qt.AlignmentFlag.AlignHCenter)
            if self.selected_download not in downloads:
                self.selected_download = downloads[0]
            for item in downloads:
                self.list_layout.addWidget(self._create_download_row(item), 0, Qt.AlignmentFlag.AlignHCenter)
            self.list_layout.addStretch()
        finally:
            self.setUpdatesEnabled(True)
            self.update()

    def _create_download_row(self, item: QWebEngineDownloadItem) -> QFrame:
        row = QFrame()
        row.setObjectName("downloadRow")
        row.setProperty("selected", item == self.selected_download)
        row.setFixedWidth(700)
        row.setMinimumHeight(74)
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.mousePressEvent = lambda event, download=item, frame=row: self._select_download(download, frame)
        self.rows.append(row)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(18, 12, 12, 12)
        layout.setSpacing(16)
        file_icon = QLabel("[ ]")
        file_icon.setObjectName("fileIcon")
        layout.addWidget(file_icon)
        info = QVBoxLayout()
        filename = QLabel(os.path.basename(item.path()) or "download")
        filename.setObjectName("fileTitle")
        filename.setWordWrap(True)
        meta = QLabel(self._meta_text(item))
        meta.setObjectName("fileMeta")
        info.addWidget(filename)
        info.addWidget(meta)
        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadInProgress:
            info.addWidget(self._progress_bar(item))
        layout.addLayout(info, 1)
        open_btn = QPushButton("Abrir")
        open_btn.setObjectName("rowAction")
        open_btn.setToolTip("Abrir arquivo")
        open_btn.clicked.connect(lambda checked=False, download=item: self._open_download(download))
        folder_btn = QPushButton("Pasta")
        folder_btn.setObjectName("rowAction")
        folder_btn.setToolTip("Abrir pasta")
        folder_btn.clicked.connect(lambda checked=False, download=item: self._open_download_folder(download))
        layout.addWidget(open_btn)
        layout.addWidget(folder_btn)
        return row

    def _progress_bar(self, item: QWebEngineDownloadItem) -> QProgressBar:
        bar = QProgressBar()
        bar.setTextVisible(False)
        percent = 0
        if item.totalBytes() > 0:
            percent = max(0, min(100, int((item.receivedBytes() / item.totalBytes()) * 100)))
        bar.setValue(percent)
        return bar

    def _meta_text(self, item: QWebEngineDownloadItem) -> str:
        return f"{self._format_file_size(item.totalBytes())}  {self._status_text(item)}"

    def _select_download(self, item: QWebEngineDownloadItem, selected_row: QFrame) -> None:
        self.selected_download = item
        for row in self.rows:
            row.setProperty("selected", row is selected_row)
            row.style().unpolish(row)
            row.style().polish(row)

    def _clear_downloads(self) -> None:
        self.download_manager.completed_downloads.clear()
        self._load_downloads()

    def _is_finished(self, item: Optional[QWebEngineDownloadItem]) -> bool:
        return bool(item and item.state() == QWebEngineDownloadItem.DownloadState.DownloadFinished)

    def _status_text(self, item: QWebEngineDownloadItem) -> str:
        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadFinished:
            return "Concluido"
        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadInProgress:
            if item.totalBytes() > 0:
                return f"Baixando {int((item.receivedBytes() / item.totalBytes()) * 100)}%"
            return "Baixando"
        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadInterrupted:
            return "Eliminado"
        return "Aguardando"

    def _format_file_size(self, size: int) -> str:
        if size <= 0:
            return "Tamanho desconhecido"
        value = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} PB"

    def _open_download(self, item: Optional[QWebEngineDownloadItem] = None) -> None:
        download = item or self.selected_download
        if not self._is_finished(download):
            self._show_notification("Download ainda nao concluido", error=True)
            return
        try:
            os.startfile(download.path())
        except Exception as e:
            self._show_notification(f"Nao foi possivel abrir: {e}", error=True)

    def _open_download_folder(self, item: Optional[QWebEngineDownloadItem] = None) -> None:
        try:
            download = item or self.selected_download
            folder = os.path.dirname(download.path()) if download else self.download_manager.download_path
            os.startfile(folder)
        except Exception as e:
            self._show_notification(f"Nao foi possivel abrir a pasta: {e}", error=True)

    def _show_notification(self, message: str, error: bool = False) -> None:
        p = self.palette
        notification = QLabel(message, self)
        notification.setStyleSheet(f"""
            QLabel {{
                background-color: {p['error'] if error else p['success']};
                color: white;
                padding: 10px 16px;
                border-radius: 8px;
                font-weight: 700;
            }}
        """)
        notification.adjustSize()
        notification.move((self.width() - notification.width()) // 2, 24)
        notification.show()
        QTimer.singleShot(2400, notification.deleteLater)


class DownloadsWidget(QWidget):
    """Chrome-style downloads page used as an internal browser tab."""

    def __init__(self, download_manager: DownloadManager, theme: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.download_manager = download_manager
        self.theme = theme
        self.palette = _internal_page_palette(theme)
        self.selected_download: Optional[QWebEngineDownloadItem] = None
        self.list_layout: Optional[QVBoxLayout] = None
        self.rows: List[QFrame] = []
        self._init_ui()
        self.download_manager.download_updated.connect(self._load_downloads)
        self.download_manager.download_finished.connect(lambda _: self._load_downloads())

    def _init_ui(self) -> None:
        p = self.palette
        self.setObjectName("chromeDownloadsPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QWidget#chromeDownloadsPage {{
                background-color: {p['page']};
                color: {p['text']};
            }}
            QLabel#downloadsTitle {{
                color: {p['text']};
                font-size: 24px;
                font-weight: 800;
            }}
            QLabel#dateLabel {{
                color: {p['muted']};
                font-size: 13px;
                font-weight: 700;
            }}
            QLineEdit#downloadSearch {{
                background-color: {p['input']};
                color: {p['text']};
                border: 2px solid {p['accent']};
                border-radius: 20px;
                padding: 9px 18px;
                min-width: 520px;
            }}
            QPushButton#topAction, QPushButton#rowAction {{
                background-color: transparent;
                color: {p['accent']};
                border: 1px solid {p['accent']};
                border-radius: 16px;
                padding: 7px 14px;
                font-weight: 700;
            }}
            QPushButton#rowAction {{
                border-color: transparent;
                color: {p['muted']};
                min-width: 34px;
                padding: 6px 8px;
            }}
            QFrame#downloadRow {{
                background-color: {p['surface']};
                border: 1px solid {p['border']};
                border-radius: 8px;
            }}
            QFrame#downloadRow[selected="true"] {{
                border: 1px solid {p['accent']};
                background-color: {p['selection']};
            }}
            QLabel#fileIcon, QLabel#fileMeta, QLabel#fileStatus, QLabel#emptyDownloads {{
                color: {p['muted']};
            }}
            QLabel#fileTitle {{
                color: {p['accent']};
                font-weight: 700;
            }}
            QLabel#fileStatus {{
                font-weight: 700;
            }}
            QLabel#emptyDownloads {{
                font-size: 16px;
            }}
            QProgressBar {{
                border: none;
                background-color: {p['surface_soft']};
                border-radius: 4px;
                max-height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {p['accent']};
                border-radius: 4px;
            }}
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                width: 10px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background-color: {p['muted']};
                border-radius: 5px;
                min-height: 34px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 0)
        root.setSpacing(18)

        header = QHBoxLayout()
        title = QLabel("Historico de transferencias")
        title.setObjectName("downloadsTitle")
        self.search = QLineEdit()
        self.search.setObjectName("downloadSearch")
        self.search.setPlaceholderText("Pesquise o historico de transferencias")
        self.search.textChanged.connect(self._load_downloads)
        clear_btn = QPushButton("Limpar tudo")
        clear_btn.setObjectName("topAction")
        clear_btn.clicked.connect(self._clear_downloads)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search)
        header.addStretch()
        header.addWidget(clear_btn)
        root.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        host = QWidget()
        host.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        host.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(host)
        self.list_layout.setContentsMargins(0, 0, 0, 30)
        self.list_layout.setSpacing(10)
        scroll.setWidget(host)
        root.addWidget(scroll, 1)
        self._load_downloads()

    def _clear_rows(self) -> None:
        self.rows.clear()
        if not self.list_layout:
            return
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _load_downloads(self, *_args) -> None:
        if not self.list_layout:
            return
        self.setUpdatesEnabled(False)
        try:
            self._clear_rows()
            query = self.search.text().strip().lower() if hasattr(self, "search") else ""
            downloads = [item for item in self.download_manager.get_all_downloads()
                         if not query or query in (os.path.basename(item.path()) or "").lower()]

            if not downloads:
                self.selected_download = None
                empty = QLabel("Nenhuma transferencia para mostrar.")
                empty.setObjectName("emptyDownloads")
                empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty.setMinimumHeight(360)
                self.list_layout.addWidget(empty)
                self.list_layout.addStretch()
                return

            day_label = QLabel("Recentes")
            day_label.setObjectName("dateLabel")
            day_label.setMaximumWidth(720)
            self.list_layout.addWidget(day_label, 0, Qt.AlignmentFlag.AlignHCenter)

            if self.selected_download not in downloads:
                self.selected_download = downloads[0]
            for item in downloads:
                self.list_layout.addWidget(self._create_download_row(item), 0, Qt.AlignmentFlag.AlignHCenter)
            self.list_layout.addStretch()
        finally:
            self.setUpdatesEnabled(True)
            self.update()

    def _create_download_row(self, item: QWebEngineDownloadItem) -> QFrame:
        row = QFrame()
        row.setObjectName("downloadRow")
        row.setProperty("selected", item == self.selected_download)
        row.setFixedWidth(700)
        row.setMinimumHeight(74)
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.mousePressEvent = lambda event, download=item, frame=row: self._select_download(download, frame)
        self.rows.append(row)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(18, 12, 12, 12)
        layout.setSpacing(16)
        file_icon = QLabel("[ ]")
        file_icon.setObjectName("fileIcon")
        layout.addWidget(file_icon)

        info = QVBoxLayout()
        filename = QLabel(os.path.basename(item.path()) or "download")
        filename.setObjectName("fileTitle")
        filename.setWordWrap(True)
        meta = QLabel(self._meta_text(item))
        meta.setObjectName("fileMeta")
        info.addWidget(filename)
        info.addWidget(meta)
        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadInProgress:
            info.addWidget(self._progress_bar(item))
        layout.addLayout(info, 1)

        open_btn = QPushButton("Abrir")
        open_btn.setObjectName("rowAction")
        open_btn.setToolTip("Abrir arquivo")
        open_btn.clicked.connect(lambda checked=False, download=item: self._open_download(download))
        folder_btn = QPushButton("Pasta")
        folder_btn.setObjectName("rowAction")
        folder_btn.setToolTip("Abrir pasta")
        folder_btn.clicked.connect(lambda checked=False, download=item: self._open_download_folder(download))
        layout.addWidget(open_btn)
        layout.addWidget(folder_btn)
        return row

    def _progress_bar(self, item: QWebEngineDownloadItem) -> QProgressBar:
        bar = QProgressBar()
        bar.setTextVisible(False)
        percent = 0
        if item.totalBytes() > 0:
            percent = max(0, min(100, int((item.receivedBytes() / item.totalBytes()) * 100)))
        bar.setValue(percent)
        return bar

    def _meta_text(self, item: QWebEngineDownloadItem) -> str:
        return f"{self._format_file_size(item.totalBytes())}  {self._status_text(item)}"

    def _select_download(self, item: QWebEngineDownloadItem, selected_row: QFrame) -> None:
        self.selected_download = item
        for row in self.rows:
            row.setProperty("selected", row is selected_row)
            row.style().unpolish(row)
            row.style().polish(row)

    def _clear_downloads(self) -> None:
        self.download_manager.completed_downloads.clear()
        self._load_downloads()

    def _is_finished(self, item: Optional[QWebEngineDownloadItem]) -> bool:
        return bool(item and item.state() == QWebEngineDownloadItem.DownloadState.DownloadFinished)

    def _status_text(self, item: QWebEngineDownloadItem) -> str:
        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadFinished:
            return "Concluido"
        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadInProgress:
            if item.totalBytes() > 0:
                return f"Baixando {int((item.receivedBytes() / item.totalBytes()) * 100)}%"
            return "Baixando"
        if item.state() == QWebEngineDownloadItem.DownloadState.DownloadInterrupted:
            return "Eliminado"
        return "Aguardando"

    def _format_file_size(self, size: int) -> str:
        if size <= 0:
            return "Tamanho desconhecido"
        value = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} PB"

    def _open_download(self, item: Optional[QWebEngineDownloadItem] = None) -> None:
        download = item or self.selected_download
        if not self._is_finished(download):
            self._show_notification("Download ainda nao concluido", error=True)
            return
        try:
            os.startfile(download.path())
        except Exception as e:
            self._show_notification(f"Nao foi possivel abrir: {e}", error=True)

    def _open_download_folder(self, item: Optional[QWebEngineDownloadItem] = None) -> None:
        try:
            download = item or self.selected_download
            folder = os.path.dirname(download.path()) if download else self.download_manager.download_path
            os.startfile(folder)
        except Exception as e:
            self._show_notification(f"Nao foi possivel abrir a pasta: {e}", error=True)

    def _show_notification(self, message: str, error: bool = False) -> None:
        p = self.palette
        notification = QLabel(message, self)
        notification.setStyleSheet(f"""
            QLabel {{
                background-color: {p['error'] if error else p['success']};
                color: white;
                padding: 10px 16px;
                border-radius: 8px;
                font-weight: 700;
            }}
        """)
        notification.adjustSize()
        notification.move((self.width() - notification.width()) // 2, 24)
        notification.show()
        QTimer.singleShot(2400, notification.deleteLater)
