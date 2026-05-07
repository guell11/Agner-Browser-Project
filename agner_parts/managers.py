# ================= CORE/ (tabs, perfil web, histórico, downloads) =================

# --- Database Managers Seguros ---
class SafeDatabaseManager:
    """
    Gerenciador de banco de dados seguro com tratamento de erros.
    Agora suporta diretórios de perfil.
    """

    def __init__(self, db_name: str, profile_dir: str):
        self.conn: Optional[sqlite3.Connection] = None
        self.db_name = db_name  # Guardar nome para debug
        try:
            db_folder = os.path.join(profile_dir, "db")
            os.makedirs(db_folder, exist_ok=True)
            self.db_path = os.path.join(db_folder, f"{db_name}.db")
            self._connect()
        except Exception as e:
            print(f"Erro inicializando banco {db_name} em {profile_dir}: {e}")
            self.conn = None

    def _connect(self) -> None:
        try:
            if self.conn:
                self.conn.close()  # Fecha conexão existente antes de reabrir
            # Aumentar timeout para evitar 'database is locked' em cenários concorrentes
            self.conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            # WAL mode melhora concorrência de leitura/escrita
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")  # Balanço entre performance e durabilidade
            self.conn.commit()
            print(f"Conectado ao DB: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Erro conectando banco {self.db_name} em {self.db_path}: {e}")
            self.conn = None

    def execute(self, query: str, params: tuple = ()) -> bool:
        """Executa uma query no banco de dados, retorna True em sucesso, False em falha."""
        try:
            if not self.conn:
                self._connect()  # Tenta reconectar se a conexão não existe
            if not self.conn:
                print(f"Erro: Conexão com o banco {self.db_name} não estabelecida para executar '{query[:50]}...'")
                return False

            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            cursor.close()
            return True
        except sqlite3.Error as e:
            print(f"Erro executando query '{query[:50]}...' no {self.db_name}: {e}")
            return False
        except Exception as e:
            print(f"Erro inesperado executando query '{query[:50]}...' no {self.db_name}: {e}")
            return False

    def fetchall(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Executa uma query e retorna todos os resultados como lista de Row."""
        try:
            if not self.conn:
                self._connect()
            if not self.conn:
                print(f"Erro: Conexão com o banco {self.db_name} não estabelecida para fetchall '{query[:50]}...'")
                return []

            cursor = self.conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results
        except sqlite3.Error as e:
            print(f"Erro no fetchall '{query[:50]}...' no {self.db_name}: {e}")
            return []
        except Exception as e:
            print(f"Erro inesperado no fetchall '{query[:50]}...' no {self.db_name}: {e}")
            return []

    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Executa uma query e retorna o primeiro resultado como Row, ou None."""
        try:
            if not self.conn:
                self._connect()
            if not self.conn:
                print(f"Erro: Conexão com o banco {self.db_name} não estabelecida para fetchone '{query[:50]}...'")
                return None

            cursor = self.conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            cursor.close()
            return result
        except sqlite3.Error as e:
            print(f"Erro no fetchone '{query[:50]}...' no {self.db_name}: {e}")
            return None
        except Exception as e:
            print(f"Erro inesperado no fetchone '{query[:50]}...' no {self.db_name}: {e}")
            return None

    def close(self) -> None:
        """Fecha a conexão com o banco de dados."""
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
                print(f"Conexão com o DB {self.db_name} fechada.")
        except Exception as e:
            print(f"Erro ao fechar conexão com o banco {self.db_name}: {e}")


class BookmarkManager:
    """Gerenciador de favoritos com interface completa, agora por perfil."""

    def __init__(self, profile_dir: str):
        self.db = SafeDatabaseManager("bookmarks", profile_dir)
        self._create_tables()

    def _create_tables(self) -> None:
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                favicon TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                folder TEXT DEFAULT 'default'
            )
        ''')

    def add_bookmark(self, title: str, url: str, favicon: Optional[str] = None) -> bool:
        return self.db.execute(
            'INSERT OR REPLACE INTO bookmarks (title, url, favicon) VALUES (?, ?, ?)',
            (title, url, favicon)
        )

    def remove_bookmark(self, url: str) -> bool:
        return self.db.execute('DELETE FROM bookmarks WHERE url = ?', (url,))

    def get_bookmark(self, url: str) -> Optional[sqlite3.Row]:
        return self.db.fetchone('SELECT * FROM bookmarks WHERE url = ?', (url,))

    def get_all_bookmarks(self) -> List[sqlite3.Row]:
        return self.db.fetchall('SELECT * FROM bookmarks ORDER BY created_at DESC')

    def is_bookmarked(self, url: str) -> bool:
        return self.get_bookmark(url) is not None


class HistoryManager:
    """Gerenciador de histórico seguro, agora por perfil."""

    def __init__(self, profile_dir: str):
        self.db = SafeDatabaseManager("history", profile_dir)
        self._create_tables()

    def _create_tables(self) -> None:
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                visit_count INTEGER DEFAULT 1
            )
        ''')
        self.db.execute('CREATE INDEX IF NOT EXISTS idx_history_url ON history (url);')

    def add_visit(self, url: str, title: Optional[str] = None) -> None:
        existing = self.db.fetchone('SELECT id, visit_count FROM history WHERE url = ?', (url,))
        if existing:
            self.db.execute(
                'UPDATE history SET visit_count = ?, visit_time = CURRENT_TIMESTAMP, title = ? WHERE id = ?',
                (existing['visit_count'] + 1, title, existing['id'])
            )
        else:
            self.db.execute('INSERT INTO history (url, title) VALUES (?, ?)', (url, title))

    def get_all_history(self) -> List[sqlite3.Row]:
        return self.db.fetchall('SELECT * FROM history ORDER BY visit_time DESC')

    def clear_history(self) -> bool:
        return self.db.execute('DELETE FROM history')


