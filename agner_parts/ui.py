# --- Base Dialog Class for Theming ---
class ThemedDialog(QDialog):
    def __init__(self, theme: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.theme = theme
        self._apply_dialog_theme()

    def _apply_dialog_theme(self) -> None:
        self.setStyleSheet(f"""
            ThemedDialog, QDialog {{
                background-color: {self.theme['dialog_bg']};
                color: {self.theme['dialog_text']};
            }}
            QLabel {{
                color: {self.theme['dialog_text']};
            }}
            QLineEdit, QComboBox, QSpinBox, QTextEdit, QListWidget {{
                background-color: {self.theme['dialog_input_bg']};
                color: {self.theme['dialog_text']};
                border: 1px solid {self.theme['divider']};
                border-radius: 8px;
                padding: 8px;
                selection-background-color: {self.theme['accent']};
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {{
                border: 1px solid {self.theme['accent']};
            }}
            QPushButton {{
                background-color: {self.theme['dialog_button_bg']};
                color: {self.theme['dialog_text']};
                border: 1px solid {self.theme['divider']};
                border-radius: 8px;
                padding: 9px 15px;
                min-height: 30px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {self.theme['dialog_button_hover']};
            }}
            QCheckBox {{
                color: {self.theme['dialog_text']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid {self.theme['divider']};
                background-color: {self.theme['dialog_input_bg']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.theme['accent']};
                border: 1px solid {self.theme['accent']};
            }}
            QTabWidget::pane {{
                border: 1px solid {self.theme['divider']};
                border-radius: 8px;
                background-color: {self.theme['card_bg']};
                margin-top: 8px;
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {self.theme['secondary_text']};
                border: none;
                border-bottom: 2px solid transparent;
                padding: 10px 16px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                color: {self.theme['primary_text']};
                border-bottom: 2px solid {self.theme['accent']};
            }}
            QListWidget::item {{
                background-color: {self.theme['card_bg']};
                color: {self.theme['primary_text']};
                border: 1px solid {self.theme['divider']};
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }}
            QListWidget::item:selected {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['primary_text']};
                border: 1px solid {self.theme['accent']};
            }}
            QDialogButtonBox QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: 1px solid {self.theme['accent']};
            }}
            QDialogButtonBox QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
            QDialogButtonBox QPushButton#qt_msgbox_buttonbox_No,
            QDialogButtonBox QPushButton#qt_msgbox_buttonbox_Cancel {{
                background-color: {self.theme['dialog_button_bg']};
                color: {self.theme['dialog_text']};
            }}
            QDialog QDialogButtonBox QPushButton#qt_msgbox_buttonbox_No:hover,
            QDialog QDialogButtonBox QPushButton#qt_msgbox_buttonbox_Cancel:hover {{
                background-color: {self.theme['dialog_button_hover']};
            }}
        """)

# --- Bookmarks Dialog ---
class BookmarksDialog(ThemedDialog):
    def __init__(self, bookmark_manager: 'BookmarkManager', theme: dict, parent: Optional[QWidget] = None):
        super().__init__(theme, parent)
        self.bookmark_manager = bookmark_manager
        self.setWindowTitle("Favoritos - AGNER")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        self._init_ui()
        self._load_bookmarks()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QHBoxLayout()
        title = QLabel("Seus Favoritos")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['primary_text']};")

        self.add_btn = QPushButton("Adicionar")
        self.add_btn.clicked.connect(self._add_bookmark)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.add_btn)

        self.bookmarks_list = QListWidget()
        self.bookmarks_list.setAlternatingRowColors(True)
        self.bookmarks_list.setViewMode(QListView.ViewMode.IconMode)
        self.bookmarks_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.bookmarks_list.setMovement(QListView.Movement.Static)
        self.bookmarks_list.setGridSize(QSize(250, 94))
        self.bookmarks_list.setSpacing(10)

        buttons = QHBoxLayout()
        self.edit_btn = QPushButton("Editar")
        self.delete_btn = QPushButton("Excluir")
        self.visit_btn = QPushButton("Visitar")

        self.edit_btn.clicked.connect(self._edit_bookmark)
        self.delete_btn.clicked.connect(self._delete_bookmark)
        self.visit_btn.clicked.connect(self._visit_bookmark)

        buttons.addWidget(self.edit_btn)
        buttons.addWidget(self.delete_btn)
        buttons.addStretch()
        buttons.addWidget(self.visit_btn)

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)

        layout.addLayout(header)
        layout.addWidget(self.bookmarks_list)
        layout.addLayout(buttons)
        layout.addWidget(close_btn)

    def _load_bookmarks(self) -> None:
        self.bookmarks_list.clear()
        bookmarks = self.bookmark_manager.get_all_bookmarks()

        for bookmark in bookmarks:
            item = QListWidgetItem()
            item.setText(f"{bookmark['title']}\n{bookmark['url']}")
            item.setData(Qt.ItemDataRole.UserRole, bookmark)
            self.bookmarks_list.addItem(item)

    def _add_bookmark(self) -> None:
        title, ok1 = QInputDialog.getText(self, "Novo Favorito", "Título:")
        if not ok1 or not title.strip():
            return

        url, ok2 = QInputDialog.getText(self, "Novo Favorito", "URL:")
        if not ok2 or not url.strip():
            return

        if self.bookmark_manager.add_bookmark(title.strip(), url.strip()):
            self._load_bookmarks()
        else:
            QMessageBox.warning(self, "Erro", "Não foi possível adicionar o favorito.")

    def _edit_bookmark(self) -> None:
        current = self.bookmarks_list.currentItem()
        if not current:
            return

        bookmark = current.data(Qt.ItemDataRole.UserRole)

        title, ok1 = QInputDialog.getText(self, "Editar Favorito", "Título:", text=bookmark['title'])
        if not ok1:
            return

        url, ok2 = QInputDialog.getText(self, "Editar Favorito", "URL:", text=bookmark['url'])
        if not ok2:
            return

        if self.bookmark_manager.add_bookmark(title.strip(), url.strip()):
            self._load_bookmarks()

    def _delete_bookmark(self) -> None:
        current = self.bookmarks_list.currentItem()
        if not current:
            return

        bookmark = current.data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self, "Confirmar",
            f"Excluir o favorito '{bookmark['title']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.bookmark_manager.remove_bookmark(bookmark['url']):
                self._load_bookmarks()

    def _visit_bookmark(self) -> None:
        current = self.bookmarks_list.currentItem()
        if not current:
            return

        bookmark = current.data(Qt.ItemDataRole.UserRole)

        # Emitir sinal para a janela principal navegar
        parent_window = self.parent()
        if isinstance(parent_window, SafeMainWindow):  # Type check for parent
            parent_window.navigate_to_url_direct(bookmark['url'])
            self.accept()


