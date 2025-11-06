# Syqlorix: Bumuo ng mga Hyper-Minimal na Web Page sa Purong Python

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

## Pangkalahatang-ideya

Ang **Syqlorix** ay isang hyper-minimalist na Python package para sa pagbuo ng buong mga dokumento ng HTML—kabilang ang **CSS** at **JavaScript**—mula sa isang **solong Python script**. Nag-aalok ito ng isang purong Python DSL (Domain-Specific Language) para sa pag-akda ng mga web interface, na may built-in na live-reloading server, dynamic na pagruruta, at isang malakas na static site generator.

Ito ay dinisenyo para sa mga developer na nais lumikha ng mga web UI, static na site, at simpleng API nang hindi iniiwan ang kaginhawaan ng Python.

### Mga Pangunahing Prinsipyo sa Disenyo

*   **All-in-One**: Sumulat ng buong mga pahina at bahagi sa mga `.py` file.
*   **Component-Based**: Buuin ang iyong UI gamit ang mga magagamit muli at may estado na mga bahagi.
*   **Minimal API**: Maliit na surface area, mabilis matutunan.
*   **Zero-Config**: Mga makabuluhang default para sa agarang pagiging produktibo.

---

## Mga Pangunahing Tampok

*   **Purong Python HTML:** Bumuo ng anumang elemento ng HTML gamit ang mga Python object.
*   **Component-Based Architecture:** Buuin ang iyong UI gamit ang mga magagamit muli na mga bahagi na sumusuporta sa mga prop, children, scoped CSS, at mga pamamaraan ng lifecycle.
*   **State Management:** Lumikha ng mga interactive na bahagi na may isang simple, server-side na pattern ng pamamahala ng estado.
*   **Live Reload Server:** Awtomatikong nire-reload ng dev server ang iyong browser sa mga pagbabago sa code.
*   **Static Site Generation (SSG):** Buuin ang iyong buong application sa isang mataas na pagganap na static na website gamit ang `build` command.
*   **Blueprints:** Ayusin ang malalaking application sa pamamagitan ng paghahati ng mga ruta sa maraming file.
*   **Dynamic Routing:** Lumikha ng malinis na mga ruta na may mga variable na path (hal., `/user/<username>`).
*   **JSON API Responses:** Ibalik ang isang `dict` o `list` mula sa isang ruta upang lumikha ng isang API endpoint.

## Mabilis na Pagsisimula

1.  **I-install ang Syqlorix:**
    ```bash
    pip install syqlorix
    ```

2.  **Gumawa ng isang file na `app.py`:**
    ```python
    from syqlorix import *
    
    doc = Syqlorix()
    
    @doc.route('/')
    def home(request):
        return Syqlorix(
            head(title("Kamusta")),
            body(
                h1("Kamusta mula sa Syqlorix!"),
                p("Ito ay isang web page na ganap na binuo mula sa Python.")
            )
        )
    ```

3.  **Patakbuhin ang development server:**
    ```bash
    syqlorix run app.py
    ```

4.  Buksan ang iyong browser sa `http://127.0.0.1:8000`. Iyon lang!

<br/>

<details>
  <summary><h2><strong>› I-click upang makita ang Gabay sa Paggamit</strong></h2></summary>

### Component-Based Architecture

Nagtatampok na ngayon ang Syqlorix ng isang malakas na arkitektura na nakabatay sa component. Ang mga component ay magagamit muli, may estado, at maaaring magkaroon ng sarili nilang mga naka-scope na istilo.

```python
# components.py
from syqlorix import Component, div, h1, p, style

class Card(Component):
    def before_render(self):
        # Paraan ng lifecycle: tumatakbo bago ang create()
        # Gamitin ito upang baguhin ang estado o mga prop bago i-render
        self.title = self.props.get("title", "Default Title").upper()

    def create(self, children=None):
        # Tukuyin ang mga naka-scope na istilo gamit ang natatanging scope_attr ng component
        scoped_style = f"""
            div[{self.scope_attr}] h1 {{
                color: blue;
            }}
        """
        
        return div(
            style(scoped_style),
            h1(self.title), # Gamitin ang pamagat mula sa before_render
            *(children or []) # I-render ang mga anak na ipinasa sa component
        )

# app.py
from syqlorix import Syqlorix, body
from components import Card

doc = Syqlorix()

@doc.route('/')
def home(request):
    return body(
        # Ipasa ang mga prop at mga anak sa iyong component
        Card(title="Aking Card",
            p("Ito ang nilalaman ng card.")
        )
    )
```

