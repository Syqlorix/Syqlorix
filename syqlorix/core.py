import sys
import asyncio
import threading
import mimetypes
import re
import json
import fnmatch
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import urllib.parse
import websockets
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import requests
from urllib.parse import urljoin
from jsmin import jsmin
from cssmin import cssmin
from .core import *

from typing import TYPE_CHECKING


class C:
    PRIMARY = '\033[38;5;51m'
    SUCCESS = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    INFO = '\033[94m'
    MUTED = '\033[90m'
    BOLD = '\033[1m'
    END = '\033[0m'

_context_stack = []

LIVE_RELOAD_SCRIPT = """
<script>
    (function() {{
        const socket = new WebSocket("ws://{host}:{port}");
        socket.onmessage = (event) => {{ if (event.data === 'reload') window.location.reload(); }};
        socket.onclose = () => {{ console.log('Syqlorix: Live-reload disconnected. Manual refresh required.'); }};
        socket.onerror = (error) => {{ console.error('Syqlorix: WebSocket error:', error); }};
    }})();
</script>
"""

def _load_access_policy(project_root: Path):
    policy_file = project_root / ".syqlorix"
    whitelist, blacklist = set(), set()
    if policy_file.exists():
        for raw in policy_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("-"):
                blacklist.add(line[1:].strip())
            else:
                whitelist.add(line)
    return whitelist, blacklist

class Plugin:
    def __init__(self):
        self.loaded: bool = False

    def on_node_init(self, node: "Node") -> None:
        pass

    def load(self):
        if self in plugins: plugins.remove(self)
        plugins.append(self)
        self.loaded = True

plugins: list[Plugin] = []

class Node:
    _SELF_CLOSING_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, *children, **attributes):
        self.tag_name = self.__class__.__name__.lower()
        if self.tag_name in ("component", "comment"):
            self.tag_name = ""
        self.attributes = {k.rstrip('_'): v for k, v in attributes.items()}
        self.children = list(children)
        for plugin in plugins:
            plugin.on_node_init(self)

        if _context_stack:
            _context_stack[-1].children.append(self)

    def __truediv__(self, other):
        if isinstance(other, Node):
            self.children.append(other)
        else:
            self.children.append(str(other))
        return self

    def __enter__(self):
        _context_stack.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _context_stack.pop()

    def _format_attrs(self):
        if not self.attributes:
            return ""
        parts = []
        for key, value in self.attributes.items():
            if isinstance(value, bool):
                if value:
                    parts.append(key)
            elif value is not None:
                parts.append(f'{key}={repr(value)}')
        return " " + " ".join(parts)

    def render(self, indent=0, pretty=True):
        pad = "  " * indent if pretty else ""
        attrs = self._format_attrs()
        if not self.tag_name:
            return "".join(c.render(indent, pretty) if isinstance(c, Node) else (f"{pad}{c}\n" if pretty else str(c)) for c in self.children)
        if self.tag_name in self._SELF_CLOSING_TAGS:
            return f"{pad}<{self.tag_name}{attrs}>" + ("\n" if pretty else "")
        nl, inner_pad = ("\n", "  " * (indent + 1)) if pretty else ("", "")
        html = f"{pad}<{self.tag_name}{attrs}>{nl}"
        for child in self.children:
            if isinstance(child, Node):
                html += child.render(indent + 1, pretty)
            else:
                html += f"{inner_pad}{child}{nl}"
        html += f"{pad}</{self.tag_name}>{nl}"
        return html

class Component(Node):
    pass

class Comment(Node):
    def render(self, indent=0, pretty=True):
        pad = "  " * indent if pretty else ""
        content = "".join(str(c) for c in self.children)
        return f"{pad}<!-- {content} -->" + ("\n" if pretty else "")

class head(Node):
    pass

class body(Node):
    pass

class style(Node):
    def __init__(self, css_content, **attributes):
        super().__init__(css_content, **attributes)

    def render(self, indent=0, pretty=True):
        content = str(self.children[0])
        if not pretty and cssmin:
            try:
                content = cssmin(content)
            except Exception as e:
                print(f"{C.WARNING}Could not minify CSS: {e}{C.END}")
        self.children = [content]
        return super().render(indent, pretty)