# --- Extensions Dialog ---
class ExtensionsDialog(ThemedDialog):
    def __init__(self, extension_manager: 'ExtensionManager', theme: dict, parent: Optional[QWidget] = None):
        super().__init__(theme, parent)
        self.extension_manager = extension_manager
        self.setWindowTitle("Extensões - AGNER")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        self._init_ui()
        self._load_extensions()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QHBoxLayout()
        title = QLabel("Suas Extensões")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['primary_text']};")

        self.add_btn = QPushButton("Instalar Extensão")
        self.add_btn.clicked.connect(self._install_extension)

        self.store_btn = QPushButton("Chrome Web Store")
        self.store_btn.clicked.connect(self._open_store)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.store_btn)
        header.addWidget(self.add_btn)

        self.extensions_list = QListWidget()
        self.extensions_list.setAlternatingRowColors(True)
        self.extensions_list.setViewMode(QListView.ViewMode.IconMode)
        self.extensions_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.extensions_list.setMovement(QListView.Movement.Static)
        self.extensions_list.setGridSize(QSize(250, 94))
        self.extensions_list.setSpacing(10)

        buttons = QHBoxLayout()
        self.remove_btn = QPushButton("Remover")

        self.remove_btn.clicked.connect(self._remove_extension)

        buttons.addWidget(self.remove_btn)
        buttons.addStretch()

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)

        layout.addLayout(header)
        layout.addWidget(self.extensions_list)
        layout.addLayout(buttons)
        layout.addWidget(close_btn)

    def _load_extensions(self) -> None:
        self.extensions_list.clear()
        for ext_id, manifest in self.extension_manager.extensions.items():
            name = manifest.get('name', 'Sem nome')
            version = manifest.get('version', 'N/A')
            item = QListWidgetItem(f"{name} (v{version})")
            item.setData(Qt.ItemDataRole.UserRole, ext_id)
            self.extensions_list.addItem(item)

    def _install_extension(self) -> None:
        zip_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Extensão", "", "ZIP Files (*.zip)")
        if zip_path:
            ext_id = self.extension_manager.install_extension(zip_path)
            if ext_id:
                self._load_extensions()
                QMessageBox.information(self, "Sucesso",
                                        "Extensão instalada com sucesso! Reinicie o navegador para aplicar.")
            else:
                QMessageBox.warning(self, "Erro", "Falha ao instalar extensão.")

    def _remove_extension(self) -> None:
        current = self.extensions_list.currentItem()
        if not current:
            return

        ext_id = current.data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self, "Confirmar",
            f"Remover a extensão '{ext_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.extension_manager.uninstall_extension(ext_id)
            self._load_extensions()

    def _open_store(self) -> None:
        parent_window = self.parent()
        if isinstance(parent_window, SafeMainWindow):  # Type check for parent
            parent_window.navigate_to_url_direct("https://chromewebstore.google.com")


