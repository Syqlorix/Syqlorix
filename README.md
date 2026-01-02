# Syqlorix: Build Hyper-Minimal Web Pages in Pure Python

<p align="center">
  <a href="README.md">English</a> |
  <a href="mds/README-fil.md">Filipino</a> |
  <a href="mds/README-ceb.md">Cebuano</a> |
  <a href="mds/README-zh-Hans.md">简体中文</a> |
  <a href="mds/README-ko.md">한국어</a> |
  <a href="mds/README-es.md">Español</a> |
  <a href="mds/README-fr.md">Français</a> |
  <a href="mds/README-de.md">Deutsch</a> |
  <a href="mds/README-ja.md">日本語</a> |
  <a href="mds/README-pt.md">Português</a> |
  <a href="mds/README-ru.md">Русский</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/Syqlorix/Syqlorix/main/syqlorix-logo-anim.svg" alt="Syqlorix Logo" width="250"/>
</p>
<div align="center">

[![PyPI version](https://badge.fury.io/py/syqlorix.svg)](https://badge.fury.io/py/syqlorix)
[![Python Version](https://img.shields.io/pypi/pyversions/syqlorix.svg)](https://pypi.org/project/syqlorix/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/Syqlorix/Syqlorix/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/Syqlorix/Syqlorix)](https://github.com/Syqlorix/Syqlorix/issues)
[![Discord](https://img.shields.io/discord/1056887212207259668?label=discord&logo=discord)](https://discord.gg/KN8qZh5c98)

</div>

## Overview

**Syqlorix** is a hyper-minimalist Python package for building full HTML documents—including **CSS** and **JavaScript**—from a **single Python script**. It offers a pure Python DSL (Domain-Specific Language) for authoring web interfaces, with a built-in live-reloading server, dynamic routing, and a powerful static site generator.

It is designed for developers who want to create web UIs, static sites, and simple APIs without leaving the comfort of Python.

### Core Design Principles

*   **All-in-One**: Write entire pages and components in `.py` files.
*   **Component-Based**: Structure your UI with reusable, stateful components.
*   **High Performance**: Native Rust core for critical hot-paths (v1.4+).
*   **Zero-Config**: Sensible defaults for instant productivity.

---

## Key Features

*   **Pure Python HTML:** Generate any HTML element using Python objects.
*   **Rust-Powered Performance:** Blazing fast ID generation and Tailwind CSS processing (up to 15x speedup).
*   **Secure Starlark Components:** Define UI logic in a deterministic, 100% sandboxed environment.
*   **Distributed Scalability:** Optional support for high-concurrency Scala backends via Apache Thrift.
*   **Component-Based Architecture:** Build your UI with reusable components that support props, children, scoped CSS, and lifecycle methods.
*   **State Management:** Create interactive components with a simple, server-side state management pattern.
*   **Live Reload Server:** The dev server automatically reloads your browser on code changes.
*   **Static Site Generation (SSG):** Build your entire application into a high-performance static website.
*   **Dynamic Routing:** Create clean routes with variable paths (e.g., `/user/<username>`).

## Quick Start

1.  **Install Syqlorix:**
    ```bash
    pip install syqlorix
    ```

2.  **Create a file `app.py`:**
    ```python
    from syqlorix import *
    
    doc = Syqlorix()
    
    @doc.route('/')
    def home(request):
        return Syqlorix(
            head(title("Hello")),
            body(
                h1("Hello from Syqlorix!"),
                p("This is a web page generated entirely from Python.")
            )
        )
    ```

3.  **Run the development server:**
    ```bash
    syqlorix run app.py
    ```

4.  Open your browser to `http://127.0.0.1:8000`. That's it!

<br/>

<details>
  <summary><h2><strong>› Click to view Usage Guide</strong></h2></summary>

### Component-Based Architecture

Syqlorix features a powerful component-based architecture. Components are reusable, stateful, and can have their own scoped styles.

```python
# components.py
from syqlorix import Component, div, h1, p, style

class Card(Component):
    def before_render(self):
        # Lifecycle method: runs before create()
        self.title = self.props.get("title", "Default Title").upper()

    def create(self, children=None):
        # Scoped styles using the component's unique scope_attr (Rust-powered)
        scoped_style = f"div[{self.scope_attr}] h1 {{ color: blue; }}"
        
        return div(
            style(scoped_style),
            h1(self.title),
            *(children or [])
        )
```

### Secure Starlark Components

Use Starlark for deterministic and sandboxed component definitions, ideal for user-generated layouts.

```python
from syqlorix import StarlarkComponent

starlark_ui = """
tag("div", 
    tag("h1", props["title"]),
    tag("p", "Rendered securely via Starlark."),
    class_="container"
)
"""

comp = StarlarkComponent(script_content=starlark_ui, title="Secure UI")
```

### High-Concurrency Backend (Optional)

Delegate rendering to an external Scala backend via Thrift for massive horizontal scaling.

```python
doc = Syqlorix()
# Enable high-performance Scala backend
doc.use_backend(host="127.0.0.1", port=9090)
```

### State Management

```python
class Counter(Component):
    def __init__(self, *children, **props):
        super().__init__(*children, **props)
        try:
            count = int(self.props.get("initial_count", 0))
        except ValueError:
            count = 0
        self.set_state({"count": count})

    def create(self, children=None):
        count = self.state.get("count", 0)
        return div(
            h1(count),
            form(
                button("-", name="count", value=count - 1),
                button("+", name="count", value=count + 1),
                method="get", action="/"
            )
        )
```

</details>

<details>
  <summary><h2><strong>› Click to view Command-Line Interface (CLI)</strong></h2></summary>

*   #### `syqlorix init [filename]`
    Creates a new project file with a helpful template.
*   #### `syqlorix run <file>`
    Runs the live-reloading development server.
*   #### `syqlorix build <file>`
    Builds a static version of your site in the `dist/` folder.

</details>

## Target Use Cases

*   **Fast Prototyping**: Quickly mock up web interfaces without juggling multiple files.
*   **High-Performance Static Sites**: Optimized build times using the Rust core.
*   **Secure Dashboards**: Sandboxed component execution via Starlark.
*   **Distributed Systems**: Web frontends that scale using the Scala backend.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Syqlorix/Syqlorix/blob/main/LICENSE) file for details.