class DownloadManager(QObject):
    download_started = pyqtSignal(QWebEngineDownloadItem)
    download_updated = pyqtSignal(QWebEngineDownloadItem)
    download_finished = pyqtSignal(QWebEngineDownloadItem)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.active_downloads: Dict[str, QWebEngineDownloadItem] = {}
        self.completed_downloads: List[QWebEngineDownloadItem] = []
        # Pasta de downloads padrão do sistema
        self.download_path = os.path.join(str(Path.home()), "Downloads")
        os.makedirs(self.download_path, exist_ok=True)  # Garante que a pasta exista

    def handle_download_requested(self, download_item: QWebEngineDownloadItem) -> None:
        try:
            suggested_filename = os.path.basename(QUrl(download_item.url()).path())
            if not suggested_filename:
                suggested_filename = "downloaded_file"

            final_path = os.path.join(self.download_path, suggested_filename)
            counter = 1
            # Evita sobrescrever arquivos existentes adicionando um contador
            while os.path.exists(final_path):
                name, ext = os.path.splitext(suggested_filename)
                final_path = os.path.join(self.download_path, f"{name}({counter}){ext}")
                counter += 1

            download_item.setPath(final_path)

            # Conecta os sinais do item de download para atualizar o progresso e estado
            download_item.stateChanged.connect(lambda state: self._on_download_state_changed(download_item, state))
            download_item.downloadProgress.connect(
                lambda bytes_received, bytes_total: self._on_download_progress(download_item, bytes_received,
                                                                               bytes_total))

            self.active_downloads[download_item.path()] = download_item
            self.download_started.emit(download_item)  # Emite sinal para UI ou logs

            download_item.accept()  # Aceita o download e inicia-o
            print(f"Download iniciado: {download_item.url().toDisplayString()} para {download_item.path()}")

        except Exception as e:
            print(f"Erro ao iniciar download: {e}")
            download_item.cancel()  # Cancela o download em caso de erro

    def _on_download_state_changed(self, download_item: QWebEngineDownloadItem,
                                   state: QWebEngineDownloadItem.DownloadState) -> None:
        if state == QWebEngineDownloadItem.DownloadState.DownloadInterrupted:
            print(f"Download interrompido: {download_item.url().toDisplayString()}")
            if download_item.path() in self.active_downloads:
                del self.active_downloads[download_item.path()]
            self.download_finished.emit(download_item)
        elif state == QWebEngineDownloadItem.DownloadState.DownloadFinished:
            print(f"Download concluído: {download_item.path()}")
            if download_item.path() in self.active_downloads:
                del self.active_downloads[download_item.path()]
            self.completed_downloads.append(download_item)
            self.download_finished.emit(download_item)

        self.download_updated.emit(download_item)  # Atualiza a UI

    def _on_download_progress(self, download_item: QWebEngineDownloadItem, bytes_received: int,
                              bytes_total: int) -> None:
        self.download_updated.emit(download_item)  # Atualiza a UI

    def get_all_downloads(self) -> List[QWebEngineDownloadItem]:
        return list(self.active_downloads.values()) + self.completed_downloads


