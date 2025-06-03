import os
import json
from typing import Callable, Any, Union, Dict

from .utils import escape_html, format_attrs
from .components import component 

class _RawHtml:
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
        "meta", "link", "base", "title",
        "textarea",
        "label",
        "audio",
        "video",
        "canvas",
        "source",
        "track",
    }
    RETURN_ONLY_TAGS = {
        "li",
        "col", "param",
        "option",
        "source",
        "track",
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
                                    "details", "summary", "button", "textarea", "label",
                                    "audio", "video", "canvas", "select"}:
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
        raw_html_marker = _RawHtml(html_content)
        self._current_parent.add_child(raw_html_marker)


    def text_input(self, name: str, value: str = None, **attrs):
        input_attrs = {"type": "text", "name": name}
        if value is not None:
            input_attrs["value"] = value
        input_attrs.update(attrs)
        return self.input(**input_attrs)

    def password_input(self, name: str, value: str = None, **attrs):
        input_attrs = {"type": "password", "name": name}
        if value is not None:
            input_attrs["value"] = value
        input_attrs.update(attrs)
        return self.input(**input_attrs)

    def email_input(self, name: str, value: str = None, **attrs):
        input_attrs = {"type": "email", "name": name}
        if value is not None:
            input_attrs["value"] = value
        input_attrs.update(attrs)
        return self.input(**input_attrs)

    def number_input(self, name: str, value: Union[int, float] = None, **attrs):
        input_attrs = {"type": "number", "name": name}
        if value is not None:
            input_attrs["value"] = value
        input_attrs.update(attrs)
        return self.input(**input_attrs)

    def checkbox(self, name: str, value: str, checked: bool = False, **attrs):
        input_attrs = {"type": "checkbox", "name": name, "value": value}
        if checked:
            input_attrs["checked"] = True
        input_attrs.update(attrs)
        return self.input(**input_attrs)

    def radio(self, name: str, value: str, checked: bool = False, **attrs):
        input_attrs = {"type": "radio", "name": name, "value": value}
        if checked:
            input_attrs["checked"] = True
        input_attrs.update(attrs)
        return self.input(**input_attrs)

    def submit_button(self, text: str = "Submit", name: str = None, **attrs):
        button_attrs = {"type": "submit"}
        if name is not None:
            button_attrs["name"] = name
        button_attrs.update(attrs)
        return self.button(text, **button_attrs)

    def select(self, *content, **attrs):
        select_elem = _Element("select", attrs)
        for item in content:
            if isinstance(item, _Element):
                select_elem.add_child(item)
            elif isinstance(item, _RawHtml):
                select_elem.add_child(item)
            else:
                select_elem.add_child(str(item))
        
        self._current_parent.add_child(select_elem)
        return _ElementContext(self, select_elem)

    def validate_form_script(self, form_id: str, fields: Dict[str, Dict[str, Any]]):
        """
        Adds a basic client-side JavaScript validation function for a form.
        Fields dictionary example:
        {
            "username": {"required": True, "minlength": 3, "pattern": "[a-zA-Z0-9]+"},
            "email": {"required": True, "type": "email"},
            "password": {"required": True, "minlength": 8},
        }
        """
        validation_script = f"""
        document.addEventListener('DOMContentLoaded', function() {{
            const form = document.getElementById('{form_id}');
            if (!form) return;

            form.addEventListener('submit', function(event) {{
                let isValid = true;
                const errors = [];

                const fieldDefinitions = {json.dumps(fields)};

                for (const fieldNameKey in fieldDefinitions) {{
                    const fieldRules = fieldDefinitions[fieldNameKey];

                    const input = form.elements[fieldNameKey];
                    if (!input) continue;

                    let fieldValue = input.value.trim();

                    // Required check
                    if (fieldRules.required && fieldValue === '') {{
                        isValid = false;
                        errors.push(`Field '${{fieldNameKey}}' is required.`); // Escape JS variable
                        input.style.borderColor = 'red';
                        continue;
                    }} else {{
                        input.style.borderColor = '';
                    }}

                    // MinLength check
                    if (fieldRules.minlength && fieldValue.length < fieldRules.minlength) {{
                        isValid = false;
                        errors.push(`Field '${{fieldNameKey}}' must be at least ${{fieldRules.minlength}} characters.`); // Escape JS variables
                        input.style.borderColor = 'red';
                    }}

                    // Pattern check
                    if (fieldRules.pattern) {{
                        const regex = new RegExp(fieldRules.pattern);
                        if (!regex.test(fieldValue)) {{
                            isValid = false;
                            errors.push(`Field '${{fieldNameKey}}' format is invalid.`); // Escape JS variable
                            input.style.borderColor = 'red';
                        }}
                    }}

                    // Type check (for email, etc.)
                    if (fieldRules.type === 'email' && !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(fieldValue) && fieldValue !== '') {{
                         isValid = false;
                         errors.push(`Field '${{fieldNameKey}}' must be a valid email address.`); // Escape JS variable
                         input.style.borderColor = 'red';
                    }}
                }}

                if (!isValid) {{
                    event.preventDefault();
                    alert('Validation Errors:\\n' + errors.join('\\n'));
                }} else {{
                    event.preventDefault();
                    alert('Form is valid! (Submission would proceed in a real app)');
                }}
            }});
        }});
        """
        self.script(validation_script)

    def add_component(self, component_func: Callable, *args, **kwargs):
        if not hasattr(component_func, '_is_syqlorix_component') or not component_func._is_syqlorix_component:
            raise TypeError(f"'{component_func.__name__}' is not a valid Syqlorix component. "
                            "Ensure it is decorated with `@component` from `syqlorix.components`.")
        
        component_func(self, *args, **kwargs)

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