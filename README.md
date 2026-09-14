<div align="center">

# AGNER Browser

### A modular desktop browser built with Python, PyQt6 and QtWebEngine

**An experimental browser focused on local-first data, isolated profiles, session persistence, extensibility and a cohesive desktop experience.**

`Python` · `PyQt6` · `QtWebEngine` · `SQLite` · `Local-first`

</div>

<p align="center">
  <img src="https://img.shields.io/badge/status-experimental-8B5CF6">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Qt-PyQt6-41CD52?logo=qt&logoColor=white">
  <img src="https://img.shields.io/badge/engine-QtWebEngine-22D3EE">
  <img src="https://img.shields.io/badge/storage-local-EC4899">
</p>

---

<img width="1854" height="1044" alt="agner" src="https://github.com/user-attachments/assets/c6a125bf-b498-43cb-92d5-1981a88ad30a" />

---

## Overview

**AGNER Browser** is an experimental desktop web browser built from scratch in Python using **PyQt6** and **QtWebEngine**.

The project explores what sits around a modern browser engine rather than attempting to implement an HTML renderer itself.

AGNER provides its own application layer for:

* tab and window management;
* isolated browser profiles;
* persistent sessions;
* browsing history;
* favorites;
* downloads;
* local extensions;
* internal browser pages;
* privacy controls;
* light and dark themes;
* local data management.

QtWebEngine handles web rendering, while AGNER implements the surrounding browser experience and application architecture.

The result is a modular browser where the interface, persistence layer, profiles and navigation logic remain under application control.

---

## Preview

<img width="1536" height="1024" alt="AGNER Browser interface" src="https://github.com/user-attachments/assets/5643cb56-5ed8-4ad1-8edf-8098bb20bbf0" />

---

## Architecture

AGNER separates browser behavior into specialized modules instead of concentrating navigation, persistence and interface logic inside a single application file.

```text id="gngbn1"
                         AGNER Browser
                               │
                               ▼
                         agner.py
                          Launcher
                               │
                               ▼
                      agner_runtime.py
                    Dynamic module runtime
                               │
                               ▼
                       main_window.py
                  Application orchestration
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       browser_tab.py      managers.py        ui.py
              │                │                │
              │                │                ▼
              │                │            widgets.py
              │                │
              ▼                ▼
        QtWebEngine        Local services
              │                │
              │       ┌────────┼────────┐
              │       ▼        ▼        ▼
              │    Profiles  History  Favorites
              │                │
              │          Downloads / Config
              │
              └────────────────┬────────────────┘
                               ▼
                         Local storage
                            SQLite
```

This separation keeps rendering, interface components and persistent browser state independently maintainable.

---

## Core features

### Tabbed browsing

AGNER provides a multi-tab browsing environment built around `QWebEngineView`.

The tab layer is responsible for:

* page navigation;
* tab lifecycle;
* per-tab browser behavior;
* internal protections;
* integration with the main window;
* session restoration.

---

### Persistent sessions

Open tabs can survive application restarts.

Session state is stored locally and reconstructed when the browser starts again, allowing the previous browsing context to be recovered without relying on an external account or synchronization service.

---

### Isolated profiles

AGNER supports independent local browser profiles.

Each profile can maintain its own:

* browsing data;
* configuration;
* history;
* favorites;
* extensions;
* session state.

```text id="k4m8ar"
                    AGNER
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
      Profile A   Profile B   Profile C
          │           │           │
          ▼           ▼           ▼
       Session      Session      Session
       History      History      History
       Favorites    Favorites    Favorites
       Settings     Settings     Settings
```

Profile isolation makes it possible to maintain separate browsing environments without mixing their local state.

---

## Local data layer

Browser data is stored locally rather than requiring a remote account.

The data layer manages:

| Component       | Responsibility                    |
| --------------- | --------------------------------- |
| **Profiles**    | isolated browsing environments    |
| **SQLite**      | structured local persistence      |
| **Favorites**   | saved pages and organization      |
| **History**     | browsing records and search       |
| **Downloads**   | download tracking                 |
| **Extensions**  | installed local extensions        |
| **Settings**    | browser and profile preferences   |
| **Quick Links** | customizable start-page shortcuts |

On Windows, application data is stored under:

```text id="q24d09"
C:\Users\<user>\.agner_browser
```

---

## Local extension system

AGNER includes its own extension-management layer inspired by the workflow of browser extension stores.

The system is designed around **local installation and management**, keeping extension resources under the user's control.

Extension handling is integrated with the rest of the browser rather than implemented as a separate external utility.

> AGNER's extension system is project-specific and should not be interpreted as full compatibility with Chrome's extension runtime or Chrome Web Store.

---

## Privacy controls

AGNER includes browser-level privacy utilities such as:

* basic advertisement blocking;
* basic tracker blocking;
* optional banner handling;
* isolated profiles;
* local browser data.

These features provide an additional application-level privacy layer around QtWebEngine.

They are not intended to claim the same coverage as mature dedicated content-blocking engines.

---

## Browser services

The service layer centralizes stateful browser functionality.

```text id="ffzq8a"
                    managers.py
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
     Profiles        Favorites         History
        │                │                │
        └────────────────┼────────────────┘
                         │
                ┌────────┴────────┐
                ▼                 ▼
            Downloads          Settings
                │                 │
                └────────┬────────┘
                         ▼
                    Local data
```

Keeping these responsibilities outside the main UI reduces coupling between browser state and presentation logic.

---

## Interface system