# --- Extension Manager ---
class ExtensionManager:
    """
    Gerenciador de extensões simples (inspirado em Chrome).
    Extensões são carregadas por perfil.
    """

    def __init__(self, profile_dir: str):
        self.extensions_dir = os.path.join(profile_dir, "extensions")
        os.makedirs(self.extensions_dir, exist_ok=True)  # Garante diretório de extensões
        self.extensions: Dict[str, Dict[str, Any]] = {}
        self.load_extensions()

    def load_extensions(self) -> None:
        self.extensions = {}
        for ext_dir_name in os.listdir(self.extensions_dir):
            ext_path = os.path.join(self.extensions_dir, ext_dir_name)
            manifest_path = os.path.join(ext_path, "manifest.json")
            if os.path.isdir(ext_path) and os.path.exists(manifest_path):
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    self.extensions[ext_dir_name] = manifest
                    print(f"Extensão carregada: {manifest.get('name', ext_dir_name)}")
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Erro ao carregar manifest da extensão '{ext_dir_name}': {e}")
            else:
                print(f"Diretório de extensão inválido ou manifest.json ausente: {ext_path}")

    def install_extension(self, zip_path: str) -> Optional[str]:
        """Instala uma extensão a partir de um arquivo ZIP."""
        try:
            # Usa o nome do arquivo zip como ID da extensão (sem a extensão .zip)
            ext_id = os.path.basename(zip_path).replace('.zip', '')
            ext_install_path = os.path.join(self.extensions_dir, ext_id)

            # Se já existir, remove para garantir uma instalação limpa
            if os.path.exists(ext_install_path):
                import shutil
                shutil.rmtree(ext_install_path)
                print(f"Extensão existente '{ext_id}' removida antes da reinstalação.")

            os.makedirs(ext_install_path, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(ext_install_path)  # Extrai para o diretório do perfil

            self.load_extensions()  # Recarrega a lista de extensões após a instalação
            print(f"Extensão '{ext_id}' instalada com sucesso.")
            return ext_id
        except Exception as e:
            print(f"Erro ao instalar extensão '{zip_path}': {e}")
            return None

    def uninstall_extension(self, ext_id: str) -> None:
        """Desinstala uma extensão pelo seu ID."""
        ext_path = os.path.join(self.extensions_dir, ext_id)
        if os.path.exists(ext_path):
            import shutil
            try:
                shutil.rmtree(ext_path)
                if ext_id in self.extensions:
                    del self.extensions[ext_id]  # Remove do cache em memória
                print(f"Extensão '{ext_id}' desinstalada com sucesso.")
            except Exception as e:
                print(f"Erro ao desinstalar extensão '{ext_id}': {e}")
        else:
            print(f"Extensão '{ext_id}' não encontrada para desinstalação.")

    def inject_extensions(self, page: QWebEnginePage) -> None:
        """Injeta scripts de conteúdo das extensões na QWebEnginePage."""
        for ext_id, manifest in self.extensions.items():
            content_scripts = manifest.get('content_scripts', [])
            for script_info in content_scripts:
                # Filtrar URLs para injeção (host, path, match_about_blank, etc.)
                # Esta é uma simplificação. Uma implementação completa usaria "matches" ou "exclude_matches".
                # Por simplicidade, injetaremos todos os content scripts em todas as páginas por enquanto,
                # ou você pode adicionar uma lógica de URL matching aqui.

                for js_file in script_info.get('js', []):
                    js_path = os.path.join(self.extensions_dir, ext_id, js_file)
                    if os.path.exists(js_path):
                        try:
                            with open(js_path, 'r', encoding='utf-8') as f:
                                js_code = f.read()

                            injection_script = QWebEngineScript()
                            injection_script.setName(f"{ext_id}_{js_file}")

                            # Definir o ponto de injeção
                            run_at = script_info.get('run_at', 'document_idle')
                            point = QWebEngineScript.InjectionPoint.DocumentReady

                            if run_at == 'document_start':
                                point = QWebEngineScript.InjectionPoint.DocumentCreation
                            elif run_at == 'document_end' or run_at == 'document_idle':
                                point = QWebEngineScript.InjectionPoint.DocumentReady

                            injection_script.setInjectionPoint(point)
                            # Usar ApplicationWorld para evitar conflitos com o JS da página
                            injection_script.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld)
                            injection_script.setSourceCode(js_code)
                            page.scripts().insert(injection_script)
                            print(f"Injetado script '{js_file}' da extensão '{ext_id}'.")
                        except Exception as e:
                            print(f"Erro ao injetar script '{js_file}' da extensão '{ext_id}': {e}")
                    else:
                        print(f"Arquivo de script não encontrado: {js_path}")


