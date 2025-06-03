from syqlorix import Page, css, component, Route, SimpleAlert, ImageGallery, load_component # Import new features
import datetime
import os

main_router = Route("/")

@component 
def common_header(page_instance: Page, current_route: str = "/"):
    with page_instance.header(_class="site-header"):
        page_instance.h1("Syqlorix Site")
        with page_instance.nav(_class="site-nav"):
            page_instance.a("Home", href="/", _class="active" if current_route == "/" else "")
            page_instance.a("About", href="/about", _class="active" if current_route == "/about" else "")
            page_instance.a("Dynamic", href="/dynamic", _class="active" if current_route == "/dynamic" else "")
            page_instance.a("Static Assets", href="/static-demo", _class="active" if current_route == "/static-demo" else "")
            page_instance.a("Forms", href="/forms", _class="active" if current_route == "/forms" else "")
            page_instance.a("Media & Comp", href="/media-comp", _class="active" if current_route == "/media-comp" else "")

@component 
def common_footer(page_instance: Page):
        page_instance.footer(f"© {datetime.datetime.now().year} Syqlorix Demo Site. Version 0.0.2.6")


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
        "font_weight": "bold",
        "padding": "5px 10px",
        "border_radius": "4px"
    },
    ".site-nav a:hover, .site-nav a.active": {
        "background_color": "#0a58ca"
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
    },
    "form label": {
        "display": "block",
        "margin_bottom": "5px",
        "font_weight": "bold"
    },
    "form input[type='text'], form input[type='password'], form input[type='email'], form input[type='number'], form textarea, form select": {
        "width": "calc(100% - 22px)",
        "padding": "10px",
        "margin_bottom": "15px",
        "border": "1px solid #ddd",
        "border_radius": "4px"
    },
    "form input[type='submit']": {
        "background_color": "#28a745",
        "color": "white",
        "border": "none",
        "padding": "12px 20px",
        "border_radius": "5px",
        "cursor": "pointer"
    },
    ".media-player": {
        "width": "100%",
        "max_width": "640px",
        "height": "auto",
        "background": "#000",
        "margin_bottom": "20px",
        "display": "block"
    },
    "canvas": {
        "border": "1px solid #ccc",
        "display": "block",
        "margin_top": "10px"
    },
    ".custom-loaded-btn": {
        "background_color": "#6f42c1", # Purple
        "color": "white",
        "border": "none",
        "padding": "10px 20px",
        "border_radius": "5px",
        "cursor": "pointer",
        "transition": "background-color 0.3s ease"
    },
    ".custom-loaded-btn:hover": {
        "background_color": "#563d7c"
    }
}
base_styles = css(**base_styles_dict)



@main_router.route("/")
def home_page_callable() -> Page:
    page = Page(title="Home - My Syqlorix Site")
    page.style(base_styles)
    page.link_css(href="/static/css/main.css")

    with page.body:
        page.add_component(common_header, current_route="/")
        with page.main():
            page.h1("Welcome to Syqlorix Site!")
            page.add_component(SimpleAlert, "This is an info alert from a pre-defined component!", type="info") # NEW
            page.p("This is the home page. Explore the new features!")
            page.p("This page links to an external CSS file: `static/css/main.css`.")
            page.p("The header and footer are reusable Python components.")
            page.p("Also, the `meta` and `title` tags are now directly addable.")
            page.br()
            page.raw("<b>This is some <i>raw</i> HTML inserted directly.</b>")
            page.p("The line above was inserted using `page.raw()`.")
        page.add_component(common_footer)
    return page

@main_router.route("/about")
def about_page_callable() -> Page:
    page = Page(title="About Us")
    page.style(base_styles)
    with page.body:
        page.add_component(common_header, current_route="/about")
        with page.main():
            page.h1("About Our Project")
            page.p("Syqlorix is an amazing Python DSL for web development.")
            page.p("It aims to simplify creating web interfaces directly in Python.")
            page.add_component(SimpleAlert, "This is a warning alert!", type="warning") # NEW
        page.add_component(common_footer)
    return page

@main_router.route("/dynamic")
def create_dynamic_page() -> Page:
    dynamic_page = Page(title="Dynamic Content")
    dynamic_page.style(base_styles)
    with dynamic_page.body:
        dynamic_page.add_component(common_header, current_route="/dynamic")
        with dynamic_page.main():
            dynamic_page.h1("Current Time")
            dynamic_page.p(f"The current time is: {datetime.datetime.now().strftime('%H:%M:%S')}")
            dynamic_page.p("This content is generated fresh on each request.")
        dynamic_page.add_component(common_footer)
    return dynamic_page

