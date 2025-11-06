# Syqlorix：用纯 Python 构建超简约的网页

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

## 概述

**Syqlorix** 是一个超简约的 Python 包，用于从**单个 Python 脚本**构建完整的 HTML 文档——包括 **CSS** 和 **JavaScript**。它提供了一个纯 Python 的 DSL（领域特定语言）来编写 Web 界面，并内置了实时重新加载服务器、动态路由和一个强大的静态网站生成器。

它专为那些希望在不离开 Python 环境的情况下创建 Web UI、静态网站和简单 API 的开发者设计。

### 核心设计原则

*   **一体化**：在 `.py` 文件中编写整个页面和组件。
*   **组件化**：使用可复用、有状态的组件来构建您的 UI。
*   **极简 API**：API 接口小，易于学习。
*   **零配置**：合理的默认设置，开箱即用。

---

## 主要功能

*   **纯 Python HTML：** 使用 Python 对象生成任何 HTML 元素。
*   **组件化架构：** 使用支持 props、children、作用域 CSS 和生命周期方法的可复用组件来构建您的 UI。
*   **状态管理：** 使用简单的服务器端状态管理模式创建交互式组件。
*   **实时重载服务器：** 开发服务器在代码更改时自动重新加载您的浏览器。
*   **静态网站生成 (SSG)：** 使用 `build` 命令将您的整个应用程序构建为高性能的静态网站。
*   **蓝图 (Blueprints)：** 通过将路由拆分到多个文件中来组织大型应用程序。
*   **动态路由：** 创建带有可变路径的简洁路由（例如 `/user/<username>`）。
*   **JSON API 响应：** 从路由返回 `dict` 或 `list` 来创建 API 端点。

## 快速入门

1.  **安装 Syqlorix：**
    ```bash
    pip install syqlorix
    ```

2.  **创建一个文件 `app.py`：**
    ```python
    from syqlorix import *
    
    doc = Syqlorix()
    
    @doc.route('/')
    def home(request):
        return Syqlorix(
            head(title("你好")),
            body(
                h1("来自 Syqlorix 的问候！"),
                p("这是一个完全由 Python 生成的网页。")
            )
        )
    ```

3.  **运行开发服务器：**
    ```bash
    syqlorix run app.py
    ```

4.  在浏览器中打开 `http://127.0.0.1:8000`。就是这样！

<br/>

<details>
  <summary><h2><strong>› 点击查看使用指南</strong></h2></summary>

### 组件化架构

Syqlorix 现在具有强大的组件化架构。组件是可复用的、有状态的，并且可以拥有自己的作用域样式。

```python
# components.py
from syqlorix import Component, div, h1, p, style

class Card(Component):
    def before_render(self):
        # 生命周期方法：在 create() 之前运行
        # 用于在渲染前修改状态或 props
        self.title = self.props.get("title", "Default Title").upper()

    def create(self, children=None):
        # 使用组件唯一的 scope_attr 定义作用域样式
        scoped_style = f"""
            div[{self.scope_attr}] h1 {{
                color: blue;
            }}
        """
        
        return div(
            style(scoped_style),
            h1(self.title), # 使用来自 before_render 的标题
            *(children or []) # 渲染传递给组件的 children
        )

# app.py
from syqlorix import Syqlorix, body
from components import Card

doc = Syqlorix()

@doc.route('/')
def home(request):
    return body(
        # 将 props 和 children 传递给您的组件
        Card(title="我的卡片",
            p("这是卡片的内容。")
        )
    )
```

### 状态管理

组件可以拥有自己的内部状态。状态在服务器端进行管理，更新由新的页面请求触发。

```python
class Counter(Component):
    def __init__(self, *children, **props):
        super().__init__(*children, **props)
        # 从 props 初始化状态（例如，从请求的查询参数）
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

### 使用蓝图 (Blueprints) 构建大型应用程序

使用蓝图将您的路由组织到不同的文件中。

```python
# pages/about.py
from syqlorix import Blueprint, h1

about_bp = Blueprint("about")

@about_bp.route('/about')
def about_page(request):
    return h1("关于我们")

# main_app.py
from syqlorix import Syqlorix
from pages.about import about_bp

doc = Syqlorix()
doc.register_blueprint(about_bp)
```

### 动态路由

使用 `<var_name>` 语法定义带有可变部分的路由。捕获的值可在 `request.path_params` 中获得。

```python
@doc.route('/user/<username>')
def user_profile(request):
    username = request.path_params.get('username', 'Guest')
    return h1(f"你好, {username}!")
```

</details>

<details>
  <summary><h2><strong>› 点击查看命令行界面 (CLI)</strong></h2></summary>

Syqlorix 带有一个简单而强大的命令行界面（CLI）。

*   #### `syqlorix init [filename]`
    创建一个带有实用模板的新项目文件，帮助您快速上手。
    ```bash
    syqlorix init my_cool_app
    ```

*   #### `syqlorix run <file>`
    运行实时重新加载的开发服务器。
    *   `--port <number>`：指定一个起始端口（默认为 8000）。
    *   `--no-reload`：禁用实时重新加载功能。
    ```bash
    syqlorix run app.py --port 8080
    ```

*   #### `syqlorix build <file>`
    从您的应用的静态路由构建站点的静态版本。
    *   `--output <dirname>` 或 `-o <dirname>`：设置输出目录的名称（默认为 `dist`）。
    ```bash
    syqlorix build main.py -o public
    ```

</details>

## 目标使用场景

*   **快速原型制作**：无需处理多个文件，快速构建 Web 界面原型。
*   **静态网站**：构建博客、作品集和文档网站。
*   **简单仪表盘**：创建内部工具或数据可视化。
*   **教育工具**：一种清晰的、纯 Python 的方式来演示 Web 基础知识。
*   **简单 API**：从 Python 脚本构建并提供 JSON 数据。

## 贡献

欢迎贡献！请随时在 [GitHub 仓库](https://github.com/Syqlorix/Syqlorix) 中提出问题或提交拉取请求。

## 许可证

该项目根据 MIT 许可证授权 - 有关详细信息，请参阅 [LICENSE](https://github.com/Syqlorix/Syqlorix/blob/main/LICENSE) 文件。