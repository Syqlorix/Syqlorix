from .page import _Element, _RawHtml 
from .utils import escape_html, format_attrs

SELF_CLOSING_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr"
}

RAW_CONTENT_TAGS = {"script", "style"} 

def _render_element(element: _Element) -> str:
    tag = element.tag
    attrs_str = format_attrs(element.attributes)
    open_tag = f"<{tag}{' ' + attrs_str if attrs_str else ''}>"

    if tag in SELF_CLOSING_TAGS:
        if element.children:
            pass
        return open_tag

    children_html = []
    for child in element.children:
        if isinstance(child, _Element):
            children_html.append(_render_element(child))
        elif isinstance(child, _RawHtml): 
            children_html.append(child.content)
        else: 
            if tag in RAW_CONTENT_TAGS:
                children_html.append(str(child))
            else:
                children_html.append(escape_html(str(child)))

    content = "".join(children_html)
    close_tag = f"</{tag}>"
    return f"{open_tag}{content}{close_tag}"

def render_page(root_element: _Element) -> str:
    if root_element.tag != "html":
        raise ValueError("Root element must be <html> for a complete HTML page.")
    
    html_content = _render_element(root_element)
    return f"<!DOCTYPE html>\n{html_content}"