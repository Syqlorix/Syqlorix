import re
import sys
import json
import asyncio
import fnmatch
import requests
import mimetypes
import threading
import websockets
import secrets
import shutil
import traceback
import urllib.parse
import starlark
import socket

# Thrift imports
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from .thrift_gen.syqlorix.thrift import SyqlorixService
from .thrift_gen.syqlorix.thrift.ttypes import ThriftRequest, ThriftResponse

from jsmin import jsmin
from cssmin import cssmin
from typing import List
from pathlib import Path

from urllib.parse import urljoin
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from http.server import HTTPServer, BaseHTTPRequestHandler

from .core import *


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

LIVE_RELOAD_SCRIPT = """<script>
    (function() {
        const httpPort = {http_port};
        const wsPort = {ws_port};
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const hostname = window.location.hostname;

        let wsUrl;
        if (hostname.includes(httpPort)) {
            const wsHost = hostname.replace(httpPort, wsPort);
            wsUrl = `${{protocol}}://${{wsHost}}`;
        } else {
            wsUrl = `${{protocol}}://${{hostname}}:${{wsPort}}`;
        }

        const socket = new WebSocket(wsUrl);
        
        socket.onmessage = (event) => {{ if (event.data === 'reload') window.location.reload(); }};
        socket.onclose = () => {{ console.log('Syqlorix: Live-reload disconnected.'); }};
        socket.onerror = (error) => {{ console.error('Syqlorix: WebSocket error:', error); }};
    })();
</script>"""

def _create_websocket_error_page():
    import base64
    from pathlib import Path

    logo_data_uri = ""
    try:
        logo_path = Path(__file__).parent.parent / "syqlorix-logo.svg"
        with open(logo_path, "rb") as f:
            logo_svg_bytes = f.read()
        logo_b64 = base64.b64encode(logo_svg_bytes).decode("utf-8")
        logo_data_uri = f"data:image/svg+xml;base64,{{logo_b64}}"
    except FileNotFoundError:
        pass  # Logo is optional

    css = """
    body {
        background-color: #1a1a2e;
        color: #e0e0e0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        display: grid;
        place-content: center;
        height: 100vh;
        margin: 0;
        padding: 2rem;
    }
    .container {
        max-width: 800px;
        margin: auto;
        background-color: #16213e;
        padding: 2rem 4rem;
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(0,0,0,0.5);
        text-align: center;
    }
    .logo {
        max-width: 100px;
        margin-bottom: 1rem;
    }
    h1 {
        color: #00a8cc;
        text-shadow: 0 0 5px #00a8cc;
        font-size: 3rem;
        margin-top: 0;
    }
    h2 {
        color: #ff5370;
        margin-bottom: 1rem;
    }
    p {
        color: #aaa;
        margin-top: 0.5rem;
        max-width: 500px;
    }
    """
    return Syqlorix(
        head(
            title("426 - Upgrade Required"),
            meta(charset="UTF-8"),
            style(css)
        ),
        body(
            div(
                img(src_=logo_data_uri, alt="Syqlorix Logo", class_="logo"),
                h1("Upgrade Required"),
                h2("This Port is for WebSockets Only"),
                p("You have tried to access a port that is used for the live-reload WebSocket connection. This port does not serve standard web pages."),
                p("Please use the main application URL provided when the server started."),
                class_="container"
            )
        )
    )


