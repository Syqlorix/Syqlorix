from typing import Any, List, Dict, Tuple, Type, Set, Callable
from http.server import BaseHTTPRequestHandler
import re

class Node:
    _SELF_CLOSING_TAGS: Set[str]
    tag_name: str
    attributes: Dict[str, Any]
    children: List[Any]
    def __init__(self, *children: Any, **attributes: Any) -> None: ...
    def __truediv__(self, other: Any) -> "Node": ...
    def __enter__(self) -> "Node": ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...
    def _format_attrs(self) -> str: ...
    def render(self, indent: int = 0, pretty: bool = True) -> str: ...

class RedirectResponse:
    location: str
    status_code: int
    def __init__(self, location: str, status_code: int = 302) -> None: ...

class Blueprint:
    name: str
    url_prefix: str
    _routes: List[Tuple[re.Pattern, Set[str], Any]]
    def __init__(self, name: str, url_prefix: str = "") -> None: ...
    def route(self, path: str, methods: List[str] = ...) -> Callable: ...

class TestResponse:
    status_code: int
    headers: Dict[str, str]
    text: str
    def __init__(self, response_data: Any, status_code: int, headers: Dict[str, str]) -> None: ...

class TestClient:
    app: "Syqlorix"
    def __init__(self, app: "Syqlorix") -> None: ...
    def get(self, path: str) -> TestResponse: ...
    def post(self, path: str, data: Dict[str, Any] | None = None) -> TestResponse: ...

class Syqlorix(Node):
    _routes: List[Tuple[re.Pattern, Set[str], Any]]
    _middleware: List[Callable]
    _error_handlers: Dict[int, Callable]

    def route(self, path: str, methods: List[str] = ...) -> Callable: ...
    def register_blueprint(self, blueprint: Blueprint) -> None: ...
    def before_request(self, func: Callable) -> Callable: ...
    def error_handler(self, code: int) -> Callable: ...
    def test_client(self) -> TestClient: ...
    
    def render(self, pretty: bool = True, live_reload_port: int | None = None, live_reload_host: str | None = None) -> str: ...
    def run(self, file_path: str, host: str = "127.0.0.1", port: int = 8000, live_reload: bool = True, max_port_attempts: int = 10) -> None: ...
    
class Component(Node): ...
class Comment(Node): ...

class Request:
    method: str
    path_full: str
    path: str
    query_params: Dict[str, Any]
    headers: Dict[str, str]
    path_params: Dict[str, str]
    body: bytes
    form_data: Dict[str, Any]
    json_data: Dict[str, Any] | List[Any]
    def __init__(self, handler: BaseHTTPRequestHandler) -> None: ...

class head(Node): ...
class body(Node): ...
class style(Node):
    def __init__(self, css_content: str, **attributes: Any) -> None: ...

class script(Node):
    def __init__(self, js_content: str = "", src: str | None = None, type: str = "text/javascript", **attributes: Any) -> None: ...

def redirect(location: str, status_code: int = 302) -> RedirectResponse: ...

doc: Syqlorix

a: Type[Node]
abbr: Type[Node]
address: Type[Node]
article: Type[Node]
aside: Type[Node]
audio: Type[Node]
b: Type[Node]
bdi: Type[Node]
bdo: Type[Node]
blockquote: Type[Node]
button: Type[Node]
canvas: Type[Node]
caption: Type[Node]
cite: Type[Node]
code: Type[Node]
data: Type[Node]
datalist: Type[Node]
dd: Type[Node]
details: Type[Node]
dfn: Type[Node]
dialog: Type[Node]
div: Type[Node]
dl: Type[Node]
dt: Type[Node]
em: Type[Node]
fieldset: Type[Node]
figcaption: Type[Node]
figure: Type[Node]
footer: Type[Node]
form: Type[Node]
h1: Type[Node]
h2: Type[Node]
h3: Type[Node]
h4: Type[Node]
h5: Type[Node]
h6: Type[Node]
header: Type[Node]
i: Type[Node]
iframe: Type[Node]
img: Type[Node]
input: Type[Node]
input_: Type[Node]
ins: Type[Node]
kbd: Type[Node]
label: Type[Node]
legend: Type[Node]
li: Type[Node]
link: Type[Node]
main: Type[Node]
map: Type[Node]
mark: Type[Node]
meta: Type[Node]
meter: Type[Node]
nav: Type[Node]
noscript: Type[Node]
object: Type[Node]
ol: Type[Node]
optgroup: Type[Node]
option: Type[Node]
output: Type[Node]
p: Type[Node]
picture: Type[Node]
pre: Type[Node]
progress: Type[Node]
q: Type[Node]
rp: Type[Node]
rt: Type[Node]
ruby: Type[Node]
s: Type[Node]
samp: Type[Node]
section: Type[Node]
select: Type[Node]
small: Type[Node]
source: Type[Node]
span: Type[Node]
strong: Type[Node]
summary: Type[Node]
sup: Type[Node]
table: Type[Node]
tbody: Type[Node]
td: Type[Node]
template: Type[Node]
textarea: Type[Node]
tfoot: Type[Node]
th: Type[Node]
thead: Type[Node]
time: Type[Node]
title: Type[Node]
tr: Type[Node]
u: Type[Node]
ul: Type[Node]
var: Type[Node]
video: Type[Node]
br: Type[Node]
hr: Type[Node]