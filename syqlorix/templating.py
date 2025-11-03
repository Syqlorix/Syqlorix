from .templating import *
from . import core


class NodeWrapper:
  def __init__(self, node, classes = None, **attrs):
    self._classlist = set(classes) if classes else {}
    self._node = node
    self._attrs = attrs
    
  def __call__(self, *children, **attrs):
    attrs["class_"]=" ".join({*self._classlist, *attrs.pop("class_","").split(" "), *attrs.pop("class","").split(" ")})
    return self._node(*children, **{**self._attrs, **attrs})
    
  def __getattr__(self, n):
    return self.__class__(self._node, {*self._classlist, n}, **self._attrs)
    
  def __repr__(self) -> str:
    return f"<{self._node.__name__}{'.' if self._classlist else ''}{'.'.join(self._classlist)} {' '.join(k+'='+repr(v) for k,v in self._attrs.items())}/>"
    
  __str__ = __repr__

@NodeWrapper
class html(core.Node):
  def render(self, *args, doctype=True, **kwargs):
    return ("<!DOCTYPE html>\n" if doctype else "")+super().render(*args, **kwargs)

def _(query, **kw):
  kw.update(dict(classes = None))
  if "#" in query:
    query, kw["id"] = query.split("#")
  if "." in query:
    kw["classes"] = query.split(".")
    query = kw["classes"].pop(0)

  tag = query or "div"
  glb = globals()
  if tag in glb and isinstance(glb[tag], NodeWrapper):
    return NodeWrapper(glb[tag]._node, **kw)
  
  return NodeWrapper(type(tag, (core.Node,), {}), **kw)


__all__ = ["NodeWrapper", "html"]

for i_ in core.__all__:
  try:
    if i_ != "Syqlorix" and issubclass(getattr(core, i_), core.Node):
      globals()[i_] = NodeWrapper(getattr(core, i_)) if i_ not in ("Component",) else getattr(core, i_)
      __all__.append(i_)
  except TypeError:
    continue