class script(Node):
    def __init__(self, js_content="", src=None, type="text/javascript", **attributes):
        if src:
            attributes['src'] = src
            super().__init__(**attributes)
        else:
            super().__init__(js_content, **attributes)
        attributes['type'] = type

    def render(self, indent=0, pretty=True):
        if not pretty and not self.attributes.get('src') and jsmin and self.children:
            content = str(self.children[0])
            try:
                content = jsmin(content)
            except Exception as e:
                print(f"{C.WARNING}Could not minify JS: {e}{C.END}")
            self.children = [content]
        return super().render(indent, pretty)

class Request:
    def __init__(self, handler: BaseHTTPRequestHandler):
        self.method = handler.command
        self.path_full = handler.path
        parsed_url = urllib.parse.urlparse(handler.path)
        self.path = parsed_url.path
        self.query_params = {k: v[0] if len(v) == 1 else v for k, v in urllib.parse.parse_qs(parsed_url.query).items()}
        self.headers = dict(handler.headers)
        self.path_params = {}
        self.body = b''
        self.form_data = {}
        self.json_data = {}
        
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            self.body = handler.rfile.read(content_length)
            content_type = self.headers.get('Content-Type', '')
            if 'application/x-www-form-urlencoded' in content_type:
                self.form_data = {k: v[0] if len(v) == 1 else v for k, v in urllib.parse.parse_qs(self.body.decode('utf-8')).items()}
            elif 'application/json' in content_type:
                try:
                    self.json_data = json.loads(self.body.decode('utf-8'))
                except json.JSONDecodeError:
                    print(f"{C.WARNING}Warning: Could not decode JSON body.{C.END}")

class RedirectResponse:
    def __init__(self, location, status_code=302):
        self.location = location
        self.status_code = status_code

def redirect(location, status_code=302):
    return RedirectResponse(location, status_code)

class TestResponse:
    def __init__(self, response_data, status_code, headers):
        self.status_code = status_code
        self.headers = headers
        
        if isinstance(response_data, Syqlorix):
            self.text = response_data.render(pretty=False)
        elif isinstance(response_data, Node):
            self.text = Syqlorix(head(), body(response_data)).render(pretty=False)
        else:
            self.text = str(response_data)

class TestClient:
    def __init__(self, app):
        self.app = app

    def _make_request(self, method, path, form_data=None):
        
        class MockTestRequest:
            def __init__(self, method, path, path_params, form_data):
                self.method = method
                self.path = path
                self.path_full = path
                self.path_params = path_params
                self.form_data = form_data or {}
                self.query_params = {}
                self.headers = {}

        for route_regex, methods, handler_func in self.app._routes:
            match = route_regex.match(path)
            if match:
                if method not in methods:
                    return TestResponse("Method Not Allowed", 405, {})

                path_params = match.groupdict()
                
                import inspect
                sig = inspect.signature(handler_func)
                if len(sig.parameters) > 0:
                    request_obj = MockTestRequest(method, path, path_params, form_data)
                    response_data = handler_func(request_obj)
                else:
                    response_data = handler_func()

                status_code = 200
                headers = {}

                if isinstance(response_data, RedirectResponse):
                    status_code = response_data.status_code
                    headers['Location'] = response_data.location
                elif isinstance(response_data, tuple):
                    response_data, status_code = response_data

                return TestResponse(response_data, status_code, headers)

        if 404 in self.app._error_handlers:
            response_data = self.app._error_handlers[404](None)
            return TestResponse(response_data, 404, {})

        return TestResponse("Not Found", 404, {})

    def get(self, path):
        return self._make_request('GET', path)

    def post(self, path, data=None):
        return self._make_request('POST', path, form_data=data)
     
class Blueprint:
    def __init__(self, name, url_prefix=""):
        self.name = name
        self.url_prefix = url_prefix.rstrip('/')
        self._routes = []

    def route(self, path, methods=['GET']):
        def decorator(handler_func):
            full_path = self.url_prefix + path
            path_regex = re.sub(r'<([^>]+)>', r'(?P<\1>[^/]+)', full_path) + '$'
            self._routes.append((re.compile(path_regex), set(m.upper() for m in methods), handler_func))
            return handler_func
        return decorator
    
    def before_request(self, func):
        self._middleware.append(func)
        return func

    def error_handler(self, code):
        def decorator(func):
            self._error_handlers[code] = func
            return func
        return decorator

    def register_blueprint(self, blueprint):
        self._routes.extend(blueprint._routes)

    def test_client(self):
        return TestClient(self)
    
