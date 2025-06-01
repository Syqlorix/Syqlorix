from .utils import escape_html, format_attrs

class _RawHtml:
    """Internal marker class for raw, unescaped HTML content."""
    def __init__(self, content: str):
        self.content = content

class _Element:
    def __init__(self, tag: str, attributes: dict = None):
        self.tag = tag
        self.attributes = attributes if attributes is not None else {}
        self.children = []

    def add_child(self, child):
        self.children.append(child)
        return self

    def __str__(self):
        attrs_str = format_attrs(self.attributes)
        return f"<{self.tag}{' ' + attrs_str if attrs_str else ''}>"

class _ElementContext:
    def __init__(self, page_instance, element: _Element):
        self._page = page_instance
        self._element = element
        self._original_parent = None

    def __enter__(self):
        self._original_parent = self._page._current_parent
        self._page._current_parent = self._element
        return self._element

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._page._current_parent = self._original_parent


class Page:
    AUTO_ADD_TAGS = {
        "html", "head", "body", "div", "ul", "ol", "p", "span",
        "h1", "h2", "h3", "h4", "h5", "h6", "form", "table", "tr", "td", "th",
        "header", "footer", "nav", "article", "section", "aside", "main", "figure",
        "figcaption", "fieldset", "legend", "details", "summary", "a", "button",
        "img", "input", "br", "hr", "embed", "wbr",
        "meta", "link", "base", "title"
    }
    RETURN_ONLY_TAGS = {
        "li",
        "col", "param", "source", "track",
    }

    def __init__(self, title: str = ""):
        self._root_element = _Element("html")
        self._head = _Element("head")
        self._body = _Element("body")

        self._root_element.add_child(self._head)
        self._root_element.add_child(self._body)

        self._current_parent = self._body

        if title:
            self.title(title)

        self._styles = []
        self._scripts = []
        self._body_scripts = []

        self.head = _ElementContext(self, self._head)
        self.body = _ElementContext(self, self._body)

    def __getattr__(self, tag_name: str):
        html_tag_name = tag_name.lower()

        if html_tag_name not in self.AUTO_ADD_TAGS and html_tag_name not in self.RETURN_ONLY_TAGS:
            self.AUTO_ADD_TAGS.add(html_tag_name)

        def tag_method(*content, **attrs):
            new_element = _Element(html_tag_name, attrs)

            for item in content:
                if isinstance(item, _Element):
                    new_element.add_child(item)
                elif isinstance(item, _RawHtml): 
                    new_element.add_child(item)
                else:
                    new_element.add_child(str(item))

            if html_tag_name in self.AUTO_ADD_TAGS:
                if html_tag_name in {"meta", "link", "base", "title"}:
                    self._head.add_child(new_element)
                else:
                    self._current_parent.add_child(new_element)
                
                if html_tag_name in {"div", "ul", "ol", "p", "span", "h1", "h2", "h3", "h4", "h5", "h6",
                                    "form", "table", "tr", "td", "th", "header", "footer", "nav", "article",
                                    "section", "aside", "main", "figure", "figcaption", "fieldset", "legend",
                                    "details", "summary", "a", "button"}:
                    return _ElementContext(self, new_element)
                else:
                    return new_element
            elif html_tag_name in self.RETURN_ONLY_TAGS:
                return new_element
            else:
                return new_element

        return tag_method

    def style(self, css_str: str):
        self._styles.append(css_str)

    def script(self, js_str: str):
        self._scripts.append(js_str)

    def link_css(self, href: str, **attrs):
        link_attrs = {"rel": "stylesheet", "href": href}
        link_attrs.update(attrs)
        self._head.add_child(_Element("link", link_attrs))

    def link_js(self, src: str, **attrs):
        script_attrs = {"src": src, "type": "text/javascript"}
        script_attrs.update(attrs)
        self._body_scripts.append(_Element("script", script_attrs))

    def raw(self, html_content: str):
        """
        Adds raw, unescaped HTML content directly to the current parent element.
        Use with caution, as this content will not be HTML-escaped.
        """
        raw_html_marker = _RawHtml(html_content)
        self._current_parent.add_child(raw_html_marker)

    def render(self) -> str:
        from .render import render_page

        if self._styles:
            style_element = _Element("style")
            style_element.add_child("\n".join(self._styles))
            self._head.add_child(style_element)

        if self._scripts:
            script_element = _Element("script")
            script_element.attributes["type"] = "text/javascript"
            script_element.add_child("\n".join(self._scripts))
            self._body.add_child(script_element)

        for script_tag in self._body_scripts:
            self._body.add_child(script_tag)

        return render_page(self._root_element)