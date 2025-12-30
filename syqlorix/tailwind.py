from .core import Node, style, Plugin
from typing import Optional, Any, Dict, Set, Tuple

def process_tailwind(tailwind_classes: Set[str]) -> Tuple[str, Optional[Exception]]:
    try:
        from . import syqlorix_rust
        html_content = f"<div class='{' '.join(tailwind_classes)}'></div>"
        css = syqlorix_rust.process_tailwind_css(html_content)
        return css, None
    except Exception as e:
        return "", e

class TailwindScope:
    """Dataclass for tailwind processing.
    
    Arguments
    ----------
    name: :class:`~str`
        Name of the scope.
    input: Optional[:class:`~str`]
        Path to input CSS file (if any!)
    config: Optional[:class:`~str`]
        Path to config file (if any!)

    Raises
    -------
    RuntimeError
        Raised when a scope with that name is already defined.
    """
    def __init__(
        self,
        name: str
    ) -> None:
        if name in scopes:
            raise RuntimeError(f"Scope '{name}' is already defined. Access it using scope() method!")
        
        self.name: str = name
        self.css = ""
        self.changed = True
        self.data: Set[str] = set()
        scopes[name] = self

    def add(self, *classes) -> None:
        """Adds class names to convert-list"""
        l = set()
        if self.name != "global":
            scopes["global"].add(*classes)

        for i in classes:
            if isinstance(i, str):
                l |= {*i.split(" ")}
            else:
                l |= {*i}

        if not all(i in self.data for i in l): self.changed = True
        self.data |= l

    def remove(self, *classes) -> None:
        """Remove class names from the list"""
        l = set()
        if self.name == "global":
            raise RuntimeWarning("Can't remove classes from 'global' scope!")

        for i in classes:
            if isinstance(i, str):
                l |= {*i.split(" ")}
            else:
                l |= {*i}

        if any(i in self.data for i in l): self.changed = True
        self.data -= l

    def process(self) -> str:
        """A method to generate CSS
        
        Returns
        -------
        str
            CSS output.
        """
        if not self.changed:
            return self.css
        
        out, err = process_tailwind(self.data)
        if err:
            print(f"\033[91m Error while generating CSS: {err}\n" + " Defaulting to previous CSS!")
        else:
            self.css = out
            self.changed = False
        return self.css

scopes: Dict[str, TailwindScope] = {}
current_scope = TailwindScope("global")

def get_scope(name: Optional[str] = None) -> TailwindScope:
    """Set current scope!
    
    Parameters
    ----------
    name: Optional[`~str`]
        name of the scope. current scope is returned if not given.
        
    Returns
    -------
    syqlorix.tailwind.TailwindScope
        The scope object.
    """
    if not name:
        return current_scope
    
    if name not in scopes:
        TailwindScope(name)

    return scopes[name]

def set_scope(name: Optional[str] = None) -> TailwindScope:
    """Set current scope!
    
    Parameters
    ----------
    name: Optional[`~str`]
        name of the scope. current scope is returned if not given.
        
    Returns
    -------
    syqlorix.tailwind.TailwindScope
        The scope object.
    """
    global current_scope
    current_scope = get_scope(name)
    return current_scope

class tailwind(Node):
    """A method to generate CSS
    
    Arguments
    ---------
    scope: Optional[:class:`~str`]
        Name of the scope through which class names are to be selected. (default: 'global')
    """
    def __init__(
        self,
        scope: Optional[str] = "global",
        **kwargs
    ):
        self.scope = set_scope(scope) if scope not in scopes else scopes[scope]
        super().__init__(**kwargs)

    def render(self, indent=0, pretty=True) -> str:
        return style(self.scope.process()).render(indent, pretty)


class TailwindPlugin(Plugin):
    def on_node_init(self, node: Node) -> None:
        current_scope.add({c for c in node.attributes.get('class',"").split(" ") if c})

tailwind_plugin = TailwindPlugin()

def load_plugin():
    """Used to load plugin"""
    if not tailwind_plugin.loaded:
        tailwind_plugin.load()

__all__ = (
    "scopes",
    "tailwind",
    "get_scope",
    "set_scope",
    "load_plugin",
    "TailwindScope",
    "TailwindPlugin",
    "process_tailwind"
)