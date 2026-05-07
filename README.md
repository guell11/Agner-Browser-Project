# AGNER Browser

<img width="2550" height="1354" alt="AGNER Browser" src="https://github.com/user-attachments/assets/f67ba505-3fe4-493f-b3b0-fd5a5c31807d" />

> Navegador desktop experimental desenvolvido em Python com PyQt6 e QtWebEngine.
> Feito para explorar uma experiencia moderna com perfis locais, gerenciamento interno de dados, personalizacao visual consistente e recursos inspirados em navegadores atuais. Porque aparentemente criar um navegador do zero ainda parece uma boa ideia para programadores. E sinceramente? Ficou bem legal 😶

---

# Visao Geral

O **AGNER Browser** combina uma estrutura modular em Python com recursos modernos de navegacao desktop:

* Sistema de perfis locais independentes.
* Restauracao de sessao entre execucoes.
* Favoritos, historico e downloads integrados.
* Pagina inicial personalizada.
* Suporte a temas claro e escuro consistentes.
* Bloqueio basico de anuncios e rastreadores.
* Sistema local de extensoes inspirado na Chrome Web Store.
* Interface baseada em QtWebEngine com arquitetura modular.
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/5643cb56-5ed8-4ad1-8edf-8098bb20bbf0" />

---

# Recursos

## Navegacao e Abas

* Abas multiplas com controle de sessao.
* Restauracao automatica de abas anteriores.
* Protecoes internas por aba.
* Paginas especiais internas do navegador.

## Perfis Locais

* Perfis separados por usuario, ambiente ou contexto.
* Configuracoes independentes por perfil.
* Dados isolados localmente.

## Sistema Interno

* Gerenciamento de favoritos.
* Historico integrado.
* Tela de downloads.
* Quick links personalizaveis na pagina inicial.

## Interface

* Tema claro e escuro totalmente coerentes.
* Componentes internos adaptados automaticamente.
* Paleta visual consistente entre menus, dialogos e paginas internas.

## Privacidade e Utilitarios

* Bloqueio simples de anuncios e rastreadores.
* Fechamento opcional de banners.
* Gerenciador local de extensoes.

---

# Requisitos

## Sistema Operacional

* Windows 10 ou superior.

## Python

* Python **3.12** recomendado.

## Dependencias

Instale os pacotes necessarios:

```powershell
pip install PyQt6 PyQt6-WebEngine cryptography
```

### Observacao

O pacote `cryptography` e utilizado para funcionalidades relacionadas a senhas.

Sem ele:

* o navegador continua funcionando normalmente;
* mas os recursos de gerenciamento de senhas ficam desativados.

Porque seguranca opcional parece exatamente algo que humanos fariam.

---

# Executando o Projeto

Na raiz do projeto:

```powershell
python app\agner.py
```

---

# Estrutura do Projeto

```text
app\
├── agner.py
├── agner_runtime.py
└── agner_parts\
    ├── bootstrap.py
    ├── browser_tab.py
    ├── entrypoint.py
    ├── main_window.py
    ├── managers.py
    ├── ui.py
    └── widgets.py
```

## Modulos

| Arquivo            | Responsabilidade                         |
| ------------------ | ---------------------------------------- |
| `agner.py`         | Launcher principal                       |
| `agner_runtime.py` | Carregamento dinamico dos modulos        |
| `bootstrap.py`     | Imports, temas, icones e HTML inicial    |
| `main_window.py`   | Janela principal e navegacao             |
| `browser_tab.py`   | Controle das abas e QWebEngineView       |
| `managers.py`      | Perfis, favoritos, historico e downloads |
| `ui.py`            | Dialogos e interfaces auxiliares         |
| `widgets.py`       | Widgets internos do navegador            |
| `entrypoint.py`    | Inicializacao complementar               |

---

# Dados Locais

Todos os dados do navegador sao armazenados localmente em:

```text
C:\Users\<usuario>\.agner_browser
```

O diretorio contem:

* perfis;
* bancos SQLite;
* favoritos;
* historico;
* downloads;
* extensoes;
* configuracoes;
* quick links.

---

# Validacao Rapida

## Validar sintaxe

```powershell
python -m py_compile ^
app\agner.py ^
app\agner_runtime.py ^
app\agner_parts\bootstrap.py ^
app\agner_parts\ui.py ^
app\agner_parts\main_window.py ^
app\agner_parts\browser_tab.py ^
app\agner_parts\managers.py ^
app\agner_parts\widgets.py ^
app\agner_parts\entrypoint.py
```

## Validar carregamento do runtime

```powershell
python -c "import sys; sys.path.insert(0, 'app'); import agner_runtime; print(callable(agner_runtime.main))"
```

Se retornar:

```text
True
```

entao o runtime principal carregou corretamente. Pequenas vitorias contra o caos computacional.

---

# Padrao Visual

O projeto segue um principio simples:

> cada tema deve parecer completo, nao apenas invertido.

## Tema Claro

* superficies claras;
* contraste suave;
* componentes internos coerentes.

## Tema Escuro

* superficies escuras reais;
* textos adaptados corretamente;
* consistencia visual em menus, abas e dialogos.


---