class RedirectResponse:
    def __init__(self, location, status_code=302):
        self.location = location
        self.status_code = status_code

def redirect(location, status_code=302):
    return RedirectResponse(location, status_code)
    

class Syqlorix(Node):
    def __init__(self, *children, **attributes):
        super().__init__(*children, **attributes)
        self.tag_name = "html"
        self._routes = []
        self._middleware = []
        self._error_handlers = {}
        self._dev_proxies = {}
        self._live_reload_ws_port = None
        self._live_reload_host = "127.0.0.1"
        self._live_reload_enabled = True

    def route(self, path, methods=['GET']):
        def decorator(handler_func):
            path_regex = re.sub(r'<([^>]+)>', r'(?P<\1>[^/]+)', path) + '$'
            self._routes.append((re.compile(path_regex), set(m.upper() for m in methods), handler_func))
            return handler_func
        return decorator
    
    def register_blueprint(self, blueprint):
        self._routes.extend(blueprint._routes)

    def test_client(self):
        return TestClient(self)
    
    def before_request(self, func):
        self._middleware.append(func)
        return func

    def error_handler(self, code):
        def decorator(func):
            self._error_handlers[code] = func
            return func
        return decorator

    def register_blueprint(self, blueprint):
        self._routes.extend(blueprint._routes)

    def test_client(self):
        return TestClient(self)
    
    def proxy(self, path_prefix, target_url):
        """Define a development proxy rule for syqlorix run server."""
        self._dev_proxies[path_prefix] = target_url.rstrip('/')
        return self

    def render(self, pretty=True, live_reload_port=None, live_reload_host=None):
        html_string = "<!DOCTYPE html>\n" + super().render(indent=0, pretty=pretty)
        if live_reload_port and pretty:
            script_tag = LIVE_RELOAD_SCRIPT.format(host=live_reload_host, port=live_reload_port)
            html_string = html_string.replace("</body>", f"{script_tag}</body>")
        return html_string

    def _live_reload_manager(self, host, ws_port, watch_dirs, file_path):
        try:
            asyncio.run(self._async_live_reload(host, ws_port, watch_dirs, file_path))
        except KeyboardInterrupt:
            pass

    async def _async_live_reload(self, host, ws_port, watch_dirs, file_path):
        active_sockets = set()

        async def send_reload_to_all():
            if active_sockets:
                await asyncio.gather(*[ws.send("reload") for ws in active_sockets])

        stop_event = asyncio.Event()

        async def websocket_handler(websocket):
            active_sockets.add(websocket)
            try:
                await websocket.wait_closed()
            finally:
                active_sockets.remove(websocket)

        class ChangeHandler(FileSystemEventHandler):
            def __init__(self, loop, sockets, file_path):
                self.loop = loop
                self.sockets = sockets
                self.file_path = file_path

            def on_modified(self, event):
                if not event.is_directory:
                    file_path = Path(event.src_path)
                    if str(file_path) == str(self.file_path):
                        print(f"✨ {C.WARNING}Main app file changed ({event.src_path}). Reloading...{C.END}")
                        
                        # Signal reload
                        asyncio.run_coroutine_threadsafe(send_reload_to_all(), self.loop)

        server = await websockets.serve(websocket_handler, host, ws_port)
        print(f"🛰️  {C.INFO}Syqlorix Live-Reload server listening on {C.BOLD}ws://{host}:{ws_port}{C.END}")

        loop = asyncio.get_running_loop()

        observer = Observer()
        for watch_dir in watch_dirs:
            observer.schedule(ChangeHandler(loop, active_sockets, file_path), path=str(watch_dir), recursive=True)
            print(f"👀 {C.INFO}Watching for changes in {C.BOLD}'{watch_dir}' (recursively){C.END}")
        observer.start()

        try:
            await stop_event.wait()
        finally:
            observer.stop()
            observer.join()
            server.close()
            await server.wait_closed()

    def run(self, file_path, host="127.0.0.1", port=8000, live_reload=True, max_port_attempts=10):
        current_port = port
        http_server = None

        print(f"🔥 {C.PRIMARY}Starting server for {C.BOLD}{Path(file_path).name}{C.END}...")

        project_root = Path(file_path).parent.resolve()

        whitelist, blacklist = _load_access_policy(project_root)
        def _is_static_allowed(file_path: Path) -> bool:
            rel = file_path.relative_to(project_root).as_posix()
            for pat in blacklist:
                if fnmatch.fnmatch(rel, pat):
                    return False
            if whitelist:
                return any(fnmatch.fnmatch(rel, pat) for pat in whitelist)
            return file_path.suffix.lower() in {
                '.html','.css','.js','.svg','.png','.jpg','.jpeg',
                '.gif','.ico','.woff','.woff2','.json','.pdf'
            }

        watch_dirs = [project_root]

        # Load the app initially to discover routes
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(Path(file_path).stem, str(file_path))
            module = importlib.util.module_from_spec(spec)
            sys.path.insert(0, str(Path(file_path).parent))
            spec.loader.exec_module(module)
            sys.path.pop(0)
            
            if hasattr(module, 'doc') and isinstance(module.doc, Syqlorix):
                app_instance = module.doc
            else:
                app_instance = None
        except Exception as e:
            print(f"{C.ERROR}Error loading app: {e}{C.END}")
            app_instance = None

        for attempt in range(max_port_attempts):
            try:
                class SyqlorixRequestHandler(BaseHTTPRequestHandler):
                    _app_instance = None

                    def __init__(self, *args, **kwargs):
                        self._load_app(file_path)
                        super().__init__(*args, **kwargs)

                    def _load_app(self, file_path):
                        """Load/reload the app module"""
                        try:
                            import importlib.util
                            import sys
                            
                            spec = importlib.util.spec_from_file_location(Path(file_path).stem, str(file_path))
                            module = importlib.util.module_from_spec(spec)
                            sys.path.insert(0, str(Path(file_path).parent))
                            spec.loader.exec_module(module)
                            sys.path.pop(0)
                            
                            if hasattr(module, 'doc') and isinstance(module.doc, Syqlorix):
                                self._app_instance = module.doc
                        except Exception as e:
                            print(f"{C.ERROR}Error loading app: {e}{C.END}")

                    def _send_syqlorix_404(self, path):
                        error_page = Syqlorix(
                            head(
                                title("404 Not Found"),
                                style("""
                                    body { background-color: #1a1a2e; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; display: grid; place-content: center; height: 100vh; margin: 0; text-align: center; }
                                    .container { padding: 2rem 4rem; border-radius: 8px; background: #2a2a4a; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
                                    h1 { color: #ff5370; font-size: 5rem; margin: 0; }
                                    h2 { color: #00a8cc; margin-bottom: 1rem; }
                                    p { color: #aaa; margin-top: 0.5rem; }
                                    code { background-color: #333; padding: 0.2rem 0.4rem; border-radius: 4px; color: #ffcb6b; }
                                    a { color: #72d5ff; font-weight: bold; text-decoration: none; }
                                    a:hover { text-decoration: underline; }
                                """)
                            ),
                            body(
                                div(
                                    h1("404"),
                                    h2("Page Not Found"),
                                    p("The requested path ", code(path), " was not found on this server."),
                                    p(a("Return to Homepage", href="/")),
                                    class_="container"
                                )
                            )
                        )
                        error_html = error_page.render(pretty=True).encode('utf-8')
                        self.send_response(404)
                        self.send_header("Content-type", "text/html")
                        self.send_header("Content-length", str(len(error_html)))
                        self.end_headers()
                        self.wfile.write(error_html)

                    def _handle_request(self, is_head=False):
                        try:
                            request = Request(self)
                            
                            if request.path == '/favicon.ico':
                                self.send_response(204)
                                self.end_headers()
                                return

                            # Check for dev proxy rules (only in development)
                            for prefix, target_url in self._app_instance._dev_proxies.items():
                                if request.path.startswith(prefix):
                                    proxy_url = urljoin(target_url + '/', request.path[len(prefix):].lstrip('/'))
                                    try:
                                        # Forward the request
                                        headers = dict(request.headers)
                                        headers.pop('Host', None)  # Remove original Host header
                                        
                                        response = requests.request(
                                            method=request.method,
                                            url=proxy_url,
                                            headers=headers,
                                            params=request.query_params,
                                            data=request.body if request.body else None,
                                            allow_redirects=False,
                                            stream=True
                                        )
                                        
                                        # Send response back to client
                                        self.send_response(response.status_code)
                                        
                                        # Add CORS header for local development
                                        self.send_header('Access-Control-Allow-Origin', '*')
                                        
                                        # Forward headers from target
                                        for key, value in response.headers.items():
                                            if key.lower() not in ['content-encoding', 'transfer-encoding', 'connection']:
                                                self.send_header(key, value)
                                        
                                        # Handle content length
                                        content = response.content
                                        self.send_header('Content-length', str(len(content)))
                                        self.end_headers()
                                        
                                        # Send response body
                                        self.wfile.write(content)
                                        return
                                        
                                    except Exception as e:
                                        print(f"{C.ERROR}Proxy error: {e}{C.END}")
                                        self.send_error(502, f"Bad Gateway: {e}")
                                        return

                            for route_regex, methods, handler_func in self._app_instance._routes:
                                match = route_regex.match(request.path)
                                if match:
                                    if request.method not in methods:
                                        if 405 in self._app_instance._error_handlers:
                                            self.send_response(405)
                                            self.send_header("Content-type", "text/html")
                                            self.end_headers()
                                            self.wfile.write(b"405 - Method Not Allowed")
                                        else:
                                            self.send_error(405, "Method Not Allowed")
                                        return
                                    request.path_params = match.groupdict()
                                    
                                    response_data = handler_func(request)
                                    if isinstance(response_data, tuple) and len(response_data) == 2:
                                        response_data, status_code = response_data
                                    else:
                                        status_code = 200

                                    content_type = "text/html"
                                    if isinstance(response_data, (dict, list)):
                                        content_type = "application/json"
                                        html_bytes = json.dumps(response_data, indent=2).encode("utf-8")
                                    elif isinstance(response_data, Syqlorix):
                                        html_bytes = response_data.render(pretty=True, live_reload_port=self._app_instance._live_reload_ws_port, live_reload_host=self._app_instance._live_reload_host).encode("utf-8")
                                    elif isinstance(response_data, Node):
                                        temp_syqlorix = Syqlorix(head(), body(response_data))
                                        html_bytes = temp_syqlorix.render(pretty=True, live_reload_port=self._app_instance._live_reload_ws_port, live_reload_host=self._app_instance._live_reload_host).encode("utf-8")
                                    else:
                                        html_bytes = str(response_data).encode("utf-8")
                                    
                                    self.send_response(status_code)
                                    self.send_header("Content-type", content_type)
                                    self.send_header("Content-length", str(len(html_bytes)))
                                    self.end_headers()
                                    self.wfile.write(html_bytes)
                                    return

                            # Check for static files
                            file_name = 'index.html' if request.path == '/' else request.path.lstrip('/')
                            static_file_path = (project_root / file_name).resolve()
                            if (
                                static_file_path.is_file()
                                and static_file_path.is_relative_to(project_root)
                                and _is_static_allowed(static_file_path)
                            ):
                                self.send_response(200)
                                mime_type, _ = mimetypes.guess_type(static_file_path)
                                self.send_header('Content-type', mime_type or 'application/octet-stream')
                                if not is_head:
                                    self.send_header("Content-length", str(static_file_path.stat().st_size))
                                self.end_headers()
                                if not is_head:
                                    with open(static_file_path, 'rb') as f:
                                        self.wfile.write(f.read())
                                return
                            
                            # Custom 404 page
                            self._send_syqlorix_404(request.path)

                        except Exception as e:
                            print(f"{C.ERROR}Error in user code: {e}{C.END}", file=sys.stderr)
                            self.send_error(500, f"Internal Server Error: {e}")

                    def do_GET(self): self._handle_request()
                    def do_POST(self): self._handle_request()
                    def do_PUT(self): self._handle_request()
                    def do_DELETE(self): self._handle_request()
                    def do_HEAD(self): self._handle_request(is_head=True)

                    def log_message(self, format, *args):
                        status_code = str(args[1])
                        color = C.WARNING
                        if status_code.startswith('2') or status_code == '304': color = C.SUCCESS
                        elif status_code.startswith('4') or status_code.startswith('5'): color = C.ERROR
                        print(f"↳  {C.MUTED}HTTP {self.command} {self.path} - {color}{status_code}{C.END}")

                http_server = HTTPServer((host, current_port), SyqlorixRequestHandler)
                break 
            except OSError as e:
                if e.errno == 98:
                    if attempt < max_port_attempts - 1:
                        print(f"{C.WARNING}Port {current_port} already in use. Trying {current_port + 2}...{C.END}")
                        current_port += 2
                    else:
                        print(f"\n{C.ERROR}ERROR: All attempts ({max_port_attempts}) to find an available port failed.{C.END}", file=sys.stderr)
                        sys.exit(1)
                else:
                    raise

        self._live_reload_ws_port = current_port + 1
        self._live_reload_enabled = live_reload
        self._live_reload_host = host

        # Show route discovery
        if app_instance and app_instance._routes:
            route_paths = [path for regex, methods, func in app_instance._routes for path in regex.pattern.split('$')[0:1]]
            print(f"🌍 {C.INFO}Routes discovered: {', '.join(sorted(route_paths))}{C.END}")
        else:
            print(f"ℹ️  {C.INFO}No routes defined. Serving default content for all requests.{C.END}")

        http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
        http_thread.start()
        print(f"🚀 {C.SUCCESS}Syqlorix server running on {C.BOLD}http://{host}:{current_port}{C.END}")

        if live_reload:
            reload_thread = threading.Thread(target=self._live_reload_manager, args=(host, self._live_reload_ws_port, watch_dirs, file_path), daemon=True)
            reload_thread.start()
        
        print(f"   {C.MUTED}Press Ctrl+C to stop.{C.END}")
        
        try:
            http_thread.join()
        except KeyboardInterrupt:
            print(f"\n🛑 {C.WARNING}Shutting down...{C.END}")
        finally:
            http_server.shutdown()
            http_server.server_close()
            print(f"   {C.SUCCESS}Server stopped.{C.END}")

