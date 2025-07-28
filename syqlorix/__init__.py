import sys
import asyncio
import threading
import mimetypes
import re
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import urllib.parse
import websockets
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from jsmin import jsmin
from cssmin import cssmin


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

class Node:
    _SELF_CLOSING_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, *children, **attributes):
        self.tag_name = self.__class__.__name__.lower()
        if self.tag_name in ("component", "comment"):
            self.tag_name = ""
        self.attributes = {k.rstrip('_'): v for k, v in attributes.items()}
        self.children = list(children)
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
                parts.append(f'{key}="{value}"')
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

class Syqlorix(Node):
    def __init__(self, *children, **attributes):
        super().__init__(*children, **attributes)
        self.tag_name = "html"
        self._routes = []

    def route(self, path, methods=['GET']):
        def decorator(handler_func):
            path_regex = re.sub(r'<([^>]+)>', r'(?P<\1>[^/]+)', path) + '$'
            self._routes.append((re.compile(path_regex), set(m.upper() for m in methods), handler_func))
            return handler_func
        return decorator

    def render(self, pretty=True, live_reload_port=None, live_reload_host=None):
        html_string = "<!DOCTYPE html>\n" + super().render(indent=0, pretty=pretty)
        if live_reload_port and pretty: # Only inject script in dev mode
            script_tag = LIVE_RELOAD_SCRIPT.format(host=live_reload_host, port=live_reload_port)
            html_string = html_string.replace("</body>", f"{script_tag}</body>")
        return html_string

    def _live_reload_manager(self, host, ws_port, watch_dirs):
        try:
            asyncio.run(self._async_live_reload(host, ws_port, watch_dirs))
        except KeyboardInterrupt:
            pass

    async def _async_live_reload(self, host, ws_port, watch_dirs):
        active_sockets = set()
        stop_event = asyncio.Event()

        async def websocket_handler(websocket):
            active_sockets.add(websocket)
            try:
                await websocket.wait_closed()
            finally:
                active_sockets.remove(websocket)

        class ChangeHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory:
                    print(f"✨ {C.WARNING}File changed ({event.src_path}). Triggering reload...{C.END}")
                    if active_sockets:
                        asyncio.create_task(asyncio.gather(*[ws.send("reload") for ws in active_sockets]))
        
        server = await websockets.serve(websocket_handler, host, ws_port)
        print(f"🛰️  {C.INFO}Syqlorix Live-Reload server listening on {C.BOLD}ws://{host}:{ws_port}{C.END}")

        observer = Observer()
        for watch_dir in watch_dirs:
            observer.schedule(ChangeHandler(), path=str(watch_dir), recursive=True)
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
        watch_dirs = [project_root] 

        potential_static_dir = project_root / 'static'
        if potential_static_dir.is_dir():
            watch_dirs.append(potential_static_dir)

        for attempt in range(max_port_attempts):
            try:
                class SyqlorixRequestHandler(BaseHTTPRequestHandler):
                    _app_instance = self

                    def handle_one_request(self):
                        try:
                            super().handle_one_request()
                        except (BrokenPipeError, ConnectionResetError):
                            pass

                    def _handle_request(self, is_head=False):
                        request = Request(self)
                        syqlorix_app = self._app_instance

                        # --- Static file handling ---
                        static_dir_abs = (project_root / 'static').resolve()
                        try:
                            req_file_abs = (project_root / request.path.lstrip('/')).resolve(strict=True)

                            if req_file_abs.is_file() and req_file_abs.is_relative_to(static_dir_abs):
                                mime_type, _ = mimetypes.guess_type(req_file_abs)
                                self.send_response(200)
                                self.send_header('Content-type', mime_type or 'application/octet-stream')
                                if not is_head: self.send_header("Content-length", str(req_file_abs.stat().st_size))
                                self.end_headers()
                                if not is_head:
                                    with open(req_file_abs, 'rb') as f:
                                        self.wfile.write(f.read())
                                return
                        except (FileNotFoundError, ValueError, NotADirectoryError):
                            pass

                        # --- Favicon handling ---
                        if request.path == '/favicon.ico':
                            self.send_response(204); self.end_headers(); return

                        # --- Dynamic route handling ---
                        for route_regex, methods, handler_func in syqlorix_app._routes:
                            match = route_regex.match(request.path)
                            if match:
                                if request.method not in methods:
                                    self.send_error(405, "Method Not Allowed"); return
                                
                                request.path_params = match.groupdict()
                                try:
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
                                        html_bytes = response_data.render(pretty=True, live_reload_port=syqlorix_app._live_reload_ws_port, live_reload_host=syqlorix_app._live_reload_host).encode("utf-8")
                                    elif isinstance(response_data, Node):
                                        temp_syqlorix = Syqlorix(head(), body(response_data))
                                        html_bytes = temp_syqlorix.render(pretty=True, live_reload_port=syqlorix_app._live_reload_ws_port, live_reload_host=syqlorix_app._live_reload_host).encode("utf-8")
                                    else:
                                        html_bytes = str(response_data).encode("utf-8")
                                    
                                    self.send_response(status_code)
                                    self.send_header("Content-type", content_type)
                                    self.send_header("Content-length", str(len(html_bytes)))
                                    self.end_headers()
                                    self.wfile.write(html_bytes)
                                    return
                                except Exception as e:
                                    print(f"{C.ERROR}Error in route handler for '{request.path}': {e}{C.END}", file=sys.stderr)
                                    self.send_error(500, f"Internal Server Error: {e}")
                                    return

                        # --- Fallback for simple apps with no routes ---
                        if not syqlorix_app._routes and request.path == '/':
                            html_bytes = syqlorix_app.render(pretty=True, live_reload_port=syqlorix_app._live_reload_ws_port, live_reload_host=syqlorix_app._live_reload_host).encode("utf-8")
                            self.send_response(200)
                            self.send_header("Content-type", "text/html")
                            self.send_header("Content-length", str(len(html_bytes)))
                            self.end_headers()
                            self.wfile.write(html_bytes)
                            return

                        self.send_error(404, "Not Found")

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
                else: raise

        self._live_reload_ws_port = current_port + 1
        self._live_reload_enabled = live_reload
        self._live_reload_host = host

        http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
        http_thread.start()
        print(f"🚀 {C.SUCCESS}Syqlorix server running on {C.BOLD}http://{host}:{current_port}{C.END}")

        if live_reload:
            reload_thread = threading.Thread(target=self._live_reload_manager, args=(host, self._live_reload_ws_port, watch_dirs), daemon=True)
            reload_thread.start()
        
        if self._routes:
            route_paths = [path for regex, methods, func in self._routes for path in regex.pattern.split('$')[0:1]]
            print(f"🌍 {C.INFO}Routes discovered: {', '.join(sorted(route_paths))}{C.END}")
        else:
            print(f"ℹ️  {C.INFO}No routes defined. Serving default content for all requests.{C.END}")

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

__all__ = [
    'Node', 'Syqlorix', 'Component', 'Comment', 'Request',
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
    'ul', 'var', 'video', 'br', 'hr'
]

__all__.extend(_TAG_NAMES)