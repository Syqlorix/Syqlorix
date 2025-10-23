from syqlorix import doc
from syqlorix.templating import *

# Define common CSS that can be reused across pages
common_css = style("""
    body {
        background-color: #1a1a2e; color: #e0e0e0; font-family: sans-serif;
        display: grid; place-content: center; height: 100vh; margin: 0;
    }
    .container { text-align: center; max-width: 600px; padding: 2rem; border-radius: 8px; background: #2a2a4a; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
    h1 { color: #00a8cc; margin-bottom: 1rem;}
    p, form { color: #aaa; line-height: 1.6; }
    nav { margin-bottom: 2rem; }
    nav a { margin: 0 1rem; color: #72d5ff; text-decoration: none; font-weight: bold; }
    nav a:hover { text-decoration: underline; }
    input, button { font-size: 1rem; padding: 0.5rem; margin: 0.2rem; border-radius: 4px; border: 1px solid #444; background: #333; color: #eee; }
    button { cursor: pointer; background: #00a8cc; color: #1a1a2e; font-weight: bold; }
    hr { border-color: #444; margin: 2rem 0; }
""")

# Define a reusable template for all pages
def page_layout(title_text, content_node):
    return html(
        head(
            title(title_text),
            common_css,
            Comment("Live-reload script is injected automatically by the dev server")
        ),
        body(
            div.container(
                nav(
                    a("Home", href="/"),
                    a("Dynamic Route", href="/user/Syqlorix"),
                    a("Form Example", href="/message"),
                ),
                content_node
            )
        )
    )

# --- Define your routes ---

@doc.route('/')
def home_page(request):
    return page_layout("Home", div(
        h1("Welcome to the New Syqlorix!"),
        p("This app demonstrates dynamic routes and form handling."),
        p(f"You made a {request.method} request to {request.path_full}."),
    ))

@doc.route('/user/<username>')
def user_profile(request):
    username = request.path_params.get('username', 'Guest')
    return page_layout(f"Profile: {username}", div(
        h1(f"Hello, {username}!"),
        p("This page was generated from a dynamic route."),
        p("Try changing the name in the URL bar, e.g., /user/Python"),
    ))

@doc.route('/message', methods=['GET', 'POST'])
def message_form(request):
    content = div()
    if request.method == 'POST':
        user_message = request.form_data.get('message', 'nothing')
        content / h1("Message Received!")
        content / p(f"You sent: '{user_message}' via a POST request.")
        content / a("Send another message", href="/message")
    else: # GET request
        content / h1("Send a Message")
        content / form(
            label("Your message:", for_="message"),
            br(),
            input_(type="text", name="message", id="message"),
            button("Submit", type="submit"),
            method="POST",
            action="/message"
        )
        content / hr()
        content / p("Submitting this form will make a POST request to the same URL.")
    
    return page_layout("Message Board", content)