# --- Settings Manager ---
class SettingsManager:
    """
    Gerenciador de configurações com QSettings seguro e suporte a múltiplos perfis.
    Gerencia um diretório base para todos os perfis e configurações específicas de cada perfil.
    """

    def __init__(self, profile_name: str):
        self._base_app_dir = os.path.join(str(Path.home()), ".agner_browser")
        os.makedirs(self._base_app_dir, exist_ok=True)  # Garante o diretório base da aplicação

        self._profiles_dir = os.path.join(self._base_app_dir, "profiles")
        os.makedirs(self._profiles_dir, exist_ok=True)  # Garante o diretório para todos os perfis

        # QSettings global para armazenar qual perfil está ativo
        self._global_settings = QSettings("AGNER", "Browser_Global")
        self._current_profile_name = self._global_settings.value("current_profile", "default", type=str)

        # Se um nome de perfil inicial for fornecido (ex: via linha de comando ou após troca), sobrescreve o global
        if profile_name and profile_name != self._current_profile_name:
            self._current_profile_name = profile_name
            self._global_settings.setValue("current_profile", profile_name)
            self._global_settings.sync()  # Garante que a mudança seja salva imediatamente

        # Define o diretório específico do perfil atual
        self.profile_dir = os.path.join(self._profiles_dir, self._current_profile_name)
        os.makedirs(self.profile_dir, exist_ok=True)  # Garante que o diretório do perfil exista

        self.settings: Optional[QSettings] = None
        self.quick_links_path: str = os.path.join(self.profile_dir, "quick_links.json")
        self.domain_zooms: Dict[str, float] = {}  # Cache in-memory para zooms por domínio

        try:
            # QSettings para as configurações específicas DESTE perfil
            self.settings = QSettings(self.profile_dir, "profile_settings")
            self._load_defaults()
            self.domain_zooms = self.get("domain_zooms", {})  # Carrega o cache de zooms
        except Exception as e:
            print(f"Erro inicializando configurações para perfil '{profile_name}': {e}")
            self.settings = None

    def _load_defaults(self) -> None:
        """Carrega ou define os valores padrão para as configurações do perfil."""
        defaults = {
            "theme": "chrome_clean",
            "homepage": "about:home",
            "startup_mode": "homepage",  # last_session, homepage, blank
            "font_size": 14,
            "zoom_factor": 1.0,  # Zoom padrão para todas as páginas
            "save_history": True,
            "block_ads": True,
            "search_engine": "https://www.google.com/search?q=",
            "window_geometry": [100, 100, 1400, 900],  # [x, y, width, height]
            "enable_javascript": True,
            "enable_dark_mode": False,
            "gamer_mode": True,
            "auto_close_popups": False,
            "restore_max_tabs": 6,
            "max_tab_width": 220,
            "domain_zooms": {}  # Armazena zooms específicos por domínio
        }

        for key, value in defaults.items():
            if self.settings and not self.settings.contains(key):
                self.set(key, value)  # Define o padrão se a configuração não existir

    def get(self, key: str, default: Any = None, type: Optional[type] = None) -> Any:
        """Obtém uma configuração, com opção de forçar tipo."""
        try:
            if not self.settings:
                return default
            val = self.settings.value(key, default)

            # Conversões de tipo explícitas para evitar problemas de QVariant
            if type is bool:
                if isinstance(val, str):
                    return val.lower() == 'true'
                elif isinstance(val, int):
                    return bool(val)
                return bool(val)  # Default boolean conversion
            if type is int:
                return int(val)
            if type is float:
                return float(val)
            return val
        except Exception as e:
            print(f"Erro ao obter configuração '{key}' com tipo '{type}': {e}")
            return default

    def set(self, key: str, value: Any) -> None:
        """Define uma configuração e salva-a."""
        try:
            if self.settings:
                self.settings.setValue(key, value)
                self.settings.sync()  # Força a gravação imediata no disco
            if key == "domain_zooms":
                self.domain_zooms = value  # Atualiza o cache in-memory
        except Exception as e:
            print(f"Erro salvando configuração {key}: {e}")

    def get_theme(self) -> dict:
        """Retorna o dicionário de tema completo com base na configuração."""
        theme_name = self.get("theme", "chrome_clean")
        if theme_name not in THEMES:
            theme_name = "chrome_clean"
            self.set("theme", theme_name)
        return THEMES.get(theme_name, THEMES["chrome_clean"])

    def _session_tab_limit(self) -> int:
        try:
            return max(1, min(12, self.get("restore_max_tabs", 6, type=int)))
        except Exception:
            return 6

    @staticmethod
    def _session_url_key(url: str) -> str:
        clean_url = (url or "").strip()
        if clean_url.startswith("http"):
            clean_url = clean_url.split("#", 1)[0]
        return clean_url.rstrip("/").lower()

    def _clean_session_urls(self, urls: Any) -> List[str]:
        if isinstance(urls, str):
            raw_urls = [urls]
        elif isinstance(urls, (list, tuple)):
            raw_urls = list(urls)
        else:
            raw_urls = []

        cleaned: List[str] = []
        seen: set[str] = set()
        limit = self._session_tab_limit()

        for raw_url in raw_urls:
            url = str(raw_url).strip() if raw_url is not None else ""
            if not url or url == "about:blank":
                continue
            if url.startswith("https://www.google.com/search?q=about%3Ablank"):
                continue

            key = "about:home" if url == "about:home" else self._session_url_key(url)
            if not key or key in seen:
                continue

            seen.add(key)
            cleaned.append(url)
            if len(cleaned) >= limit:
                break

        return cleaned or ["about:home"]

    def save_session(self, tabs: List[QWidget]) -> None:
        """Salva as URLs das abas abertas (exceto anônimas) para a próxima sessão."""
        try:
            urls = []
            for tab in tabs:
                if isinstance(tab, SafeBrowserTab) and hasattr(tab, 'view') and tab.view and not tab.is_incognito:
                    url = tab.view.url().toString()
                    if url:
                        urls.append(url)

            if urls:
                self.set("last_session", self._clean_session_urls(urls))
            else:
                self.set("last_session", ["about:home"])  # Se não houver abas válidas, volta para a página inicial
        except Exception as e:
            print(f"Erro salvando sessão: {e}")

    def load_session(self) -> List[str]:
        """Carrega as URLs da última sessão."""
        try:
            urls = self.get("last_session", ["about:home"])
            cleaned = self._clean_session_urls(urls)
            if cleaned != urls:
                self.set("last_session", cleaned)
            return cleaned
        except Exception as e:
            print(f"Erro carregando sessão: {e}")
            return ["about:home"]

    def get_profile_dir(self, profile_name: str) -> str:
        """Retorna o caminho completo para o diretório de um perfil específico."""
        return os.path.join(self._profiles_dir, profile_name)

    def get_all_profiles(self) -> List[str]:
        """Retorna uma lista de todos os nomes de perfis existentes."""
        return [d for d in os.listdir(self._profiles_dir) if os.path.isdir(os.path.join(self._profiles_dir, d))]

    def get_current_profile_name(self) -> str:
        """Retorna o nome do perfil ativo atualmente."""
        return self._current_profile_name

    def add_profile(self, profile_name: str) -> bool:
        """Adiciona um novo perfil."""
        if not profile_name or not profile_name.strip():
            return False  # Nome inválido
        # Remove caracteres inválidos para nome de diretório
        profile_name = re.sub(r'[\\/:*?"<>|]', '', profile_name.strip())
        if not profile_name: return False

        profile_path = self.get_profile_dir(profile_name)
        if os.path.exists(profile_path):
            return False  # Perfil já existe

        try:
            os.makedirs(profile_path)
            # Cria configurações padrão para o novo perfil
            new_profile_settings = QSettings(profile_path, "profile_settings")
            defaults = {
                "theme": "chrome_clean", "homepage": "about:home", "startup_mode": "homepage",
                "font_size": 14, "zoom_factor": 1.0, "save_history": True, "block_ads": True,
                "search_engine": "https://www.google.com/search?q=",
                "enable_javascript": True, "enable_dark_mode": False, "max_tab_width": 220,
                "gamer_mode": True, "auto_close_popups": False, "restore_max_tabs": 6,
                "domain_zooms": {}
            }
            for key, value in defaults.items():
                new_profile_settings.setValue(key, value)
            new_profile_settings.sync()
            print(f"Perfil '{profile_name}' criado em {profile_path}")
            return True
        except Exception as e:
            print(f"Erro ao criar diretório para o novo perfil '{profile_name}': {e}")
            return False

    def set_current_profile(self, profile_name: str) -> None:
        """Define o perfil ativo (isto requer reinício do navegador)."""
        if profile_name in self.get_all_profiles():
            self._global_settings.setValue("current_profile", profile_name)
            self._global_settings.sync()
            self._current_profile_name = profile_name
            print(f"Perfil atual definido para '{profile_name}'. Reinicie o navegador.")
        else:
            raise ValueError(f"Profile '{profile_name}' does not exist.")

    def delete_profile(self, profile_name: str) -> bool:
        """Exclui um perfil e todos os seus dados."""
        if profile_name == self._current_profile_name:
            return False  # Não pode excluir o perfil ativo
        profile_path = self.get_profile_dir(profile_name)
        if os.path.exists(profile_path):
            import shutil
            try:
                shutil.rmtree(profile_path)
                print(f"Perfil '{profile_name}' e seus dados excluídos de {profile_path}.")
                return True
            except Exception as e:
                print(f"Erro ao excluir diretório do perfil '{profile_name}': {e}")
                return False
        return False


