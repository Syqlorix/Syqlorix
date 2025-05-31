import argparse
import os
import shutil
import importlib.util
from typing import Callable, Dict, Union

from .page import Page
from .devserver import serve_pages_dev

def _find_project_root_from_path(start_path):
    current_dir = os.path.abspath(start_path)
    while current_dir != os.path.dirname(current_dir):
        if os.path.exists(os.path.join(current_dir, 'pyproject.toml')) or \
           os.path.exists(os.path.join(current_dir, '.git')): 
            return current_dir
        current_dir = os.path.dirname(current_dir)
    return os.path.abspath(start_path) 

PROJECT_ROOT = _find_project_root_from_path(os.getcwd())

def build_static_site(routes_file: str, output_dir: str):
    spec = importlib.util.spec_from_file_location("routes_module", routes_file)
    routes_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(routes_module)

    if not hasattr(routes_module, 'routes'):
        raise ValueError(f"Routes file '{routes_file}' must contain a 'routes' dictionary.")
    
    routes = routes_module.routes

    os.makedirs(output_dir, exist_ok=True)

    print(f"Building static site to: {os.path.abspath(output_dir)}")
    for path, page_source in routes.items():
        if path == '/':
            output_filepath = os.path.join(output_dir, "index.html")
        else:
            page_dir = os.path.join(output_dir, path.strip('/'))
            os.makedirs(page_dir, exist_ok=True)
            output_filepath = os.path.join(page_dir, "index.html")

        if isinstance(page_source, Page):
            html_content = page_source.render()
        elif callable(page_source):
            html_content = page_source().render()
        else:
            print(f"Skipping route {path}: Invalid page source type.")
            continue

        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"  - Generated {os.path.relpath(output_filepath, output_dir)}")
    
    # Use the globally determined PROJECT_ROOT for static asset source
    static_source_dir = os.path.join(PROJECT_ROOT, 'static')
    static_dest_dir = os.path.join(output_dir, 'static')

    if os.path.exists(static_source_dir) and os.path.isdir(static_source_dir):
        print(f"Copying static assets from '{static_source_dir}' to '{static_dest_dir}'")
        if os.path.exists(static_dest_dir):
            shutil.rmtree(static_dest_dir)
        shutil.copytree(static_source_dir, static_dest_dir)
    else:
        print(f"No static directory found at '{static_source_dir}', skipping static asset copy.")
    
    print("Static site build complete.")


def main():
    parser = argparse.ArgumentParser(
        prog="syqlorix",
        description="Syqlorix CLI for building and serving web pages.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    serve_parser = subparsers.add_parser(
        "serve", 
        help="Serve Syqlorix pages locally for development.\n\n"
             "Usage: syqlorix serve <routes_file.py> [--port <port_number>]\n"
             "Example: syqlorix serve examples/multi_page_site.py --port 8000"
    )
    serve_parser.add_argument("routes_file", help="Path to the Python file defining the 'routes' dictionary.")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to serve on.")

    build_parser = subparsers.add_parser(
        "build", 
        help="Build static HTML files from Syqlorix pages.\n\n"
             "Usage: syqlorix build <routes_file.py> [--output <output_directory>]\n"
             "Example: syqlorix build examples/multi_page_site.py -o build_output"
    )
    build_parser.add_argument("routes_file", help="Path to the Python file defining the 'routes' dictionary.")
    build_parser.add_argument("--output", "-o", default="public", help="Output directory for static files.")

    args = parser.parse_args()

    if args.command == "serve":
        spec = importlib.util.spec_from_file_location("routes_module", args.routes_file)
        routes_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(routes_module)

        if not hasattr(routes_module, 'routes'):
            raise ValueError(f"Routes file '{args.routes_file}' must contain a 'routes' dictionary.")
        
        serve_pages_dev(routes_module.routes, args.port, project_root=PROJECT_ROOT)
    elif args.command == "build":
        build_static_site(args.routes_file, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()