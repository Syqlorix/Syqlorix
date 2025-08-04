import click
import sys
import os
from pathlib import Path
import importlib.util
from importlib import metadata as importlib_metadata
from jsmin import jsmin
from cssmin import cssmin
from . import *

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
@click.option('--output', '-o', 'output_path_str', default=None, help='Output directory name. Defaults to "dist".')
@click.option('--minify', is_flag=True, default=False, help='Minify HTML, and inline CSS/JS.')
def build(file, output_path_str, minify):

    if not file.endswith('.py'):
        click.echo(f"{C.ERROR}Error: Input file must be a Python script.{C.END}")
        sys.exit(1)

    path = Path(file)
    output_dir_name = output_path_str if output_path_str else 'dist'
    output_path = path.parent / output_dir_name

    click.echo(f"🛠️  {C.PRIMARY}Building static site from {C.BOLD}{path.name}{C.END}...")

    doc_instance = find_doc_instance(file)
    if not doc_instance._routes:
        click.echo(f"{C.WARNING}Warning: No routes found to build.{C.END}")
        return

    os.makedirs(output_path, exist_ok=True)
    click.echo(f"   Writing to {C.BOLD}'{output_path}'{C.END}...")

    for route_regex, methods, handler_func in doc_instance._routes:
        if 'GET' not in methods:
            continue

        route_path = route_regex.pattern.replace('$', '').replace('(?P<', '').replace('>[^/]+)', '')
        if route_path == '/':
            file_name = 'index.html'
        else:
            file_name = route_path.strip('/') + '.html'

        file_dest = output_path / file_name
        os.makedirs(file_dest.parent, exist_ok=True)
        
        class MockRequest:
            method = 'GET'
            path = route_path
            path_full = route_path
            path_params = {}
            query_params = {}
            headers = {}

        try:
            response_data = handler_func(MockRequest())
            if isinstance(response_data, tuple):
                response_data, _ = response_data
            
            html_content = ""
            if isinstance(response_data, Syqlorix):
                html_content = response_data.render(pretty=not minify)
            elif isinstance(response_data, Node):
                temp_syqlorix = Syqlorix(head(), body(response_data))
                html_content = temp_syqlorix.render(pretty=not minify)
            else:
                html_content = str(response_data)

            with open(file_dest, 'w', encoding='utf-8') as f:
                f.write(html_content)
            click.echo(f"   - Built {C.SUCCESS}{route_path}{C.END} -> {C.BOLD}{file_dest.relative_to(path.parent)}{C.END}")

        except Exception as e:
            click.echo(f"   - {C.ERROR}Failed to build {route_path}: {e}{C.END}")

    click.echo(f"✅ {C.SUCCESS}Success! Static site build complete.{C.END}")

INIT_TEMPLATE = '''from syqlorix import *

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
    else:
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
    if not filename.endswith('.py'):
        filename += '.py'

    if os.path.exists(filename):
        click.echo(f"{C.ERROR}Error: File '{filename}' already exists.{C.END}")
        return
    with open(filename, 'w') as f:
        f.write(INIT_TEMPLATE)
    click.echo(f"🚀 {C.SUCCESS}Created a new Syqlorix project in {C.BOLD}{filename}{C.END}.")
    run_command_filename = filename.split(os.sep)[-1]
    click.echo(f"   {C.MUTED}To run it, use: {C.PRIMARY}syqlorix run {run_command_filename}{C.END}")

if __name__ == '__main__':
    main()