@main_router.route("/static-demo")
def static_demo_page_callable() -> Page:
    page = Page(title="Static Assets Demo")
    page.style(base_styles)
    page.link_css(href="/static/css/main.css") 
    page.link_js(src="/static/js/app.js", defer=True)

    with page.body:
        page.add_component(common_header, current_route="/static-demo")
        with page.main():
            page.h1("External Static Assets")
            page.p("This page uses an external CSS file and an external JavaScript file.")
            page.div("This box is styled by `static/css/main.css`.", _class="external-box")
            page.button("Click Me (External JS)", id="externalBtn")
            page.p("Check the browser's console for a message from `static/js/app.js`.")
        page.add_component(common_footer)
    return page

@main_router.route("/forms")
def forms_page_callable() -> Page:
    page = Page(title="Syqlorix Forms Demo")
    page.style(base_styles)
    with page.body:
        page.add_component(common_header, current_route="/forms")
        with page.main():
            page.h1("Form Elements Demo")
            page.add_component(SimpleAlert, "Fill out the form below!", type="info")
            page.p("Demonstrating Syqlorix's new specialized form input helpers.")
            
            with page.form(action="/submit-form", method="post", id="myForm"):
                page.label("Username (min 3 chars, alphanumeric):", _for="username")
                page.text_input(name="username", id="username", placeholder="Enter your username", required=True)
                
                page.label("Password (min 8 chars):", _for="password")
                page.password_input(name="password", id="password", required=True)
                
                page.label("Email:", _for="email")
                page.email_input(name="email", id="email", placeholder="your.email@example.com")
                
                page.label("Quantity:", _for="qty")
                page.number_input(name="qty", id="qty", value=1, min=1, max=10)
                
                page.label("Your Message:", _for="message")
                with page.textarea(name="message", id="message", rows=5, placeholder="Type your message here"):
                    page.raw("Optional initial message content.")
                
                page.p("Choose your favorite fruit:")
                page.checkbox(name="fruit", value="apple", id="apple_chk", checked=True)
                page.label("Apple", _for="apple_chk")
                page.br()
                page.checkbox(name="fruit", value="banana", id="banana_chk")
                page.label("Banana", _for="banana_chk")
                page.br()
                
                page.p("Select an option:")
                page.select(
                    page.option("Option 1", value="opt1"),
                    page.option("Option 2", value="opt2", selected=True),
                    page.option("Option 3", value="opt3"),
                    name="options",
                    id="options"
                )
                
                page.br()
                page.submit_button("Submit Form", _class="my-submit-btn")
        page.add_component(common_footer)
    
    page.validate_form_script(
        form_id="myForm",
        fields={
            "username": {"required": True, "minlength": 3, "pattern": "^[a-zA-Z0-9]+$"},
            "email": {"required": True, "type": "email"},
            "password": {"required": True, "minlength": 8},
        }
    )
    return page

@main_router.route("/media-comp")
def media_comp_page_callable() -> Page:
    page = Page(title="Media & Components Demo")
    page.style(base_styles)
    dummy_comp_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_custom_button_comp.py")
    if not os.path.exists(dummy_comp_file_path):
        with open(dummy_comp_file_path, "w") as f:
            f.write("""
from syqlorix import Page, component

@component
def CustomButtonComponent(page_instance: Page, text: str = "Loaded Button", **attrs):
    page_instance.button(text, _class="custom-loaded-btn", **attrs)
""")

    CustomButtonComponent = load_component(dummy_comp_file_path, "CustomButtonComponent")

    with page.body:
        page.add_component(common_header, current_route="/media-comp")
        with page.main():
            page.h1("Media Elements")
            page.p("Audio Player:")
            with page.audio(controls=True, _class="media-player"):
                page.source(src="/static/audio/sample.mp3", type="audio/mpeg")
                page.raw("Your browser does not support the audio element.")
            
            page.p("Video Player:")
            with page.video(controls=True, width="640", height="360", _class="media-player"):
                page.source(src="/static/video/sample.mp4", type="video/mp4")
                page.raw("Your browser does not support the video tag.")
            
            page.p("Canvas Element (drawn with JS):")
            page.canvas(id="myCanvas", width="200", height="100")
            page.script("""
                const canvas = document.getElementById('myCanvas');
                if (canvas) {
                    const ctx = canvas.getContext('2d');
                    ctx.fillStyle = 'green';
                    ctx.fillRect(10, 10, 150, 75);
                }
            """)

            page.h2("Pre-defined Components")
            page.add_component(SimpleAlert, "This is a success alert from `components_lib`!", type="success")
            page.add_component(ImageGallery, images=["/static/img/img1.png", "/static/img/img2.png"]) # changed to local image so it'll be easier to know when we have some issue
            
            page.h2("Dynamically Loaded Component")
            page.add_component(CustomButtonComponent, "I'm a Loaded Button!")

        page.add_component(common_footer)
    return page



if __name__ == '__main__':
    from syqlorix import start_dev_server

    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_for_example = os.path.dirname(current_script_dir) 

    start_dev_server(main_router, port=8000, project_root=project_root_for_example)