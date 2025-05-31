from syqlorix import Page

page = Page(title="Welcome to Syqlorix")

with page.body:
    page.h1("Build Pages in Python")
    page.p("No need for HTML files. This is all Python.")

    with page.div(id="features"):
        page.h2("Key Features")
        page.ul(
            page.li("HTML via functions"),
            page.li("Inline CSS/JS blocks"),
            page.li("Flask integration"),
        )
    page.button("Click Me", id="btn", _class="my-button")

page.style("""
    body { font-family: system-ui; margin: 40px; }
    #features { background: #f0f0f0; padding: 10px; border-radius: 6px; }
    .my-button { background: #0d6efd; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; }
    .my-button:hover { background: #0a58ca; }
""")

page.script("""
    document.getElementById('btn').onclick = function() {
        alert('Clicked with Syqlorix!');
    };
""")

html_output = page.render()

print(html_output)