def _load_app_from_file(file_path):
    try:
        import importlib.util
        import sys
        import syqlorix

        # Clear cached user modules before reloading, excluding the framework itself
        project_root = str(Path(file_path).parent.resolve())
        modules_to_remove = [
            name for name, mod in sys.modules.items()
            if hasattr(mod, '__file__') and mod.__file__ 
            and mod.__file__.startswith(project_root) 
            and 'syqlorix' not in name
        ]
        for name in modules_to_remove:
            del sys.modules[name]

        syqlorix.doc = syqlorix.Syqlorix()
        spec = importlib.util.spec_from_file_location(Path(file_path).stem, str(file_path))
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(Path(file_path).parent))
        spec.loader.exec_module(module)
        sys.path.pop(0)
        
        app_instance = None
        for obj in module.__dict__.values():
            if isinstance(obj, syqlorix.Syqlorix):
                app_instance = obj
                break
        return app_instance
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_frames = traceback.extract_tb(exc_traceback)
        
        user_code_traceback = []
        for frame in tb_frames:
            if 'syqlorix/' not in frame.filename and '<frozen importlib' not in frame.filename:
                user_code_traceback.append(frame)

        terminal_width = shutil.get_terminal_size().columns
        title = f" Application Error ".center(terminal_width, "═")
        print(f"{C.ERROR}{title}{C.END}")

        if user_code_traceback:
            print("Traceback (most recent call last):")
            for frame in traceback.format_list(user_code_traceback):
                print(frame, end="")
        
        for line in traceback.format_exception_only(exc_type, exc_value):
            print(line, end="")

        print(f"{C.ERROR}{'═' * terminal_width}{C.END}\n")
        return None

def _load_access_policy(project_root: Path):
    policy_file = project_root / ".syqlorix"
    whitelist, blacklist = set(), set()
    if policy_file.exists():
        for raw in policy_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            
            is_blacklist = line.startswith("-")
            pattern = line[1:].strip() if is_blacklist else line
            
            if pattern.endswith('/'):
                pattern += '*'
            
            if is_blacklist:
                blacklist.add(pattern)
            else:
                whitelist.add(pattern)
    return whitelist, blacklist

def _create_generic_error_page():
    return Syqlorix(
        head(
            title("500 - Server Error"),
            meta(charset="UTF-8"),
            style("body { background-color: #1a1a2e; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; display: grid; place-content: center; height: 100vh; margin: 0; text-align: center; } .container { padding: 2rem 4rem; border-radius: 8px; background: #2a2a4a; box-shadow: 0 4px 12px rgba(0,0,0,0.3); } h1 { color: #ff5370; font-size: 5rem; margin: 0; } h2 { color: #00a8cc; margin-bottom: 1rem; } p { color: #aaa; margin-top: 0.5rem; } a { color: #72d5ff; font-weight: bold; text-decoration: none; } a:hover { text-decoration: underline; }")
        ),
        body(
            div(
                h1("500"),
                h2("Internal Server Error"),
                p("Something went wrong on our end. Please try again later."),
                p(a("Return to Homepage", href="/")),
                class_="container"
            )
        )
    )

class Plugin:
    def __init__(self):
        self.loaded: bool = False

    def on_node_init(self, node: "Node") -> None:
        pass

    def load(self):
        if self in plugins: plugins.remove(self)
        plugins.append(self)
        self.loaded = True

plugins: List[Plugin] = []

class Safe(str):
    """A string subclass that indicates the content is safe for raw rendering."""
    pass

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
                # Escape attribute values as well
                try:
                    from . import syqlorix_rust
                    escaped_val = syqlorix_rust.escape_html(str(value))
                except Exception:
                    escaped_val = str(value).replace('<', '&lt;').replace('>', '&gt;')
                parts.append(f'{key}={repr(escaped_val)}')
        return " " + " ".join(parts)

    def render(self, indent=0, pretty=True):
        from .templating import NodeWrapper
        
        pad = "  " * indent if pretty else ""
        attrs = self._format_attrs()
        if not self.tag_name:
            return "".join(c.render(indent, pretty) if isinstance(c, Node) else (f"{pad}{c}\n" if pretty else str(c)) for c in self.children)
        if self.tag_name in self._SELF_CLOSING_TAGS:
            return f"{pad}<{self.tag_name}{attrs}>" + ("\n" if pretty else "")
        nl, inner_pad = ("\n", "  " * (indent + 1)) if pretty else ("", "")
        html = f"{pad}<{self.tag_name}{attrs}>{nl}"
        for child in self.children:
            if isinstance(child, NodeWrapper):
                child = child()
            if isinstance(child, Node):
                html += child.render(indent + 1, pretty)
            else:
                if not isinstance(child, Safe):
                    try:
                        from . import syqlorix_rust
                        child = syqlorix_rust.escape_html(str(child))
                    except Exception:
                        child = str(child).replace('<', '&lt;').replace('>', '&gt;')
                
                html += f"{inner_pad}{child}{nl}"
        html += f"{pad}</{self.tag_name}>{nl}"
        return html

