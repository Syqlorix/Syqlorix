import os
import http.server
import socketserver
import threading
import time
import importlib.util
from typing import Callable, Dict, Union

from .page import Page

class SyqlorixDevServerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        server_instance = args[2]
        
        self.routes_map = server_instance.routes_map
        self.project_root_directory = server_instance.directory 
        self.static_source_directory = os.path.join(self.project_root_directory, 'static')
        
        super().__init__(*args, directory=self.project_root_directory, **kwargs) 

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
            requested_static_file_path = os.path.join(self.static_source_directory, path[len('/static/'):])
                       
            original_path = self.path 
            self.path = os.path.relpath(requested_static_file_path, self.project_root_directory) # Path relative to project root
            
            try:
                if os.path.exists(requested_static_file_path) and os.path.isfile(requested_static_file_path):
                    super().do_GET() 
                else:
                    self.send_error(404, "Static file not found")
            except Exception:
                self.send_error(404, "Static file not found")
            finally:
                self.path = original_path 
        else:
            self.send_error(404, "Page not found")


class SyqlorixDevServer(socketserver.TCPServer):
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, routes_map, directory, bind_and_activate=True):
        self.routes_map = routes_map
        self.directory = directory
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)

class Route:
  def __init__(self, path: str = "/"):
    self.path = path
    self.ROUTES = {}
  
  def route(self, path: str = "/"):
    assert path.startswith("/"), ValueError("Path must start with '/'")
    def decorator(func):
      self.ROUTES[path] = func
      return func
      
    return decorator
    
  def map_routes(self):
    resp = {}
    path = self.path.rstrip("/")
    for p, c in self.ROUTES.items():
      if isinstance(c, Route):
        resp.update(c.map_routes())
      else:
        resp[path+p.rstrip("/")] = c
      
    return resp
    
  def subroute(self, path: Union[str, "Route"]):
    route=path if isinstance(path, Route) else self.__class__(path)
    self.ROUTES[route.path] = route
    return route
    
  def serve(self, bind: str = "localhost", port: int = 8000, project_root: str = None):
    return serve_pages_dev(self.map_routes(), bind, port, project_root)

def serve_pages_dev(routes: Dict[str, Union[Page, Callable[[], Page]]], bind: str = "localhost", port: int = 8000, project_root: str = None):
    route, routes = routes, {}
    for p, c in route.items():
      if isinstance(c, Route):
        routes.update(c.map_routes())
      else: routes[p] = c
        
    if project_root is None:
        original_cwd = os.getcwd()
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_script_dir)) 
    else:
        original_cwd = os.getcwd()

    os.chdir(project_root)

    server_instance_holder = {}

    def _start_server():
        with SyqlorixDevServer((bind, port), SyqlorixDevServerHandler, routes_map=routes, directory=project_root) as httpd:
            server_instance_holder['httpd'] = httpd
            print(f"Syqlorix Dev Server running at http://{bind}:{port}/")
            print("Available routes:")
            for route_path in routes.keys():
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
