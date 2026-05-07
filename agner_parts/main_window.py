# --- Main Window ---
class SafeMainWindow(QMainWindow):
    def __init__(self, initial_profile_name: str = "default") -> None:
        super().__init__()
        self._current_profile_name = initial_profile_name
        self.current_theme: str = 'chrome_clean'
        self.devtools_window: Optional[DevToolsWindow] = None
        self._incognito_profile: Optional[QWebEngineProfile] = None  # Single incognito profile
        self._last_window_open_at: float = 0.0
        self._window_open_burst: int = 0

        self._initialize_managers()
        self._initialize_ui_components()
        self._initialize_browser_components()
        self._initialize_extension_manager()

        self.tabs_list: List[QWidget] = []
        self._closed_tabs_urls: deque[str] = deque(maxlen=10)

        self._setup_ui()
        self._apply_theme()
        self._connect_all_signals()
        self._setup_shortcuts()

        QTimer.singleShot(100, self._load_initial_state)
        QTimer.singleShot(250, self._refresh_omnibox_suggestions)

    def _initialize_managers(self) -> None:
        print(f"[MainWindow] Inicializando managers para perfil: {self._current_profile_name}...")
        try:
            # SettingsManager global para gerenciar qual perfil está ativo
            # e SettingsManager específico do perfil para as configurações daquele perfil
            self.settings_manager = SettingsManager(self._current_profile_name)
            self._migrate_lightweight_defaults()
            self.bookmark_manager = BookmarkManager(self.settings_manager.profile_dir)
            self.history_manager = HistoryManager(self.settings_manager.profile_dir)
            self.download_manager = DownloadManager(self)
            self.master_key_manager = MasterKeyManager(self.settings_manager.profile_dir)
            if self.settings_manager.get("theme", "chrome_clean") not in THEMES:
                self.settings_manager.set("theme", "chrome_clean")
            self.theme = self.settings_manager.get_theme()
            print("[MainWindow] Managers inicializados com sucesso.")
        except Exception as e:
            print(f"[MainWindow] Erro inicializando managers: {e}")
            self.theme = THEMES["chrome_clean"]

    def _migrate_lightweight_defaults(self) -> None:
        try:
            migration_key = "session_safety_migration_v3"
            if self.settings_manager.get(migration_key, False, type=bool):
                return

            self.settings_manager.set("startup_mode", "homepage")
            self.settings_manager.set("last_session", ["about:home"])
            self.settings_manager.set("auto_close_popups", False)
            self.settings_manager.set("restore_max_tabs", 6)
            self.settings_manager.set(migration_key, True)
            print("[MainWindow] Migracao de sessao segura aplicada.")
        except Exception as e:
            print(f"[MainWindow] Erro ao aplicar migracao de sessao segura: {e}")

    def _initialize_ui_components(self) -> None:
        print("[MainWindow] Inicializando componentes UI...")
        try:
            self.login_handler = SafeLoginHandler(self)
            self.web_channel = QWebChannel(self)
            self.web_channel.registerObject("agnerBrowserBridge", self.login_handler)
            print("[MainWindow] Componentes UI inicializados com sucesso.")
        except Exception as e:
            print(f"[MainWindow] Erro inicializando componentes UI: {e}")

    def _initialize_browser_components(self) -> None:
        print("[MainWindow] Inicializando componentes do navegador...")
        try:
            self.ad_blocker = AdBlocker()
            self.ad_blocker.enabled = self.settings_manager.get("block_ads", True, type=bool)
            self._web_profile = self._create_web_profile(self._current_profile_name)
            self._incognito_profile = self._create_incognito_web_profile()
            print("[MainWindow] Componentes do navegador inicializados com sucesso.")
        except Exception as e:
            print(f"[MainWindow] Erro inicializando componentes do navegador: {e}")
            self._web_profile = QWebEngineProfile.defaultProfile()
            self._incognito_profile = QWebEngineProfile.defaultProfile()  # Fallback

    def _initialize_extension_manager(self) -> None:
        print("[MainWindow] Inicializando gerenciador de extensões...")
        try:
            self.extension_manager = ExtensionManager(self.settings_manager.profile_dir)
            print("[MainWindow] Gerenciador de extensões inicializado com sucesso.")
        except Exception as e:
            print(f"[MainWindow] Erro inicializando gerenciador de extensões: {e}")

    def _create_web_profile(self, profile_name: str) -> QWebEngineProfile:
        """Cria e configura o QWebEngineProfile para um perfil específico."""
        print(f"[MainWindow] Criando novo perfil web para '{profile_name}'...")
        profile = QWebEngineProfile(profile_name, self)
        try:
            profile_dir = self.settings_manager.get_profile_dir(profile_name)
            storage_path = os.path.join(profile_dir, "web_storage")
            cache_path = os.path.join(profile_dir, "web_cache")

            os.makedirs(storage_path, exist_ok=True)
            os.makedirs(cache_path, exist_ok=True)

            profile.setPersistentStoragePath(storage_path)
            profile.setCachePath(cache_path)
            profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
            gamer_mode = self.settings_manager.get("gamer_mode", True, type=bool)
            try:
                cache_mb = 128 if gamer_mode else 384
                profile.setHttpCacheMaximumSize(cache_mb * 1024 * 1024)
            except AttributeError as e:
                print(f"[Profile '{profile_name}'] Warning: Could not set cache size: {e}")

            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 AGNER/2.0"
            profile.setHttpUserAgent(user_agent)

            self.ad_interceptor = SafeAdRequestInterceptor(self.ad_blocker, self)
            profile.setUrlRequestInterceptor(self.ad_interceptor)

            settings = profile.settings()
            # CORRIGIDO: Envolver setAttribute em try-except para lidar com atributos ausentes
            try:
                settings.setAttribute(QWebEngineSettings.WebAttribute.DeveloperExtrasEnabled, True)
            except AttributeError as e:
                print(f"[Profile '{profile_name}'] Warning: Could not set DeveloperExtrasEnabled: {e}")
            try:
                settings.setAttribute(QWebEngineSettings.WebAttribute.AutoFillEnabled, True)
            except AttributeError as e:
                print(f"[Profile '{profile_name}'] Warning: Could not set AutoFillEnabled: {e}")
            try:
                settings.setAttribute(QWebEngineSettings.WebAttribute.PasswordSavingEnabled, True)
            except AttributeError as e:
                print(f"[Profile '{profile_name}'] Warning: Could not set PasswordSavingEnabled: {e}")
            try:
                settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenEnabled, True)
            except AttributeError as e:
                print(f"[Profile '{profile_name}'] Warning: Could not set FullScreenEnabled: {e}")
            try:
                settings.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchingEnabled, True)
            except AttributeError as e:
                print(f"[Profile '{profile_name}'] Warning: Could not set DnsPrefetchingEnabled: {e}")
            try:
                settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
            except AttributeError as e:
                print(f"[Profile '{profile_name}'] Warning: Could not set JavascriptCanOpenWindows: {e}")
            try:
                settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
            except AttributeError as e:
                print(f"[Profile '{profile_name}'] Warning: Could not set JavascriptCanAccessClipboard: {e}")
            try:
                settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            except AttributeError as e:
                print(f"[Profile '{profile_name}'] Warning: Could not set LocalContentCanAccessRemoteUrls: {e}")
            try:
                settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
            except AttributeError as e:
                print(f"[Profile '{profile_name}'] Warning: Could not set AllowWindowActivationFromJavaScript: {e}")
            try:
                settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, not gamer_mode)
            except AttributeError as e:
                print(f"[Profile '{profile_name}'] Warning: Could not set ScrollAnimatorEnabled: {e}")
            try:
                settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
            except AttributeError as e:
                print(f"[Profile '{profile_name}'] Warning: Could not set WebGLEnabled: {e}")
            try:
                settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
            except AttributeError as e:
                print(f"[Profile '{profile_name}'] Warning: Could not set Accelerated2dCanvasEnabled: {e}")

            print(f"[MainWindow] Perfil web '{profile_name}' criado: {profile.persistentStoragePath()}")
            return profile
        except Exception as e:
            print(f"[MainWindow] Erro geral ao configurar perfil web '{profile_name}': {e}")
            traceback.print_exc()
            return QWebEngineProfile.defaultProfile()

    def _create_incognito_web_profile(self) -> QWebEngineProfile:
        """Cria e configura o QWebEngineProfile para navegação anônima."""
        print("[MainWindow] Criando perfil web anônimo...")
        incognito_profile = QWebEngineProfile("AgnerIncognitoProfile", self)
        try:
            # Adicionado try-except para setOffTheRecord()
            incognito_profile.setOffTheRecord(True)  # Isso o torna não persistente (dados em memória)
            print(f"[MainWindow] setOffTheRecord(True) aplicado com sucesso para perfil anônimo.")
        except AttributeError:
            print(
                "[MainWindow] WARNING: QWebEngineProfile.setOffTheRecord() não disponível. Usando fallback de caminhos não persistentes.")
            # Se setOffTheRecord não está disponível, QtWebEngine irá usar armazenamento em memória/temporário
            # por padrão se setPersistentStoragePath/setCachePath NÃO forem chamados.
            # Portanto, apenas não chame esses métodos aqui para o perfil anônimo.

        incognito_profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 AGNER/2.0 (Incognito)")

        # Perfil anônimo ainda deve usar o Ad Blocker
        self.incognito_ad_interceptor = SafeAdRequestInterceptor(self.ad_blocker, self)
        incognito_profile.setUrlRequestInterceptor(self.incognito_ad_interceptor)

        settings = incognito_profile.settings()
        gamer_mode = self.settings_manager.get("gamer_mode", True, type=bool)
        # CORRIGIDO: Envolver setAttribute em try-except para lidar com atributos ausentes
        try:
            settings.setAttribute(QWebEngineSettings.WebAttribute.DeveloperExtrasEnabled, True)
        except AttributeError as e:
            print(f"[Incognito Profile] Warning: Could not set DeveloperExtrasEnabled: {e}")
        try:
            settings.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchingEnabled, True)
        except AttributeError as e:
            print(f"[Incognito Profile] Warning: Could not set DnsPrefetchingEnabled: {e}")
        try:
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        except AttributeError as e:
            print(f"[Incognito Profile] Warning: Could not set JavascriptCanOpenWindows: {e}")
        try:
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        except AttributeError as e:
            print(f"[Incognito Profile] Warning: Could not set JavascriptCanAccessClipboard: {e}")
        try:
            settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
        except AttributeError as e:
            print(f"[Incognito Profile] Warning: Could not set AllowWindowActivationFromJavaScript: {e}")
        try:
            settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, not gamer_mode)
        except AttributeError as e:
            print(f"[Incognito Profile] Warning: Could not set ScrollAnimatorEnabled: {e}")
        try:
            settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        except AttributeError as e:
            print(f"[Incognito Profile] Warning: Could not set WebGLEnabled: {e}")
        try:
            settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        except AttributeError as e:
            print(f"[Incognito Profile] Warning: Could not set Accelerated2dCanvasEnabled: {e}")

        print("[MainWindow] Perfil web anônimo criado.")
        return incognito_profile

    def _clear_browser_profile_data(self) -> None:
        """Limpa dados de navegação do perfil atual."""
        print("[MainWindow] Limpando dados do perfil do navegador...")
        if self._web_profile:
            self._web_profile.clearHttpCache()
            self._web_profile.clearAllVisitedLinks()

            storage_path = self._web_profile.persistentStoragePath()
            cache_path = self._web_profile.cachePath()

            try:
                if os.path.exists(storage_path):
                    # Only remove content, not the directory itself, as it's managed by the profile
                    for item in os.listdir(storage_path):
                        item_path = os.path.join(storage_path, item)
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            import shutil
                            shutil.rmtree(item_path)
                    print(f"[MainWindow] Cache de armazenamento persistente limpo: {storage_path}")
                if os.path.exists(cache_path):
                    for item in os.listdir(cache_path):
                        item_path = os.path.join(cache_path, item)
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            import shutil
                            shutil.rmtree(item_path)
                    print(f"[MainWindow] Cache HTTP limpo: {cache_path}")
                print("[MainWindow] Dados do perfil limpos com sucesso.")
            except Exception as e:
                print(f"[MainWindow] Erro ao limpar diretórios de dados do navegador: {e}")

    def _setup_ui(self) -> None:
        print("[MainWindow] Configurando UI principal...")
        self.setWindowTitle("AGNER Browser")
        self.setWindowIcon(SafeIconProvider.get_icon(SVG_ICONS['home'], self.theme['accent']))

        geometry = self.settings_manager.get("window_geometry", [100, 100, 1400, 900])
        self.setGeometry(*[int(v) for v in geometry])

        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Browser Area
        self.browser_area = QWidget()
        self.browser_area.setObjectName("browserArea")
        self.browser_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # Adicionado
        browser_layout = QVBoxLayout(self.browser_area)
        browser_layout.setContentsMargins(0, 0, 0, 0)
        browser_layout.setSpacing(0)

        tab_container = QWidget()
        tab_container.setObjectName("tabContainer")
        tab_layout = QHBoxLayout(tab_container)
        tab_layout.setContentsMargins(8, 6, 8, 0)
        tab_layout.setSpacing(3)

        self.tab_bar = QTabBar()
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setMovable(True)
        self.tab_bar.setObjectName("modernTabBar")
        self.tab_bar.setExpanding(False)
        self.tab_bar.setDocumentMode(True)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.setUsesScrollButtons(True)
        self.tab_bar.setElideMode(Qt.TextElideMode.ElideRight)
        self.tab_bar.setSelectionBehaviorOnRemove(QTabBar.SelectionBehavior.SelectPreviousTab)
        self.tab_bar.setMinimumHeight(36)

        self.new_tab_btn = QToolButton()
        self.new_tab_btn.setObjectName("newTabButton")
        self.new_tab_btn.setToolTip("Nova aba (Ctrl+T)")
        self.new_tab_btn.setFixedSize(30, 30)
        self.new_tab_btn.setAutoRaise(True)

        tab_layout.addWidget(self.tab_bar, 1)
        tab_layout.addWidget(self.new_tab_btn)

        # Navigation Toolbar
        self.navigation_toolbar = QWidget()
        self.navigation_toolbar.setObjectName("navigationToolbar")
        toolbar_layout = QHBoxLayout(self.navigation_toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 6)
        toolbar_layout.setSpacing(4)

        self.back_btn = QToolButton()
        self.forward_btn = QToolButton()
        self.reload_btn = QToolButton()
        self.home_btn = QToolButton()
        for btn in [self.back_btn, self.forward_btn, self.reload_btn, self.home_btn]:
            btn.setObjectName("navButton")
            btn.setFixedSize(32, 32)
            btn.setAutoRaise(True)

        self.address_bar = QLineEdit()
        self.address_bar.setObjectName("modernAddressBar")
        self.address_bar.setPlaceholderText("Pesquisar no Google ou digitar URL")
        self.address_bar.setClearButtonEnabled(True)
        self.address_bar.setMinimumHeight(36)
        self.address_completer = QCompleter([], self)
        self.address_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.address_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.address_bar.setCompleter(self.address_completer)

        self.bookmark_btn = QToolButton()
        self.extensions_btn = QToolButton()
        self.menu_btn = QToolButton()
        for btn in [self.bookmark_btn, self.extensions_btn, self.menu_btn]:
            btn.setObjectName("navButton")
            btn.setFixedSize(32, 32)
            btn.setAutoRaise(True)

        toolbar_layout.addWidget(self.back_btn)
        toolbar_layout.addWidget(self.forward_btn)
        toolbar_layout.addWidget(self.reload_btn)
        toolbar_layout.addWidget(self.home_btn)
        toolbar_layout.addWidget(self.address_bar, 1)
        toolbar_layout.addWidget(self.bookmark_btn)
        toolbar_layout.addWidget(self.extensions_btn)
        toolbar_layout.addWidget(self.menu_btn)

        # Tab Stack
        self.tab_stack = QStackedWidget()
        self.tab_stack.setObjectName("tabStack")

        browser_layout.addWidget(tab_container)
        browser_layout.addWidget(self.navigation_toolbar)
        browser_layout.addWidget(self.tab_stack, 1)

        main_layout.addWidget(self.browser_area)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setMaximumHeight(24)
        self.status_label = QLabel("Pronto")
        self.status_bar.addPermanentWidget(self.status_label)
        self.status_bar.hide()
        print("[MainWindow] UI principal configurada.")

    def _apply_theme(self) -> None:
        print(f"[MainWindow] Aplicando tema: {self.theme.get('name', 'N/A')}")
        font_size = self.settings_manager.get("font_size", 14, type=int)

        close_icon_color = self.theme['secondary_text']
        close_icon_hover_color = self.theme['primary_text']

        close_icon_svg_data = SVG_ICONS['close_tab'].replace('currentColor', close_icon_color)
        close_icon_svg_data_encoded = QUrl.toPercentEncoding(
            f'data:image/svg+xml;utf8,{close_icon_svg_data}').data().decode()

        close_icon_svg_hover_data = SVG_ICONS['close_tab'].replace('currentColor', close_icon_hover_color)
        close_icon_svg_hover_data_encoded = QUrl.toPercentEncoding(
            f'data:image/svg+xml;utf8,{close_icon_svg_hover_data}').data().decode()

        max_tab_width = self.settings_manager.get("max_tab_width", 240, type=int)
        self.setStyleSheet(f"""
            QMainWindow, #centralWidget {{
                background-color: {self.theme['window_bg']};
            }}
            QWidget {{
                color: {self.theme['primary_text']};
                font-family: "Segoe UI", "Roboto", sans-serif;
                font-size: {font_size}px;
            }}
            #tabContainer {{
                background-color: {self.theme['tab_bar_bg']};
            }}
            QTabBar#modernTabBar {{
                background-color: {self.theme['tab_bar_bg']};
            }}
            QTabBar#modernTabBar::tab {{
                background-color: {self.theme['tab_bg']};
                color: {self.theme['tab_text']};
                border: 1px solid transparent;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-height: 30px;
                min-width: 120px;
                max-width: {max_tab_width}px;
                padding: 0 34px 0 14px;
                margin-right: 2px;
            }}
            QTabBar#modernTabBar::tab:hover:!selected {{
                background-color: {self.theme['button_hover']};
            }}
            QTabBar#modernTabBar::tab:selected {{
                background-color: {self.theme['tab_selected_bg']};
                color: {self.theme['tab_selected_text']};
                border-color: {self.theme['tab_selected_bg']};
                margin-bottom: -1px;
            }}
            QTabBar#modernTabBar::close-button {{
                image: url('{close_icon_svg_data_encoded}');
                subcontrol-position: right;
                subcontrol-origin: padding;
                right: 8px;
                width: 16px;
                height: 16px;
                border-radius: 8px;
            }}
            QTabBar#modernTabBar::close-button:hover {{
                background-color: {self.theme['button_hover']};
                image: url('{close_icon_svg_hover_data_encoded}');
            }}
            QToolButton#newTabButton, QToolButton#navButton {{
                background-color: transparent;
                border: none;
                border-radius: 16px;
                padding: 4px;
            }}
            QToolButton#newTabButton:hover, QToolButton#navButton:hover {{
                background-color: {self.theme['button_hover']};
            }}
            QToolButton#newTabButton:pressed, QToolButton#navButton:pressed {{
                background-color: {self.theme['divider']};
            }}
            QToolButton#navButton:disabled {{
                background-color: transparent;
            }}
            #navigationToolbar {{
                background-color: {self.theme['navbar_bg']};
                border-bottom: 1px solid {self.theme['divider']};
            }}
            #modernAddressBar {{
                background-color: {self.theme['input_bg']};
                border: 1px solid transparent;
                border-radius: 18px;
                color: {self.theme['primary_text']};
                padding: 0 14px;
                selection-background-color: {self.theme['accent']};
                min-height: 36px;
            }}
            #modernAddressBar:hover {{
                background-color: {self.theme['card_bg']};
            }}
            #modernAddressBar:focus {{
                background-color: {self.theme['card_bg']};
                border: 1px solid {self.theme['accent']};
            }}
            #tabStack, QWebEngineView {{
                background-color: {self.theme['web_bg']};
            }}
            QStatusBar {{
                background-color: {self.theme['navbar_bg']};
                border-top: 1px solid {self.theme['divider']};
                min-height: 20px;
                max-height: 24px;
            }}
            QStatusBar QLabel {{
                color: {self.theme['secondary_text']};
                font-size: 12px;
            }}
            QMenu {{
                background-color: {self.theme['card_bg']};
                border: 1px solid {self.theme['divider']};
                border-radius: 8px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 22px;
                border-radius: 6px;
            }}
            QMenu::item:selected {{
                background-color: {self.theme['button_hover']};
                color: {self.theme['primary_text']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {self.theme['divider']};
                margin: 6px 4px;
            }}
            QToolTip {{
                background-color: {self.theme['card_bg']};
                color: {self.theme['primary_text']};
                border: 1px solid {self.theme['divider']};
                padding: 6px;
                border-radius: 6px;
            }}
        """)

        icon_color = self.theme['icon_color']
        self.back_btn.setIcon(SafeIconProvider.get_icon(SVG_ICONS['back'], icon_color))
        self.forward_btn.setIcon(SafeIconProvider.get_icon(SVG_ICONS['forward'], icon_color))
        self.reload_btn.setIcon(SafeIconProvider.get_icon(SVG_ICONS['reload'], icon_color))
        self.home_btn.setIcon(SafeIconProvider.get_icon(SVG_ICONS['home'], icon_color))
        self.new_tab_btn.setIcon(SafeIconProvider.get_icon(SVG_ICONS['add'], icon_color))
        self.bookmark_btn.setIcon(SafeIconProvider.get_icon(SVG_ICONS['bookmark_outline'], icon_color))
        self.extensions_btn.setIcon(SafeIconProvider.get_icon(SVG_ICONS['extensions'], icon_color))
        self.menu_btn.setIcon(SafeIconProvider.get_icon(SVG_ICONS['menu'], icon_color))

        self._update_bookmark_icon()
        print("[MainWindow] UI principal configurada.")

    def _connect_all_signals(self) -> None:
        print("[MainWindow] Conectando todos os sinais...")
        self.back_btn.clicked.connect(self._navigate_back)
        self.forward_btn.clicked.connect(self._navigate_forward)
        self.reload_btn.clicked.connect(self._reload_page)
        self.home_btn.clicked.connect(self._navigate_home)
        self.new_tab_btn.clicked.connect(self._add_new_tab)
        self.address_bar.returnPressed.connect(self._navigate_to_address)
        self.address_bar.textEdited.connect(lambda _: self._refresh_omnibox_suggestions())
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        self.tab_bar.tabCloseRequested.connect(self._close_tab)
        self.bookmark_btn.clicked.connect(self._toggle_bookmark)
        self.extensions_btn.clicked.connect(self._show_extensions)
        self.menu_btn.clicked.connect(self._show_menu)
        print("[MainWindow] Sinais conectados.")

    def _setup_shortcuts(self) -> None:
        print("[MainWindow] Configurando atalhos de teclado...")
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self._add_new_tab)
        QShortcut(QKeySequence("Ctrl+Shift+N"), self).activated.connect(self._add_incognito_tab)  # New incognito tab
        QShortcut(QKeySequence("Ctrl+Shift+T"), self).activated.connect(self._reopen_last_closed_tab)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(lambda: self._close_tab(self.tab_bar.currentIndex()))
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self._focus_address_bar)
        QShortcut(QKeySequence("Alt+D"), self).activated.connect(self._focus_address_bar)
        QShortcut(QKeySequence("Ctrl+K"), self).activated.connect(self._focus_address_bar)
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self._focus_address_bar)
        QShortcut(QKeySequence("F6"), self).activated.connect(self._focus_address_bar)
        QShortcut(QKeySequence("F5"), self).activated.connect(self._reload_page)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self._reload_page)
        QShortcut(QKeySequence("Alt+Left"), self).activated.connect(self._navigate_back)
        QShortcut(QKeySequence("Alt+Right"), self).activated.connect(self._navigate_forward)
        QShortcut(QKeySequence("Alt+Home"), self).activated.connect(self._navigate_home)
        QShortcut(QKeySequence("Ctrl+Tab"), self).activated.connect(self._select_next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self).activated.connect(self._select_previous_tab)
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self._toggle_bookmark)
        QShortcut(QKeySequence("Ctrl+H"), self).activated.connect(self._show_history)
        QShortcut(QKeySequence("Ctrl+J"), self).activated.connect(self._show_downloads)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self._find_in_page)
        QShortcut(QKeySequence("F3"), self).activated.connect(self._find_in_page)
        QShortcut(QKeySequence("Ctrl++"), self).activated.connect(lambda: self._adjust_zoom(0.1))
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(lambda: self._adjust_zoom(0.1))
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(lambda: self._adjust_zoom(-0.1))
        QShortcut(QKeySequence("Ctrl+0"), self).activated.connect(self._reset_zoom)
        QShortcut(QKeySequence("Ctrl+Shift+D"), self).activated.connect(self._duplicate_current_tab)
        QShortcut(QKeySequence("Ctrl+Shift+C"), self).activated.connect(self._copy_current_url)
        QShortcut(QKeySequence("Ctrl+Shift+Delete"), self).activated.connect(self._clear_browsing_data_prompt)
        QShortcut(QKeySequence("F12"), self).activated.connect(self._open_devtools)
        QShortcut(QKeySequence("Ctrl+Shift+J"), self).activated.connect(self._open_devtools)
        QShortcut(QKeySequence("Esc"), self).activated.connect(self._stop_loading)
        QShortcut(QKeySequence("Ctrl+,"), self).activated.connect(self._show_settings)
        for tab_number in range(1, 9):
            QShortcut(QKeySequence(f"Ctrl+{tab_number}"), self).activated.connect(
                lambda index=tab_number - 1: self._select_tab_by_index(index)
            )
        QShortcut(QKeySequence("Ctrl+9"), self).activated.connect(lambda: self._select_tab_by_index(len(self.tabs_list) - 1))
        print("[MainWindow] Atalhos configurados.")

    def _allow_new_window(self, source_tab: QWidget) -> bool:
        try:
            if source_tab is not self.get_current_browser_tab():
                print("[MainWindow] Pop-up bloqueado: aba de origem nao esta ativa.")
                return False

            now = datetime.datetime.now().timestamp()
            if now - self._last_window_open_at > 2.0:
                self._window_open_burst = 0
            self._last_window_open_at = now
            self._window_open_burst += 1

            burst_limit = 2 if self.settings_manager.get("gamer_mode", True, type=bool) else 4
            if self._window_open_burst > burst_limit:
                print("[MainWindow] Pop-up bloqueado: limite de novas abas atingido.")
                self.status_label.setText("Pop-up bloqueado.")
                return False
            return True
        except Exception as e:
            print(f"[MainWindow] Erro validando nova janela: {e}")
            return False

    def _load_initial_state(self) -> None:
        print("[MainWindow] Carregando estado inicial...")
        try:
            startup_mode = self.settings_manager.get("startup_mode", "homepage")
            print(f"[MainWindow] Modo de inicialização: {startup_mode}")
            if startup_mode == "last_session":
                session_urls = self.settings_manager.load_session()
                urls_to_load = session_urls if session_urls else ["about:home"]
            elif startup_mode == "homepage":
                urls_to_load = [self.settings_manager.get("homepage", "about:home")]
            else:
                urls_to_load = ["about:blank"]

            if not urls_to_load:
                urls_to_load = ["about:home"]

            for i, url in enumerate(urls_to_load):
                print(f"[MainWindow] Adicionando aba inicial: {url}")
                # Pequeno delay para garantir que a UI tenha tempo de renderizar entre as abas
                QTimer.singleShot(i * 100, lambda u=url: self._add_tab(u))

        except Exception as e:
            print(f"Erro carregando estado inicial: {e}")
            self._add_tab("about:home")
        print("[MainWindow] Estado inicial carregado.")

    # ================= Métodos de Navegação =================
    def _add_tab(self, url_string: Optional[str] = None, title: str = "Nova Aba",
                 profile: Optional[QWebEngineProfile] = None, is_incognito: bool = False) -> 'SafeBrowserTab':
        print(f"[MainWindow] Adicionando nova aba. URL: {url_string}, Incognito: {is_incognito}")
        if url_string is None:
            url_string = self.settings_manager.get("homepage", "about:home")

        if profile is None:
            profile = self._web_profile

        tab = SafeBrowserTab(profile, url_string, self, self.theme, is_incognito)
        tab.titleChanged.connect(self._on_tab_title_changed)
        tab.urlChanged.connect(self._on_tab_url_changed)
        tab.iconChanged.connect(self._on_tab_icon_changed)
        tab.loadingChanged.connect(self._on_tab_loading_changed)
        tab.loadFinishedSignal.connect(self._on_page_load_finished)
        tab.zoomChanged.connect(self._on_tab_zoom_changed) # Conecta o sinal ao novo método

        self.tabs_list.append(tab)
        self.tab_stack.addWidget(tab)
        tab_index = self.tab_bar.addTab(title)
        self.tab_bar.setCurrentIndex(tab_index)

        if is_incognito:
            self.tab_bar.setTabIcon(tab_index,
                                    SafeIconProvider.get_icon(SVG_ICONS['incognito'], self.theme['incognito_text'], 16))
            # Usamos setProperty para estilizar via CSS diretamente para incognito
            self.tab_bar.tabButton(tab_index, QTabBar.ButtonPosition.RightSide).setProperty("data-incognito", "true")
            # Estilo do botão de fechar para incognito para ter cores diferentes
            self.tab_bar.tabButton(tab_index, QTabBar.ButtonPosition.RightSide).setStyleSheet(f"""
                QToolButton[data-incognito="true"] {{
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                    image: url('{QUrl.toPercentEncoding(f'data:image/svg+xml;utf8,{SVG_ICONS["close_tab"].replace("currentColor", self.theme["incognito_text"])}').data().decode()}');
                }}
                QToolButton[data-incognito="true"]:hover {{
                    background-color: rgba(255,255,255,0.1);
                }}
            """)
            self.tab_bar.setTabToolTip(tab_index, "Aba anônima - não salva histórico ou cookies.")
            self.tab_bar.tabButton(tab_index, QTabBar.ButtonPosition.RightSide).setToolTip("Fechar aba anônima")
        else:
            self.tab_bar.tabButton(tab_index, QTabBar.ButtonPosition.RightSide).setProperty("data-incognito", "false")

        print(f"[MainWindow] Aba adicionada com índice: {tab_index}")

        self._update_nav_buttons()
        self._update_bookmark_icon()
        return tab

    def _add_special_tab(self, title: str, widget: QWidget) -> QWidget:
        print(f"[MainWindow] Adicionando aba especial: {title}")
        widget.setObjectName(widget.__class__.__name__)

        self.tabs_list.append(widget)
        self.tab_stack.addWidget(widget)
        tab_index = self.tab_bar.addTab(title)
        self.tab_bar.setCurrentIndex(tab_index)
        # Abas especiais não são anônimas, mas também não devem ter icones de favoritos
        self.tab_bar.tabButton(tab_index, QTabBar.ButtonPosition.RightSide).setProperty("data-incognito", "false")
        print(f"[MainWindow] Aba especial adicionada com índice: {tab_index}")

        self.navigation_toolbar.setEnabled(True)
        return widget

    def _add_new_tab(self) -> None:
        print("[MainWindow] Ação: Adicionar nova aba.")
        self._add_tab()

    def _add_incognito_tab(self) -> None:
        print("[MainWindow] Ação: Adicionar aba anônima.")
        self._add_tab(url_string="about:blank", title="Anônimo", profile=self._incognito_profile, is_incognito=True)

    def _close_tab(self, index: int) -> None:
        print(f"[MainWindow] Ação: Fechar aba no índice {index}.")
        if not (0 <= index < len(self.tabs_list)):
            return

        if len(self.tabs_list) <= 1:
            print("[MainWindow] Última aba. Fechando navegador.")
            self.close()
            return

        tab_to_close = self.tabs_list[index]

        if isinstance(tab_to_close, SafeBrowserTab) and tab_to_close.view and not tab_to_close.is_incognito and tab_to_close.view.url().toString() not in ["about:blank", "about:home"]:
            self._closed_tabs_urls.appendleft(tab_to_close.view.url().toString())

        self.tabs_list.pop(index)
        self.tab_stack.removeWidget(tab_to_close)
        self.tab_bar.removeTab(index)

        if hasattr(tab_to_close, 'dispose'):
            tab_to_close.dispose()
        else:
            tab_to_close.deleteLater()

        self._update_nav_buttons()
        self._update_bookmark_icon()
        self.navigation_toolbar.setEnabled(True)

    def _reopen_last_closed_tab(self) -> None:
        print("[MainWindow] Ação: Reabrir última aba fechada.")
        if self._closed_tabs_urls:
            url = self._closed_tabs_urls.popleft()
            self._add_tab(url)
            self.status_label.setText(f"Reabrindo: {url}")
            print(f"[MainWindow] Reabrindo URL: {url}")
        else:
            self.status_label.setText("Nenhuma aba fechada para reabrir.")
            print("[MainWindow] Nenhuma aba fechada para reabrir.")

    def _navigate_back(self) -> None:
        print("[MainWindow] Ação: Navegar para trás.")
        if tab := self.get_current_browser_tab():
            tab.view.back()

    def _navigate_forward(self) -> None:
        print("[MainWindow] Ação: Navegar para frente.")
        if tab := self.get_current_browser_tab():
            tab.view.forward()

    def _reload_page(self) -> None:
        print("[MainWindow] Ação: Recarregar página.")
        if tab := self.get_current_browser_tab():
            tab.view.stop() if tab._is_loading else tab.view.reload()

    def _stop_loading(self) -> None:
        print("[MainWindow] Ação: Parar carregamento.")
        if tab := self.get_current_browser_tab():
            if tab._is_loading:
                tab.view.stop()

    def _find_in_page(self) -> None:
        print("[MainWindow] Ação: Buscar na página.")
        tab = self.get_current_browser_tab()
        if not tab or not tab.view:
            self.status_label.setText("Abra uma página para buscar.")
            return

        text, ok = QInputDialog.getText(self, "Buscar na página", "Texto:")
        text = text.strip() if ok else ""
        if not text:
            return

        tab.view.findText(text)
        self.status_label.setText(f"Busca na página: {text}")

    def _adjust_zoom(self, delta: float) -> None:
        tab = self.get_current_browser_tab()
        if not tab or not tab.view:
            return

        zoom = max(0.25, min(5.0, tab.view.zoomFactor() + delta))
        tab.view.setZoomFactor(zoom)
        self.status_label.setText(f"Zoom: {zoom * 100:.0f}%")

    def _reset_zoom(self) -> None:
        tab = self.get_current_browser_tab()
        if not tab or not tab.view:
            return

        tab.view.setZoomFactor(1.0)
        self.status_label.setText("Zoom: 100%")

    def _duplicate_current_tab(self) -> None:
        print("[MainWindow] Ação: Duplicar aba atual.")
        tab = self.get_current_browser_tab()
        if not tab or not tab.view:
            self._add_tab("about:home")
            return

        url = tab.view.url().toString() or "about:home"
        profile = self._incognito_profile if tab.is_incognito else self._web_profile
        title = tab.view.title() or "Nova Aba"
        self._add_tab(url, title, profile, tab.is_incognito)

    def _copy_current_url(self) -> None:
        tab = self.get_current_browser_tab()
        if not tab or not tab.view:
            self.status_label.setText("Nenhuma URL para copiar.")
            return

        url = tab.view.url().toString()
        QApplication.clipboard().setText(url)
        self.status_label.setText("URL copiada.")

    def _focus_address_bar(self) -> None:
        self.address_bar.setFocus()
        self.address_bar.selectAll()

    def _select_next_tab(self) -> None:
        if self.tab_bar.count() <= 1:
            return
        self.tab_bar.setCurrentIndex((self.tab_bar.currentIndex() + 1) % self.tab_bar.count())

    def _select_previous_tab(self) -> None:
        if self.tab_bar.count() <= 1:
            return
        self.tab_bar.setCurrentIndex((self.tab_bar.currentIndex() - 1) % self.tab_bar.count())

    def _select_tab_by_index(self, index: int) -> None:
        if 0 <= index < self.tab_bar.count():
            self.tab_bar.setCurrentIndex(index)

    def _clear_browsing_data_prompt(self) -> None:
        reply = QMessageBox.question(
            self,
            "Limpar dados de navegação",
            "Limpar cache, armazenamento local e histórico do perfil atual?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._clear_browser_profile_data()
        if hasattr(self, "history_manager"):
            self.history_manager.clear_history()
        self.status_label.setText("Dados de navegação limpos.")

    def _navigate_home(self) -> None:
        print("[MainWindow] Ação: Ir para página inicial.")
        if tab := self.get_current_browser_tab():
            tab.navigate(self.settings_manager.get("homepage", "about:home"))

    def _navigate_to_address(self) -> None:
        address = self.address_bar.text().strip()
        print(f"[MainWindow] Ação: Navegar para endereço/pesquisar: '{address}'")
        if not address: return

        if address == "about:downloads":
            self._show_downloads()
            return
        if address == "about:history":
            self._show_history()
            return
        if address == "about:home":
            self._navigate_home()
            return
        if address == "about:blank":
            # Add a new blank tab. If current is special, it will be added.
            # If current is browser, it will navigate the current tab.
            self._add_tab("about:blank")
            return

        if tab := self.get_current_browser_tab():
            tab.navigate(address)
        else:
            self._add_tab(address)
        return

    def navigate_to_url_direct(self, url: str) -> None:
        """Navega para uma URL diretamente na aba atual ou abre uma nova."""
        print(f"[MainWindow] Navegação direta solicitada para: {url}")
        if tab := self.get_current_browser_tab():
            tab.navigate(url)
        else:
            self._add_tab(url)

    def _refresh_omnibox_suggestions(self) -> None:
        """Atualiza sugestoes da omnibox com favoritos, historico e atalhos comuns."""
        try:
            suggestions: list[str] = [
                "https://www.google.com",
                "https://www.youtube.com",
                "https://github.com",
                "https://www.wikipedia.org",
            ]
            if hasattr(self, "bookmark_manager"):
                for row in self.bookmark_manager.get_all_bookmarks()[:25]:
                    url = row["url"]
                    if url and url not in suggestions:
                        suggestions.append(url)
            if hasattr(self, "history_manager"):
                for row in self.history_manager.get_all_history()[:50]:
                    url = row["url"]
                    if url and url not in suggestions:
                        suggestions.append(url)

            model = self.address_completer.model()
            if hasattr(model, "setStringList"):
                model.setStringList(suggestions)
        except Exception as e:
            print(f"[MainWindow] Erro atualizando sugestoes da omnibox: {e}")

    def get_current_browser_tab(self) -> Optional['SafeBrowserTab']:
        """Retorna a SafeBrowserTab ativa, ou None se for uma aba especial."""
        current_index = self.tab_bar.currentIndex()
        if 0 <= current_index < len(self.tabs_list):
            tab = self.tabs_list[current_index]
            if isinstance(tab, SafeBrowserTab):
                return tab
        return None

    # ================= Eventos das Abas =================
    def _on_tab_changed(self, index: int) -> None:
        try:
            if not (0 <= index < len(self.tabs_list)):
                self.navigation_toolbar.setEnabled(True)
                self.reload_btn.setEnabled(False)
                self.address_bar.clear()
                self._update_nav_buttons()
                self._update_bookmark_icon()
                return

            self.tab_stack.setCurrentIndex(index)
            tab = self.tabs_list[index]
            is_browser_tab = isinstance(tab, SafeBrowserTab) and bool(tab.view)
            self.navigation_toolbar.setEnabled(True)
            self.reload_btn.setEnabled(is_browser_tab)

            if is_browser_tab:
                url = tab.view.url().toString()
                self.address_bar.setText("" if url == "about:home" else url)
                icon_name = 'stop' if tab._is_loading else 'reload'
                self.reload_btn.setIcon(SafeIconProvider.get_icon(SVG_ICONS[icon_name], self.theme['icon_color']))
                self.reload_btn.setToolTip("Parar carregamento (Esc)" if tab._is_loading else "Recarregar (F5)")
                self.status_label.setText("Carregando..." if tab._is_loading else "Pronto")
                print(f"[MainWindow] Aba alterada para indice {index}. URL: {url}")
            else:
                title = self.tab_bar.tabText(index) or tab.objectName() or "Aba especial"
                self.address_bar.setText(f"about:{title.lower()}")
                self.status_label.setText(title)
                print(f"[MainWindow] Aba especial selecionada no indice {index}: {title}")

            self._update_nav_buttons()
            self._update_bookmark_icon()
        except (AttributeError, RuntimeError) as e:
            print(f"[MainWindow] Erro ao acessar aba {index}: {e}")
        except Exception as e:
            print(f"[MainWindow] Erro geral no _on_tab_changed: {e}")
        return

        """Lida com mudança de aba ativa - VERSÃO CORRIGIDA"""
        try:
            # CORRETO: Usar tabstack ao invés de tabs/tabslist
            if hasattr(self, 'tabstack') and 0 <= index < self.tabstack.count():
                tab = self.tabstack.widget(index)

                if hasattr(tab, 'view') and tab.view:
                    url = tab.view.url().toString()
                    print(f"[MainWindow] Aba alterada para índice {index}")

                    # Verifica se é aba de navegador
                    if hasattr(tab, 'isincognito'):
                        print(f"[MainWindow] Aba atual é um navegador. URL: {url}")
                    else:
                        print(f"[MainWindow] Aba especial no índice {index}")
                else:
                    print(f"[MainWindow] Aba especial no índice {index}")

        except (AttributeError, RuntimeError) as e:
            print(f"[MainWindow] Erro ao acessar aba {index}: {e}")
        except Exception as e:
            print(f"[MainWindow] Erro geral no _on_tab_changed: {e}")

    def _setup_web_profile(self, profile_name: str):
        """Configura perfil web com cache seguro"""
        try:
            # Use pasta temporária se houver problemas de permissão
            import tempfile
            cache_dir = os.path.join(tempfile.gettempdir(), f"agner_cache_{profile_name}")

            profile = QWebEngineProfile(profile_name)
            profile.setCachePath(cache_dir)
            profile.setPersistentStoragePath(cache_dir)

            # Cria diretório se não existir
            os.makedirs(cache_dir, exist_ok=True)

            return profile
        except Exception as e:
            print(f"[Profile] Erro configurando cache: {e}")
            # Fallback para perfil padrão
            return QWebEngineProfile.defaultProfile()

    def safe_access_qt_object(obj, method_name, *args, **kwargs):
        """Acesso seguro a objetos Qt"""
        try:
            if obj is None:
                print(f"[SafeAccess] Objeto é None, pulando {method_name}")
                return None

            if not hasattr(obj, method_name):
                print(f"[SafeAccess] Objeto não tem método {method_name}")
                return None

            method = getattr(obj, method_name)
            return method(*args, **kwargs)

        except (AttributeError, RuntimeError) as e:
            print(f"[SafeAccess] Erro chamando {method_name}: {e}")
            return None

    # Uso:
    # url = safe_access_qt_object(tab.view, 'url')
    # if url:
    #     url_string = safe_access_qt_object(url, 'toString')

    def _on_tab_title_changed(self, tab: QWidget, title: str) -> None:
        if (index := self._find_tab_index(tab)) is not None:
            display_title = title[:30] + '...' if len(title) > 30 else title or "Carregando..."
            if isinstance(tab, SafeBrowserTab) and tab.is_incognito:
                display_title = "Anonimo - " + display_title  # Prefixo para abas anônimas
            self.tab_bar.setTabText(index, display_title)

    def _on_tab_url_changed(self, tab: QWidget, url: QUrl) -> None:
        if tab == self.get_current_browser_tab():
            self.address_bar.setText(url.toString() if url.toString() != "about:home" else "")
            self._update_nav_buttons()
            self._update_bookmark_icon()

    def _on_tab_icon_changed(self, tab: QWidget, icon: QIcon) -> None:
        if (index := self._find_tab_index(tab)) is not None and not icon.isNull():
            if isinstance(tab, SafeBrowserTab) and tab.is_incognito:
                # Manter o ícone de anônimo, não atualizar com o favicon do site
                pass
            else:
                self.tab_bar.setTabIcon(index, icon)

    def _on_tab_loading_changed(self, tab: QWidget, is_loading: bool) -> None:
        if tab == self.get_current_browser_tab():
            icon_color = self.theme['icon_color']
            if is_loading:
                self.reload_btn.setIcon(SafeIconProvider.get_icon(SVG_ICONS['stop'], icon_color))
                self.reload_btn.setToolTip("Parar carregamento (Esc)")
                self.status_label.setText("Carregando...")
            else:
                self.reload_btn.setIcon(SafeIconProvider.get_icon(SVG_ICONS['reload'], icon_color))
                self.reload_btn.setToolTip("Recarregar (F5)")
                self.status_label.setText("Pronto")
            self._update_nav_buttons()

    def _on_page_load_finished(self, tab: QWidget, success: bool) -> None:
        print(
            f"[MainWindow] Carregamento da página concluído para {tab.view.url().toString() if isinstance(tab, SafeBrowserTab) and hasattr(tab, 'view') and tab.view else 'N/A'}. Sucesso: {success}")
        self._update_nav_buttons()

    def _on_tab_zoom_changed(self, zoom_factor: float) -> None:
        """
        Lida com as mudanças no fator de zoom da aba atual.
        A lógica de salvar o zoom por domínio já é tratada dentro da SafeBrowserTab.
        Este método pode ser usado para atualizações da UI na MainWindow, se necessário.
        """
        print(f"[MainWindow] Zoom da aba atual alterado para: {zoom_factor*100:.0f}%")
        self.status_label.setText(f"Zoom: {zoom_factor*100:.0f}%")

    def _find_tab_index(self, tab_widget: QWidget) -> Optional[int]:
        try:
            return self.tabs_list.index(tab_widget)
        except ValueError:
            return None

    def _update_nav_buttons(self) -> None:
        if tab := self.get_current_browser_tab():
            if isinstance(tab, SafeBrowserTab) and tab.view:  # Only enable nav buttons for browser tabs
                history = tab.view.page().history()
                self.back_btn.setEnabled(history.canGoBack())
                self.forward_btn.setEnabled(history.canGoForward())
            else:
                self.back_btn.setEnabled(False)
                self.forward_btn.setEnabled(False)
        else:
            self.back_btn.setEnabled(False)
            self.forward_btn.setEnabled(False)

    # ================= Favoritos, Extensões, Menu, Configurações =================
    def _toggle_bookmark(self) -> None:
        print("[MainWindow] Ação: Alternar favorito.")
        tab = self.get_current_browser_tab()
        if not tab or not tab.view or tab.is_incognito:  # Não permite favoritar em aba anônima
            self.status_label.setText("Não é possível favoritar esta página (modo anônimo ou aba especial)")
            print("[MainWindow] Não é possível favoritar: Aba inválida, anônima ou não é uma aba de navegador.")
            return

        url = tab.view.url().toString()
        title = tab.view.title() or url

        if not url or url.startswith("about:"):
            self.status_label.setText("Não é possível favoritar esta página")
            print(f"[MainWindow] Não é possível favoritar: URL inválida ou interna ({url}).")
            return

        if self.bookmark_manager.is_bookmarked(url):
            if self.bookmark_manager.remove_bookmark(url):
                self.status_label.setText("Favorito removido")
                print(f"[MainWindow] Favorito removido: {url}")
            else:
                self.status_label.setText("Erro ao remover favorito")
                print(f"[MainWindow] Erro ao remover favorito: {url}")
        else:
            if self.bookmark_manager.add_bookmark(title, url):
                self.status_label.setText("Favorito adicionado")
                print(f"[MainWindow] Favorito adicionado: {url}")
            else:
                self.status_label.setText("Erro ao adicionar favorito")
                print(f"[MainWindow] Erro ao adicionar favorito: {url}")

        self._update_bookmark_icon()

    def _show_bookmarks(self) -> None:
        print("[MainWindow] Ação: Mostrar favoritos.")
        dialog = BookmarksDialog(self.bookmark_manager, self.theme, self)
        dialog.exec()

    def _show_history(self) -> None:
        print("[MainWindow] Ação: Mostrar histórico.")
        for i, tab in enumerate(self.tabs_list):
            if isinstance(tab, HistoryWidget):
                self.tab_bar.setCurrentIndex(i)
                print("[MainWindow] Aba de histórico já aberta, focando.")
                return
        history_widget = HistoryWidget(self.history_manager, self.theme, self)
        self._add_special_tab("Histórico", history_widget)
        print("[MainWindow] Nova aba de histórico adicionada.")

    def _show_downloads(self) -> None:
        print("[MainWindow] Ação: Mostrar downloads.")
        for i, tab in enumerate(self.tabs_list):
            if isinstance(tab, DownloadsWidget):
                self.tab_bar.setCurrentIndex(i)
                print("[MainWindow] Aba de downloads já aberta, focando.")
                return
        downloads_widget = DownloadsWidget(self.download_manager, self.theme, self)
        self._add_special_tab("Downloads", downloads_widget)
        print("[MainWindow] Nova aba de downloads adicionada.")

    def _update_bookmark_icon(self) -> None:
        if (tab := self.get_current_browser_tab()) and tab.view:
            url = tab.view.url().toString()
            if url and not url.startswith(
                    "about:") and not tab.is_incognito:  # Ícone de favorito desabilitado para incognito
                if self.bookmark_manager.is_bookmarked(url):
                    self.bookmark_btn.setIcon(
                        SafeIconProvider.get_icon(SVG_ICONS['bookmark_filled'], self.theme['accent']))
                    self.bookmark_btn.setToolTip("Remover dos favoritos (Ctrl+D)")
                else:
                    self.bookmark_btn.setIcon(
                        SafeIconProvider.get_icon(SVG_ICONS['bookmark_outline'], self.theme['icon_color']))
                    self.bookmark_btn.setToolTip("Adicionar aos favoritos (Ctrl+D)")
                self.bookmark_btn.setEnabled(True)
            else:
                self.bookmark_btn.setIcon(
                    SafeIconProvider.get_icon(SVG_ICONS['bookmark_outline'], self.theme['secondary_text']))
                self.bookmark_btn.setEnabled(False)
        else:
            self.bookmark_btn.setEnabled(False)

    def _show_extensions(self) -> None:
        print("[MainWindow] Ação: Mostrar extensões.")
        dialog = ExtensionsDialog(self.extension_manager, self.theme, self)
        dialog.exec()

    def _show_menu(self) -> None:
        print("[MainWindow] Ação: Abrir menu.")
        menu = QMenu(self)
        menu.addAction(SafeIconProvider.get_icon(SVG_ICONS['add'], self.theme['icon_color']), "Nova Aba",
                       self._add_new_tab)
        menu.addAction(SafeIconProvider.get_icon(SVG_ICONS['incognito'], self.theme['icon_color']), "Nova Aba Anônima",
                       self._add_incognito_tab)
        menu.addAction("Duplicar Aba", self._duplicate_current_tab)
        menu.addSeparator()
        menu.addAction("Buscar na Página", self._find_in_page)
        menu.addAction("Copiar URL", self._copy_current_url)
        zoom_menu = menu.addMenu("Zoom")
        zoom_menu.addAction("Aumentar Zoom", lambda: self._adjust_zoom(0.1))
        zoom_menu.addAction("Diminuir Zoom", lambda: self._adjust_zoom(-0.1))
        zoom_menu.addAction("Resetar Zoom", self._reset_zoom)
        menu.addSeparator()
        menu.addAction(SafeIconProvider.get_icon(SVG_ICONS['bookmark_filled'], self.theme['icon_color']), "Favoritos",
                       self._show_bookmarks)
        menu.addAction(SafeIconProvider.get_icon(SVG_ICONS['history'], self.theme['icon_color']), "Histórico",
                       self._show_history)
        menu.addAction(SafeIconProvider.get_icon(SVG_ICONS['download'], self.theme['icon_color']), "Downloads",
                       self._show_downloads)
        menu.addAction(SafeIconProvider.get_icon(SVG_ICONS['extensions'], self.theme['icon_color']), "Extensões",
                       self._show_extensions)
        menu.addSeparator()
        menu.addAction(SafeIconProvider.get_icon(SVG_ICONS['settings'], self.theme['icon_color']), "Configurações",
                       self._show_settings)
        menu.addAction("Limpar Dados de Navegação", self._clear_browsing_data_prompt)
        menu.addAction(SafeIconProvider.get_icon(SVG_ICONS['profile'], self.theme['icon_color']),
                       "Gerenciar Perfis", self._show_profile_manager)

        menu.addSeparator()
        menu.addAction(SafeIconProvider.get_icon(SVG_ICONS['settings'], self.theme['icon_color']),
                       "Ferramentas do Desenvolvedor",
                       self._open_devtools)

        menu.addSeparator()
        menu.addAction("Sobre AGNER", self._show_about)
        menu.exec(self.menu_btn.mapToGlobal(QPoint(0, self.menu_btn.height())))

    def _open_devtools(self) -> None:
        print("[MainWindow] Ação: Abrir Ferramentas do Desenvolvedor.")
        current_tab = self.get_current_browser_tab()
        if not current_tab:
            QMessageBox.warning(self, "Ferramentas do Desenvolvedor",
                                "Selecione uma aba de navegador para inspecionar.")
            print("[MainWindow] Não foi possível abrir DevTools: Nenhuma aba de navegador ativa.")
            return

        if not self.devtools_window:
            self.devtools_window = DevToolsWindow(self)

        try:
            # Tenta setar a página de DevTools. Isso pode falhar se DeveloperExtrasEnabled não estiver disponível.
            current_tab.view.page().setDevToolsPage(self.devtools_window.view.page())
            self.devtools_window.show()
            print(f"[MainWindow] Ferramentas do Desenvolvedor abertas para URL: {current_tab.view.url().toString()}")
        except Exception as e:
            QMessageBox.warning(self, "Ferramentas do Desenvolvedor",
                                f"Não foi possível abrir as Ferramentas do Desenvolvedor. Erro: {e}\n"
                                "Sua versão do QtWebEngine pode não suportar esta funcionalidade ou DeveloperExtrasEnabled não está ativo.")
            print(f"[MainWindow] Erro ao abrir DevTools: {e}")
            traceback.print_exc()

    def _show_settings(self) -> None:
        print("[MainWindow] Ação: Abrir configurações.")
        dialog = FunctionalSettingsDialog(self.settings_manager, self.theme, self)
        dialog.theme_changed.connect(self._on_theme_changed_preview)
        dialog.settings_applied.connect(self._reload_settings)
        if dialog.exec() == QDialog.DialogCode.Rejected:
            print("[MainWindow] Configurações rejeitadas. Recarregando configurações salvas.")
            # Se o usuário cancelou, recarregar as configurações para reverter preview
            self.theme = self.settings_manager.get_theme()
            self._apply_theme()

    def _show_profile_manager(self) -> None:
        print("[MainWindow] Ação: Abrir gerenciador de perfis.")
        dialog = ProfileManagerDialog(self.settings_manager, self.theme, self)
        dialog.profile_switched.connect(self._handle_profile_switch_request)
        dialog.exec()

    def _handle_profile_switch_request(self, profile_name: str) -> None:
        print(f"[MainWindow] Solicitação de troca de perfil para: {profile_name}. Reiniciando...")
        QMessageBox.information(self, "Reiniciar Navegador",
                                "O navegador será reiniciado para aplicar a troca de perfil.")
        # Define o perfil globalmente para que a próxima inicialização o carregue
        global_settings = QSettings("AGNER", "Browser_Global")
        global_settings.setValue("current_profile", profile_name)
        global_settings.sync()
        QApplication.instance().quit()  # Força o encerramento da aplicação atual

    def _on_theme_changed_preview(self, theme_name: str) -> None:
        print(f"[MainWindow] Pré-visualização de tema alterada para: {theme_name}")
        self.theme = THEMES.get(theme_name, THEMES["chrome_clean"])
        self._apply_theme()

    def _clean_tabs_to_recreate(self, tabs: List[tuple[Optional[str], str, bool]]) -> List[tuple[Optional[str], str, bool]]:
        cleaned: List[tuple[Optional[str], str, bool]] = []
        seen: set[str] = set()
        regular_count = 0
        max_tabs = max(1, min(12, self.settings_manager.get("restore_max_tabs", 6, type=int)))

        for url, title, is_incognito in tabs:
            if not url:
                key = f"special:{title}"
                if title in {"HistoryWidget", "DownloadsWidget"} and key not in seen:
                    seen.add(key)
                    cleaned.append((url, title, is_incognito))
                continue

            if url == "about:blank" or url.startswith("https://www.google.com/search?q=about%3Ablank"):
                continue

            if regular_count >= max_tabs:
                continue

            key = self.settings_manager._session_url_key(url) if hasattr(self.settings_manager, "_session_url_key") else url
            if key in seen:
                continue

            seen.add(key)
            regular_count += 1
            cleaned.append((url, title, is_incognito))

        return cleaned or [("about:home", "Nova Aba", False)]

    def _reload_settings(self) -> None:
        """
        Recarrega todas as configurações do SettingsManager e reaplica o tema,
        recriando abas e perfis para garantir que as novas configurações
        (como Javascript, Dark Mode, etc.) sejam aplicadas.
        """
        print("[MainWindow] --- INICIANDO RECARREGAMENTO DE CONFIGURAÇÕES ---")
        try:
            tabs_to_recreate: List[tuple[Optional[str], str, bool]] = []  # (url, title, is_incognito)
            for tab in self.tabs_list:
                if isinstance(tab, SafeBrowserTab) and hasattr(tab, 'view') and tab.view:
                    url = tab.view.url().toString()
                    if url and url not in ["", "about:blank"]:
                        tabs_to_recreate.append((url, tab.view.title(), tab.is_incognito))
                else:
                    tabs_to_recreate.append((None, tab.objectName(), False))  # Special tabs are never incognito
            tabs_to_recreate = self._clean_tabs_to_recreate(tabs_to_recreate)
            print(f"[MainWindow] Abas atuais salvas para recriação: {len(tabs_to_recreate)} abas.")

            # Desconecte e descarte todas as abas existentes
            # Itera sobre uma cópia para evitar problemas de índice ao remover
            for i in range(len(self.tabs_list) - 1, -1, -1):
                tab = self.tabs_list[i]
                i = self.tabs_list.index(tab) # Pega o índice atual
                print(f"[MainWindow] Descartando aba {i}: {tab.objectName()}")

                # É crucial desconectar os sinais para evitar referências circulares e leaks
                # Alguns sinais são desconectados dentro de dispose()
                if hasattr(tab, 'titleChanged'):
                    try:
                        tab.titleChanged.disconnect(self._on_tab_title_changed)
                    except (TypeError, RuntimeError):
                        pass
                if hasattr(tab, 'urlChanged'):
                    try:
                        tab.urlChanged.disconnect(self._on_tab_url_changed)
                    except (TypeError, RuntimeError):
                        pass
                if hasattr(tab, 'iconChanged'):
                    try:
                        tab.iconChanged.disconnect(self._on_tab_icon_changed)
                    except (TypeError, RuntimeError):
                        pass
                if hasattr(tab, 'loadingChanged'):
                    try:
                        tab.loadingChanged.disconnect(self._on_tab_loading_changed)
                    except (TypeError, RuntimeError):
                        pass
                if hasattr(tab, 'loadFinishedSignal'):
                    try:
                        tab.loadFinishedSignal.disconnect(self._on_page_load_finished)
                    except (TypeError, RuntimeError):
                        pass
                if hasattr(tab, 'zoomChanged'):
                    try:
                        tab.zoomChanged.disconnect(self._on_tab_zoom_changed)
                    except (TypeError, RuntimeError):
                        pass
                print(f"[MainWindow] Sinais da aba {i} desconectados.")

                # Remover do stacked widget e tab bar
                self.tab_stack.removeWidget(tab)
                self.tab_bar.removeTab(i)
                print(f"[MainWindow] Aba {i} removida do stack e tab bar.")

                # Chamar dispose ou deleteLater
                if hasattr(tab, 'dispose'):
                    tab.dispose()  # SafeBrowserTab tem um método dispose mais completo
                else:
                    tab.deleteLater()  # Para outros QWidgets
                    print(f"[MainWindow] Aba especial {tab.objectName()} agendada para exclusão.")

            self.tabs_list = []
            print("[MainWindow] Lista de abas limpa.")

            # CRÍTICO: Descartar perfis QWebEngineProfile antigos antes de recriá-los
            if self._web_profile:
                self._web_profile.deleteLater()
                self._web_profile = None
                print("[MainWindow] Perfil web antigo descartado.")
            if self._incognito_profile:
                self._incognito_profile.deleteLater()
                self._incognito_profile = None
                print("[MainWindow] Perfil anônimo antigo descartado.")

            # Re-inicializar managers e perfis para pegar as novas configurações
            # Isso é crucial para JavaScript, Dark Mode e AdBlocker
            self._initialize_managers()
            self._initialize_browser_components()  # Recria _web_profile e _incognito_profile

            # Reaplicar tema e configurações que não exigem recriação de perfis/abas
            self.theme = self.settings_manager.get_theme()
            if self.ad_blocker:
                self.ad_blocker.enabled = self.settings_manager.get("block_ads", True, type=bool)
            self._apply_theme()  # Isso também atualiza ícones etc.
            print("[MainWindow] Tema e configurações do navegador reaplicados.")

            # Recriar as abas salvas
            if not tabs_to_recreate:
                print("[MainWindow] Nenhuma aba para recriar. Adicionando aba inicial padrão.")
                self._add_tab(self.settings_manager.get("homepage", "about:home"))
            else:
                print(f"[MainWindow] Recriando {len(tabs_to_recreate)} abas...")
                for url, title, is_incognito in tabs_to_recreate:
                    if url:
                        profile_to_use = self._incognito_profile if is_incognito else self._web_profile
                        self._add_tab(url, title, profile_to_use, is_incognito)
                    else:
                        # Re-adicionar abas especiais
                        if "HistoryWidget" == title:
                            self._show_history()
                        elif "DownloadsWidget" == title:
                            self._show_downloads()
            print("[MainWindow] Abas recriadas.")
            self.status_label.setText("Configurações aplicadas. Reinicie para aplicar totalmente extensões.")
            print("[MainWindow] --- RECARREGAMENTO DE CONFIGURAÇÕES CONCLUÍDO ---")

        except Exception as e:
            print(f"[MainWindow] ERRO CRÍTICO NO RECARREGAMENTO DE CONFIGURAÇÕES: {e}")
            traceback.print_exc()
            self.status_label.setText("Erro ao aplicar configurações.")

    def _show_about(self) -> None:
        print("[MainWindow] Ação: Mostrar 'Sobre AGNER'.")
        QMessageBox.about(self, "Sobre AGNER", """
        <h2>AGNER Browser</h2>
        <p><b>Navegação rápida com abas, perfis, favoritos, histórico, downloads,
        bloqueio de anúncios e ferramentas de desenvolvedor.</b></p>
        <p>Motor: PyQt6 + QtWebEngine</p>
        <p>Um navegador de desktop limpo, direto e focado em navegação real.</p>
        <p>Ícones por: Lucide Icons & Heroicons</p>
        """)

    # ================= Eventos da Janela =================
    def closeEvent(self, event) -> None:
        print("[MainWindow] Evento de fechamento da janela. Salvando estado...")
        self.settings_manager.set("window_geometry", [self.x(), self.y(), self.width(), self.height()])
        self.settings_manager.save_session(self.tabs_list)

        # Descartar todas as abas para liberar recursos
        for tab in self.tabs_list:
            if hasattr(tab, 'dispose'):
                tab.dispose()
            else:
                tab.deleteLater()

        # Fechar e descartar a janela de ferramentas de desenvolvedor se estiver aberta
        if self.devtools_window:
            self.devtools_window.close()
            self.devtools_window.deleteLater()
            self.devtools_window = None

        # Descartar perfis QWebEngineProfile
        if self._web_profile:
            self._web_profile.deleteLater()
            self._web_profile = None
        if self._incognito_profile:
            self._incognito_profile.deleteLater()
            self._incognito_profile = None

        # Fechar as conexões com o banco de dados
        self.bookmark_manager.db.close()
        self.history_manager.db.close()
        self.master_key_manager.db.close()  # Close master key db

        print("[MainWindow] Estado salvo e recursos liberados. Encerrando aplicação.")
        event.accept()