class Component(Node):
    def __init__(self, *children, **props):
        super().__init__()
        self.tag_name = ""
        self.props = props
        self.children = list(children)
        try:
            from . import syqlorix_rust
            scope_id = syqlorix_rust.generate_scope_id()
        except Exception:
            scope_id = secrets.token_hex(4)
        self.scope_attr = f"data-syq-{scope_id}"
        self.state = {}

    def set_state(self, new_state):
        self.state.update(new_state)

    def before_render(self):
        pass

    def after_render(self, node):
        pass

    def render(self, indent=0, pretty=True):
        self.before_render()
        node = self.create(children=self.children)
        self.after_render(node)
        
        if isinstance(node, Node):
            # Add the scope attribute to the root node of the component
            if not hasattr(node, 'scope_attr'):
                node.attributes[self.scope_attr] = ""
            return node.render(indent, pretty)
        elif node is not None:
            return str(node)
        return ""

    def create(self, children=None):
        raise NotImplementedError(
            f"Component '{self.__class__.__name__}' does not implement the create method."
        )

class StarlarkComponent(Component):
    def __init__(self, script_content=None, script_path=None, **props):
        super().__init__(**props)
        self.script_content = script_content
        if script_path:
            self.script_content = Path(script_path).read_text()
        
    def create(self, children=None):
        if not self.script_content:
            return ""
        
        def create_tag(name, *children, **attrs):
            tag_class = globals().get(name)
            if not tag_class:
                # Fallback to generic Node if tag not found
                res = Node(*children, **attrs)
            else:
                res = tag_class(*children, **attrs)
            return starlark.OpaquePythonObject(res)

        ast = starlark.parse("component.star", self.script_content)
        module = starlark.Module()
        globals_ = starlark.Globals.standard()
        
        # Expose props and tag creation function
        module["props"] = self.props
        module.add_callable("tag", create_tag)
        
        result = starlark.eval(module, ast, globals_)
        return result

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
        super().__init__(Safe(css_content), **attributes)

    def render(self, indent=0, pretty=True):
        content = str(self.children[0])
        if not pretty and cssmin:
            try:
                content = cssmin(content)
            except Exception as e:
                print(f"{C.WARNING}Could not minify CSS: {e}{C.END}")
        self.children = [Safe(content)]
        return super().render(indent, pretty)