# --- AdBlocker ---
class AdBlocker:
    def __init__(self):
        self.enabled: bool = True
        self.blocked_count: int = 0
        # Lista de padrões comuns de anúncios e rastreadores.
        # Em uma aplicação real, isso viria de uma lista de filtros muito maior (ex: EasyList).
        self.patterns: List[str] = [
            "doubleclick.net", "googlesyndication.com", "googletagmanager.com",
            "google-analytics.com", "facebook.net/ads", "criteo.com", "outbrain.com",
            "taboola.com", "adservice.google.com", "adsensecustomsearchads.com",
            "cdn.jsdelivr.net/gh/AdguardTeam/AdguardFilters/",
            # Exemplo de URL de lista de filtros (não o arquivo em si)
            "ad.doubleclick.net", "ad.youtube.com", "admob.com", "ads.com", "adtech.com",
            "analytics.google.com", "pixel.facebook.com", "track.com", "tracker.com",
            "googletagservices.com", "adroll.com", "adnxs.com", "rubiconproject.com",
            "openx.net", "yieldmo.com", "pubmatic.com", "appnexus.com", "bidswitch.net",
            "lijit.com", "sharethrough.com", "indexexchange.com", "sonobi.com", "teads.tv",
            "adform.net", "adition.com", "smartadserver.com", "adzerk.net", "adreactor.com",
            "adcash.com", "popads.net", "propellerads.com", "adfly.com", "mgid.com",
            "exoclick.com", "trafficjunky.net", "adultadworld.com", "eromanga-ads.com",
            "porn-ads.com", "sexad.com", "adult-content.com", "erotic-ads.com",
            "malwarebytes.com/adblock",  # Exemplo de fonte de lista de anúncios
            "easylist.txt", "fanboy-annoyance.txt", "adguard-base.txt"  # Nomes de listas comuns (não URLs reais)
        ]

    def should_block(self, url: QUrl) -> bool:
        """Verifica se uma URL deve ser bloqueada."""
        if not self.enabled:
            return False

        url_str = url.toString().lower()

        # Bloqueia acesso a arquivos locais por script/recursos para segurança
        # A menos que seja do diretório de extensões do próprio navegador.
        profile_dir = ""
        # Tenta obter a instância da MainWindow para pegar o profile_dir atual
        parent_window = QApplication.instance().findChild(SafeMainWindow)
        if parent_window and hasattr(parent_window, 'settings_manager'):
            profile_dir = parent_window.settings_manager.profile_dir.lower()

        if url.scheme() == "file" and not url.path().lower().startswith(
                os.path.join(profile_dir, "extensions").lower()):
            # Permite o acesso a recursos dentro do próprio diretório de extensões do perfil
            print(f"Blocking file:// access for: {url_str}")
            self.blocked_count += 1
            return True

        for pattern in self.patterns:
            if pattern in url_str:
                self.blocked_count += 1
                return True
        return False


