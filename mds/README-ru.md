# Syqlorix: Создавайте гиперминималистичные веб-страницы на чистом Python

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

## Обзор

**Syqlorix** — это гиперминималистичный пакет Python для создания полных HTML-документов, включая **CSS** и **JavaScript**, из **одного скрипта Python**. Он предлагает чистый Python DSL (предметно-ориентированный язык) для создания веб-интерфейсов, со встроенным сервером с живой перезагрузкой, динамической маршрутизацией и мощным генератором статических сайтов.

Он разработан для разработчиков, которые хотят создавать веб-интерфейсы, статические сайты и простые API, не выходя из комфортной среды Python.

### Основные принципы дизайна

*   **Все в одном**: Пишите целые страницы и компоненты в файлах `.py`.
*   **Компонентный подход**: Структурируйте свой UI с помощью повторно используемых компонентов с состоянием.
*   **Минимальный API**: Небольшая поверхность API, легко изучить.
*   **Нулевая конфигурация**: Разумные значения по умолчанию для мгновенной продуктивности.

---

## Ключевые особенности

*   **Чистый Python HTML:** Генерируйте любой HTML-элемент с помощью объектов Python.
*   **Компонентная архитектура:** Создавайте свой UI с помощью повторно используемых компонентов, которые поддерживают props, children, стили с ограниченной областью видимости и методы жизненного цикла.
*   **Управление состоянием:** Создавайте интерактивные компоненты с помощью простого серверного паттерна управления состоянием.
*   **Сервер с живой перезагрузкой:** Сервер разработки автоматически перезагружает ваш браузер при изменении кода.
*   **Генерация статических сайтов (SSG):** Соберите все ваше приложение в высокопроизводительный статический сайт с помощью команды `build`.
*   **Blueprints (Чертежи):** Организуйте большие приложения, разделяя маршруты на несколько файлов.
*   **Динамическая маршрутизация:** Создавайте чистые маршруты с переменными путями (например, `/user/<username>`).
*   **Ответы JSON API:** Возвращайте `dict` или `list` из маршрута для создания конечной точки API.

## Быстрый старт

1.  **Установите Syqlorix:**
    ```bash
    pip install syqlorix
    ```

2.  **Создайте файл `app.py`:**
    ```python
    from syqlorix import *
    
    doc = Syqlorix()
    
    @doc.route('/')
    def home(request):
        return Syqlorix(
            head(title("Привет")),
            body(
                h1("Привет от Syqlorix!"),
                p("Это веб-страница, полностью сгенерированная из Python.")
            )
        )
    ```

3.  **Запустите сервер для разработки:**
    ```bash
    syqlorix run app.py
    ```

4.  Откройте браузер по адресу `http://127.0.0.1:8000`. Вот и все!

<br/>

<details>
  <summary><h2><strong>› Нажмите, чтобы просмотреть Руководство по использованию</strong></h2></summary>

### Компонентная архитектура

Syqlorix теперь имеет мощную компонентную архитектуру. Компоненты являются повторно используемыми, имеют состояние и могут иметь свои собственные стили с ограниченной областью видимости.

```python
# components.py
from syqlorix import Component, div, h1, p, style

class Card(Component):
    def before_render(self):
        # Метод жизненного цикла: запускается перед create()
        # Используйте его для изменения состояния или props перед рендерингом
        self.title = self.props.get("title", "Default Title").upper()

    def create(self, children=None):
        # Определите стили с ограниченной областью видимости, используя уникальный scope_attr компонента
        scoped_style = f"""
            div[{self.scope_attr}] h1 {{
                color: blue;
            }}
        """
        
        return div(
            style(scoped_style),
            h1(self.title), # Используйте заголовок из before_render
            *(children or []) # Рендеринг дочерних элементов, переданных компоненту
        )

# app.py
from syqlorix import Syqlorix, body
from components import Card

doc = Syqlorix()

@doc.route('/')
def home(request):
    return body(
        # Передайте props и дочерние элементы вашему компоненту
        Card(title="Моя карточка",
            p("Это содержимое карточки.")
        )
    )
```

### Управление состоянием

Компоненты могут иметь свое собственное внутреннее состояние. Состояние управляется на сервере, а обновления вызываются новыми запросами страниц.

```python
class Counter(Component):
    def __init__(self, *children, **props):
        super().__init__(*children, **props)
        # Инициализируйте состояние из props (например, из параметров запроса)
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

### Структурирование больших приложений с помощью Blueprints

Используйте Blueprints для организации ваших маршрутов в отдельные файлы.

```python
# pages/about.py
from syqlorix import Blueprint, h1

about_bp = Blueprint("about")

@about_bp.route('/about')
def about_page(request):
    return h1("О нас")

# main_app.py
from syqlorix import Syqlorix
from pages.about import about_bp

doc = Syqlorix()
doc.register_blueprint(about_bp)
```

### Динамическая маршрутизация

Определяйте маршруты с переменными участками, используя синтаксис `<var_name>`. Захваченные значения доступны в `request.path_params`.

```python
@doc.route('/user/<username>')
def user_profile(request):
    username = request.path_params.get('username', 'Guest')
    return h1(f"Привет, {username}!")
```

</details>

<details>
  <summary><h2><strong>› Нажмите, чтобы просмотреть Интерфейс командной строки (CLI)</strong></h2></summary>

Syqlorix поставляется с простым и мощным CLI.

*   #### `syqlorix init [filename]`
    Создает новый файл проекта с полезным шаблоном, чтобы помочь вам начать.
    ```bash
    syqlorix init my_cool_app
    ```

*   #### `syqlorix run <file>`
    Запускает сервер разработки с живой перезагрузкой.
    *   `--port <number>`: Укажите начальный порт (по умолчанию 8000).
    *   `--no-reload`: Отключить функцию живой перезагрузки.
    ```bash
    syqlorix run app.py --port 8080
    ```

*   #### `syqlorix build <file>`
    Создает статическую версию вашего сайта из статических маршрутов вашего приложения.
    *   `--output <dirname>` или `-o <dirname>`: Установите имя выходного каталога (по умолчанию `dist`).
    ```bash
    syqlorix build main.py -o public
    ```

</details>

## Целевые случаи использования

*   **Быстрое прототипирование**: Быстро создавайте макеты веб-интерфейсов, не переключаясь между несколькими файлами.
*   **Статические сайты**: Создавайте блоги, портфолио и сайты документации.
*   **Простые панели мониторинга**: Создавайте внутренние инструменты или визуализации данных.
*   **Образовательные инструменты**: Ясный, только на Python, способ демонстрации основ веба.
*   **Простые API**: Создавайте и обслуживайте данные JSON из скриптов Python.

## Вклад

Вклад приветствуется! Не стесняйтесь открывать issues или отправлять pull requests в [репозитории на GitHub](https://github.com/Syqlorix/Syqlorix).

## Лицензия

Этот проект лицензирован по лицензии MIT - подробности см. в файле [LICENSE](https://github.com/Syqlorix/Syqlorix/blob/main/LICENSE).