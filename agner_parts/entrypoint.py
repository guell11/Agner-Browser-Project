# ================= Função Principal =================
def main() -> None:
    try:
        print("Iniciando AGNER Browser...")
        os.environ.setdefault(
            "QTWEBENGINE_CHROMIUM_FLAGS",
            "--disable-gpu --disable-gpu-compositing --disable-zero-copy --disable-features=CalculateNativeWinOcclusion"
        )
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings, True)
        app = QApplication(sys.argv)
        app.setApplicationName("AGNER Browser")
        app.setApplicationVersion("2.0.0")
        app.setOrganizationName("AGNER")
        app.setStyle("Fusion") # Estilo moderno para a aplicação

        # Determina o perfil atual a ser carregado
        # Lê a configuração global para saber qual perfil usar
        global_settings = QSettings("AGNER", "Browser_Global")
        current_profile_name = global_settings.value("current_profile", "default", type=str)
        print(f"Carregando perfil inicial: {current_profile_name}")

        main_window = SafeMainWindow(initial_profile_name=current_profile_name)
        main_window.show()
        print("AGNER Browser iniciado.")

        # Executa o loop de eventos da aplicação.
        # sys.exit(app.exec()) é preferível para garantir que a aplicação saia corretamente.
        exit_code = app.exec()
        print(f"AGNER Browser finalizado (código: {exit_code})")
        sys.exit(exit_code)
    except Exception as e:
        print(f"Erro crítico: {e}")
        traceback.print_exc() # Imprime o stack trace completo para depuração
        sys.exit(1)


if __name__ == "__main__":
    main()
