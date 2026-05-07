# AGNER Browser

AGNER Browser e um navegador desktop experimental feito em Python, PyQt6 e QtWebEngine.
O projeto usa perfis locais, favoritos, historico, downloads, pagina inicial customizada,
abas especiais e temas claro/escuro consistentes.

## Recursos

- Abas com restauracao de sessao controlada.
- Perfis locais separados por usuario ou contexto.
- Favoritos, historico e downloads em telas internas.
- Pagina inicial com atalhos rapidos.
- Temas claro e escuro aplicados de forma consistente nas telas internas.
- Bloqueio simples de anuncios/rastreadores e fechamento opcional de banners.
- Gerenciador local de extensoes em estilo Chrome Web Store.

## Requisitos

- Windows 10 ou superior.
- Python 3.12 recomendado.
- Pacotes Python:

```powershell
pip install PyQt6 PyQt6-WebEngine cryptography
```

`cryptography` e usado para recursos de senha. Sem ele, o navegador inicia, mas o
gerenciamento de senhas fica desativado.

## Como executar

Na raiz do projeto:

```powershell
python app\agner.py
```

## Dados locais

Os dados do navegador ficam no diretorio do usuario:

```text
C:\Users\<usuario>\.agner_browser
```

Ali ficam perfis, bancos SQLite, favoritos, historico, quick links, extensoes e
configuracoes por perfil.

## Estrutura

```text
app\agner.py                    Launcher principal.
app\agner_runtime.py            Carrega os modulos divididos em agner_parts.
app\agner_parts\bootstrap.py    Imports, temas, icones e HTML da nova aba.
app\agner_parts\main_window.py  Janela principal, abas, menus e navegacao.
app\agner_parts\browser_tab.py  QWebEngineView, pagina web e protecoes de aba.
app\agner_parts\managers.py     Settings, favoritos, historico, downloads e perfis.
app\agner_parts\ui.py           Dialogos de perfis, favoritos, extensoes e definicoes.
app\agner_parts\widgets.py      Telas internas de historico e downloads.
```

## Validacao rapida

Para checar sintaxe dos arquivos principais:

```powershell
python -m py_compile app\agner.py app\agner_runtime.py app\agner_parts\bootstrap.py app\agner_parts\ui.py app\agner_parts\main_window.py app\agner_parts\browser_tab.py app\agner_parts\managers.py app\agner_parts\widgets.py app\agner_parts\entrypoint.py
```

Para validar que o runtime carrega:

```powershell
python -c "import sys; sys.path.insert(0, 'app'); import agner_runtime; print(callable(agner_runtime.main))"
```

## Padrao visual

O navegador deve manter cada modo de tema inteiro e coerente:

- No modo claro, telas, dialogos e abas internas devem usar superficies claras.
- No modo escuro, telas, dialogos e abas internas devem usar superficies escuras.
- Textos, botoes, cards e campos devem derivar da paleta ativa.
- A interface nao deve usar emojis em textos, botoes, titulos, status ou logs visiveis.

## Observacoes

Este ainda e um projeto em evolucao. Algumas APIs do QtWebEngine mudam entre versoes
do PyQt6, entao bugs de renderizacao e comportamento devem ser validados sempre na
versao instalada localmente.