AGNER's interface is implemented as a dedicated application layer rather than a collection of default Qt dialogs.

It includes:

* browser chrome;
* navigation controls;
* tab interface;
* menus;
* dialogs;
* internal pages;
* history views;
* download views;
* favorites management;
* extension management;
* settings.

The UI layer is split between reusable widgets and higher-level interfaces.

---

## Theme system

AGNER includes native light and dark themes designed around a shared visual language.

The goal is not simply to invert colors.

Each theme defines appropriate:

* surfaces;
* foreground colors;
* borders;
* interactive states;
* menus;
* dialogs;
* internal pages;
* browser controls.

This keeps the application visually coherent when switching between appearance modes.

---

## Project structure

```text id="eq8q0u"
app/
├── agner.py
├── agner_runtime.py
│
└── agner_parts/
    ├── bootstrap.py
    ├── browser_tab.py
    ├── entrypoint.py
    ├── main_window.py
    ├── managers.py
    ├── ui.py
    └── widgets.py
```

### Module responsibilities

| Module             | Responsibility                                               |
| ------------------ | ------------------------------------------------------------ |
| `agner.py`         | application launcher                                         |
| `agner_runtime.py` | dynamic module loading and runtime bootstrap                 |
| `bootstrap.py`     | shared imports, themes, icons and initial HTML               |
| `main_window.py`   | main window, menus and navigation                            |
| `browser_tab.py`   | individual tabs and `QWebEngineView` lifecycle               |
| `managers.py`      | profiles, favorites, history, downloads and persistent state |
| `ui.py`            | dialogs and auxiliary interfaces                             |
| `widgets.py`       | reusable internal browser widgets                            |
| `entrypoint.py`    | application initialization                                   |

---

## Runtime flow

```text id="r4k5vh"
python app/agner.py
        │
        ▼
    agner.py
        │
        ▼
agner_runtime.py
        │
        ▼
Load application modules
        │
        ▼
Initialize local services
        │
        ▼
Restore active profile
        │
        ▼
Restore previous session
        │
        ▼
Create main window
        │
        ▼
Start Qt event loop
```

---

## Technology stack

| Layer                   | Technology                      |
| ----------------------- | ------------------------------- |
| Language                | **Python**                      |
| Desktop framework       | **PyQt6**                       |
| Web engine              | **QtWebEngine**                 |
| Rendering engine        | **Chromium via QtWebEngine**    |
| Persistence             | **SQLite + local files**        |
| Cryptographic utilities | **cryptography**                |
| Architecture            | **Modular desktop application** |

A useful distinction: AGNER implements the **browser application**, while QtWebEngine provides the underlying web rendering engine.

Writing a modern HTML/CSS/JavaScript engine from scratch would turn this project from an interesting portfolio piece into a multigenerational family obligation.

---

## Requirements

### Python

**Python 3.12** is recommended.

Install the required packages:

```powershell id="qu4q4a"
pip install PyQt6 PyQt6-WebEngine cryptography
```

`cryptography` is used by password-related functionality.

If it is unavailable, the core browser can continue operating while the dependent password-management features remain disabled.

---

## Running

From the project root:

```powershell id="f8ijzt"
python app\agner.py
```

---

## Validation

### Syntax validation

```powershell id="ahll7x"
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

### Runtime validation

```powershell id="xptowd"
python -c "import sys; sys.path.insert(0, 'app'); import agner_runtime; print(callable(agner_runtime.main))"
```

Expected output:

```text id="0pl69a"
True
```

This confirms that the primary runtime entry point can be imported successfully.

---

## Engineering focus

AGNER is primarily an exploration of **desktop browser architecture**.

Instead of treating `QWebEngineView` as the entire application, the project builds the systems expected around a rendering engine:

* navigation lifecycle;
* tab management;
* state persistence;
* profile isolation;
* session recovery;
* local databases;
* downloads;
* extension management;
* privacy controls;
* browser-specific UI;
* theme propagation.

The interesting engineering problem is not displaying a web page.

Qt can already do that.

The challenge is coordinating all of the surrounding state and services so they behave as a single browser.

---

## Design principles

**Modular**
Browser responsibilities are divided into specialized components rather than concentrated in one monolithic application class.

**Local-first**
Profiles, history, favorites, configuration and session state remain on the local machine.

**Persistent**
The application is designed to recover useful state between executions.

**Extensible**
Browser features can evolve through isolated modules and the local extension layer.

**Consistent**
Internal pages, dialogs and navigation components share the same visual system.

---

## Current status

AGNER is an **experimental browser project under active development**.

Implemented areas include:

* multi-tab browsing;
* session persistence;
* local profiles;
* favorites;
* history;
* downloads;
* custom start page;
* light and dark themes;
* privacy utilities;
* local extension management;
* modular runtime architecture;
* local persistent storage.

The project is intended as an exploration of browser engineering and desktop application architecture rather than a replacement for production browsers with decades of security hardening behind them.

---

## Security scope

AGNER relies on QtWebEngine for the underlying web engine and Chromium-based rendering behavior.

Application-level features such as profiles, local storage, password handling, content filtering and extensions add their own security considerations.

For that reason, AGNER should currently be treated as an **experimental browser**, not as a security-hardened replacement for a mainstream browser in high-risk environments.

That distinction is boring, responsible and considerably preferable to discovering it through an incident report.

---

<div align="center">

### AGNER Browser

**A browser is more than a web view.**

Built with Python, PyQt6 and QtWebEngine to explore the architecture surrounding a modern desktop browsing experience.

</div>
