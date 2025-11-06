# Syqlorix: Paghimo og mga Hyper-Minimal nga Web Page sa Purong Python

<p align="center">
  <a href="../README.md">English</a> |
  <a href="README-fil.md">Filipino</a> |
  <a href="README-ceb.md">Cebuano</a> |
  <a href="README-zh-Hans.md">简体中文</a> |
  <a href="README-ko.md">한국어</a> |
  <a href="README-es.md">Español</a> |
  <a href="README-fr.md">Français</a> |
  <a href="README-de.md">Deutsch</a> |
  <a href="README-ja.md">日本語</a> |
  <a href="README-pt.md">Português</a> |
  <a href="README-ru.md">Русский</a>
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

## Kinatibuk-ang Paglantaw

Ang **Syqlorix** kay usa ka hyper-minimalist nga Python package para sa paghimo og tibuok HTML nga mga dokumento—apil ang **CSS** ug **JavaScript**—gikan sa **usa ka Python script**. Nagtanyag kini og purong Python DSL (Domain-Specific Language) para sa pagsulat og mga web interface, nga naay built-in nga live-reloading server, dinamikong pag-ruta, ug usa ka gamhanan nga static site generator.

Gidisenyo kini para sa mga developer nga gustong mohimo og mga web UI, static site, ug yanong mga API nga dili kinahanglan mobiya sa kasayon sa Python.

### Mga Pangunang Prinsipyo sa Disenyo

*   **All-in-One**: Pagsulat og tibuok nga mga panid ug component sa `.py` files.
*   **Component-Based**: Istruktura ang imong UI gamit ang magamit pag-usab, ug naay estado nga mga component.
*   **Minimal API**: Gamay nga surface area, dali makat-unan.
*   **Zero-Config**: Makatarunganon nga mga default para sa dihadiha nga pagka-produktibo.

---

## Mga Pangunang Features

*   **Purong Python HTML:** Paghimo og bisan unsang HTML element gamit ang mga Python object.
*   **Component-Based Architecture:** Pagtukod sa imong UI gamit ang magamit pag-usab nga mga component nga nagsuporta sa props, children, scoped CSS, ug lifecycle methods.
*   **State Management:** Paghimo og mga interactive nga component nga naay yano, server-side nga pattern sa pagdumala sa estado.
*   **Live Reload Server:** Ang dev server awtomatik nga nag-reload sa imong browser sa matag kausaban sa code.
*   **Static Site Generation (SSG):** Tukora ang imong tibuok aplikasyon ngadto sa usa ka high-performance nga static website gamit ang `build` command.
*   **Blueprints:** Organisaha ang dagkong mga aplikasyon pinaagi sa pagbahin sa mga ruta ngadto sa daghang mga file.
*   **Dynamic Routing:** Paghimo og limpyo nga mga ruta nga naay variable paths (e.g., `/user/<username>`).
*   **JSON API Responses:** I-return ang usa ka `dict` o `list` gikan sa usa ka ruta aron makahimo og usa ka API endpoint.

## Dali nga Pagsugod

1.  **I-install ang Syqlorix:**
    ```bash
    pip install syqlorix
    ```

2.  **Paghimo og file nga `app.py`:**
    ```python
    from syqlorix import *
    
    doc = Syqlorix()
    
    @doc.route('/')
    def home(request):
        return Syqlorix(
            head(title("Kumusta")),
            body(
                h1("Kumusta gikan sa Syqlorix!"),
                p("Kini usa ka web page nga gihimo sa hingpit gikan sa Python.")
            )
        )
    ```

3.  **Padagana ang development server:**
    ```bash
    syqlorix run app.py
    ```

4.  Ablihi ang imong browser sa `http://127.0.0.1:8000`. Mao na!

<br/>

<details>
  <summary><h2><strong>› I-klik para makita ang Giya sa Paggamit</strong></h2></summary>

### Component-Based Architecture

Ang Syqlorix karon adunay usa ka gamhanan nga arkitektura nga gibase sa component. Ang mga component magamit pag-usab, adunay estado, ug mahimong adunay kaugalingon nga mga scoped style.

