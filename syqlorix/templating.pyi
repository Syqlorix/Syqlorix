from typing import Type, Iterable, Optional, Dict
from .core import Node

class NodeWrapper:
  _classlist: set
  _node: Node
  _attrs: Dict[str, str]
  def __init__(
    self,
    node: Node,
    classes: Optional[Iterable[str]] = None,
    **attrs: Dict[str, str]
  ) -> None: ...
    
  def __call__(self, *children, **attrs) -> Node: ...
    
  def __getattr__(self, n: str) -> "NodeWrapper": ...
  def __repr__(self) -> str: ...
  __str__ = __repr__

def _(query: str, **kw: Dict[str, str]) -> NodeWrapper: ...

class html(NodeWrapper):
  class _node(Node):
    def render(self, *args, doctype=True, **kwargs) -> str: ...

html = html()

head: NodeWrapper
body: NodeWrapper
style: NodeWrapper
script: NodeWrapper
Component: Type[Node]
a: NodeWrapper
abbr: NodeWrapper
address: NodeWrapper
article: NodeWrapper
aside: NodeWrapper
audio: NodeWrapper
b: NodeWrapper
bdi: NodeWrapper
bdo: NodeWrapper
blockquote: NodeWrapper
button: NodeWrapper
canvas: NodeWrapper
caption: NodeWrapper
cite: NodeWrapper
code: NodeWrapper
data: NodeWrapper
datalist: NodeWrapper
dd: NodeWrapper
details: NodeWrapper
dfn: NodeWrapper
dialog: NodeWrapper
div: NodeWrapper
dl: NodeWrapper
dt: NodeWrapper
em: NodeWrapper
fieldset: NodeWrapper
figcaption: NodeWrapper
figure: NodeWrapper
footer: NodeWrapper
form: NodeWrapper
h1: NodeWrapper
h2: NodeWrapper
h3: NodeWrapper
h4: NodeWrapper
h5: NodeWrapper
h6: NodeWrapper
header: NodeWrapper
i: NodeWrapper
iframe: NodeWrapper
img: NodeWrapper
input: NodeWrapper
input_: NodeWrapper
ins: NodeWrapper
kbd: NodeWrapper
label: NodeWrapper
legend: NodeWrapper
li: NodeWrapper
link: NodeWrapper
main: NodeWrapper
map: NodeWrapper
mark: NodeWrapper
meta: NodeWrapper
meter: NodeWrapper
nav: NodeWrapper
noscript: NodeWrapper
object: NodeWrapper
ol: NodeWrapper
optgroup: NodeWrapper
option: NodeWrapper
output: NodeWrapper
p: NodeWrapper
picture: NodeWrapper
pre: NodeWrapper
progress: NodeWrapper
q: NodeWrapper
rp: NodeWrapper
rt: NodeWrapper
ruby: NodeWrapper
s: NodeWrapper
samp: NodeWrapper
section: NodeWrapper
select: NodeWrapper
small: NodeWrapper
source: NodeWrapper
span: NodeWrapper
strong: NodeWrapper
summary: NodeWrapper
sup: NodeWrapper
table: NodeWrapper
tbody: NodeWrapper
td: NodeWrapper
template: NodeWrapper
textarea: NodeWrapper
tfoot: NodeWrapper
th: NodeWrapper
thead: NodeWrapper
time: NodeWrapper
title: NodeWrapper
tr: NodeWrapper
u: NodeWrapper
ul: NodeWrapper
var: NodeWrapper
video: NodeWrapper
br: NodeWrapper
hr: NodeWrapper

