from typing import Any, List, Dict, Tuple, Type, Set
from http.server import BaseHTTPRequestHandler
import re


class Plugin:
    def on_node_init(self, node: "Node") -> None: ...
    def load(self) -> None: ...

plugins: List[Plugin]
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

class Syqlorix(Node):
    _routes: List[Tuple[re.Pattern, Set[str], Any]]
    def route(self, path: str, methods: List[str] = ...) -> Any: ...
    def render(self, indent: int = 0, pretty: bool = True, live_reload: bool = False, ws_port: int | None = None, http_port: int | None = None) -> str: ...
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