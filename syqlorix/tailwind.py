try:
    from tailwind_processor import TailwindProcessor
except ImportError:
    raise RuntimeError("Tailwind plugin not supported unless installed by 'pip install syqlorix[tailwind]'")

from .core import Node, style, Plugin

import os
import tempfile
from pathlib import Path
from typing import Optional, Any, Dict, Set, Tuple


# Implementation of tailwind_processor library's TailwindProcessor class (src at
# https://github.com/choinhet/tailwind-processor/blob/main/tailwind_processor/tailwind_processor.py#L16-L181)

class SyqlorixTailwindProcessor(TailwindProcessor):
    """Tailwind to CSS converter
    
    Arguments
    ----------
    version: Optional[:class:`~str`]
        TailwindCSS version to use. (Default: `v3.4.17`)
    """
    def __init__(self, version: Optional[str] = None):
        self.version = version or "v3.4.17"

    def _get_environment(self) -> Dict[str, Any]:
        env = os.environ.copy()
        env["TAILWINDCSS_VERSION"] = self.version
        return env
    
    def _run_for_content(
        self,
        parent,
        content_path,
        tw_classes: Optional[list] = None,
        input_path: Optional[Path] = None,
        config_path: Optional[Path] = None,
        output_path: Optional[Path] = None
    ):
        tw_classes = tw_classes or []

        input_path, err = (input_path, None) if input_path else self._set_input(parent)
        if err:
            return "", err

        config_path, err = (config_path, None) if config_path else self._set_configs(parent, content_path)
        if err:
            return "", err

        output_path, err = (output_path, None) if output_path else self._set_output(parent)
        if err:
            return "", err

        err = self._run_command(
            config_path=config_path,
            input_path=input_path,
            output_path=output_path,
        )
        if err:
            return "", err

        try:
            return output_path.read_text(), None
        except Exception as e:
            return "", Exception(f"Failed to read output file:\n" + str(e))

    def process(self, tailwind_classes: Set[str], input_path: str = None, config_path: str = None) -> Tuple[str, Optional[Exception]]: # type: ignore
        """
        Process Tailwind classes into CSS.

        Args:
            tailwind_classes - Classes to process
            input_path - path to input CSS (optional)
            config_path - path to config file (optional)

        Returns:
            Processed style file string, Potential Error
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                parent = Path(temp_dir)
                parent.mkdir(parents=True, exist_ok=True)
                content_file = parent / "content.html"
                if input_path:
                    inp, _ = self._set_input(parent=parent)
                    with open(input_path, "r") as f:
                        inp.write_text(f.read())

                    input_path = inp

                if config_path:
                    config_path, _ = self._set_configs(parent=parent, content_file=config_path)

                tw_classes = " ".join(tailwind_classes)
                content_file.write_text(f'<div class="{tw_classes}"></div>')
                content_path = content_file.as_posix()

                result, err = self._run_for_content(
                    parent=parent,
                    content_path=content_path,
                    tw_classes=tailwind_classes,
                    input_path=input_path,
                    config_path=config_path
                )
                if err:
                    return "", err

                return result, None
        except Exception as e:
            return "", Exception(f"Failed to process tailwind classes:\n" + str(e))

tp = SyqlorixTailwindProcessor()
tp.process({"x"}) # to install tailwind executable.

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
        name: str,
        input: Optional[str] = None,
        config: Optional[str] = None
    ) -> None:
        if name in scopes:
            raise RuntimeError(f"Scope '{name}' is already defined. Access it using scope() method!")
        
        self.name: str = name
        self.css = ""
        self.changed = True
        self.input = input
        self.config = config
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

    def process(self, tp: Optional[SyqlorixTailwindProcessor] = tp, input: Optional[str] = None, config: Optional[str] = None) -> str:
        """A method to generate CSS
        
        Parameters
        -----------
        tp: Optional[:class:`syqlorix.tailwind.SyqlorixTailwindProcessor`]
            Processor (Optional)
        input: Optional[:class:`~str`]
            Path to input CSS file (if any!)
        config: Optional[:class:`~str`]
            Path to config file (if any!)
        
        Returns
        -------
        str
            CSS output.
        """
        if self.input != input or self.config != config:
            self.config = config
            self.input = input
            self.changed = True
        
        if not self.changed:
            return self.css
        
        out, err = tp.process(
            self.data,
            self.input,
            self.config
        )
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
    input: Optional[:class:`~str`]
        Path to input CSS file (if any!)
    config: Optional[:class:`~str`]
        Path to config file (if any!)
    scope: Optional[:class:`~str`]
        Name of the scope through which class names are to be selected. (default: 'global')
    """
    def __init__(
        self,
        input: Optional[str] = None,
        config: Optional[str] = None,
        scope: Optional[str] = "global",
        **kwargs
    ):
        self.input = input
        self.config = config
        self.scope = set_scope(scope) if scope not in scopes else scopes[scope]
        self.processor: SyqlorixTailwindProcessor = tp
        super().__init__(**kwargs)

    def render(self, indent=0, pretty=True) -> str:
        return style(self.scope.process(
            self.processor,
            self.input,
            self.config
        )).render(indent, pretty)


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
    "SyqlorixTailwindProcessor"
)