class script(Node):
    def __init__(self, js_content="", src=None, type="text/javascript", **attributes):
        if src:
            attributes['src'] = src
            super().__init__(**attributes)
        else:
            super().__init__(Safe(js_content), **attributes)
        attributes['type'] = type

    def render(self, indent=0, pretty=True):
        if not pretty and not self.attributes.get('src') and jsmin and self.children:
            content = str(self.children[0])
            try:
                content = jsmin(content)
            except Exception as e:
                print(f"{C.WARNING}Could not minify JS: {e}{C.END}")
            self.children = [Safe(content)]
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
            self.text = response_data.render(pretty=True)
        elif isinstance(response_data, Node):
            self.text = Syqlorix(head(), body(response_data)).render(pretty=True)
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
        self._backend_host = None
        self._backend_port = None

    def use_backend(self, host="127.0.0.1", port=9090):
        self._backend_host = host
        self._backend_port = port
        return self

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

    def build(self, output_dir):
        """Generates static HTML files for all static routes."""
        print(f"🚀 {C.INFO}Building static routes to {C.BOLD}{output_dir}{C.END}...")
        client = self.test_client()
        static_routes = [
            route[0].pattern.replace('$', '') 
            for route in self._routes 
            if '<' not in route[0].pattern
        ]

        if not static_routes:
            print(f"{C.WARNING}   -> No static routes found to build.{C.END}")
            return

        for path in static_routes:
            try:
                print(f"   -> Rendering {C.BOLD}{path}{C.END}...")
                response = client.get(path)
                if response.status_code == 200:
                    if path == '/':
                        file_path = output_dir / "index.html"
                    else:
                        file_path = output_dir / path.lstrip('/') / "index.html"
                    
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(response.text, encoding="utf-8")
                else:
                    print(f"  {C.WARNING}Warning: Could not render path {path} (status: {response.status_code}){C.END}")
            except Exception as e:
                print(f"  {C.ERROR}Error rendering path {path}: {e}{C.END}")

    def render(self, indent=0, pretty=True, live_reload=False, ws_port=None, http_port=None):
        html_string = "<!DOCTYPE html>\n" + super().render(indent=0, pretty=pretty)
        if live_reload and ws_port and http_port:
            script_tag = LIVE_RELOAD_SCRIPT.format(http_port=http_port, ws_port=ws_port)
            html_string = html_string.replace("</body>", f"{script_tag}</body>")
        return html_string

    def _live_reload_manager(self, host, ws_port, watch_dirs, file_path):
        try:
            asyncio.run(self._async_live_reload(host, ws_port, watch_dirs, file_path))
        except KeyboardInterrupt:
            pass

    async def _async_live_reload(self, host, ws_port, watch_dirs, file_path):
        import logging
        logging.getLogger("websockets").setLevel(logging.CRITICAL)

        active_sockets = set()

        async def send_reload_to_all():
            if active_sockets:
                await asyncio.gather(*[ws.send("reload") for ws in active_sockets])

        async def websocket_handler(websocket):
            active_sockets.add(websocket)
            try:
                await websocket.wait_closed()
            finally:
                active_sockets.remove(websocket)

        async def process_http_request(path, headers):
            request_headers = headers
            if not hasattr(headers, 'get'):
                if hasattr(headers, 'headers'):
                    request_headers = headers.headers
                else:
                    return None

            if request_headers.get("Upgrade", "").lower() != "websocket":
                print(f"🔥 {C.ERROR}Failed to open a WebSocket connection: missing Connection header.{C.END}")
                print(f"   {C.WARNING}You cannot access a WebSocket server directly with a browser. You need a WebSocket client.{C.END}")
            return None

        class ChangeHandler(FileSystemEventHandler):
            def __init__(self, loop, sockets, file_path):
                self.loop = loop
                self.sockets = sockets
                self.file_path = file_path

            def on_modified(self, event):
                if not event.is_directory:
                    print(f"✨ {C.WARNING}Project file changed ({event.src_path}). Reloading...{C.END}")
                    asyncio.run_coroutine_threadsafe(send_reload_to_all(), self.loop)

        server = await websockets.serve(
            websocket_handler, 
            host, 
            ws_port,
            process_request=process_http_request
        )
        print(f"🛰️  {C.INFO}Syqlorix Live-Reload server listening on {C.BOLD}ws://{host}:{ws_port}{C.END}")

        loop = asyncio.get_running_loop()

        observer = Observer()
        for watch_dir in watch_dirs:
            observer.schedule(ChangeHandler(loop, active_sockets, file_path), path=str(watch_dir), recursive=True)
            print(f"👀 {C.INFO}Watching for changes in {C.BOLD}'{watch_dir}' (recursively){C.END}")
        observer.start()

        try:
            await asyncio.Event().wait()
        finally:
            observer.stop()
            observer.join()
            server.close()
            await server.wait_closed()

    def run(self, file_path, host="127.0.0.1", port=8000, live_reload=True, max_port_attempts=10, _reloader_process=False):
        current_port = port
        http_server = None

        if not _reloader_process:
            print(f"🔥 {C.PRIMARY}Starting server for {C.BOLD}{Path(file_path).name}{C.END}...")

        project_root = Path(file_path).parent.resolve()
        whitelist, blacklist = _load_access_policy(project_root)

        app_instance = self if live_reload else _load_app_from_file(file_path)

        class SyqlorixRequestHandler(BaseHTTPRequestHandler):
            _app_instance = app_instance
            _whitelist = whitelist
            _blacklist = blacklist

            def __init__(self, *args, **kwargs):
                self.http_port = current_port
                if live_reload:
                    self.__class__._app_instance = _load_app_from_file(file_path)
                    # Reload the access policy on each request in live-reload mode
                    whitelist, blacklist = _load_access_policy(project_root)
                    self.__class__._whitelist = whitelist
                    self.__class__._blacklist = blacklist
                super().__init__(*args, **kwargs)

            def _send_syqlorix_404(self, path):
                error_page = Syqlorix(
                    head(
                        title("404 Not Found"),
                        style("body { background-color: #1a1a2e; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; display: grid; place-content: center; height: 100vh; margin: 0; text-align: center; } .container { padding: 2rem 4rem; border-radius: 8px; background: #2a2a4a; box-shadow: 0 4px 12px rgba(0,0,0,0.3); } h1 { color: #ff5370; font-size: 5rem; margin: 0; } h2 { color: #00a8cc; margin-bottom: 1rem; } p { color: #aaa; margin-top: 0.5rem; } a { color: #72d5ff; font-weight: bold; text-decoration: none; } a:hover { text-decoration: underline; }")
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
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Content-length", str(len(error_html)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                self.end_headers()
                self.wfile.write(error_html)

            def _handle_request(self, is_head=False):
                if not self._app_instance:
                    error_page = _create_generic_error_page()
                    error_html = error_page.render(pretty=True).encode('utf-8')
                    self.send_response(500)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.send_header("Content-length", str(len(error_html)))
                    self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(error_html)
                    return
                try:
                    request = Request(self)

                    # Use backend if configured
                    if self._app_instance._backend_host:
                        try:
                            # Make a thrift call to the backend
                            transport = TSocket.TSocket(self._app_instance._backend_host, self._app_instance._backend_port)
                            transport = TTransport.TBufferedTransport(transport)
                            protocol = TBinaryProtocol.TBinaryProtocol(transport)
                            client = SyqlorixService.Client(protocol)
                            transport.open()

                            thrift_request = ThriftRequest(
                                method=request.method,
                                path=request.path,
                                headers={str(k): str(v) for k, v in request.headers.items()},
                                query_params={str(k): str(v) for k, v in request.query_params.items()},
                                form_data={str(k): str(v) for k, v in request.form_data.items()},
                                body=request.body
                            )

                            thrift_response = client.render(thrift_request)
                            transport.close()

                            html_bytes = thrift_response.html.encode("utf-8")
                            self.send_response(thrift_response.status_code)
                            for key, value in thrift_response.headers.items():
                                self.send_header(key, value)
                            self.send_header("Content-length", str(len(html_bytes)))
                            self.end_headers()
                            self.wfile.write(html_bytes)
                            return
                        except Exception as e:
                            print(f"{C.ERROR}Backend error: {e}{C.END}")
                            # Fallback to local rendering if backend fails? 
                            # For now, just continue to local handling if backend is not used or fails
                    
                    if request.path == '/favicon.ico':
                        self.send_response(204)
                        self.end_headers()
                        return

                    for prefix, target_url in self._app_instance._dev_proxies.items():
                        if request.path.startswith(prefix):
                            proxy_url = urljoin(target_url + '/', request.path[len(prefix):].lstrip('/'))
                            try:
                                headers = dict(request.headers)
                                headers.pop('Host', None)
                                response = requests.request(
                                    method=request.method,
                                    url=proxy_url,
                                    headers=headers,
                                    params=request.query_params,
                                    data=request.body if request.body else None,
                                    allow_redirects=False,
                                    stream=True
                                )
                                self.send_response(response.status_code)
                                self.send_header('Access-Control-Allow-Origin', '*')
                                for key, value in response.headers.items():
                                    if key.lower() not in ['content-encoding', 'transfer-encoding', 'connection']:
                                        self.send_header(key, value)
                                content = response.content
                                self.send_header('Content-length', str(len(content)))
                                self.end_headers()
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
                                self.send_error(405, "Method Not Allowed")
                                return
                            request.path_params = match.groupdict()
                            response_data = handler_func(request)
                            if isinstance(response_data, tuple) and len(response_data) == 2:
                                response_data, status_code = response_data
                            else:
                                status_code = 200

                            content_type = "text/html; charset=utf-8"
                            if isinstance(response_data, (dict, list)):
                                content_type = "application/json"
                                html_bytes = json.dumps(response_data, indent=2).encode("utf-8")
                            elif isinstance(response_data, Syqlorix):
                                html_bytes = response_data.render(pretty=True, live_reload=live_reload, ws_port=self._app_instance._live_reload_ws_port, http_port=self.http_port).encode("utf-8")
                            elif isinstance(response_data, Node):
                                temp_syqlorix = Syqlorix(head(), body(response_data))
                                html_bytes = temp_syqlorix.render(pretty=True, live_reload=live_reload, ws_port=self._app_instance._live_reload_ws_port, http_port=self.http_port).encode("utf-8")
                            else:
                                html_bytes = str(response_data).encode("utf-8")
                            
                            self.send_response(status_code)
                            self.send_header("Content-type", content_type)
                            self.send_header("Content-length", str(len(html_bytes)))
                            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                            self.send_header("Pragma", "no-cache")
                            self.send_header("Expires", "0")
                            self.end_headers()
                            self.wfile.write(html_bytes)
                            return

                    file_name = 'index.html' if request.path == '/' else request.path.lstrip('/')
                    static_file_path = (project_root / file_name).resolve()

                    # Enforce access policy for static files
                    relative_path = static_file_path.relative_to(project_root).as_posix()
                    is_blacklisted = any(fnmatch.fnmatch(relative_path, pattern) for pattern in self._blacklist)
                    is_whitelisted = any(fnmatch.fnmatch(relative_path, pattern) for pattern in self._whitelist)

                    if is_blacklisted or (self._whitelist and not is_whitelisted):
                        self._send_syqlorix_404(request.path)
                        return

                    if static_file_path.is_file() and static_file_path.is_relative_to(project_root):
                        self.send_response(200)
                        mime_type, _ = mimetypes.guess_type(static_file_path)
                        self.send_header('Content-type', mime_type or 'application/octet-stream')
                        self.send_header("Content-length", str(static_file_path.stat().st_size))
                        self.end_headers()
                        with open(static_file_path, 'rb') as f:
                            self.wfile.write(f.read())
                        return
                    
                    self._send_syqlorix_404(request.path)

                except Exception as e:
                    terminal_width = shutil.get_terminal_size().columns
                    tb = traceback.extract_tb(e.__traceback__)
                    user_code_entry = None
                    for frame in reversed(tb):
                        if 'syqlorix/' not in frame.filename:
                            user_code_entry = frame
                            break
                    
                    if user_code_entry:
                        title = f" Code Error in {Path(user_code_entry.filename).name} ".center(terminal_width, "═")
                        print(f"{C.ERROR}{title}{C.END}")
                        print(f"{C.BOLD}File    : {C.END}{user_code_entry.filename}")
                        print(f"{C.BOLD}Line    : {C.END}{user_code_entry.lineno}")
                        print(f"{C.BOLD}Function: {C.END}{user_code_entry.name}")
                        print(f"{C.BOLD}Code    : {C.END}{C.WARNING}{user_code_entry.line}{C.END}")
                        try:
                            import inspect
                            source_lines, start_line = inspect.getsourcelines(inspect.getmodule(e.__traceback__))
                            underline = f"{C.ERROR}{'~' * len(user_code_entry.line.strip())}^{C.END}"
                            print(' ' * len("Code    : ") + underline)
                        except Exception:
                            pass 
                        print(f"{C.BOLD}Error   : {C.END}{C.ERROR}{type(e).__name__}: {e}{C.END}")
                    else:
                        title = f" Internal Framework Error ".center(terminal_width, "═")
                        print(f"{C.ERROR}{title}{C.END}")
                        print(f"{C.ERROR}An internal framework error occurred: {e}{C.END}")
                        traceback.print_exc()
                    print(f"{C.ERROR}{'═' * terminal_width}{C.END}")

                    error_page = _create_generic_error_page()
                    error_html = error_page.render(pretty=True).encode('utf-8')
                    self.send_response(500)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.send_header("Content-length", str(len(error_html)))
                    self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(error_html)

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

        for attempt in range(max_port_attempts):
            try:
                http_server = HTTPServer((host, current_port), SyqlorixRequestHandler)
                if current_port != port:
                    print(f"✅ {C.SUCCESS}Port {port} was busy. Server is now running on port {current_port}.{C.END}")
                break
            except PermissionError:
                print(f"{C.ERROR}Permission denied: Port {current_port} is a privileged port.\n   Try running with 'sudo' or use a port number higher than 1024.{C.END}", file=sys.stderr)
                sys.exit(1)
            except socket.gaierror:
                print(f"{C.ERROR}DNS Error: Could not resolve hostname '{host}'. Please check the spelling or network connection.{C.END}", file=sys.stderr)
                sys.exit(1)
            except OSError as e:
                if e.errno == 98: # Address already in use
                    if attempt < max_port_attempts - 1:
                        print(f"{C.WARNING}Port {current_port} is in use. Trying port {current_port + 1}...{C.END}")
                        current_port += 1
                    else:
                        print(f"{C.ERROR}Failed to find an available port after {max_port_attempts} attempts.{C.END}", file=sys.stderr)
                        sys.exit(1)
                elif e.errno == 99: # Cannot assign requested address
                    print(f"{C.ERROR}Invalid address: '{host}' is not assigned to any local network interface on this machine.\n   Try using '0.0.0.0' (all interfaces) or '127.0.0.1' (localhost).{C.END}", file=sys.stderr)
                    sys.exit(1)
                else:
                    print(f"{C.ERROR}System Error: Failed to bind to {host}:{current_port}.\n   Reason: {e.strerror} (Errno {e.errno}){C.END}", file=sys.stderr)
                    sys.exit(1)
        
        if http_server:
            self._live_reload_ws_port = current_port + 1
            self._live_reload_host = host

            if self._routes:
                route_paths = [regex.pattern.split('$')[0] for regex, _, _ in self._routes]
                print(f"🌍 {C.INFO}Routes discovered: {C.BOLD}{C.SUCCESS}{', '.join(sorted(route_paths))}{C.END}")
            else:
                print(f"🌍 {C.INFO}No routes defined. Serving static files only.{C.END}")

            http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
            http_thread.start()

            print(f"🚀 {C.SUCCESS}Syqlorix server running on {C.BOLD}http://{host}:{current_port}{C.END}")
            print(f"   {C.MUTED}Press Ctrl+C to stop.{C.END}")

            if live_reload:
                watch_dirs = [project_root]
                reload_thread = threading.Thread(target=self._live_reload_manager, args=(host, self._live_reload_ws_port, watch_dirs, file_path), daemon=True)
                reload_thread.start()
            
            try:
                http_thread.join()
            except KeyboardInterrupt:
                print("\n" + f"{C.WARNING}Shutting down...{C.END}")
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
    'Node', 'Syqlorix', 'Component', 'StarlarkComponent', 'Comment', 'Request', 'Blueprint', 'redirect',
    'Safe',
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