class SafeAdRequestInterceptor(QWebEngineUrlRequestInterceptor):
    """
    Interceptor de requisições de URL que usa o AdBlocker para bloquear URLs.
    """

    def __init__(self, blocker: AdBlocker, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.blocker = blocker

    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
        """
        Intercepta a requisição e a bloqueia se o AdBlocker determinar que sim.
        """
        try:
            if self.blocker.should_block(info.requestUrl()):
                info.block(True)  # Bloqueia a requisição
        except Exception as e:
            print(f"Erro no interceptor: {e}")


# --- Master Key Manager (for passwords) ---
class MasterKeyManager:
    """
    Gerencia a chave mestra e a criptografia/descriptografia de senhas.
    A chave mestra é derivada de uma senha fixa de placeholder e um salt por perfil.
    ATENÇÃO: Em uma aplicação real, a "senha mestra" seria solicitada ao usuário
    ou gerenciada por um sistema de chaves do sistema operacional (keyring).
    O uso de um placeholder FIXO torna este sistema INSEGURO para senhas reais.
    """

    def __init__(self, profile_dir: str):
        self.db = SafeDatabaseManager("passwords", profile_dir)  # Banco de dados de senhas por perfil
        self._create_tables()
        self._master_key: Optional[bytes] = None
        self.profile_dir = profile_dir  # Usado para armazenar o salt por perfil

        # Placeholder para a senha mestra para demonstração.
        # NUNCA USE ISSO EM PRODUÇÃO.
        self._placeholder_master_password = b"MySuperSecretMasterPassword123!"  # MUITO INSEGURO
        self._salt_file_path = os.path.join(self.profile_dir, "master_key_salt.bin")
        self._load_master_key()

    def _create_tables(self) -> None:
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hostname TEXT NOT NULL,
                username TEXT NOT NULL,
                encrypted_password TEXT NOT NULL,
                UNIQUE(hostname, username)
            )
        ''')

    def _load_master_key(self) -> None:
        if not CRYPTO_AVAILABLE:
            print("Criptografia não disponível. MasterKeyManager desabilitado.")
            return

        salt: bytes
        # Carrega o salt existente ou gera um novo e o salva
        if os.path.exists(self._salt_file_path):
            with open(self._salt_file_path, 'rb') as f:
                salt = f.read()
        else:
            salt = os.urandom(16)  # Gera um salt aleatório de 16 bytes
            with open(self._salt_file_path, 'wb') as f:
                f.write(salt)

        # Deriva a chave de criptografia usando Scrypt (resistente a ataques de força bruta)
        kdf = Scrypt(
            salt=salt,
            length=32,  # Tamanho da chave de saída em bytes
            n=2 ** 14,  # Fator de custo de CPU/memória (2^14 iterações)
            r=8,  # Fator de custo de bloco (8 blocos)
            p=1,  # Fator de paralelização (1 thread)
            backend=default_backend()
        )
        try:
            # Deriva a chave mestra a partir da senha placeholder e do salt
            self._master_key = kdf.derive(self._placeholder_master_password)
            print("Master key derivada com sucesso (usando placeholder).")
        except Exception as e:
            print(f"Erro ao derivar chave mestra: {e}")
            self._master_key = None

    def encrypt_password(self, password: str) -> Optional[str]:
        """Criptografa uma senha usando Fernet."""
        if not self._master_key:
            print("Chave mestra não disponível para criptografia.")
            return None
        try:
            # Fernet requer uma chave base64 URL-safe de 32 bytes
            f = Fernet(base64.urlsafe_b64encode(self._master_key))
            return f.encrypt(password.encode()).decode()  # Criptografa e retorna como string
        except Exception as e:
            print(f"Erro ao criptografar senha: {e}")
            return None

    def decrypt_password(self, encrypted_password: str) -> Optional[str]:
        """Descriptografa uma senha usando Fernet."""
        if not self._master_key:
            print("Chave mestra não disponível para descriptografia.")
            return None
        try:
            f = Fernet(base64.urlsafe_b64encode(self._master_key))
            return f.decrypt(encrypted_password.encode()).decode()  # Descriptografa e retorna como string
        except InvalidToken:
            print("Token de criptografia inválido (senha incorreta ou dados corrompidos).")
            return None
        except Exception as e:
            print(f"Erro ao descriptografar senha: {e}")
            return None

    def save_password(self, hostname: str, username: str, encrypted_password: str) -> bool:
        """Salva uma senha criptografada no banco de dados."""
        return self.db.execute(
            'INSERT OR REPLACE INTO passwords (hostname, username, encrypted_password) VALUES (?, ?, ?)',
            (hostname, username, encrypted_password)
        )

    def get_password(self, hostname: str, username: str) -> Optional[str]:
        """Recupera e descriptografa uma senha do banco de dados."""
        row = self.db.fetchone('SELECT encrypted_password FROM passwords WHERE hostname = ? AND username = ?',
                               (hostname, username))
        if row:
            return self.decrypt_password(row['encrypted_password'])
        return None

    def get_all_passwords(self) -> List[sqlite3.Row]:
        """Retorna todas as senhas (criptografadas) do banco de dados."""
        return self.db.fetchall('SELECT hostname, username, encrypted_password FROM passwords')