_TAG_NAMES = [
    'a', 'abbr', 'address', 'article', 'aside', 'audio', 'b', 'bdi', 'bdo', 'blockquote', 'button', 'canvas', 
    'caption', 'cite', 'code', 'data', 'datalist', 'dd', 'details', 'dfn', 'dialog', 'div', 'dl', 'dt', 'em', 
    'fieldset', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'i', 
    'iframe', 'img', 'input', 'ins', 'kbd', 'label', 'legend', 'li', 'link', 'main', 'map', 'mark', 'meta', 'meter', 
    'nav', 'noscript', 'object', 'ol', 'optgroup', 'option', 'output', 'p', 'picture', 'pre', 'progress', 'q', 
    'rp', 'rt', 'ruby', 's', 'samp', 'section', 'select', 'small', 'source', 'span', 'strong', 'summary', 
    'sup', 'table', 'tbody', 'td', 'template', 'textarea', 'tfoot', 'th', 'thead', 'time', 'title', 'tr', 'u', 
    'ul', 'var', 'video', 'br', 'hr'
]

for tag in _TAG_NAMES:
    if tag not in ['style', 'script', 'head', 'body']:
        globals()[tag] = type(tag, (Node,), {})

input_ = globals()['input']

doc = Syqlorix()

# I only use this when I want to add some customs that are requested      
__all__ = [
    'Node', 'Syqlorix', 'Component', 'Comment', 'Request', 'Blueprint', 'redirect',
    'head', 'body', 'style', 'script',
    'doc',
    'input_',
    'a', 'abbr', 'address', 'article', 'aside', 'audio', 'b', 'bdi', 'bdo', 'blockquote', 'button', 'canvas', 
    'caption', 'cite', 'code', 'data', 'datalist', 'dd', 'details', 'dfn', 'dialog', 'div', 'dl', 'dt', 'em', 
    'fieldset', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'i', 
    'iframe', 'img', 'input', 'ins', 'kbd', 'label', 'legend', 'li', 'link', 'main', 'map', 'mark', 'meta', 'meter', 
    'nav', 'noscript', 'object', 'ol', 'optgroup', 'option', 'output', 'p', 'picture', 'pre', 'progress', 'q', 
    'rp', 'rt', 'ruby', 's', 'samp', 'section', 'select', 'small', 'source', 'span', 'strong', 'summary', 
    'sup', 'table', 'tbody', 'td', 'template', 'textarea', 'tfoot', 'th', 'thead', 'time', 'title', 'tr', 'u', 
    'ul', 'var', 'video', 'br', 'hr', 'plugins', 'Plugin'
]

__all__.extend(_TAG_NAMES)