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
        click.echo(f"{C.ERROR}Error loading '{file_path}':\n" + str(e) + C.END)
        sys.exit(1)

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(version=PACKAGE_VERSION, prog_name="syqlorix")
@click.option('--debug/--no-debug', default=False, help='Enable debug output.')
@click.pass_context
def main(ctx, debug):
    ctx.obj = {'DEBUG': debug}

@main.command()
@click.argument('file', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--host', '-H', default='127.0.0.1', help='The interface to bind to.')
@click.option('--port', '-p', default=8000, type=int, help='The port to start searching from.')
@click.option('--no-reload', is_flag=True, default=False, help='Disable live-reloading.')
@click.pass_context
def run(ctx, file, host, port, no_reload):
    if ctx.obj.get('DEBUG'):
        click.echo(f"{C.MUTED}Debug mode is on. Loading file: {file}{C.END}")
    click.echo(SYQLORIX_BANNER)
    doc_instance = find_doc_instance(file)
    if ctx.obj.get('DEBUG'):
        click.echo(f"{C.MUTED}Found doc instance: {doc_instance}{C.END}")
        click.echo(f"{C.MUTED}Starting server with options: host={host}, port={port}, live_reload={not no_reload}{C.END}")
    doc_instance.run(file_path=file, host=host, port=port, live_reload=not no_reload)

@main.command()
@click.argument('file', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--output', '-o', 'output_path_str', default='dist', help='Output directory name.')
@click.pass_context
def build(ctx, file, output_path_str):
    """Build a static version of the Syqlorix application."""
    import shutil
    from .core import _load_app_from_file

    if ctx.obj.get('DEBUG'):
        click.echo(f"{C.MUTED}Debug mode is on. Starting build for: {file}{C.END}")

    click.echo(SYQLORIX_BANNER)
    click.echo(f"🔥 {C.PRIMARY}Starting static build for {C.BOLD}{Path(file).name}{C.END}...")

    app_instance = _load_app_from_file(file)
    if not app_instance:
        click.echo(f"❌ {C.ERROR}Build failed: Could not load Syqlorix instance.{C.END}", err=True)
        sys.exit(1)
        
    if ctx.obj.get('DEBUG'):
        click.echo(f"{C.MUTED}Found app instance: {app_instance}{C.END}")

    output_path = Path(output_path_str).resolve()
    project_root = Path(file).parent.resolve()
    
    if ctx.obj.get('DEBUG'):
        click.echo(f"{C.MUTED}Output path resolved to: {output_path}{C.END}")
        click.echo(f"{C.MUTED}Project root resolved to: {project_root}{C.END}")

    # Clean and create output directory
    if output_path.exists():
        if ctx.obj.get('DEBUG'):
            click.echo(f"{C.MUTED}Output path exists. Removing: {output_path}{C.END}")
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build the app routes
    app_instance.build(output_path)

    # Copy static assets
    click.echo(f"📂 {C.INFO}Copying static assets...{C.END}")
    static_extensions = {'.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2'}
    ignore_dirs = {'.git', 'venv', '__pycache__', output_path.name, '.pytest_cache'}

    for path in project_root.rglob('*'):
        is_in_ignored_dir = any(d in path.parts for d in ignore_dirs)
        if is_in_ignored_dir:
            continue
        
        if path.is_file() and path.suffix in static_extensions:
            dest_path = output_path / path.relative_to(project_root)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest_path)
            click.echo(f"   -> Copied {C.BOLD}{path.relative_to(project_root)}{C.END}")

    click.echo(f"✅ {C.SUCCESS}Build successful! Files are in '{output_path}'.{C.END}")

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

doc = Syqlorix()

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

# This block allows you to run the app directly with `python <filename>.py`
if __name__ == "__main__":
    # __file__ is the path to the current script
    # This starts the server with live-reloading enabled by default
    doc.run(file_path=__file__)

'''

@main.command()
@click.argument('path', default='.', type=click.Path(resolve_path=False)) # Don't resolve path immediately
def init(path):
    input_path = Path(path)
    
    if str(path).endswith(os.sep) or (input_path.exists() and input_path.is_dir()):
        # User explicitly provided a directory or an existing directory without trailing slash
        output_dir = input_path
        output_file = output_dir / 'app.py'
    else: # User provided a file path or a non-existent path that is not a directory
        output_file = input_path
        if not output_file.name.endswith('.py'):
            output_file = output_file.with_suffix('.py')
        output_dir = output_file.parent

    # Ensure parent directories exist
    output_dir.mkdir(parents=True, exist_ok=True)

    if output_file.exists():
        click.echo(f"{C.ERROR}Error: File '{output_file}' already exists.{C.END}")
        return
    
    with open(output_file, 'w') as f:
        f.write(INIT_TEMPLATE)
    click.echo(f"🚀 {C.SUCCESS}Created a new Syqlorix project in {C.BOLD}{output_file}{C.END}.")
    
    try:
        # Get path relative to current working directory
        run_command_suggestion = output_file.relative_to(Path.cwd()).as_posix()
    except ValueError:
        # If not relative (e.g., different drive or parent), use the full path
        run_command_suggestion = output_file.as_posix()

    click.echo(f"   {C.MUTED}To run it, use: {C.PRIMARY}syqlorix run {run_command_suggestion}{C.END}")

if __name__ == '__main__':
    main()
