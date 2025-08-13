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

**Syqlorix** is a hyper-minimalist Python package for building full HTML documents—including **CSS** and **JavaScript**—from a **single Python script**. It offers a pure Python DSL (Domain-Specific Language) for authoring web interfaces, with a built-in live-reloading server, dynamic routing, and a simple build process.

It is designed for developers who want to create web UIs and simple APIs without leaving the comfort of Python.

### Core Design Principles

*   **All-in-One**: Write entire pages in one `.py` file.
*   **Minimal API**: Small surface area, quick to learn.
*   **Super Readable**: Feels like Python, acts like HTML.
*   **Zero-Config**: Sensible defaults for instant productivity.

---

## Key Features

*   **Pure Python HTML:** Generate any HTML element using Python objects and operators.
*   **Enhanced Live Reload Server:** The dev server automatically reloads your browser on code changes across your project, including files in the `static/` directory and your main Python script, enabling seamless multi-file development.
*   **Dynamic Routing:** Create clean routes with variable paths (e.g., `/user/<username>`).
*   **POST/GET Handling:** Easily handle different HTTP methods to process form data.
*   **JSON API Responses:** Return a `dict` or `list` from a route to create an API endpoint.
*   **Static File Serving:** Automatically serves files from a `./static` directory.
*   **Zero-Config Build:** Compile your app into a single, minified HTML file for production.
*   **Simple CLI:** Get started instantly with `init`, `run`, and `build` commands.

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

### Serving Static Files
1. Create file `app.py`.  
2. Drop any file inside the same directory, e.g. `logo.png`.  
3. Reference it from a route handler:

   ```python
   @doc.route('/')
   def home(request):
       return Syqlorix(
           head(
               title("Demo"),
               link(rel="stylesheet", href="/custom.css")
           ),
           body(
               img(src="logo.png", alt="My Logo", width="150")
           )
       )
   ```

*Changes to any files within the directory (e.g., `custom.css`, `logo.png`) will automatically trigger a live reload in your browser.*

#### Whitelisting / Blacklisting Static Files with `.syqlorix`

Drop a file named `.syqlorix` in your project root to control which static files are served.

*Rules (one per line):*  
- Use glob patterns (`*.pdf`, `docs/**`)  
- **Whitelist** (allowed) → write the pattern as-is  
- **Blacklist** (blocked) → prefix the pattern with a minus `-`

Example `.syqlorix`:
```
# Allow everything
*  # can be a single file too, e.g. - *new-page.py

# Block sensitive or bulky items
- secrets/*
- testings-only/*.py
- *.png
- old-page.py
```

### Dynamic Routing

Define routes with variable sections using `<var_name>` syntax. The captured values are available in `request.path_params`.

```python
@doc.route('/user/<username>')
def user_profile(request):
    username = request.path_params.get('username', 'Guest')
    return h1(f"Hello, {username}!")
```

### Handling Forms & POST Requests

Specify which HTTP methods a route accepts with the `methods` argument. The `request` object contains `form_data` for form submissions.

```python
@doc.route('/message', methods=['GET', 'POST'])
def message_form(request):
    if request.method == 'POST':
        user_message = request.form_data.get('message', 'nothing')
        return h1(f"You sent: '{user_message}'")
    
    # On GET request, show the form
    return form(
        input_(type="text", name="message"), # Use input_ to avoid conflict
        button("Submit"),
        method="POST"
    )
```

### Returning JSON for APIs

Simply return a Python dictionary or list from a route to create a JSON API. Syqlorix automatically sets the correct `Content-Type` header.

```python
@doc.route('/api/health')
def health_check(request):
    return {"status": "ok", "method": request.method}
```

</details>

<details>
  <summary><h2><strong>› Click to view Command-Line Interface (CLI)</strong></h2></summary>

Syqlorix comes with a simple and powerful CLI.

*   #### `syqlorix init [filename]`
    Creates a new project file with a helpful template to get you started. Automatically ensures the filename ends with `.py` (e.g., `syqlorix init my_app` creates `my_app.py`, `syqlorix init page.html` creates `page.html.py`). Defaults to `app.py`.
    ```bash
    syqlorix init my_cool_app
    ```
    (This will create `my_cool_app.py`)

*   #### `syqlorix run <file>`
    Runs the live-reloading development server. It will automatically find an open port if the default is busy.
    *   `--port <number>`: Specify a starting port (defaults to 8000).
    *   `--no-reload`: Disable the live-reload feature.
    ```bash
    syqlorix run app.py --port 8080
    ```

*   #### `syqlorix build <file>`
    Builds a single, static HTML file from your script's default state. This command does not execute routes.
    *   `--output <filename>` or `-o <filename>`: Set the output file name.
    *   `--minify`: Minifies the HTML and any inline CSS/JS for production.
    ```bash
    syqlorix build main.py -o index.html --minify
    ```

    
<details><summary><strong>CLI Reference</strong></summary>

| Command | Purpose |
|---------|---------|
| `syqlorix init [file]` | Scaffolds a ready-to-run template (`app.py` by default) |
| `syqlorix run <file>` | Starts live-reload server on port 8000 (or next free) |
| `syqlorix build <file>` | Outputs a single **static HTML** file (`dist/index.html`) |

Options  
- `--port 8080` – start on a specific port  
- `--no-reload` – disable live-reload  
- `-o file.html --minify` – custom build name + minify

</details>

</details>

## Target Use Cases

*   **Fast Prototyping**: Quickly mock up web interfaces without juggling multiple files.
*   **Simple Dashboards**: Create internal tools or data visualizations.
*   **Educational Tools**: A clear, Python-only way to demonstrate web fundamentals.
*   **Simple APIs**: Build and serve JSON data from Python scripts.
*   **Single-File Web Apps**: Package an entire web utility into one `.py` file.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests on the [GitHub repository](https://github.com/Syqlorix/Syqlorix).

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Syqlorix/Syqlorix/blob/main/LICENSE) file for details.
