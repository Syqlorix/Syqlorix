from syqlorix import Page, css
import datetime
import os 

def common_header(page_instance: Page):
    with page_instance.header(_class="site-header"):
        page_instance.h1("Syqlorix Site")
        with page_instance.nav(_class="site-nav"):
            page_instance.a("Home", href="/")
            page_instance.a("About", href="/about")
            page_instance.a("Dynamic", href="/dynamic")
            page_instance.a("Static Assets", href="/static-demo")

def common_footer(page_instance: Page):
    page_instance.footer(f"© {datetime.datetime.now().year} Syqlorix Demo Site")

base_styles_dict = {
    "body": {
        "font_family": "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        "margin": "0",
        "padding": "0",
        "background": "#f8f9fa",
        "color": "#333",
        "line_height": "1.6"
    },
    ".site-header": {
        "background_color": "#0d6efd",
        "color": "white",
        "padding": "20px 40px",
        "text_align": "center"
    },
    ".site-nav a": {
        "color": "white",
        "margin": "0 15px",
        "text_decoration": "none",
        "font_weight": "bold"
    },
    ".site-nav a:hover": {
        "text_decoration": "underline"
    },
    "main": {
        "padding": "20px 40px",
        "max_width": "800px",
        "margin": "20px auto",
        "background": "white",
        "border_radius": "8px",
        "box_shadow": "0 2px 10px rgba(0,0,0,0.05)"
    },
    "footer": {
        "text_align": "center",
        "padding": "20px",
        "margin_top": "50px",
        "color": "#666",
        "border_top": "1px solid #eee"
    }
}
base_styles = css(**base_styles_dict)


home_page = Page(title="Home - My Syqlorix Site")
home_page.style(base_styles)
home_page.link_css(href="/static/css/main.css")

with home_page.body:
    common_header(home_page)
    with home_page.main():
        home_page.h1("Welcome to Syqlorix Site!")
        home_page.p("This is the home page. Explore the new features!")
        home_page.p("This page links to an external CSS file: `static/css/main.css`.")
        home_page.p("The header and footer are reusable Python components.")
        home_page.p("Also, the `meta` and `title` tags are now directly addable.")
    common_footer(home_page)

about_page = Page(title="About Us")
about_page.style(base_styles)
with about_page.body:
    common_header(about_page)
    with about_page.main():
        about_page.h1("About Our Project")
        about_page.p("Syqlorix is an amazing Python DSL for web development.")
        about_page.p("It aims to simplify creating web interfaces directly in Python.")
    common_footer(about_page)

def create_dynamic_page() -> Page:
    dynamic_page = Page(title="Dynamic Content")
    dynamic_page.style(base_styles)
    with dynamic_page.body:
        common_header(dynamic_page)
        with dynamic_page.main():
            dynamic_page.h1("Current Time")
            dynamic_page.p(f"The current time is: {datetime.datetime.now().strftime('%H:%M:%S')}")
            dynamic_page.p("This content is generated fresh on each request.")
        common_footer(dynamic_page)
    return dynamic_page

static_demo_page = Page(title="Static Assets Demo")
static_demo_page.style(base_styles)
static_demo_page.link_css(href="/static/css/main.css") 
static_demo_page.link_js(src="/static/js/app.js", defer=True)

with static_demo_page.body:
    common_header(static_demo_page)
    with static_demo_page.main():
        static_demo_page.h1("External Static Assets")
        static_demo_page.p("This page uses an external CSS file and an external JavaScript file.")
        static_demo_page.div("This box is styled by `static/css/main.css`.", _class="external-box")
        static_demo_page.button("Click Me (External JS)", id="externalBtn")
        static_demo_page.p("Check the browser's console for a message from `static/js/app.js`.")
    common_footer(static_demo_page)


routes = {
    "/": home_page,
    "/about": about_page,
    "/dynamic": create_dynamic_page,
    "/static-demo": static_demo_page,
}

if __name__ == '__main__':
    from syqlorix import serve_pages_dev

    
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_for_example = os.path.dirname(current_script_dir) 

    
    serve_pages_dev(routes, port=8000, project_root=project_root_for_example)