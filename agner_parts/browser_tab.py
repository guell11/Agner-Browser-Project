# ================= CORE/ (tabs, perfil web, histórico, downloads) =================

# --- LoginBridge Seguro ---
class SafeLoginHandler(QObject):
    """Handler seguro para login e quick links"""

    def __init__(self, main_window: 'SafeMainWindow'):
        super().__init__()
        self.main_window_ref = weakref.ref(main_window)  # Use weakref to prevent circular reference

    @pyqtSlot(str, str, str, str, result=bool)
    def handleSubmitFromPage(self, username: str, password: str, hostname: str, full_url: str) -> bool:
        main_window = self.main_window_ref()
        if not main_window: return False

        current_tab = main_window.get_current_browser_tab()
        if current_tab and current_tab.is_incognito:
            QMessageBox.information(main_window, "Modo Anônimo", "Não é possível salvar senhas no modo anônimo.")
            return False

        if not CRYPTO_AVAILABLE:
            print("Criptografia não disponível. Não salvando senha.")
            QMessageBox.warning(main_window, "Erro de Segurança",
                                "A biblioteca de criptografia não está disponível. Não é possível salvar senhas.")
            return False

        reply = QMessageBox.question(main_window, "Salvar Senha",
                                     f"Deseja salvar a senha para '{username}' em '{hostname}'?",
                                     QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard)
        if reply == QMessageBox.StandardButton.Discard:
            return False

        try:
            # Chama o MasterKeyManager para criptografar e salvar a senha
            encrypted_pw = main_window.master_key_manager.encrypt_password(password)
            if encrypted_pw is None:
                QMessageBox.warning(main_window, "Erro de Segurança",
                                    "Não foi possível criptografar a senha. Verifique a chave mestra.")
                return False

            return main_window.master_key_manager.save_password(hostname, username, encrypted_pw)
        except Exception as e:
            print(f"Erro ao salvar senha: {e}")
            QMessageBox.critical(main_window, "Erro", f"Erro ao salvar senha: {e}")
            return False

    @pyqtSlot(result=str)
    def getCurrentTheme(self) -> str:
        main_window = self.main_window_ref()
        if not main_window:
            return "chrome_clean"
        theme_name = main_window.settings_manager.get("theme", "chrome_clean")
        return theme_name if theme_name in THEMES else "chrome_clean"

    @pyqtSlot(str)
    def saveQuickLinks(self, links_json: str) -> None:
        main_window = self.main_window_ref()
        if not main_window: return

        current_tab = main_window.get_current_browser_tab()
        if current_tab and current_tab.is_incognito:
            print("Não salvando quick links no modo anônimo.")
            return

        try:
            data = json.loads(links_json)
            # Salva no caminho do quick_links_path do settings_manager do perfil atual
            with open(main_window.settings_manager.quick_links_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro salvando quick links: {e}")

    @pyqtSlot(str)
    def navigate(self, url_string: str) -> None:
        main_window = self.main_window_ref()
        if not main_window: return

        try:
            # Reutiliza a função de navegação da main_window
            tab = main_window.get_current_browser_tab()
            if tab and hasattr(tab, 'navigate'):
                tab.navigate(url_string)
            else:
                main_window._add_tab(url_string)
        except Exception as e:
            print(f"Erro navegando: {e}")


# --- BrowserTab Seguro ---
class SafeWebPage(QWebEnginePage):
    """Pagina WebEngine que abre pop-ups e target=_blank em novas abas reais."""

    def __init__(self, web_profile: QWebEngineProfile, parent, browser_tab: 'SafeBrowserTab'):
        super().__init__(web_profile, parent)
        self.browser_tab_ref = weakref.ref(browser_tab)

    def createWindow(self, _type):
        browser_tab = self.browser_tab_ref()
        if not browser_tab:
            return None

        parent_ref = getattr(browser_tab, 'parent_window_ref', None)
        if not callable(parent_ref):
            return None

        main_window = parent_ref()
        if not main_window:
            return None

        now = datetime.datetime.now().timestamp()
        if now < getattr(browser_tab, '_suppress_new_windows_until', 0.0):
            print("[SafeWebPage] Nova janela bloqueada durante limpeza automatica de pop-ups.")
            if hasattr(main_window, "status_label"):
                main_window.status_label.setText("Pop-up bloqueado.")
            return None

        if hasattr(main_window, "_allow_new_window") and not main_window._allow_new_window(browser_tab):
            return None

        profile = main_window._incognito_profile if browser_tab.is_incognito else main_window._web_profile
        new_tab = main_window._add_tab("about:blank", "Nova Aba", profile, browser_tab.is_incognito)
        return new_tab.page if new_tab and new_tab.page else None


class SafeBrowserTab(QWidget):
    titleChanged = pyqtSignal(QWidget, str)
    urlChanged = pyqtSignal(QWidget, QUrl)
    iconChanged = pyqtSignal(QWidget, QIcon)
    loadingChanged = pyqtSignal(QWidget, bool)
    loadFinishedSignal = pyqtSignal(QWidget, bool)
    zoomChanged = pyqtSignal(float)

    def __init__(self, web_profile: QWebEngineProfile, url_string: Optional[str] = None,
                 parent_window: Optional['SafeMainWindow'] = None, theme: Optional[dict] = None,
                 is_incognito: bool = False):
        super().__init__(parent_window)
        self.parent_window_ref = weakref.ref(parent_window) if parent_window else None
        self.theme = theme or THEMES["chrome_clean"]
        self.is_incognito = is_incognito
        self._is_loading: bool = False
        self._disposed: bool = False  # Flag para indicar que a aba está em processo de descarte
        self._suppress_new_windows_until: float = 0.0

        self._web_profile = web_profile
        self.view: Optional[QWebEngineView] = None  # Initialize as Optional
        self.page: Optional[QWebEnginePage] = None # CRÍTICO: Manter referência forte à página

        self._init_ui()
        self._connect_signals()

        if url_string == "about:home" or not url_string:
            self.load_home()
        else:
            self.navigate(url_string)

    def _init_ui(self) -> None:
        try:
            print(f"[SafeBrowserTab] Inicializando UI para nova aba. Incognito: {self.is_incognito}")
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            self.progress = QProgressBar()
            self.progress.setMaximumHeight(3)
            self.progress.setTextVisible(False)
            self.progress.setStyleSheet(f"""
                QProgressBar {{
                    background: transparent;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background: {self.theme['loading_color']};
                    border-radius: 1px;
                }}
            """)
            self.progress.hide()
            layout.addWidget(self.progress)

            self.view = QWebEngineView()
            self.page = SafeWebPage(self._web_profile, self.view, self) # CRITICO: manter referencia forte da pagina

            settings = self.page.settings()
            parent_window = self.parent_window_ref()
            if parent_window:
                # CORRIGIDO: Envolver setAttribute em try-except para lidar com atributos ausentes
                try:
                    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled,
                                          parent_window.settings_manager.get("enable_javascript", True, type=bool))
                except AttributeError as e:
                    print(f"[SafeBrowserTab] Warning: Could not set JavascriptEnabled: {e}")
                try:
                    settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
                except AttributeError as e:
                    print(f"[SafeBrowserTab] Warning: Could not set AutoLoadImages: {e}")
                try:
                    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
                except AttributeError as e:
                    print(f"[SafeBrowserTab] Warning: Could not set LocalStorageEnabled: {e}")
                try:
                    settings.setAttribute(QWebEngineSettings.WebAttribute.XSSAuditingEnabled, True)
                except AttributeError as e:
                    print(f"[SafeBrowserTab] Warning: Could not set XSSAuditingEnabled: {e}")
                try:
                    settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
                except AttributeError as e:
                    print(f"[SafeBrowserTab] Warning: Could not set ScrollAnimatorEnabled: {e}")
                try:
                    settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenEnabled, True)
                except AttributeError as e:
                    print(f"[SafeBrowserTab] Warning: Could not set FullScreenEnabled: {e}")
                try:
                    settings.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchingEnabled, True)
                except AttributeError as e:
                    print(f"[SafeBrowserTab] Warning: Could not set DnsPrefetchingEnabled: {e}")
                try:
                    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
                except AttributeError as e:
                    print(f"[SafeBrowserTab] Warning: Could not set JavascriptCanOpenWindows: {e}")
                try:
                    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
                except AttributeError as e:
                    print(f"[SafeBrowserTab] Warning: Could not set JavascriptCanAccessClipboard: {e}")
                try:
                    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
                except AttributeError as e:
                    print(f"[SafeBrowserTab] Warning: Could not set LocalContentCanAccessRemoteUrls: {e}")
                try:
                    settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
                except AttributeError as e:
                    print(f"[SafeBrowserTab] Warning: Could not set AllowWindowActivationFromJavaScript: {e}")
                try:
                    settings.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, False)
                except AttributeError as e:
                    print(f"[SafeBrowserTab] Warning: Could not set ScreenCaptureEnabled: {e}")

                font_size = parent_window.settings_manager.get("font_size", 14, type=int)
                settings.setFontSize(QWebEngineSettings.FontSize.DefaultFontSize, font_size)
                settings.setFontSize(QWebEngineSettings.FontSize.DefaultFixedFontSize, font_size)

                # Injeção do script de modo escuro
                if parent_window.settings_manager.get("enable_dark_mode", False, type=bool):
                    dark_mode_script_code = """
                    (function() {
                        const existingStyle = document.getElementById('agner-dark-mode-style');
                        if (existingStyle) existingStyle.remove();

                        function applyDarkMode() {
                            const style = document.createElement('style');
                            style.id = 'agner-dark-mode-style';
                            style.textContent = `
                                html, body, img, video, canvas {
                                    filter: invert(0.9) hue-rotate(180deg) brightness(0.9);
                                    background-color: #1a1a1a !important;
                                }
                                /* Re-invert elements that should remain normal */
                                input, textarea, select, button {
                                    filter: invert(1) hue-rotate(180deg) brightness(1.2) !important;
                                }
                                img[src*=".svg"], [background*=".svg"], svg, path { filter: invert(0.9) hue-rotate(180deg) brightness(0.9); }
                                iframe { filter: invert(0) hue-rotate(0deg) !important; } /* Iframes são problemáticos, manter normal */
                                body { background-color: #1a1a1a !important; }
                            `;
                            (document.head || document.documentElement).appendChild(style);
                        }
                        // Apply immediately if DOM is ready, otherwise wait for it
                        if (document.readyState === 'loading') {
                            document.addEventListener('DOMContentLoaded', applyDarkMode);
                        } else {
                            applyDarkMode();
                        }
                    })();
                    """
                    dark_mode_script = QWebEngineScript()
                    dark_mode_script.setSourceCode(dark_mode_script_code)
                    dark_mode_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
                    dark_mode_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
                    self.page.scripts().insert(dark_mode_script)

            self.view.setPage(self.page)
            if parent_window:
                zoom = parent_window.settings_manager.get("zoom_factor", 1.0, type=float)
                self.view.setZoomFactor(zoom)
            layout.addWidget(self.view)

            # Configurar WebChannel para comunicação JavaScript-Python
            if parent_window and hasattr(parent_window, 'web_channel'):
                try:
                    self.page.setWebChannel(parent_window.web_channel)
                except Exception as e:
                    print(f"Erro configurando web channel: {e}")

            # Injeção de extensões (não em modo anônimo)
            if parent_window and hasattr(parent_window, 'extension_manager') and not self.is_incognito:
                parent_window.extension_manager.inject_extensions(self.page)

            # Conectar sinal de download ao gerenciador de downloads
            if parent_window:
                self.page.profile().downloadRequested.connect(parent_window.download_manager.handle_download_requested)
            print(f"[SafeBrowserTab] UI da aba inicializada com sucesso.")

        except Exception as e:
            print(f"[SafeBrowserTab] Erro inicializando UI da aba: {e}")
            self.view = None  # Garante que view seja None se falhar a inicialização
            self.page = None # Garante que page seja None se falhar a inicialização
            traceback.print_exc()  # Imprime o traceback completo para depuração

    def _connect_signals(self) -> None:
        if not self.view or not self.page: return  # Não conecta se a view/page falhou na inicialização
        try:
            self.view.loadStarted.connect(self._on_load_started)
            self.view.loadProgress.connect(self._on_load_progress)
            self.view.loadFinished.connect(self._on_load_finished)
            self.view.titleChanged.connect(self._on_title_changed)
            self.view.iconChanged.connect(self._on_icon_changed)
            self.view.urlChanged.connect(self._on_url_changed)
            self.page.zoomFactorChanged.connect(self._on_zoom_changed)
        except Exception as e:
            print(f"Erro conectando sinais: {e}")

    def _on_load_started(self) -> None:
        if self._disposed or not self.view: return
        self._is_loading = True
        self.progress.setValue(0)
        self.progress.show()
        self.loadingChanged.emit(self, True)

    def _on_load_progress(self, progress: int) -> None:
        if self._disposed or not self.view: return
        self.progress.setValue(progress)

    def _on_load_finished(self, ok: bool) -> None:
        if self._disposed or not self.view: return
        self._is_loading = False
        self.progress.hide()
        self.loadingChanged.emit(self, False)
        self.loadFinishedSignal.emit(self, ok)

        parent_window = self.parent_window_ref()
        # Adiciona ao histórico apenas se não for aba anônima
        if ok and parent_window and hasattr(parent_window, 'history_manager') and not self.is_incognito:
            try:
                url = self.view.url().toString()
                title = self.view.page().title()
                if url and not url.startswith("about:") and parent_window.settings_manager.get("save_history",
                                                                                               True, type=bool):
                    parent_window.history_manager.add_visit(url, title)
            except Exception as e:
                print(f"Erro adicionando ao histórico: {e}")

        self._apply_saved_zoom()

        if ok and parent_window and parent_window.settings_manager.get("auto_close_popups", False, type=bool):
            self._check_and_close_popups()

    def _on_title_changed(self, title: str) -> None:
        if not self._disposed:
            self.titleChanged.emit(self, title)

    def _on_icon_changed(self, icon: QIcon) -> None:
        if not self._disposed:
            self.iconChanged.emit(self, icon)

    def _on_url_changed(self, url: QUrl) -> None:
        if not self._disposed:
            self.urlChanged.emit(self, url)
            self._apply_saved_zoom()

    def _on_zoom_changed(self, zoom: float) -> None:
        if not self._disposed:
            self.zoomChanged.emit(zoom)
            self._save_zoom_for_domain(zoom)

    def _save_zoom_for_domain(self, zoom: float) -> None:
        parent_window = self.parent_window_ref()
        if parent_window and self.view and not self.is_incognito:  # Não salva zoom para incognito
            domain = QUrl(self.view.url()).host()
            if domain:
                zooms = parent_window.settings_manager.get("domain_zooms", {})
                zooms[domain] = zoom
                parent_window.settings_manager.set("domain_zooms", zooms)

    def _apply_saved_zoom(self) -> None:
        parent_window = self.parent_window_ref()
        if parent_window and self.view and not self.is_incognito:  # Não aplica zoom salvo para incognito
            domain = QUrl(self.view.url()).host()
            if domain:
                zooms = parent_window.settings_manager.get("domain_zooms", {})
                saved_zoom = zooms.get(domain)
                if saved_zoom and self.view.zoomFactor() != saved_zoom:
                    self.view.setZoomFactor(saved_zoom)

    def load_home(self) -> None:
        if not self.view or not self.page: return  # Cannot load if view/page not initialized
        try:
            html_content = HTML_START_PAGE
            placeholder = "[]; //DATA_PLACEHOLDER"

            parent_window = self.parent_window_ref()
            # Carregar quick links apenas se não for uma aba anônima
            if parent_window and hasattr(parent_window, 'settings_manager') and not self.is_incognito:
                quick_links_path = parent_window.settings_manager.quick_links_path
                try:
                    if os.path.exists(quick_links_path):
                        with open(quick_links_path, 'r', encoding='utf-8') as f:
                            data = f.read() or "[]"
                        html_content = html_content.replace(placeholder, data)
                    else:
                        html_content = html_content.replace(placeholder, "[]")
                except Exception as e:
                    print(f"Erro carregando quick links: {e}")
                    html_content = html_content.replace(placeholder, "[]")
            else:
                html_content = html_content.replace(placeholder,
                                                    "[]")  # Sem quick links para incognito ou se não há settings_manager

            self.view.setHtml(html_content, QUrl("about:home"))
        except Exception as e:
            print(f"Erro carregando página inicial: {e}")

    def navigate(self, url_string: str) -> None:
        if not self.view: return  # Cannot navigate if view not initialized
        try:
            if url_string == "about:home":
                self.load_home()
                return
            if url_string == "about:blank":
                self.view.setUrl(QUrl("about:blank"))
                return
            parent_window = self.parent_window_ref()
            if parent_window:
                # Se for URL interna, abre a aba especial ou navega nela
                if url_string == "about:downloads":
                    parent_window._show_downloads()
                    return
                if url_string == "about:history":
                    parent_window._show_history()
                    return

            url = QUrl.fromUserInput(url_string)
            if not url.scheme():
                url.setScheme("https")

            # Se não for uma URL válida, trata como pesquisa (a menos que seja um path de arquivo)
            if not url.isValid() or (not url.host() and not url_string.startswith("file://")):
                if parent_window:
                    search_engine = parent_window.settings_manager.get("search_engine")
                    if search_engine:
                        search_url = search_engine + QUrl.toPercentEncoding(url_string).data().decode()
                        url = QUrl(search_url)
                    else:
                        url = QUrl(
                            f"https://www.google.com/search?q={QUrl.toPercentEncoding(url_string).data().decode()}")

            self.view.setUrl(url)
        except Exception as e:
            print(f"Erro navegando para {url_string}: {e}")

    def extract_interactive_elements(self) -> None:
        """Extrai elementos interativos da página para ferramentas internas."""
        if not self.view or not self.page: return  # Cannot extract if view/page not initialized
        # JavaScript para coletar informações de elementos interativos
        js_code = """
        (function() {
            try {
                let elementId = 0;
                const elements = [];
                const selectors = [
                    'input:not([type="hidden"]):not([disabled])',
                    'textarea:not([disabled])',
                    'button:not([disabled])',
                    '[role="button"]',
                    'a[href]',
                    '[contenteditable="true"]',
                    'select:not([disabled])'
                ].join(',');

                const allElements = document.querySelectorAll(selectors);
                let isComplex = allElements.length > 50;

                let fullHtml = '';
                if (isComplex) {
                    // Limita o HTML para evitar sobrecarga de memória na comunicação IPC
                    fullHtml = document.body.outerHTML.substring(0, 5000);
                }

                allElements.forEach(el => {
                    try {
                        const rect = el.getBoundingClientRect();
                        const style = getComputedStyle(el);

                        // Filtra elementos não visíveis
                        if (rect.width === 0 || rect.height === 0 ||
                            style.visibility === 'hidden' ||
                            style.display === 'none') {
                            return;
                        }

                        const agnerId = 'agner-el-' + (elementId++);
                        el.dataset.agnerId = agnerId; // Adiciona um ID para fácil referência via JS

                        const innerText = (el.innerText || '').trim().substring(0, 100);
                        const placeholder = el.placeholder || '';
                        const ariaLabel = el.ariaLabel || '';
                        const title = el.title || '';
                        const name = el.name || '';
                        const value = el.value || '';

                        let labelText = '';
                        if (el.id) {
                            const label = document.querySelector(`label[for="${el.id}"]`);
                            if (label) labelText = (label.innerText || '').trim().substring(0, 50);
                        } else if (el.closest('label')) {
                            labelText = (el.closest('label').innerText || '').trim().substring(0, 50);
                        }

                        const context = [
                            placeholder, ariaLabel, title, innerText, labelText, name
                        ].filter(Boolean).join(' | ').trim();

                        let surrounding = '';
                        const parent = el.parentElement;
                        if (parent) {
                            surrounding = Array.from(parent.childNodes)
                                .filter(node => node.nodeType === 3 && node.textContent.trim())
                                .map(node => node.textContent.trim().substring(0, 50))
                                .join(' | ');
                        }

                        let positionDesc = ''; // Descrição da posição na tela
                        if (rect.top < window.innerHeight / 3) positionDesc += 'top ';
                        else if (rect.top > 2 * window.innerHeight / 3) positionDesc += 'bottom ';
                        else positionDesc += 'middle ';

                        if (rect.left < window.innerWidth / 3) positionDesc += 'left';
                        else if (rect.left > 2 * window.innerWidth / 3) positionDesc += 'right';
                        else positionDesc += 'center';

                        const outerHtmlSnippet = el.outerHTML ? el.outerHTML.substring(0, 200) : '';

                        elements.push({
                            id: agnerId,
                            tag: el.tagName.toLowerCase(),
                            type: el.type || el.getAttribute('role') || '',
                            name: name,
                            value: value,
                            label_text: labelText,
                            context: context,
                            surrounding: surrounding,
                            position: positionDesc.trim(),
                            classes: el.className,
                            htmlId: el.id,
                            outer_html_snippet: outerHtmlSnippet,
                            rect: {top: rect.top, left: rect.left, width: rect.width, height: rect.height},
                            visible: true // Presumimos visível após as verificações iniciais
                        });
                    } catch (e) {
                        console.log('Erro processando elemento:', e);
                    }
                });

                const pageInfo = {
                    title: document.title,
                    url: location.href,
                    domain: location.hostname,
                    total: elements.length,
                    is_complex: isComplex,
                    full_html: fullHtml
                };
                console.log("Extracted elements:", elements.length);
                // Limitar elementos para evitar sobrecarga na comunicação IPC
                return {
                    elements: elements.slice(0, 100),
                    pageInfo: pageInfo
                };
            } catch (e) {
                console.log('Erro na extração:', e);
                return { elements: [], pageInfo: {} };
            }
        })();
        """

        try:
            print(f"[SafeBrowserTab] Executando JS para extração de elementos na URL: {self.view.url().toString()}")
            self.page.runJavaScript(js_code, self._on_elements_extracted)
        except Exception as e:
            print(f"Erro ao executar JS para extração: {e}")

    def _on_elements_extracted(self, result: Any) -> None:
        try:
            if self._disposed or not self.view:
                print("[SafeBrowserTab] _on_elements_extracted chamado em aba descartada. Ignorando.")
                return

            url = self.view.url().toString()
            if isinstance(result, dict):
                elements = result.get('elements', [])
                page_info = result.get('pageInfo', {})
                print(f"[SafeBrowserTab] Elementos extraídos do JS. Total: {len(elements)}. URL: {url}")
                self._last_interactive_elements = (url, elements, page_info)
            else:
                print(f"[SafeBrowserTab] Resultado da extração de elementos não é um dicionário: {result}")
        except Exception as e:
            print(f"[SafeBrowserTab] Erro processando elementos extraídos: {e}")

    def click_element(self, element_id: str) -> None:
        """Executa um clique JavaScript em um elemento pelo seu agner-id."""
        if not self.view or not self.page: return  # Cannot click if view/page not initialized
        js_code = f"""
        (function() {{
            try {{
                const el = document.querySelector('[data-agner-id="{element_id}"]');
                if (!el) {{
                    console.error('Elemento com agner-id "{element_id}" não encontrado para clique.');
                    return {{ ok: false, error: 'Element not found' }};
                }}

                el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});

                // Pequeno atraso para a rolagem visual acontecer antes do clique
                setTimeout(() => {{
                    el.click(); // Tenta o método click nativo
                    // Dispara um evento de mouse sintético para garantir o clique
                    const evt = new MouseEvent('click', {{
                        bubbles: true,
                        cancelable: true,
                        view: window
                    }});
                    el.dispatchEvent(evt);
                    console.log('Clicado elemento com agner-id:', '{element_id}');
                }}, 100);

                return {{ ok: true }};
            }} catch (e) {{
                console.error('Erro ao clicar elemento com agner-id "{element_id}":', e);
                return {{ ok: false, error: e.message }};
            }}
        }})();
        """

        try:
            self.page.runJavaScript(js_code)
        except Exception as e:
            print(f"Erro executando click: {e}")

    def _check_and_close_popups(self) -> None:
        """
        Tenta fechar pop-ups e banners de consentimento de cookies usando JavaScript.
        Executado após o carregamento da página.
        """
        if self._disposed or not self.view or not self.page: return  # Cannot check popups if view/page not initialized
        self._suppress_new_windows_until = datetime.datetime.now().timestamp() + 5.0
        js_code = """
        (function() {
            const modalSelectors = [
                '[role="dialog"]', '.modal', '.popup', '.dialog', '.overlay', '.lightbox',
                '.cookie-consent', '.gdpr-banner', '.fc-dialog', '.qc-cmp2-container', // Adicionados seletores comuns
                'div[id*="modal"]', 'div[class*="modal"]',
                'div[id*="popup"]', 'div[class*="popup"]',
                'div[id*="dialog"]', 'div[class*="dialog"]',
                'div[id*="overlay"]', 'div[class*="overlay"]',
                'div[id*="consent"]', 'div[class*="consent"]',
            ];
            const closeButtonSelectors = [
                'button.close', 'button[aria-label*="close" i]', 'button[title*="close" i]',
                'button[aria-label*="fechar" i]', 'button[title*="fechar" i]',
                'button[class*="close"]', 'button[class*="dismiss"]',
                'span.close', 'span.x-icon', 'a.close',
                '[role="button"][aria-label*="close" i]',
                'svg[data-icon="times"]', 'svg[data-testid*="close-icon"]', // Ícones de fechar comuns
                'button[class*="accept"]', 'button[class*="agree"]', 'button[class*="consent"]',
                'a[class*="close"]', 'a[class*="dismiss"]'
            ];

            let closedCount = 0;

            function attemptCloseModal(modal) {
                // Tenta encontrar e clicar um botão de fechar dentro do modal
                for (const selector of closeButtonSelectors) {
                    const closeButton = modal.querySelector(selector);
                    if (closeButton && closeButton.offsetParent !== null && getComputedStyle(closeButton).display !== 'none' && getComputedStyle(closeButton).visibility !== 'hidden') {
                        console.log('Attempting to click close button:', closeButton);
                        closeButton.click();
                        closedCount++;
                        return true;
                    }
                }
                return false;
            }

            for (const selector of modalSelectors) {
                const modals = document.querySelectorAll(selector);
                for (const modal of modals) {
                    const rect = modal.getBoundingClientRect();
                    const isVisible = rect.width > 50 && rect.height > 50 && // Tamanho mínimo para ser um modal
                                     rect.top < window.innerHeight && rect.left < window.innerWidth && // Dentro da viewport
                                     getComputedStyle(modal).visibility !== 'hidden' &&
                                     getComputedStyle(modal).display !== 'none' &&
                                     getComputedStyle(modal).opacity > 0;

                    if (isVisible) {
                        console.log('Found potential modal:', modal);
                        if (attemptCloseModal(modal)) {
                            // Pequeno delay para verificar se o modal realmente desapareceu
                            setTimeout(() => {
                                if (modal.offsetParent !== null && getComputedStyle(modal).display !== 'none' && getComputedStyle(modal).opacity > 0) {
                                    console.log('Modal still visible after click, attempting direct removal:', modal);
                                    modal.remove(); // Remove o modal diretamente do DOM
                                    const backdrop = document.querySelector('.modal-backdrop, .overlay-backdrop');
                                    if (backdrop) backdrop.remove(); // Remove o overlay se houver
                                    closedCount++;
                                }
                            }, 500);
                        }
                    }
                }
            }

            // Fallback para botões de consentimento diretos que não estão em modais óbvios
            if (closedCount === 0) {
                const consentWords = [
                    'accept', 'accept all', 'accept cookies', 'agree', 'agree to all', 'ok',
                    'aceitar', 'aceitar tudo', 'concordar', 'continuar', 'permitir'
                ];
                const directConsentButtons = Array.from(document.querySelectorAll('button, [role="button"], a')).filter((btn) => {
                    const text = (btn.innerText || btn.textContent || btn.getAttribute('aria-label') || '').trim().toLowerCase();
                    const marker = `${btn.className || ''} ${btn.id || ''}`.toLowerCase();
                    return marker.includes('accept') || marker.includes('agree') || marker.includes('consent') ||
                           consentWords.some((word) => text.includes(word));
                });
                for (const btn of directConsentButtons) {
                    if (btn.offsetParent !== null && getComputedStyle(btn).visibility !== 'hidden' && getComputedStyle(btn).display !== 'none' && getComputedStyle(btn).opacity > 0) {
                        console.log('Found direct consent button, clicking:', btn);
                        btn.click();
                        closedCount++;
                        break; // Clique apenas um para evitar múltiplos consentimentos
                    }
                }
            }

            return { closedPopups: closedCount > 0, count: closedCount };
        })();
        """
        # Executa o script com um pequeno atraso para dar tempo ao modal carregar
        # Ao invés disso (que quebra):
        # FUNCIONA - Versão blindada
        def safe_execute_js():
            try:
                if not self._disposed and hasattr(self, 'page') and self.page is not None and hasattr(self.page, 'runJavaScript'):
                    self.page.runJavaScript(js_code, self._on_popups_closed)
                else:
                    print("[SafeBrowserTab] Página já foi descartada, cancelando JavaScript.")
            except (AttributeError, RuntimeError) as e:
                print(f"[SafeBrowserTab] Erro ao executar JS: {e}")

        QTimer.singleShot(3000, safe_execute_js)
        return

        # Use isso (que é blindado):
        def safe_run_javascript():
            try:
                if self.page is not None and hasattr(self.page, 'runJavaScript'):
                    self.page.runJavaScript(js_code, self._on_popups_closed)
                else:
                    print("[SafeBrowserTab] Página já foi descartada, cancelando JavaScript.")
            except (AttributeError, RuntimeError):
                print("[SafeBrowserTab] Erro ao executar JavaScript, página não existe mais.")
                pass


    def _on_popups_closed(self, result: Any) -> None:
        parent_ref = getattr(self, 'parent_window_ref', None)
        if self._disposed or not callable(parent_ref):
            return
        parent_window = parent_ref()
        if not parent_window:
            return
        if result and result.get('closedPopups'):
            print(f"[SafeBrowserTab] Fechou {result.get('count')} pop-up(s).")
            if parent_window:
                parent_window.status_label.setText("Pop-up(s) fechado(s).")
        else:
            print("[SafeBrowserTab] Nenhum pop-up encontrado ou fechado.")

    def dispose(self) -> None:
        """
        Método de dispose seguro para a aba. Libera recursos e desconecta sinais.
        Essencial para evitar vazamentos de memória e crashes.
        """
        tab_url = self.view.url().toString() if self.view else 'N/A'
        print(f"[SafeBrowserTab] Iniciando dispose para aba: {tab_url}")
        self._disposed = True  # Define a flag para evitar que callbacks tardios causem erros

        if self.view and self.page:
            try:
                # Desconectar SINAIS da view (QWebEngineView)
                self.view.loadStarted.disconnect(self._on_load_started)
                self.view.loadProgress.disconnect(self._on_load_progress)
                self.view.loadFinished.disconnect(self._on_load_finished)
                self.view.titleChanged.disconnect(self._on_title_changed)
                self.view.iconChanged.disconnect(self._on_icon_changed)
                self.view.urlChanged.disconnect(self._on_url_changed)
                print(f"[SafeBrowserTab] Sinais de QWebEngineView desconectados para {tab_url}.")
            except (TypeError, RuntimeError) as e:
                print(
                    f"[SafeBrowserTab] Aviso: Não foi possível desconectar todos os sinais de QWebEngineView para {tab_url}: {e}")

            try:
                # Desconectar SINAIS da page (QWebEnginePage)
                self.page.zoomFactorChanged.disconnect(self._on_zoom_changed)
                # O sinal downloadRequested do QWebEngineProfile é conectado ao DownloadManager,
                # que é um objeto de nível superior (MainWindow), então não precisa ser desconectado aqui.
                print(f"[SafeBrowserTab] Sinais de QWebEnginePage desconectados para {tab_url}.")
            except (TypeError, RuntimeError) as e:
                print(
                    f"[SafeBrowserTab] Aviso: Não foi possível desconectar todos os sinais de QWebEnginePage para {tab_url}: {e}")

            try:
                # Desconectar SINAIS CUSTOMIZADOS da SafeBrowserTab
                self.loadFinishedSignal.disconnect(self._on_load_finished)
                self.loadingChanged.disconnect(self._on_tab_loading_changed)
                self.zoomChanged.disconnect(self._on_zoom_changed)
                print(f"[SafeBrowserTab] Sinais customizados desconectados para {tab_url}.")
            except (TypeError, RuntimeError) as e:
                print(
                    f"[SafeBrowserTab] Aviso: Não foi possível desconectar todos os sinais customizados para {tab_url}: {e}")

            # Parar qualquer carregamento em andamento
            if self._is_loading:
                try:
                    self.view.stop()
                    print(f"[SafeBrowserTab] Carregamento parado para {tab_url}.")
                except Exception as e:
                    print(f"[SafeBrowserTab] Erro ao parar carregamento: {e}")

            # Desassociar a página da view antes de deletar a view
            if self.page:
                self.page.setWebChannel(None)  # Desconecta o WebChannel
                self.view.setPage(None)  # Desvincula a página da view
                self.page.deleteLater() # Agenda a página para exclusão
                self.page = None # Limpa a referência
                print(f"[SafeBrowserTab] QWebEnginePage desvinculada e agendada para exclusão para {tab_url}.")

            # Agendar a view para exclusão. Isso deve liberar a memória alocada pelo Chromium.
            self.view.deleteLater()
            print(f"[SafeBrowserTab] QWebEngineView ({self.view}) agendada para exclusão para {tab_url}.")
            self.view = None  # Limpa a referência para evitar ponteiros pendentes
            self.parent_window_ref = None  # Limpa a weakref

        print(f"[SafeBrowserTab] Dispose de SafeBrowserTab concluído para {tab_url}.")


