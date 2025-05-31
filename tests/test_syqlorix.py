import pytest
from syqlorix import Page

def test_basic_page_structure():
    page = Page(title="Test Page")
    with page.body:
        page.h1("Hello")
        page.p("World")

    html = page.render()
    assert "<!DOCTYPE html>" in html
    assert "<title>Test Page</title>" in html
    assert "<body>" in html
    assert "<h1>Hello</h1>" in html
    assert "<p>World</p>" in html
    assert "</body>" in html
    assert "</html>" in html

def test_nested_elements():
    page = Page()
    with page.body:
        with page.div(id="container"):
            page.span("Nested content")
            page.p("Another paragraph")
    
    html = page.render()
    assert '<div id="container">' in html
    assert '<span>Nested content</span>' in html
    assert '<p>Another paragraph</p>' in html
    assert '</div>' in html
    assert 'div id="container"><span>' in html
    assert '</span><p>' in html

def test_list_items_composition():
    page = Page()
    with page.body:
        page.ul(
            page.li("Item 1"),
            page.li("Item 2", _class="special"),
            page.li("Item 3")
        )
    
    html = page.render()
    assert "<ul>" in html
    assert "<li>Item 1</li>" in html
    assert '<li class="special">Item 2</li>' in html
    assert "<li>Item 3</li>" in html
    assert "</ul>" in html
    assert '<ul><li>Item 1</li><li class="special">Item 2</li><li>Item 3</li></ul>' in html

def test_css_and_js_injection():
    page = Page(title="Scripted Page")
    page.style("body { color: red; }")
    page.script("alert('Hello');")

    html = page.render()
    assert "<title>Scripted Page</title>" in html
    assert "<style>body { color: red; }</style>" in html
    assert '<script type="text/javascript">alert(\'Hello\');</script>' in html
    assert "<head><title>Scripted Page</title><style>body { color: red; }</style></head>" in html
    assert '<body><script type="text/javascript">alert(\'Hello\');</script></body>' in html


def test_attributes_handling():
    page = Page()
    with page.body:
        page.a("Link", href="https://example.com", target="_blank")
        page.input(type="text", placeholder="Enter text", required=True)

    html = page.render()
    assert '<a href="https://example.com" target="_blank">Link</a>' in html
    assert '<input type="text" placeholder="Enter text" required>' in html or \
           '<input placeholder="Enter text" type="text" required>' in html