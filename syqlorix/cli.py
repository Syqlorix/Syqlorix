import click
import sys
import os
from pathlib import Path
import importlib.util
from importlib import metadata as importlib_metadata
from jsmin import jsmin
from cssmin import cssmin

PACKAGE_VERSION = importlib_metadata.version('syqlorix')


class C:
    BANNER_START = '\033[38;5;27m'
    BANNER_END = '\033[38;5;201m'
    PRIMARY = '\033[38;5;51m'
    SUCCESS = '\033[92m'
    ERROR = '\033[91m'
    INFO = '\033[94m'
    MUTED = '\033[90m'
    BOLD = '\033[1m'
    END = '\033[0m'

SYQLORIX_BANNER = rf"""{C.BANNER_START}
 .oooooo..o                        oooo                      o8o              
d8P'    `Y8                        `888                      `"'              
Y88bo.      oooo    ooo  .ooooo oo  888   .ooooo.  oooo d8b oooo  oooo    ooo 
 `"Y8888o.   `88.  .8'  d88' `888   888  d88' `88b `888""8P `888   `88b..8P'  
     `"Y88b   `88..8'   888   888   888  888   888  888      888     Y888'    
oo     .d8P    `888'    888   888   888  888   888  888      888   .o8"'88b   
8""88888P'      .8'     `V8bod888  o888o `Y8bod8P' d888b    o888o o88'   888o 
            .o..P'            888.                                            
            `Y8P'             8P'                                             
                              "                    {C.END}{C.BANNER_END}{C.END}{C.MUTED}v{PACKAGE_VERSION}{C.END}
"""

def find_doc_instance(file_path):
    try:
        path = Path(file_path).resolve()
        spec = importlib.util.spec_from_file_location(path.stem, str(path))
        if not spec or not spec.loader:
            raise ImportError(f"Could not load spec for module {path.stem}")
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(path.parent))
        spec.loader.exec_module(module)
        sys.path.pop(0)
        from . import Syqlorix
        if hasattr(module, 'doc') and isinstance(module.doc, Syqlorix):
            return module.doc
        else:
            click.echo(f"{C.ERROR}Error: Could not find a 'doc = Syqlorix()' instance in '{file_path}'.{C.END}")
            sys.exit(1)
    except Exception as e:
        click.echo(f"{C.ERROR}Error loading '{file_path}':\n{e}{C.END}")
        sys.exit(1)

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(version=PACKAGE_VERSION, prog_name="syqlorix")
def main():
    pass

@main.command()
@click.argument('file', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--host', '-H', default='127.0.0.1', help='The interface to bind to.')
@click.option('--port', '-p', default=8000, type=int, help='The port to start searching from.')
@click.option('--no-reload', is_flag=True, default=False, help='Disable live-reloading.')
def run(file, host, port, no_reload):
    click.echo(SYQLORIX_BANNER)
    doc_instance = find_doc_instance(file)
    doc_instance.run(file_path=file, host=host, port=port, live_reload=not no_reload)

@main.command()
@click.argument('file', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--output', '-o', default=None, help='Output file name. Defaults to <input_name>.html.')
@click.option('--minify', is_flag=True, default=False, help='Minify HTML, and inline CSS/JS.')
def build(file, output, minify):    
    path = Path(file)
    if output is None:
        output = path.with_suffix('.html').name
    click.echo(f"🛠️  {C.PRIMARY}Building {C.BOLD}{path.name}{C.END}...")
    doc_instance = find_doc_instance(file)
    html_content = doc_instance.render(pretty=not minify)
    with open(output, 'w', encoding='utf-8') as f:
        f.write(html_content)
    click.echo(f"✅ {C.SUCCESS}Success! Static file saved to {C.BOLD}{output}{C.END}.")

INIT_TEMPLATE = '''from syqlorix import *

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
    return Syqlorix(
        head(
            title(title_text),
            common_css,
            Comment("Live-reload script is injected automatically by the dev server")
        ),
        body(
            div(
                nav(
                    a("Home", href="/"),
                    a("Dynamic Route", href="/user/Syqlorix"),
                    a("Form Example", href="/message"),
                ),
                content_node,
                class_="container"
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

'''

@main.command()
@click.argument('filename', default='app.py', type=click.Path())
def init(filename):
    if os.path.exists(filename):
        click.echo(f"{C.ERROR}Error: File '{filename}' already exists.{C.END}")
        return
    with open(filename, 'w') as f:
        f.write(INIT_TEMPLATE)
    click.echo(f"🚀 {C.SUCCESS}Created a new Syqlorix project in {C.BOLD}{filename}{C.END}.")
    click.echo(f"   {C.MUTED}To run it, use: {C.PRIMARY}syqlorix run {filename}{C.END}")

if __name__ == '__main__':
    main()