# --- Settings Dialog Funcional ---
class FunctionalSettingsDialog(ThemedDialog):
    theme_changed = pyqtSignal(str)
    settings_applied = pyqtSignal()

    def __init__(self, settings_manager: 'SettingsManager', theme: dict, parent: Optional[QWidget] = None):
        super().__init__(theme, parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Configurações - AGNER")
        self.setMinimumSize(760, 620)
        self.setModal(True)

        self._init_ui()
        self._load_current_settings()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        self.tabs = QTabWidget()

        # Aba Geral
        general_tab = QWidget()
        general_form = QFormLayout(general_tab)
        general_form.setSpacing(15)
        self.homepage_input = QLineEdit()
        self.homepage_input.setPlaceholderText("about:home ou https://...")
        general_form.addRow("Página inicial:", self.homepage_input)
        self.search_engine_input = QLineEdit()
        self.search_engine_input.setPlaceholderText("Ex: https://www.google.com/search?q=")
        general_form.addRow("Motor de busca:", self.search_engine_input)
        self.startup_combo = QComboBox()
        self.startup_combo.addItems(["Última sessão", "Página inicial", "Página em branco"])
        general_form.addRow("Ao iniciar:", self.startup_combo)
        self.save_history_check = QCheckBox("Salvar histórico de navegação")
        general_form.addRow(self.save_history_check)
        self.block_ads_check = QCheckBox("Bloquear anúncios e rastreadores")
        general_form.addRow(self.block_ads_check)
        self.gamer_mode_check = QCheckBox("Modo gamer leve")
        general_form.addRow(self.gamer_mode_check)
        self.auto_close_popups_check = QCheckBox("Fechar banners e pop-ups automaticamente")
        general_form.addRow(self.auto_close_popups_check)
        self.enable_javascript_check = QCheckBox("Habilitar JavaScript (requer reinício)")
        general_form.addRow(self.enable_javascript_check)

        # Clear browsing data button
        clear_data_btn = QPushButton("Limpar Dados de Navegação")
        clear_data_btn.setIcon(SafeIconProvider.get_icon(SVG_ICONS['clear_data'], self.theme['icon_color']))
        clear_data_btn.clicked.connect(self._clear_browsing_data)
        general_form.addRow(clear_data_btn)

        self.tabs.addTab(general_tab, "Geral")

        # Aba Aparência
        appearance_tab = QWidget()
        appearance_form = QFormLayout(appearance_tab)
        appearance_form.setSpacing(15)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.currentTextChanged.connect(self.theme_changed.emit)
        appearance_form.addRow("Tema:", self.theme_combo)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 24)
        self.font_size_spin.setSuffix(" px")
        appearance_form.addRow("Tamanho da fonte (UI):", self.font_size_spin)
        self.zoom_factor_spin = QSpinBox()
        self.zoom_factor_spin.setRange(50, 200)
        self.zoom_factor_spin.setSuffix("%")
        appearance_form.addRow("Zoom padrão (Páginas):", self.zoom_factor_spin)
        self.enable_dark_mode_check = QCheckBox("Forçar modo escuro em sites (experimental, requer reinício)")
        appearance_form.addRow(self.enable_dark_mode_check)

        self.tabs.addTab(appearance_tab, "Aparência")

        layout.addWidget(self.tabs)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply_settings)
        layout.addWidget(buttons)

    def _load_current_settings(self) -> None:
        try:
            self.homepage_input.setText(self.settings_manager.get("homepage", "about:home"))
            self.search_engine_input.setText(
                self.settings_manager.get("search_engine", "https://www.google.com/search?q="))
            startup_mode = self.settings_manager.get("startup_mode", "homepage")
            startup_map = {"last_session": "Última sessão", "homepage": "Página inicial",
                           "blank": "Página em branco"}  # Corrected "Página em branco"
            self.startup_combo.setCurrentText(startup_map.get(startup_mode, "Última sessão"))

            self.save_history_check.setChecked(self.settings_manager.get("save_history", True, type=bool))
            self.block_ads_check.setChecked(self.settings_manager.get("block_ads", True, type=bool))
            self.gamer_mode_check.setChecked(self.settings_manager.get("gamer_mode", True, type=bool))
            self.auto_close_popups_check.setChecked(self.settings_manager.get("auto_close_popups", False, type=bool))
            self.enable_javascript_check.setChecked(self.settings_manager.get("enable_javascript", True, type=bool))
            self.enable_dark_mode_check.setChecked(self.settings_manager.get("enable_dark_mode", False, type=bool))

            theme_name = self.settings_manager.get("theme", "chrome_clean")
            self.theme_combo.setCurrentText(theme_name if theme_name in THEMES else "chrome_clean")
            self.font_size_spin.setValue(self.settings_manager.get("font_size", 14, type=int))
            self.zoom_factor_spin.setValue(int(self.settings_manager.get("zoom_factor", 1.0, type=float) * 100))
        except Exception as e:
            print(f"Erro carregando configurações: {e}")

    def _apply_settings(self) -> None:
        print("[SettingsDialog] Aplicando configurações...")
        try:
            self.settings_manager.set("homepage", self.homepage_input.text().strip() or "about:home")
            self.settings_manager.set("search_engine",
                                      self.search_engine_input.text().strip() or "https://www.google.com/search?q=")
            startup_map = {"Última sessão": "last_session", "Página inicial": "homepage", "Página em branco": "blank"}
            self.settings_manager.set("startup_mode", startup_map[self.startup_combo.currentText()])
            self.settings_manager.set("save_history", self.save_history_check.isChecked())
            self.settings_manager.set("block_ads", self.block_ads_check.isChecked())
            self.settings_manager.set("gamer_mode", self.gamer_mode_check.isChecked())
            self.settings_manager.set("auto_close_popups", self.auto_close_popups_check.isChecked())
            self.settings_manager.set("enable_javascript", self.enable_javascript_check.isChecked())
            self.settings_manager.set("enable_dark_mode", self.enable_dark_mode_check.isChecked())

            self.settings_manager.set("theme", self.theme_combo.currentText())
            self.settings_manager.set("font_size", self.font_size_spin.value())
            self.settings_manager.set("zoom_factor", self.zoom_factor_spin.value() / 100.0)

            self.settings_applied.emit()
            print("[SettingsDialog] Sinal settings_applied emitido.")

            apply_button = self.sender()
            if isinstance(apply_button, QPushButton):
                original_text = apply_button.text()
                apply_button.setText("Aplicado")

                # Solução segura para restaurar o texto depois do feedback visual.
                def restore_text():
                    try:
                        # Verifica se o botão ainda existe E não foi deletado
                        if apply_button and hasattr(apply_button, 'setText'):
                            apply_button.setText(original_text)
                    except (RuntimeError, AttributeError):
                        # Se o botão foi deletado, só ignora graciosamente
                        print("[SettingsDialog] Botão já foi deletado, ignorando restore.")
                        pass

                QTimer.singleShot(1500, restore_text)

        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao salvar configurações: {str(e)}")

    def _clear_browsing_data(self) -> None:
        reply = QMessageBox.question(self, "Limpar Dados de Navegação",
                                     "Isso removerá cookies, cache, e outros dados de sites.\n"
                                     "Você pode precisar reiniciar o navegador para que todas as mudanças sejam aplicadas. Deseja continuar?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            parent_window = self.parent()
            if isinstance(parent_window, SafeMainWindow):
                parent_window._clear_browser_profile_data()
                QMessageBox.information(self, "Dados Limpos",
                                        "Dados de navegação foram limpos. Reinicie o navegador para aplicar completamente.")
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível acessar a função de limpeza de dados.")

    def accept(self) -> None:
        self._apply_settings()
        super().accept()


# --- Profile Manager Dialog ---
class ProfileManagerDialog(ThemedDialog):
    profile_switched = pyqtSignal(str)

    def __init__(self, settings_manager: 'SettingsManager', theme: dict, parent: Optional[QWidget] = None):
        super().__init__(theme, parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Gerenciar Perfis - AGNER")
        self.setMinimumSize(400, 300)
        self.setModal(True)

        self._init_ui()
        self._load_profiles()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Seus Perfis")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['primary_text']};")
        layout.addWidget(title)

        self.profile_list = QListWidget()
        self.profile_list.setViewMode(QListView.ViewMode.IconMode)
        self.profile_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.profile_list.setMovement(QListView.Movement.Static)
        self.profile_list.setGridSize(QSize(180, 82))
        self.profile_list.setSpacing(10)
        layout.addWidget(self.profile_list)

        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("Novo Perfil")
        self.switch_btn = QPushButton("Trocar para")
        self.delete_btn = QPushButton("Excluir Perfil")

        self.add_btn.clicked.connect(self._add_profile)
        self.switch_btn.clicked.connect(self._switch_profile)
        self.delete_btn.clicked.connect(self._delete_profile)

        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.switch_btn)
        buttons_layout.addWidget(self.delete_btn)
        layout.addLayout(buttons_layout)

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _load_profiles(self) -> None:
        self.profile_list.clear()
        profiles = self.settings_manager.get_all_profiles()
        current_profile = self.settings_manager.get_current_profile_name()

        for profile_name in profiles:
            item = QListWidgetItem(profile_name)
            if profile_name == current_profile:
                item.setText(f"{profile_name} (Atual)")
                item.setFlags(
                    item.flags() & ~Qt.ItemFlag.ItemIsSelectable)  # Make current profile non-selectable for switching
            self.profile_list.addItem(item)

    def _add_profile(self) -> None:
        profile_name, ok = QInputDialog.getText(self, "Novo Perfil", "Nome do novo perfil:")
        if ok and profile_name.strip():
            profile_name = profile_name.strip()
            if self.settings_manager.add_profile(profile_name):
                self._load_profiles()
                QMessageBox.information(self, "Sucesso", f"Perfil '{profile_name}' criado.")
            else:
                QMessageBox.warning(self, "Erro", f"Perfil '{profile_name}' já existe ou nome inválido.")

    def _switch_profile(self) -> None:
        current_item = self.profile_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Trocar Perfil", "Selecione um perfil para trocar.")
            return

        profile_name = current_item.text().replace(" (Atual)", "")
        if profile_name == self.settings_manager.get_current_profile_name():
            QMessageBox.information(self, "Trocar Perfil", "Este já é o perfil ativo.")
            return

        reply = QMessageBox.question(self, "Trocar Perfil",
                                     f"Deseja trocar para o perfil '{profile_name}'? O navegador será reiniciado.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.set_current_profile(profile_name)
            self.profile_switched.emit(profile_name)
            self.accept()  # Close dialog

    def _delete_profile(self) -> None:
        current_item = self.profile_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Excluir Perfil", "Selecione um perfil para excluir.")
            return

        profile_name = current_item.text().replace(" (Atual)", "")
        if profile_name == self.settings_manager.get_current_profile_name():
            QMessageBox.warning(self, "Excluir Perfil", "Não é possível excluir o perfil ativo.")
            return

        reply = QMessageBox.question(self, "Excluir Perfil",
                                     f"Tem certeza que deseja excluir o perfil '{profile_name}' e todos os seus dados (histórico, favoritos, senhas)? Esta ação é irreversível.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.settings_manager.delete_profile(profile_name):
                self._load_profiles()
                QMessageBox.information(self, "Sucesso", f"Perfil '{profile_name}' excluído.")
            else:
                QMessageBox.warning(self, "Erro", f"Não foi possível excluir o perfil '{profile_name}'.")


# --- DevTools Window ---
class DevToolsWindow(QMainWindow):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("AGNER DevTools")
        self.setGeometry(100, 100, 800, 600)
        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)
        self.setWindowIcon(SafeIconProvider.get_icon(SVG_ICONS['settings'], "#ffffff"))

        if parent and hasattr(parent, 'theme'):
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-color: {getattr(parent, 'theme')['dialog_bg']};
                    color: {getattr(parent, 'theme')['dialog_text']};
                    border-radius: 12px;
                }}
            """)
        print("[DevToolsWindow] Janela de DevTools inicializada.")


# --- Chrome-style replacement dialogs ---
class ExtensionsDialog(ThemedDialog):
    def __init__(self, extension_manager: 'ExtensionManager', theme: dict, parent: Optional[QWidget] = None):
        super().__init__(theme, parent)
        self.extension_manager = extension_manager
        self.setWindowTitle("Chrome Web Store - AGNER")
        self.setMinimumSize(1080, 720)
        self.setModal(True)
        self._init_ui()
        self._load_extensions()

    def _init_ui(self) -> None:
        self.setStyleSheet(f"""
            ExtensionsDialog {{
                background-color: #ffffff;
                color: #202124;
            }}
            QLabel#storeBrand {{
                color: #3c4043;
                font-size: 15px;
                font-weight: 600;
            }}
            QLabel#tabLabel {{
                color: #5f6368;
                padding: 10px 14px;
                font-weight: 700;
            }}
            QLabel#tabLabel[selected="true"] {{
                color: #1a73e8;
                border-bottom: 3px solid #1a73e8;
            }}
            QLineEdit#storeSearch {{
                background-color: #f1f3f4;
                color: #202124;
                border: 1px solid transparent;
                border-radius: 20px;
                padding: 10px 18px;
                min-width: 420px;
            }}
            QFrame#hero {{
                background-color: #062a62;
                border-radius: 20px;
            }}
            QLabel#heroTitle {{
                color: white;
                font-size: 28px;
                font-weight: 800;
            }}
            QLabel#heroText {{
                color: #dbeafe;
                font-size: 14px;
            }}
            QPushButton#primaryStore {{
                background-color: #0b57d0;
                color: white;
                border: none;
                border-radius: 18px;
                padding: 9px 18px;
                font-weight: 700;
            }}
            QPushButton#outlineStore {{
                background-color: transparent;
                color: #0b57d0;
                border: 1px solid #0b57d0;
                border-radius: 18px;
                padding: 9px 18px;
                font-weight: 700;
            }}
            QListWidget#extensionGrid {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget#extensionGrid::item {{
                background-color: #f1f3f4;
                color: #202124;
                border: 1px solid #e0e3e7;
                border-radius: 12px;
                padding: 14px;
                margin: 8px;
            }}
            QListWidget#extensionGrid::item:selected {{
                background-color: #e8f0fe;
                border: 1px solid #1a73e8;
            }}
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(22)

        header = QHBoxLayout()
        brand = QLabel("chrome web store")
        brand.setObjectName("storeBrand")
        search = QLineEdit()
        search.setObjectName("storeSearch")
        search.setPlaceholderText("Search extensions and themes")
        close_btn = QPushButton("Sign in")
        close_btn.setObjectName("primaryStore")
        close_btn.clicked.connect(self.accept)
        header.addWidget(brand)
        header.addStretch()
        header.addWidget(search)
        header.addStretch()
        header.addWidget(close_btn)
        root.addLayout(header)

        tabs = QHBoxLayout()
        for text, selected in (("Discover", True), ("Extensions", False), ("Themes", False)):
            label = QLabel(text)
            label.setObjectName("tabLabel")
            label.setProperty("selected", selected)
            tabs.addWidget(label)
        tabs.addStretch()
        root.addLayout(tabs)

        hero = QFrame()
        hero.setObjectName("hero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(42, 34, 42, 34)
        copy = QVBoxLayout()
        hero_title = QLabel("Extensions for AGNER")
        hero_title.setObjectName("heroTitle")
        hero_text = QLabel("Manage local extensions, install ZIP packages and open the Chrome Web Store.")
        hero_text.setObjectName("heroText")
        hero_text.setWordWrap(True)
        copy.addWidget(hero_title)
        copy.addWidget(hero_text)
        hero_actions = QHBoxLayout()
        self.store_btn = QPushButton("Chrome Web Store")
        self.store_btn.setObjectName("outlineStore")
        self.store_btn.clicked.connect(self._open_store)
        self.add_btn = QPushButton("Install extension")
        self.add_btn.setObjectName("primaryStore")
        self.add_btn.clicked.connect(self._install_extension)
        hero_actions.addWidget(self.store_btn)
        hero_actions.addWidget(self.add_btn)
        copy.addLayout(hero_actions)
        hero_layout.addLayout(copy, 1)
        root.addWidget(hero)

        section = QHBoxLayout()
        heading = QLabel("Installed extensions")
        heading.setStyleSheet("font-size: 22px; font-weight: 800; color: #202124;")
        self.remove_btn = QPushButton("Remove selected")
        self.remove_btn.setObjectName("outlineStore")
        self.remove_btn.clicked.connect(self._remove_extension)
        section.addWidget(heading)
        section.addStretch()
        section.addWidget(self.remove_btn)
        root.addLayout(section)

        self.extensions_list = QListWidget()
        self.extensions_list.setObjectName("extensionGrid")
        self.extensions_list.setViewMode(QListView.ViewMode.IconMode)
        self.extensions_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.extensions_list.setMovement(QListView.Movement.Static)
        self.extensions_list.setGridSize(QSize(260, 150))
        self.extensions_list.setSpacing(8)
        root.addWidget(self.extensions_list, 1)

    def _load_extensions(self) -> None:
        self.extensions_list.clear()
        if not self.extension_manager.extensions:
            item = QListWidgetItem("No extensions installed\nUse Install extension to add a ZIP package.")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.extensions_list.addItem(item)
            return
        for ext_id, manifest in self.extension_manager.extensions.items():
            name = manifest.get('name', 'Unnamed extension')
            version = manifest.get('version', 'N/A')
            item = QListWidgetItem(f"{name}\nVersion {version}\nLocal package")
            item.setData(Qt.ItemDataRole.UserRole, ext_id)
            self.extensions_list.addItem(item)

    def _install_extension(self) -> None:
        zip_path, _ = QFileDialog.getOpenFileName(self, "Selecionar extensao", "", "ZIP Files (*.zip)")
        if zip_path:
            ext_id = self.extension_manager.install_extension(zip_path)
            if ext_id:
                self._load_extensions()
                QMessageBox.information(self, "Extensao instalada", "Reinicie o navegador para aplicar.")
            else:
                QMessageBox.warning(self, "Erro", "Falha ao instalar extensao.")

    def _remove_extension(self) -> None:
        current = self.extensions_list.currentItem()
        if not current:
            return
        ext_id = current.data(Qt.ItemDataRole.UserRole)
        if not ext_id:
            return
        if QMessageBox.question(self, "Confirmar", f"Remover a extensao '{ext_id}'?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.extension_manager.uninstall_extension(ext_id)
            self._load_extensions()

    def _open_store(self) -> None:
        parent_window = self.parent()
        if isinstance(parent_window, SafeMainWindow):
            parent_window.navigate_to_url_direct("https://chromewebstore.google.com")
            self.accept()


class FunctionalSettingsDialog(ThemedDialog):
    theme_changed = pyqtSignal(str)
    settings_applied = pyqtSignal()

    def __init__(self, settings_manager: 'SettingsManager', theme: dict, parent: Optional[QWidget] = None):
        super().__init__(theme, parent)
        self.settings_manager = settings_manager
        self.nav_buttons: List[QPushButton] = []
        self.setWindowTitle("Definicoes - AGNER")
        self.setMinimumSize(980, 700)
        self.setModal(True)
        self._init_ui()
        self._load_current_settings()

    def _init_ui(self) -> None:
        p = _chrome_palette(self.theme)
        bg = p['page']
        card = p['surface']
        text = p['text']
        muted = p['muted']
        border = p['border']
        accent = p['accent']
        input_bg = p['input']
        selected_bg = p['selection']
        button_bg = p['surface_soft']
        self.setStyleSheet(f"""
            FunctionalSettingsDialog {{
                background-color: {bg};
                color: {text};
            }}
            QLabel#settingsTitle {{
                color: {text};
                font-size: 24px;
                font-weight: 800;
            }}
            QLabel#sectionTitle {{
                color: {text};
                font-size: 16px;
                font-weight: 800;
            }}
            QLabel#muted {{
                color: {muted};
            }}
            QFrame#settingsCard {{
                background-color: {card};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QPushButton#navButton {{
                background: transparent;
                border: none;
                border-radius: 18px;
                color: {text};
                padding: 10px 14px;
                text-align: left;
                font-weight: 650;
            }}
            QPushButton#navButton:checked {{
                background-color: {selected_bg};
                color: {accent};
            }}
            QLineEdit, QComboBox, QSpinBox {{
                background-color: {input_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px 10px;
            }}
            QCheckBox {{
                color: {text};
                spacing: 10px;
            }}
            QPushButton#primarySettings {{
                background-color: {accent};
                color: white;
                border: none;
                border-radius: 18px;
                padding: 9px 18px;
                font-weight: 700;
            }}
            QPushButton#ghostSettings {{
                background-color: transparent;
                color: {accent};
                border: 1px solid {accent};
                border-radius: 18px;
                padding: 9px 18px;
                font-weight: 700;
            }}
            QPushButton#ghostSettings:hover, QPushButton#navButton:hover {{
                background-color: {button_bg};
            }}
        """)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 24, 18, 24)
        title = QLabel("Definicoes")
        title.setObjectName("settingsTitle")
        sidebar_layout.addWidget(title)
        for index, label in enumerate(["Eu e a AGNER", "Privacidade", "Desempenho", "No arranque", "Aspecto"]):
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, page=index: self._select_page(page))
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)
        sidebar_layout.addStretch()
        root.addWidget(sidebar)

        content = QVBoxLayout()
        content.setContentsMargins(34, 24, 34, 24)
        search = QLineEdit()
        search.setPlaceholderText("Pesquise definicoes")
        search.setMaximumWidth(560)
        content.addWidget(search, 0, Qt.AlignmentFlag.AlignHCenter)
        self.pages = QStackedWidget()
        self.pages.addWidget(self._profile_page())
        self.pages.addWidget(self._privacy_page())
        self.pages.addWidget(self._performance_page())
        self.pages.addWidget(self._startup_page())
        self.pages.addWidget(self._appearance_page())
        content.addWidget(self.pages, 1)

        actions = QHBoxLayout()
        actions.addStretch()
        cancel = QPushButton("Cancelar")
        cancel.setObjectName("ghostSettings")
        cancel.clicked.connect(self.reject)
        apply_btn = QPushButton("Aplicar")
        apply_btn.setObjectName("primarySettings")
        apply_btn.clicked.connect(self._apply_settings)
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primarySettings")
        ok_btn.clicked.connect(self.accept)
        actions.addWidget(cancel)
        actions.addWidget(apply_btn)
        actions.addWidget(ok_btn)
        content.addLayout(actions)
        root.addLayout(content, 1)
        self._select_page(0)

    def _select_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def _card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("settingsCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)
        return frame, layout

    def _profile_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 26, 0, 0)
        card, body = self._card("Eu e a AGNER")
        body.addWidget(QLabel(f"Perfil atual: {self.settings_manager.get_current_profile_name()}"))
        note = QLabel("Sincronizacao local de favoritos, historico, downloads e extensoes.")
        note.setObjectName("muted")
        body.addWidget(note)
        layout.addWidget(card)
        layout.addStretch()
        return page

    def _privacy_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 26, 0, 0)
        card, body = self._card("Privacidade e seguranca")
        self.save_history_check = QCheckBox("Salvar historico de navegacao")
        self.block_ads_check = QCheckBox("Bloquear anuncios e rastreadores")
        self.auto_close_popups_check = QCheckBox("Fechar banners e pop-ups automaticamente")
        clear_data_btn = QPushButton("Limpar dados de navegacao")
        clear_data_btn.setObjectName("ghostSettings")
        clear_data_btn.clicked.connect(self._clear_browsing_data)
        for widget in (self.save_history_check, self.block_ads_check, self.auto_close_popups_check, clear_data_btn):
            body.addWidget(widget)
        layout.addWidget(card)
        layout.addStretch()
        return page

    def _performance_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 26, 0, 0)
        card, body = self._card("Desempenho")
        self.gamer_mode_check = QCheckBox("Modo leve para reduzir travadas")
        self.enable_javascript_check = QCheckBox("Habilitar JavaScript")
        self.enable_dark_mode_check = QCheckBox("Forcar modo escuro em sites")
        for widget in (self.gamer_mode_check, self.enable_javascript_check, self.enable_dark_mode_check):
            body.addWidget(widget)
        layout.addWidget(card)
        layout.addStretch()
        return page

    def _startup_page(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(0, 26, 0, 0)
        self.homepage_input = QLineEdit()
        self.search_engine_input = QLineEdit()
        self.startup_combo = QComboBox()
        self.startup_combo.addItems(["Ultima sessao", "Pagina inicial", "Pagina em branco"])
        form.addRow("Pagina inicial", self.homepage_input)
        form.addRow("Motor de busca", self.search_engine_input)
        form.addRow("Ao iniciar", self.startup_combo)
        return page

    def _appearance_page(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(0, 26, 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.currentTextChanged.connect(self.theme_changed.emit)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 24)
        self.font_size_spin.setSuffix(" px")
        self.zoom_factor_spin = QSpinBox()
        self.zoom_factor_spin.setRange(50, 200)
        self.zoom_factor_spin.setSuffix("%")
        form.addRow("Tema", self.theme_combo)
        form.addRow("Tamanho da fonte", self.font_size_spin)
        form.addRow("Zoom padrao", self.zoom_factor_spin)
        return page

    def _load_current_settings(self) -> None:
        self.homepage_input.setText(self.settings_manager.get("homepage", "about:home"))
        self.search_engine_input.setText(self.settings_manager.get("search_engine", "https://www.google.com/search?q="))
        startup_map = {"last_session": "Ultima sessao", "homepage": "Pagina inicial", "blank": "Pagina em branco"}
        self.startup_combo.setCurrentText(startup_map.get(self.settings_manager.get("startup_mode", "homepage"), "Pagina inicial"))
        self.save_history_check.setChecked(self.settings_manager.get("save_history", True, type=bool))
        self.block_ads_check.setChecked(self.settings_manager.get("block_ads", True, type=bool))
        self.gamer_mode_check.setChecked(self.settings_manager.get("gamer_mode", True, type=bool))
        self.auto_close_popups_check.setChecked(self.settings_manager.get("auto_close_popups", False, type=bool))
        self.enable_javascript_check.setChecked(self.settings_manager.get("enable_javascript", True, type=bool))
        self.enable_dark_mode_check.setChecked(self.settings_manager.get("enable_dark_mode", False, type=bool))
        theme_name = self.settings_manager.get("theme", "chrome_clean")
        self.theme_combo.setCurrentText(theme_name if theme_name in THEMES else "chrome_clean")
        self.font_size_spin.setValue(self.settings_manager.get("font_size", 14, type=int))
        self.zoom_factor_spin.setValue(int(self.settings_manager.get("zoom_factor", 1.0, type=float) * 100))

    def _apply_settings(self) -> None:
        try:
            self.settings_manager.set("homepage", self.homepage_input.text().strip() or "about:home")
            self.settings_manager.set("search_engine", self.search_engine_input.text().strip() or "https://www.google.com/search?q=")
            startup_map = {"Ultima sessao": "last_session", "Pagina inicial": "homepage", "Pagina em branco": "blank"}
            self.settings_manager.set("startup_mode", startup_map[self.startup_combo.currentText()])
            self.settings_manager.set("save_history", self.save_history_check.isChecked())
            self.settings_manager.set("block_ads", self.block_ads_check.isChecked())
            self.settings_manager.set("gamer_mode", self.gamer_mode_check.isChecked())
            self.settings_manager.set("auto_close_popups", self.auto_close_popups_check.isChecked())
            self.settings_manager.set("enable_javascript", self.enable_javascript_check.isChecked())
            self.settings_manager.set("enable_dark_mode", self.enable_dark_mode_check.isChecked())
            self.settings_manager.set("theme", self.theme_combo.currentText())
            self.settings_manager.set("font_size", self.font_size_spin.value())
            self.settings_manager.set("zoom_factor", self.zoom_factor_spin.value() / 100.0)
            self.settings_applied.emit()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao salvar definicoes: {e}")

    def _clear_browsing_data(self) -> None:
        parent_window = self.parent()
        if isinstance(parent_window, SafeMainWindow):
            parent_window._clear_browser_profile_data()
            QMessageBox.information(self, "Dados limpos", "Reinicie o navegador para aplicar completamente.")

    def accept(self) -> None:
        self._apply_settings()
        super().accept()


class ProfileManagerDialog(ThemedDialog):
    profile_switched = pyqtSignal(str)

    def __init__(self, settings_manager: 'SettingsManager', theme: dict, parent: Optional[QWidget] = None):
        super().__init__(theme, parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Perfis - AGNER")
        self.setMinimumSize(860, 620)
        self.setModal(True)
        self._init_ui()
        self._load_profiles()

    def _init_ui(self) -> None:
        self.setStyleSheet("""
            ProfileManagerDialog {
                background-color: #292a2d;
                color: #e8eaed;
            }
            QLabel#profileTitle {
                color: #e8eaed;
                font-size: 28px;
                font-weight: 500;
            }
            QLabel#profileSubtitle {
                color: #bdc1c6;
                font-size: 14px;
            }
            QListWidget#profileGrid {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget#profileGrid::item {
                background-color: #202124;
                color: #e8eaed;
                border: 1px solid transparent;
                border-radius: 8px;
                padding: 12px;
                margin: 8px;
            }
            QListWidget#profileGrid::item:selected {
                border: 1px solid #8ab4f8;
                background-color: #303134;
            }
            QPushButton#guestButton, QPushButton#profileAction {
                background-color: transparent;
                color: #8ab4f8;
                border: 1px solid #1a73e8;
                border-radius: 18px;
                padding: 9px 18px;
                font-weight: 700;
            }
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 34, 36, 30)
        root.setSpacing(18)
        title = QLabel("Boas-vindas aos perfis do AGNER")
        title.setObjectName("profileTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Separe favoritos, historico e configuracoes por pessoa ou uso.")
        subtitle.setObjectName("profileSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)
        root.addWidget(subtitle)

        self.profile_list = QListWidget()
        self.profile_list.setObjectName("profileGrid")
        self.profile_list.setViewMode(QListView.ViewMode.IconMode)
        self.profile_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.profile_list.setMovement(QListView.Movement.Static)
        self.profile_list.setGridSize(QSize(168, 178))
        self.profile_list.setIconSize(QSize(74, 74))
        self.profile_list.itemDoubleClicked.connect(self._activate_item)
        root.addWidget(self.profile_list, 1, Qt.AlignmentFlag.AlignHCenter)

        actions = QHBoxLayout()
        guest = QPushButton("Modo convidado")
        guest.setObjectName("guestButton")
        guest.clicked.connect(self._open_guest)
        add = QPushButton("Adicionar")
        add.setObjectName("profileAction")
        add.clicked.connect(self._add_profile)
        switch = QPushButton("Abrir perfil")
        switch.setObjectName("profileAction")
        switch.clicked.connect(self._switch_profile)
        delete = QPushButton("Excluir")
        delete.setObjectName("profileAction")
        delete.clicked.connect(self._delete_profile)
        close = QPushButton("Fechar")
        close.setObjectName("profileAction")
        close.clicked.connect(self.accept)
        actions.addWidget(guest)
        actions.addStretch()
        actions.addWidget(add)
        actions.addWidget(switch)
        actions.addWidget(delete)
        actions.addWidget(close)
        root.addLayout(actions)

    def _avatar_icon(self, text: str, add: bool = False) -> QIcon:
        pixmap = QPixmap(96, 96)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#9aa0a6" if add else "#8ab4f8"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(8, 8, 80, 80)
        painter.setPen(QColor("#202124"))
        font = QFont()
        font.setPointSize(32 if add else 24)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "+" if add else text[:1].upper())
        painter.end()
        return QIcon(pixmap)

    def _load_profiles(self) -> None:
        self.profile_list.clear()
        current_profile = self.settings_manager.get_current_profile_name()
        for profile_name in self.settings_manager.get_all_profiles():
            label = f"{profile_name}\nAtual" if profile_name == current_profile else profile_name
            item = QListWidgetItem(self._avatar_icon(profile_name), label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setData(Qt.ItemDataRole.UserRole, profile_name)
            self.profile_list.addItem(item)
        add_item = QListWidgetItem(self._avatar_icon("", True), "Adicionar")
        add_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        add_item.setData(Qt.ItemDataRole.UserRole, "__add__")
        self.profile_list.addItem(add_item)

    def _activate_item(self, item: QListWidgetItem) -> None:
        if item.data(Qt.ItemDataRole.UserRole) == "__add__":
            self._add_profile()
        else:
            self._switch_profile()

    def _add_profile(self) -> None:
        profile_name, ok = QInputDialog.getText(self, "Novo perfil", "Nome do novo perfil:")
        if ok and profile_name.strip():
            if self.settings_manager.add_profile(profile_name.strip()):
                self._load_profiles()
            else:
                QMessageBox.warning(self, "Erro", "Perfil ja existe ou nome invalido.")

    def _switch_profile(self) -> None:
        item = self.profile_list.currentItem()
        if not item:
            return
        profile_name = item.data(Qt.ItemDataRole.UserRole)
        if profile_name == "__add__":
            self._add_profile()
            return
        if profile_name == self.settings_manager.get_current_profile_name():
            self.accept()
            return
        self.settings_manager.set_current_profile(profile_name)
        self.profile_switched.emit(profile_name)
        self.accept()

    def _delete_profile(self) -> None:
        item = self.profile_list.currentItem()
        if not item:
            return
        profile_name = item.data(Qt.ItemDataRole.UserRole)
        if profile_name in ("__add__", self.settings_manager.get_current_profile_name()):
            QMessageBox.warning(self, "Excluir perfil", "Selecione um perfil que nao seja o atual.")
            return
        if QMessageBox.question(self, "Excluir perfil", f"Excluir '{profile_name}' e todos os dados?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.settings_manager.delete_profile(profile_name)
            self._load_profiles()

    def _open_guest(self) -> None:
        parent_window = self.parent()
        if isinstance(parent_window, SafeMainWindow):
            parent_window._add_incognito_tab()
            self.accept()


def _chrome_palette(theme: dict) -> dict:
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
            "hero": "#174ea6",
            "hero_text": "#ffffff",
            "hero_muted": "#dbeafe",
            "selection": theme.get("input_bg", "#303134"),
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
        "hero": "#e8f0fe",
        "hero_text": "#202124",
        "hero_muted": "#5f6368",
        "selection": theme.get("input_bg", "#e8f0fe"),
    }


class BookmarksDialog(ThemedDialog):
    def __init__(self, bookmark_manager: 'BookmarkManager', theme: dict, parent: Optional[QWidget] = None):
        super().__init__(theme, parent)
        self.bookmark_manager = bookmark_manager
        self.palette = _chrome_palette(theme)
        self.setWindowTitle("Favoritos - AGNER")
        self.setMinimumSize(900, 620)
        self.setModal(True)
        self._init_ui()
        self._load_bookmarks()

    def _init_ui(self) -> None:
        p = self.palette
        self.setStyleSheet(f"""
            BookmarksDialog {{
                background-color: {p['page']};
                color: {p['text']};
            }}
            QLabel#title {{
                color: {p['text']};
                font-size: 24px;
                font-weight: 800;
            }}
            QLabel#subtitle {{
                color: {p['muted']};
                font-size: 13px;
            }}
            QFrame#hero {{
                background-color: {p['surface']};
                border: 1px solid {p['border']};
                border-radius: 8px;
            }}
            QLineEdit#search {{
                background-color: {p['input']};
                color: {p['text']};
                border: 1px solid {p['border']};
                border-radius: 18px;
                padding: 9px 16px;
                min-width: 360px;
            }}
            QPushButton#primary, QPushButton#ghost {{
                border-radius: 18px;
                padding: 8px 16px;
                font-weight: 700;
            }}
            QPushButton#primary {{
                background-color: {p['accent']};
                color: white;
                border: 1px solid {p['accent']};
            }}
            QPushButton#ghost {{
                background-color: transparent;
                color: {p['accent']};
                border: 1px solid {p['accent']};
            }}
            QListWidget#bookmarkGrid {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget#bookmarkGrid::item {{
                background-color: {p['surface']};
                color: {p['text']};
                border: 1px solid {p['border']};
                border-radius: 8px;
                padding: 14px;
                margin: 8px;
            }}
            QListWidget#bookmarkGrid::item:selected {{
                background-color: {p['selection']};
                border: 1px solid {p['accent']};
            }}
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(18)

        hero = QFrame()
        hero.setObjectName("hero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(22, 18, 22, 18)
        title_box = QVBoxLayout()
        title = QLabel("Favoritos")
        title.setObjectName("title")
        subtitle = QLabel("Atalhos salvos em cards, com busca e acoes rapidas.")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("search")
        self.search_input.setPlaceholderText("Pesquisar favoritos")
        self.search_input.textChanged.connect(self._load_bookmarks)
        self.add_btn = QPushButton("Adicionar")
        self.add_btn.setObjectName("primary")
        self.add_btn.clicked.connect(self._add_bookmark)
        hero_layout.addLayout(title_box, 1)
        hero_layout.addWidget(self.search_input)
        hero_layout.addWidget(self.add_btn)
        root.addWidget(hero)

        self.bookmarks_list = QListWidget()
        self.bookmarks_list.setObjectName("bookmarkGrid")
        self.bookmarks_list.setViewMode(QListView.ViewMode.IconMode)
        self.bookmarks_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.bookmarks_list.setMovement(QListView.Movement.Static)
        self.bookmarks_list.setGridSize(QSize(260, 132))
        self.bookmarks_list.setSpacing(8)
        self.bookmarks_list.itemDoubleClicked.connect(lambda _: self._visit_bookmark())
        root.addWidget(self.bookmarks_list, 1)

        actions = QHBoxLayout()
        self.edit_btn = QPushButton("Editar")
        self.delete_btn = QPushButton("Excluir")
        self.visit_btn = QPushButton("Abrir")
        close_btn = QPushButton("Fechar")
        for btn in (self.edit_btn, self.delete_btn, self.visit_btn, close_btn):
            btn.setObjectName("ghost")
        self.edit_btn.clicked.connect(self._edit_bookmark)
        self.delete_btn.clicked.connect(self._delete_bookmark)
        self.visit_btn.clicked.connect(self._visit_bookmark)
        close_btn.clicked.connect(self.accept)
        actions.addWidget(self.edit_btn)
        actions.addWidget(self.delete_btn)
        actions.addStretch()
        actions.addWidget(self.visit_btn)
        actions.addWidget(close_btn)
        root.addLayout(actions)

    def _load_bookmarks(self) -> None:
        self.bookmarks_list.clear()
        query = self.search_input.text().strip().lower() if hasattr(self, "search_input") else ""
        bookmarks = self.bookmark_manager.get_all_bookmarks()
        for bookmark in bookmarks:
            title = bookmark.get("title", "Sem titulo")
            url = bookmark.get("url", "")
            if query and query not in title.lower() and query not in url.lower():
                continue
            host = QUrl(url).host() or url
            item = QListWidgetItem(f"{title}\n{host}")
            item.setData(Qt.ItemDataRole.UserRole, bookmark)
            self.bookmarks_list.addItem(item)
        if self.bookmarks_list.count() == 0:
            item = QListWidgetItem("Nenhum favorito encontrado\nAdicione um favorito para ele aparecer aqui.")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.bookmarks_list.addItem(item)

    def _add_bookmark(self) -> None:
        title, ok1 = QInputDialog.getText(self, "Novo favorito", "Titulo:")
        if not ok1 or not title.strip():
            return
        url, ok2 = QInputDialog.getText(self, "Novo favorito", "URL:")
        if not ok2 or not url.strip():
            return
        if self.bookmark_manager.add_bookmark(title.strip(), url.strip()):
            self._load_bookmarks()
        else:
            QMessageBox.warning(self, "Erro", "Nao foi possivel adicionar o favorito.")

    def _edit_bookmark(self) -> None:
        current = self.bookmarks_list.currentItem()
        if not current or not current.data(Qt.ItemDataRole.UserRole):
            return
        bookmark = current.data(Qt.ItemDataRole.UserRole)
        title, ok1 = QInputDialog.getText(self, "Editar favorito", "Titulo:", text=bookmark['title'])
        if not ok1:
            return
        url, ok2 = QInputDialog.getText(self, "Editar favorito", "URL:", text=bookmark['url'])
        if not ok2:
            return
        self.bookmark_manager.remove_bookmark(bookmark['url'])
        self.bookmark_manager.add_bookmark(title.strip(), url.strip())
        self._load_bookmarks()

    def _delete_bookmark(self) -> None:
        current = self.bookmarks_list.currentItem()
        if not current or not current.data(Qt.ItemDataRole.UserRole):
            return
        bookmark = current.data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(self, "Confirmar", f"Excluir o favorito '{bookmark['title']}'?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.bookmark_manager.remove_bookmark(bookmark['url'])
            self._load_bookmarks()

    def _visit_bookmark(self) -> None:
        current = self.bookmarks_list.currentItem()
        if not current or not current.data(Qt.ItemDataRole.UserRole):
            return
        parent_window = self.parent()
        if isinstance(parent_window, SafeMainWindow):
            parent_window.navigate_to_url_direct(current.data(Qt.ItemDataRole.UserRole)['url'])
            self.accept()


class ExtensionsDialog(ThemedDialog):
    def __init__(self, extension_manager: 'ExtensionManager', theme: dict, parent: Optional[QWidget] = None):
        super().__init__(theme, parent)
        self.extension_manager = extension_manager
        self.palette = _chrome_palette(theme)
        self.setWindowTitle("Extensoes - AGNER")
        self.setMinimumSize(1080, 720)
        self.setModal(True)
        self._init_ui()
        self._load_extensions()

    def _init_ui(self) -> None:
        p = self.palette
        self.setStyleSheet(f"""
            ExtensionsDialog {{
                background-color: {p['page']};
                color: {p['text']};
            }}
            QLabel#storeBrand, QLabel#sectionHeading {{
                color: {p['text']};
                font-weight: 800;
            }}
            QLabel#tabLabel {{
                color: {p['muted']};
                padding: 10px 14px;
                font-weight: 700;
            }}
            QLabel#tabLabel[selected="true"] {{
                color: {p['accent']};
                border-bottom: 3px solid {p['accent']};
            }}
            QLineEdit#storeSearch {{
                background-color: {p['input']};
                color: {p['text']};
                border: 1px solid {p['border']};
                border-radius: 20px;
                padding: 10px 18px;
                min-width: 420px;
            }}
            QFrame#hero {{
                background-color: {p['hero']};
                border: 1px solid {p['border']};
                border-radius: 18px;
            }}
            QLabel#heroTitle {{
                color: {p['hero_text']};
                font-size: 28px;
                font-weight: 800;
            }}
            QLabel#heroText {{
                color: {p['hero_muted']};
                font-size: 14px;
            }}
            QPushButton#primaryStore, QPushButton#outlineStore {{
                border-radius: 18px;
                padding: 9px 18px;
                font-weight: 700;
            }}
            QPushButton#primaryStore {{
                background-color: {p['accent']};
                color: white;
                border: 1px solid {p['accent']};
            }}
            QPushButton#outlineStore {{
                background-color: transparent;
                color: {p['accent']};
                border: 1px solid {p['accent']};
            }}
            QListWidget#extensionGrid {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget#extensionGrid::item {{
                background-color: {p['surface']};
                color: {p['text']};
                border: 1px solid {p['border']};
                border-radius: 8px;
                padding: 14px;
                margin: 8px;
            }}
            QListWidget#extensionGrid::item:selected {{
                background-color: {p['selection']};
                border: 1px solid {p['accent']};
            }}
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(22)

        header = QHBoxLayout()
        brand = QLabel("Chrome Web Store")
        brand.setObjectName("storeBrand")
        search = QLineEdit()
        search.setObjectName("storeSearch")
        search.setPlaceholderText("Pesquisar extensoes e temas")
        close_btn = QPushButton("Fechar")
        close_btn.setObjectName("outlineStore")
        close_btn.clicked.connect(self.accept)
        header.addWidget(brand)
        header.addStretch()
        header.addWidget(search)
        header.addStretch()
        header.addWidget(close_btn)
        root.addLayout(header)

        tabs = QHBoxLayout()
        for text, selected in (("Descobrir", True), ("Extensoes", False), ("Temas", False)):
            label = QLabel(text)
            label.setObjectName("tabLabel")
            label.setProperty("selected", selected)
            tabs.addWidget(label)
        tabs.addStretch()
        root.addLayout(tabs)

        hero = QFrame()
        hero.setObjectName("hero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(36, 30, 36, 30)
        copy = QVBoxLayout()
        hero_title = QLabel("Extensoes para AGNER")
        hero_title.setObjectName("heroTitle")
        hero_text = QLabel("Gerencie pacotes locais, instale arquivos ZIP e abra a Chrome Web Store.")
        hero_text.setObjectName("heroText")
        hero_text.setWordWrap(True)
        copy.addWidget(hero_title)
        copy.addWidget(hero_text)
        hero_actions = QHBoxLayout()
        self.store_btn = QPushButton("Chrome Web Store")
        self.store_btn.setObjectName("outlineStore")
        self.store_btn.clicked.connect(self._open_store)
        self.add_btn = QPushButton("Instalar extensao")
        self.add_btn.setObjectName("primaryStore")
        self.add_btn.clicked.connect(self._install_extension)
        hero_actions.addWidget(self.store_btn)
        hero_actions.addWidget(self.add_btn)
        copy.addLayout(hero_actions)
        hero_layout.addLayout(copy, 1)
        root.addWidget(hero)

        section = QHBoxLayout()
        heading = QLabel("Extensoes instaladas")
        heading.setObjectName("sectionHeading")
        heading.setStyleSheet("font-size: 22px;")
        self.remove_btn = QPushButton("Remover selecionada")
        self.remove_btn.setObjectName("outlineStore")
        self.remove_btn.clicked.connect(self._remove_extension)
        section.addWidget(heading)
        section.addStretch()
        section.addWidget(self.remove_btn)
        root.addLayout(section)

        self.extensions_list = QListWidget()
        self.extensions_list.setObjectName("extensionGrid")
        self.extensions_list.setViewMode(QListView.ViewMode.IconMode)
        self.extensions_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.extensions_list.setMovement(QListView.Movement.Static)
        self.extensions_list.setGridSize(QSize(260, 150))
        self.extensions_list.setSpacing(8)
        root.addWidget(self.extensions_list, 1)

    def _load_extensions(self) -> None:
        self.extensions_list.clear()
        if not self.extension_manager.extensions:
            item = QListWidgetItem("Nenhuma extensao instalada\nUse Instalar extensao para adicionar um pacote ZIP.")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.extensions_list.addItem(item)
            return
        for ext_id, manifest in self.extension_manager.extensions.items():
            name = manifest.get('name', 'Extensao sem nome')
            version = manifest.get('version', 'N/A')
            item = QListWidgetItem(f"{name}\nVersao {version}\nPacote local")
            item.setData(Qt.ItemDataRole.UserRole, ext_id)
            self.extensions_list.addItem(item)

    def _install_extension(self) -> None:
        zip_path, _ = QFileDialog.getOpenFileName(self, "Selecionar extensao", "", "ZIP Files (*.zip)")
        if zip_path:
            ext_id = self.extension_manager.install_extension(zip_path)
            if ext_id:
                self._load_extensions()
                QMessageBox.information(self, "Extensao instalada", "Reinicie o navegador para aplicar.")
            else:
                QMessageBox.warning(self, "Erro", "Falha ao instalar extensao.")

    def _remove_extension(self) -> None:
        current = self.extensions_list.currentItem()
        if not current:
            return
        ext_id = current.data(Qt.ItemDataRole.UserRole)
        if not ext_id:
            return
        if QMessageBox.question(self, "Confirmar", f"Remover a extensao '{ext_id}'?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.extension_manager.uninstall_extension(ext_id)
            self._load_extensions()

    def _open_store(self) -> None:
        parent_window = self.parent()
        if isinstance(parent_window, SafeMainWindow):
            parent_window.navigate_to_url_direct("https://chromewebstore.google.com")
            self.accept()


class ProfileManagerDialog(ThemedDialog):
    profile_switched = pyqtSignal(str)

    def __init__(self, settings_manager: 'SettingsManager', theme: dict, parent: Optional[QWidget] = None):
        super().__init__(theme, parent)
        self.settings_manager = settings_manager
        self.palette = _chrome_palette(theme)
        self.setWindowTitle("Perfis - AGNER")
        self.setMinimumSize(860, 620)
        self.setModal(True)
        self._init_ui()
        self._load_profiles()

    def _init_ui(self) -> None:
        p = self.palette
        self.setStyleSheet(f"""
            ProfileManagerDialog {{
                background-color: {p['page']};
                color: {p['text']};
            }}
            QLabel#profileTitle {{
                color: {p['text']};
                font-size: 28px;
                font-weight: 500;
            }}
            QLabel#profileSubtitle {{
                color: {p['muted']};
                font-size: 14px;
            }}
            QListWidget#profileGrid {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget#profileGrid::item {{
                background-color: {p['surface']};
                color: {p['text']};
                border: 1px solid {p['border']};
                border-radius: 8px;
                padding: 12px;
                margin: 8px;
            }}
            QListWidget#profileGrid::item:selected {{
                border: 1px solid {p['accent']};
                background-color: {p['selection']};
            }}
            QPushButton#guestButton, QPushButton#profileAction {{
                background-color: transparent;
                color: {p['accent']};
                border: 1px solid {p['accent']};
                border-radius: 18px;
                padding: 9px 18px;
                font-weight: 700;
            }}
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 34, 36, 30)
        root.setSpacing(18)
        title = QLabel("Boas-vindas aos perfis do AGNER")
        title.setObjectName("profileTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Separe favoritos, historico e configuracoes por pessoa ou uso.")
        subtitle.setObjectName("profileSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)
        root.addWidget(subtitle)

        self.profile_list = QListWidget()
        self.profile_list.setObjectName("profileGrid")
        self.profile_list.setViewMode(QListView.ViewMode.IconMode)
        self.profile_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.profile_list.setMovement(QListView.Movement.Static)
        self.profile_list.setGridSize(QSize(168, 178))
        self.profile_list.setIconSize(QSize(74, 74))
        self.profile_list.itemDoubleClicked.connect(self._activate_item)
        root.addWidget(self.profile_list, 1, Qt.AlignmentFlag.AlignHCenter)

        actions = QHBoxLayout()
        guest = QPushButton("Modo convidado")
        guest.setObjectName("guestButton")
        guest.clicked.connect(self._open_guest)
        add = QPushButton("Adicionar")
        add.setObjectName("profileAction")
        add.clicked.connect(self._add_profile)
        switch = QPushButton("Abrir perfil")
        switch.setObjectName("profileAction")
        switch.clicked.connect(self._switch_profile)
        delete = QPushButton("Excluir")
        delete.setObjectName("profileAction")
        delete.clicked.connect(self._delete_profile)
        close = QPushButton("Fechar")
        close.setObjectName("profileAction")
        close.clicked.connect(self.accept)
        actions.addWidget(guest)
        actions.addStretch()
        actions.addWidget(add)
        actions.addWidget(switch)
        actions.addWidget(delete)
        actions.addWidget(close)
        root.addLayout(actions)

    def _avatar_icon(self, text: str, add: bool = False) -> QIcon:
        p = self.palette
        pixmap = QPixmap(96, 96)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(p["muted"] if add else p["accent"]))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(8, 8, 80, 80)
        painter.setPen(QColor(p["page"]))
        font = QFont()
        font.setPointSize(32 if add else 24)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "+" if add else text[:1].upper())
        painter.end()
        return QIcon(pixmap)

    def _load_profiles(self) -> None:
        self.profile_list.clear()
        current_profile = self.settings_manager.get_current_profile_name()
        for profile_name in self.settings_manager.get_all_profiles():
            label = f"{profile_name}\nAtual" if profile_name == current_profile else profile_name
            item = QListWidgetItem(self._avatar_icon(profile_name), label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setData(Qt.ItemDataRole.UserRole, profile_name)
            self.profile_list.addItem(item)
        add_item = QListWidgetItem(self._avatar_icon("", True), "Adicionar")
        add_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        add_item.setData(Qt.ItemDataRole.UserRole, "__add__")
        self.profile_list.addItem(add_item)

    def _activate_item(self, item: QListWidgetItem) -> None:
        if item.data(Qt.ItemDataRole.UserRole) == "__add__":
            self._add_profile()
        else:
            self._switch_profile()

    def _add_profile(self) -> None:
        profile_name, ok = QInputDialog.getText(self, "Novo perfil", "Nome do novo perfil:")
        if ok and profile_name.strip():
            if self.settings_manager.add_profile(profile_name.strip()):
                self._load_profiles()
            else:
                QMessageBox.warning(self, "Erro", "Perfil ja existe ou nome invalido.")

    def _switch_profile(self) -> None:
        item = self.profile_list.currentItem()
        if not item:
            return
        profile_name = item.data(Qt.ItemDataRole.UserRole)
        if profile_name == "__add__":
            self._add_profile()
            return
        if profile_name == self.settings_manager.get_current_profile_name():
            self.accept()
            return
        self.settings_manager.set_current_profile(profile_name)
        self.profile_switched.emit(profile_name)
        self.accept()

    def _delete_profile(self) -> None:
        item = self.profile_list.currentItem()
        if not item:
            return
        profile_name = item.data(Qt.ItemDataRole.UserRole)
        if profile_name in ("__add__", self.settings_manager.get_current_profile_name()):
            QMessageBox.warning(self, "Excluir perfil", "Selecione um perfil que nao seja o atual.")
            return
        if QMessageBox.question(self, "Excluir perfil", f"Excluir '{profile_name}' e todos os dados?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.settings_manager.delete_profile(profile_name)
            self._load_profiles()

    def _open_guest(self) -> None:
        parent_window = self.parent()
        if isinstance(parent_window, SafeMainWindow):
            parent_window._add_incognito_tab()
            self.accept()