### Pamamahala ng Estado

Ang mga component ay maaaring magkaroon ng kanilang sariling panloob na estado. Ang estado ay pinamamahalaan sa server, at ang mga update ay na-trigger ng mga bagong kahilingan sa pahina.

```python
class Counter(Component):
    def __init__(self, *children, **props):
        super().__init__(*children, **props)
        # Simulan ang estado mula sa mga prop (hal., mula sa mga query param ng kahilingan)
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

### Pag-istruktura ng Malalaking Aplikasyon gamit ang mga Blueprint

Gamitin ang mga Blueprint upang ayusin ang iyong mga ruta sa magkakahiwalay na mga file.

```python
# pages/about.py
from syqlorix import Blueprint, h1

about_bp = Blueprint("about")

@about_bp.route('/about')
def about_page(request):
    return h1("Tungkol sa Amin")

# main_app.py
from syqlorix import Syqlorix
from pages.about import about_bp

doc = Syqlorix()
doc.register_blueprint(about_bp)
```

### Dynamic na Pagruruta

Tukuyin ang mga ruta na may mga variable na seksyon gamit ang `<var_name>` syntax. Ang mga nakuhang halaga ay magagamit sa `request.path_params`.

```python
@doc.route('/user/<username>')
def user_profile(request):
    username = request.path_params.get('username', 'Guest')
    return h1(f"Kamusta, {username}!")
```

</details>

<details>
  <summary><h2><strong>› I-click upang makita ang Command-Line Interface (CLI)</strong></h2></summary>

Ang Syqlorix ay may kasamang simple at malakas na CLI.

*   #### `syqlorix init [filename]`
    Gumagawa ng bagong file ng proyekto na may isang kapaki-pakinabang na template upang makapagsimula ka.
    ```bash
    syqlorix init my_cool_app
    ```

*   #### `syqlorix run <file>`
    Nagpapatakbo ng live-reloading development server.
    *   `--port <number>`: Tukuyin ang isang panimulang port (default sa 8000).
    *   `--no-reload`: Huwag paganahin ang tampok na live-reload.
    ```bash
    syqlorix run app.py --port 8080
    ```

*   #### `syqlorix build <file>`
    Bumubuo ng isang static na bersyon ng iyong site mula sa mga static na ruta ng iyong app.
    *   `--output <dirname>` o `-o <dirname>`: Itakda ang pangalan ng direktoryo ng output (default sa `dist`).
    ```bash
    syqlorix build main.py -o public
    ```

</details>

## Mga Target na Kaso ng Paggamit

*   **Mabilis na Prototyping**: Mabilis na i-mock up ang mga web interface nang hindi pinagsasabay-sabay ang maraming file.
*   **Mga Static na Site**: Bumuo ng mga blog, portfolio, at mga site ng dokumentasyon.
*   **Mga Simpleng Dashboard**: Lumikha ng mga panloob na tool o mga visualization ng data.
*   **Mga Tool na Pang-edukasyon**: Isang malinaw, Python-only na paraan upang ipakita ang mga pangunahing kaalaman sa web.
*   **Mga Simpleng API**: Bumuo at maghain ng data ng JSON mula sa mga Python script.

## Pag-aambag

Ang mga kontribusyon ay malugod na tinatanggap! Huwag mag-atubiling magbukas ng mga isyu o magsumite ng mga pull request sa [repositoryo ng GitHub](https://github.com/Syqlorix/Syqlorix).

## Lisensya

Ang proyektong ito ay lisensyado sa ilalim ng Lisensya ng MIT - tingnan ang file na [LICENSE](https://github.com/Syqlorix/Syqlorix/blob/main/LICENSE) para sa mga detalye.