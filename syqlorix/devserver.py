import os
import http.server
import socketserver
import threading
import time
import importlib.util
import mimetypes
from typing import Callable, Dict, Union, Any

from .page import Page

class Route:
    def __init__(self, path: str = "/"):
        if not path.startswith("/"):
            raise ValueError("Route path must start with '/'")
        self.path = path.rstrip("/") if path != "/" else "/"
        self.ROUTES: Dict[str, Union[Callable[..., Any], "Route"]] = {}

    def route(self, path: str = "/"):
        if not path.startswith("/"):
            raise ValueError("Nested route path must start with '/'")
        
        def decorator(func: Callable[..., Any]):
            self.ROUTES[path] = func
            return func
        return decorator

    def subroute(self, route_instance: "Route"):
        if not isinstance(route_instance, Route):
            raise TypeError("subroute must be a Route instance.")
        if not route_instance.path.startswith("/"):
            raise ValueError("Subroute path must start with '/'")
        
        normalized_subpath = route_instance.path.rstrip("/") if route_instance.path != "/" else "/"
        self.ROUTES[normalized_subpath] = route_instance
        return route_instance
    
    def map_routes(self) -> Dict[str, Union[Page, Callable[[], Page], str]]:
        flat_routes = {}
        base_path = self.path if self.path != "/" else ""

        for sub_path, content_source in self.ROUTES.items():
            full_route_path = f"{base_path}{sub_path}" if sub_path != "/" else base_path
            
            full_route_path = full_route_path.replace("//", "/")
            if not full_route_path: full_route_path = "/"

            if isinstance(content_source, Route):
                sub_mapped_routes = content_source.map_routes()
                for k, v in sub_mapped_routes.items():
                    final_path = f"{base_path}{k}" if k != "/" else base_path
                    final_path = final_path.replace("//", "/")
                    if not final_path: final_path = "/"
                    flat_routes[final_path] = v
            else:
                flat_routes[full_route_path] = content_source
        return flat_routes

class SyqlorixDevServerHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, routes_map=None, project_root_directory=None, **kwargs):
        self.routes_map = routes_map if routes_map is not None else {}
        self.project_root_directory = project_root_directory if project_root_directory is not None else os.getcwd()
        self.static_source_directory = os.path.join(self.project_root_directory, 'static')
        
        super().__init__(*args, **kwargs)

    def do_GET(self):
        path = self.path.split('?')[0]
        if path.endswith('/'):
            path = path[:-1]
        if path == '':
            path = '/'

        if path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return

        if path in self.routes_map:
            page_source = self.routes_map[path]
            try:
                if callable(page_source):
                    page_source = page_source()
                if isinstance(page_source, Page):
                    html_content = page_source.render()
                elif isinstance(page_source, str):
                    html_content = page_source
                else:
                    self.send_error(500, "Invalid page source in route map.")
                    return
            except Exception as e:
                self.send_error(500, f"Error rendering page: {e}")
                self.log_error(f"Error rendering page for path {path}: {e}")
                return

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))
        elif path.startswith('/static/'):
            # Manually serve static files
            requested_file_relative_path = path[len('/static/'):] # e.g., 'css/main.css' from '/static/css/main.css'
            full_static_file_path = os.path.join(self.static_source_directory, requested_file_relative_path)
            
            if os.path.exists(full_static_file_path) and os.path.isfile(full_static_file_path):
                try:
                    self.send_response(200)
                    content_type, _ = mimetypes.guess_type(full_static_file_path)
                    if content_type:
                        self.send_header("Content-type", content_type)
                    else:
                        self.send_header("Content-type", "application/octet-stream")
                    self.end_headers()
                    
                    with open(full_static_file_path, 'rb') as f:
                        self.wfile.write(f.read())
                except Exception as e:
                    self.send_error(500, f"Error serving static file: {e}")
                    self.log_error(f"Error serving static file {path}: {e}")
            else:
                self.send_error(404, "Static file not found")
        else:
            self.send_error(404, "Page not found")


class SyqlorixDevServer(socketserver.TCPServer):
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, routes_map, directory, bind_and_activate=True):
        self.routes_map = routes_map
        self.directory = directory
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, routes_map=self.routes_map, project_root_directory=self.directory)


def start_dev_server(routes_source: Union[Dict[str, Union[Page, Callable[[], Page], str]], Route], bind: str = "localhost", port: int = 8000, project_root: str = None):
    
    if isinstance(routes_source, Route):
        routes_to_serve = routes_source.map_routes()
    elif isinstance(routes_source, Dict):
        routes_to_serve = routes_source
    else:
        raise TypeError("routes_source must be a dictionary of routes or a Route instance.")
        
    if project_root is None:
        try:
            syqlorix_pkg_path = os.path.dirname(importlib.import_module('syqlorix').__file__)
            project_root = os.path.dirname(syqlorix_pkg_path)
        except Exception:
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_script_dir))
        if not os.path.exists(os.path.join(project_root, 'static')):
            project_root = os.path.abspath(os.getcwd())

        original_cwd = os.getcwd()
    else:
        original_cwd = os.getcwd()

    os.chdir(project_root)

    server_instance_holder = {}

    def _start_server():
        with SyqlorixDevServer((bind, port), SyqlorixDevServerHandler, routes_map=routes_to_serve, directory=project_root) as httpd:
            server_instance_holder['httpd'] = httpd
            print(f"Syqlorix Dev Server running at http://{bind}:{port}/")
            print("Available routes:")
            for route_path in routes_to_serve.keys():
                print(f"  - http://{bind}:{port}{route_path}")
            print(f"Serving static files from: {os.path.join(project_root, 'static')}")
            httpd.serve_forever()

    server_thread = threading.Thread(target=_start_server, daemon=True)
    server_thread.start()

    time.sleep(1.0)

    print("\n" + "="*50)
    print(" Your Syqlorix site is ready! ")
    print(" Access it via the Codespaces 'Ports' tab or click a link above.")
    print(f"   Main page: http://{bind}:{port}/")
    print("="*50 + "\n")
    print("Press Enter to close the server and exit...")
    input()

    if 'httpd' in server_instance_holder and server_instance_holder['httpd']:
        print("Shutting down Syqlorix Dev Server...")
        server_instance_holder['httpd'].shutdown()
        server_instance_holder['httpd'].server_close()
    
    server_thread.join(timeout=1)

    if 'original_cwd' in locals():
        os.chdir(original_cwd)
    print("Server closed. Goodbye!")