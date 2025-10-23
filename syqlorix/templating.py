from .templating import *
from . import core


class NodeWrapper:
  def __init__(self, node, classes = None):
    self._classlist = set(classes) if classes else {}
    self._node = node
    
  def __call__(self, *children, **attrs):
    attrs["class_"]=" ".join({*self._classlist, *attrs.pop("class_","").split(" "), *attrs.pop("class","").split(" ")})
    return self._node(*children, **attrs)
    
  def __getattr__(self, n):
    return self.__class__(self._node, {*self._classlist, n})
    
  def __repr__(self) -> str:
    return f"<{self._node.__name__}{'.' if self._classlist else ''}{'.'.join(self._classlist)} />"
    
  __str__ = __repr__

@NodeWrapper
class html(core.Node):
  def render(self, *args, **kwargs):
    return "<!DOCTYPE html>\n"+super().render(*args, **kwargs)


__all__ = ["NodeWrapper", "html"]

for i_ in core.__all__:
  try:
    if issubclass(getattr(core, i_), core.Node):
      globals()[i_] = NodeWrapper(getattr(core, i_)) if i_ not in ("Component", "Syqlorix") else getattr(core, i_)
      __all__.append(i_)
  except TypeError:
    continue

del Syqlorix # type: ignore
__all__.remove("Syqlorix")
