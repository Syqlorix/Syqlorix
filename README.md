# Syqlorix: Build Hyper-Minimal Web Pages in Pure Python

<p align="center">
  <img src="https://raw.githubusercontent.com/Syqlorix/Syqlorix/main/syqlorix-logo.svg" alt="Syqlorix Logo" width="250"/>
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
*   **Minimal API**: Small surface area, quick to learn.
*   **Zero-Config**: Sensible defaults for instant productivity.

---

## Key Features

*   **Pure Python HTML:** Generate any HTML element using Python objects.
*   **Component-Based Architecture:** Build your UI with reusable components that support props, children, scoped CSS, and lifecycle methods.
*   **State Management:** Create interactive components with a simple, server-side state management pattern.
*   **Live Reload Server:** The dev server automatically reloads your browser on code changes.
*   **Static Site Generation (SSG):** Build your entire application into a high-performance static website with the `build` command.
*   **Blueprints:** Organize large applications by splitting routes into multiple files.
*   **Dynamic Routing:** Create clean routes with variable paths (e.g., `/user/<username>`).
*   **JSON API Responses:** Return a `dict` or `list` from a route to create an API endpoint.

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

Syqlorix now features a powerful component-based architecture. Components are reusable, stateful, and can have their own scoped styles.

```python
# components.py
from syqlorix import Component, div, h1, p, style

class Card(Component):
    def before_render(self):
        # Lifecycle method: runs before create()
        # Use this to modify state or props before rendering
        self.title = self.props.get("title", "Default Title").upper()

    def create(self, children=None):
        # Define scoped styles using the component's unique scope_attr
        scoped_style = f"""
            div[{self.scope_attr}] h1 {{
                color: blue;
            }}
        """
        
        return div(
            style(scoped_style),
            h1(self.title), # Use the title from before_render
            *(children or []) # Render children passed to the component
        )

# app.py
from syqlorix import Syqlorix, body
from components import Card

doc = Syqlorix()

@doc.route('/')
def home(request):
    return body(
        # Pass props and children to your component
        Card(title="My Card",
            p("This is the content of the card.")
        )
    )
```

### State Management

Components can have their own internal state. State is managed on the server, and updates are triggered by new page requests.

```python
class Counter(Component):
    def __init__(self, *children, **props):
        super().__init__(*children, **props)
        # Initialize state from props (e.g., from request query params)
        self.set_state({"count": int(self.props.get("initial_count", 0))})

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

### Structuring Large Applications with Blueprints

Use Blueprints to organize your routes into separate files.

```python
# pages/about.py
from syqlorix import Blueprint, h1

about_bp = Blueprint("about")

@about_bp.route('/about')
def about_page(request):
    return h1("About Us")

# main_app.py
from syqlorix import Syqlorix
from pages.about import about_bp

doc = Syqlorix()
doc.register_blueprint(about_bp)
```

### Dynamic Routing

Define routes with variable sections using `<var_name>` syntax. The captured values are available in `request.path_params`.

```python
@doc.route('/user/<username>')
def user_profile(request):
    username = request.path_params.get('username', 'Guest')
    return h1(f"Hello, {username}!")
```

</details>

<details>
  <summary><h2><strong>› Click to view Command-Line Interface (CLI)</strong></h2></summary>

Syqlorix comes with a simple and powerful CLI.

*   #### `syqlorix init [filename]`
    Creates a new project file with a helpful template to get you started.
    ```bash
    syqlorix init my_cool_app
    ```

*   #### `syqlorix run <file>`
    Runs the live-reloading development server.
    *   `--port <number>`: Specify a starting port (defaults to 8000).
    *   `--no-reload`: Disable the live-reload feature.
    ```bash
    syqlorix run app.py --port 8080
    ```

*   #### `syqlorix build <file>`
    Builds a static version of your site from your app's static routes.
    *   `--output <dirname>` or `-o <dirname>`: Set the output directory name (defaults to `dist`).
    ```bash
    syqlorix build main.py -o public
    ```

</details>

## Target Use Cases

*   **Fast Prototyping**: Quickly mock up web interfaces without juggling multiple files.
*   **Static Sites**: Build blogs, portfolios, and documentation sites.
*   **Simple Dashboards**: Create internal tools or data visualizations.
*   **Educational Tools**: A clear, Python-only way to demonstrate web fundamentals.
*   **Simple APIs**: Build and serve JSON data from Python scripts.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests on the [GitHub repository](https://github.com/Syqlorix/Syqlorix).

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Syqlorix/Syqlorix/blob/main/LICENSE) file for details.