```python
# components.py
from syqlorix import Component, div, h1, p, style

class Card(Component):
    def before_render(self):
        # Lifecycle method: modagan sa dili pa ang create()
        # Gamita kini aron usbon ang estado o mga prop sa dili pa i-render
        self.title = self.props.get("title", "Default Title").upper()

    def create(self, children=None):
        # Ipasabot ang mga scoped style gamit ang talagsaon nga scope_attr sa component
        scoped_style = f"""
            div[{self.scope_attr}] h1 {{
                color: blue;
            }}
        """
        
        return div(
            style(scoped_style),
            h1(self.title), # Gamita ang titulo gikan sa before_render
            *(children or []) # I-render ang mga anak nga gipasa sa component
        )

# app.py
from syqlorix import Syqlorix, body
from components import Card

doc = Syqlorix()

@doc.route('/')
def home(request):
    return body(
        # Ipasa ang mga prop ug mga anak sa imong component
        Card(title="Akong Card",
            p("Kini ang sulod sa card.")
        )
    )
```

### Pagdumala sa Estado

Ang mga component mahimong adunay ilang kaugalingon nga internal nga estado. Ang estado gidumala sa server, ug ang mga update ma-trigger sa mga bag-ong hangyo sa panid.

```python
class Counter(Component):
    def __init__(self, *children, **props):
        super().__init__(*children, **props)
        # Sugdi ang estado gikan sa mga prop (e.g., gikan sa request query params)
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

### Pag-istruktura sa Dagkong mga Aplikasyon gamit ang mga Blueprint

Gamita ang mga Blueprint aron maorganisar ang imong mga ruta ngadto sa managlahing mga file.

```python
# pages/about.py
from syqlorix import Blueprint, h1

about_bp = Blueprint("about")

@about_bp.route('/about')
def about_page(request):
    return h1("Mahitungod Kanato")

# main_app.py
from syqlorix import Syqlorix
from pages.about import about_bp

doc = Syqlorix()
doc.register_blueprint(about_bp)
```

### Dinamikong Pag-ruta

Ipasabot ang mga ruta nga naay mga variable nga seksyon gamit ang `<var_name>` syntax. Ang mga nakuha nga bili anaa sa `request.path_params`.

```python
@doc.route('/user/<username>')
def user_profile(request):
    username = request.path_params.get('username', 'Guest')
    return h1(f"Kumusta, {username}!")
```

</details>

<details>
  <summary><h2><strong>› I-klik para makita ang Command-Line Interface (CLI)</strong></h2></summary>

Ang Syqlorix naay kauban nga yano ug gamhanan nga CLI.

*   #### `syqlorix init [filename]`
    Naghimo og bag-ong file sa proyekto nga naay makatabang nga template aron makasugod ka.
    ```bash
    syqlorix init my_cool_app
    ```

*   #### `syqlorix run <file>`
    Nagpadagan sa live-reloading development server.
    *   `--port <number>`: I-specify ang usa ka sugod nga port (default sa 8000).
    *   `--no-reload`: I-disable ang live-reload feature.
    ```bash
    syqlorix run app.py --port 8080
    ```

*   #### `syqlorix build <file>`
    Nagtukod og usa ka static nga bersyon sa imong site gikan sa mga static nga ruta sa imong app.
    *   `--output <dirname>` o `-o <dirname>`: I-set ang ngalan sa output directory (default sa `dist`).
    ```bash
    syqlorix build main.py -o public
    ```

</details>

## Mga Target nga Kaso sa Paggamit

*   **Paspas nga Prototyping**: Paspas nga pag-mock up sa mga web interface nga walay pagdumala sa daghang mga file.
*   **Static Sites**: Paghimo og mga blog, portfolio, ug mga site sa dokumentasyon.
*   **Yano nga mga Dashboard**: Paghimo og mga internal nga himan o mga data visualization.
*   **Mga Gamit sa Edukasyon**: Usa ka klaro, Python-only nga paagi sa pagpakita sa mga sukaranan sa web.
*   **Yano nga mga API**: Paghimo ug pag-serve sa JSON data gikan sa mga Python script.

## Pag-amot

Giabi-abi ang mga kontribusyon! Ayaw pagpanuko sa pag-abli og mga isyu o pagsumite og mga pull request sa [GitHub repository](https://github.com/Syqlorix/Syqlorix).

## Lisensya

Kini nga proyekto lisensyado ubos sa MIT License - tan-awa ang [LICENSE](https://github.com/Syqlorix/Syqlorix/blob/main/LICENSE) file para sa mga detalye.