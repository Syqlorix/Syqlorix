# Syqlorix: Build Hyper-Minimal Web Pages in Pure Python

<p align="center">
  <img src="https://raw.githubusercontent.com/Syqlorix/Syqlorix/refs/heads/main/syqlorix-logo.svg" alt="Syqlorix Logo" width="250"/>
</p>

## Overview

**Syqlorix** is a futuristic Python package inspired by Flask and Dominate, designed to build full HTML documents—including **CSS** and **JavaScript**—from a **single Python script**. It offers a pure Python DSL (Domain-Specific Language) for authoring web interfaces, making it a single-file web page builder that is zero-dependency, readable, and easily embeddable for dynamic web content creation.

## Goals & Design Philosophy

-   **Simpler than Dominate**
-   **More readable than raw HTML**
-   **No need for separate `.html`, `.css`, or `.js` files**

### Core Design Principles

*   **All-in-One**: Write entire pages in one `.py` file.
*   **Minimal API**: Small surface area, quick to learn.
*   **Super Readable**: Feels like Markdown, acts like HTML.
*   **Framework-Ready**: Works seamlessly with Flask, Starlette, etc.
*   **Tech-Aesthetic**: Feels modern, futuristic, efficient.

## Example Usage

For comprehensive examples and detailed usage instructions, please refer to the [Syqlorix Documentation Repository](https://github.com/Syqlorix/syqlorix.github.io).

---

## Key API Features

*   `Page(...)` -> Main class to construct a page.
*   `page.h1()`, `page.div()`, `page.ul()` -> HTML tag functions.
*   `with page.body:` -> Context-managed content creation for nesting.
*   **Components**: Use the `@syqlorix.component` decorator to define reusable Python functions that build parts of your page. Integrate them using `page.add_component(my_component, *args, **kwargs)`.
*   `page.style(css_str)` -> Add CSS inline within a `<style>` tag in the `<head>`.
*   `syqlorix.css(**rules)` -> Programmatic CSS DSL to generate CSS strings from Python dictionaries.
*   `page.link_css(href='...')` -> Add an external CSS file link to the `<head>`.
*   `page.script(js_str)` -> Add JS inline within a `<script>` tag before `</body>`.
*   `page.link_js(src='...')` -> Add an external JavaScript file link to the `</body>`.
*   `page.meta(...)`, `page.link(...)`, `page.base(...)`, `page.title(...)` -> These tags can now be directly called on the `page` object and are automatically added to the `<head>`.
*   `page.raw(html_content)` -> Inserts raw, unescaped HTML content directly into the page.
*   **Form Helpers**: Specialized methods for common form elements:
    *   `page.text_input(name, ...)`
    *   `page.password_input(name, ...)`
    *   `page.email_input(name, ...)`
    *   `page.number_input(name, ...)`
    *   `page.checkbox(name, value, ...)`
    *   `page.radio(name, value, ...)`
    *   `page.textarea(name, ...)`
    *   `page.select(name, ...)` (context manager)
    *   `page.option(text, value, ...)`
    *   `page.label(text, _for, ...)`
    *   `page.submit_button(text, ...)`
*   **Routing System (`syqlorix.Route`)**:
    *   `main_router = syqlorix.Route("/")`: Initialize a router instance.
    *   `@main_router.route("/path")`: Decorator to map Python functions (which return `Page` objects) to URL paths.
    *   `router.subroute(sub_router)`: Nest router instances for modular routing.
*   `page.render()` -> Outputs the full HTML page string including `<!DOCTYPE html>`.
*   `syqlorix serve <routes_file.py>` -> CLI command to start a multi-page development server, serving pages and static assets from the project root, providing a clickable link and auto-detection in Codespaces.
*   `syqlorix build <routes_file.py> -o <output_dir>` -> CLI command to generate a static site from a routes file, including copying static assets.

## Target Use Cases

*   **Fast Prototyping**: Quickly mock up HTML content without juggling multiple files, using `syqlorix serve`.
*   **Dynamic HTML Generation**: For developers who need to generate HTML on the fly without a full-blown templating engine.
*   **Educational Tools**: A clear, Python-only way to demonstrate HTML structure.
*   **Static Site Generation**: Build simple static sites purely with Python scripts using `syqlorix build`.
*   **Small Web Services**: Embed HTML generation directly into Flask/Starlette applications.

## Name Rationale: “Syqlorix”

Syqlorix is an invented word, providing a unique word for the project. Its tech-aesthetic, futuristic, and protocol-sounding nature is distinctive and easily pronounced, aiming for a brand-ready feel.

## Future Directions

*   More specialized element helpers for media elements (audio, video, canvas).
*   Built-in validation or client-side form helpers (requires careful design to remain zero-dependency).
*   Pre-defined common components (e.g., alert boxes, simple modals).
*   Component loading from separate files (e.g., `syqlorix.load_component("my_comp.py")`).

## Get Started (Local Installation)

1.  **Clone this repository**
2.  **Navigate to the project root** in your terminal.
3.  **Install in editable mode** (for development) or as a regular package:

    ```bash
    pip install .
    ```

    You can install directly:
    ```bash
    pip install syqlorix
    ```

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.