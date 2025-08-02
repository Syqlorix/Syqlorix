import click
import sys
import os
from pathlib import Path
import importlib.util
from importlib import metadata as importlib_metadata
from jsmin import jsmin
from . import Syqlorix, Node, Request, head, body, redirect

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
import time

# --- Main Application Setup ---
# All routes and handlers will be attached to this 'doc' object.
doc = Syqlorix()

# --- Blueprints (for organizing larger apps) ---
# Create a Blueprint, which is like a mini-app for a section of your site.
main_pages = Blueprint("main", url_prefix="/pages")

# --- Middleware ---
# This function will run BEFORE every single request.
@doc.before_request
def log_request(request):
    print(f"Request received for: {request.path} at {time.time()}")
    # Middleware can add data to the request for later use in routes
    request.start_time = time.time()
    # If middleware returns anything, it stops the request and sends the response.

# --- Custom Error Handlers ---
# Create a custom, branded page for 404 Not Found errors.
@doc.error_handler(404)
def not_found_handler(request):
    # You can reuse your page_layout to keep the branding consistent!
    return page_layout("404 - Not Found", div(
        h1("Oops! Page Not Found."),
        p("The page you're looking for doesn't seem to exist.")
    )), 404

# --- Reusable Components & Layouts ---
common_css = style("""
    body { background-color: #1a1a2e; color: #e0e0e0; font-family: sans-serif; margin: 0; }
    .container { max-width: 700px; margin: 2rem auto; padding: 2rem; border-radius: 8px; background: #2a2a4a; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
    h1 { color: #00a8cc; margin-bottom: 1rem; }
    p { color: #aaa; line-height: 1.6; }
    nav { text-align: center; padding: 1.5rem; background-color: #1e1e3a; }
    nav a { margin: 0 1.5rem; color: #72d5ff; text-decoration: none; font-weight: bold; font-size: 1.1rem; }
    nav a:hover { text-decoration: underline; }
""")

def page_layout(title_text, content_node):
    return Syqlorix(
        head(
            title(title_text),
            common_css
        ),
        body(
            nav(
                a("Home", href="/"),
                a("Page 1", href="/pages/page1"),
                a("Redirect", href="/old")
            ),
            div(content_node, class_="container")
        )
    )

# --- Define Routes on the Main 'doc' object ---
@doc.route('/')
def home_page(request):
    processing_time = (time.time() - request.start_time) * 1000
    return page_layout("Home", div(
        h1("Welcome to Syqlorix!"),
        p("This page demonstrates Middleware, Blueprints, and Error Handlers."),
        p(f"Request processed in: {processing_time:.2f} ms (thanks to middleware!)")
    ))

@doc.route('/old')
def old_page(request):
    return redirect('/') # Test the redirect helper

# --- Define Routes on the Blueprint ---
@main_pages.route('/page1')
def blueprint_page_1(request):
    return page_layout("Page 1", div(
        h1("Blueprint Page 1"),
        p("This route is part of the 'main_pages' blueprint, served under '/pages/page1'.")
    ))

# --- Register Blueprints ---
# Finally, attach all blueprints to the main application.
doc.register_blueprint(main_pages)
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