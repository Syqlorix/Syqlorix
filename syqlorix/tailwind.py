from .core import Node, style, Plugin, plugins

try:
    from tailwind_processor import TailwindProcessor
except ImportError:
    raise RuntimeError("Tailwind plugin not supported unless installed by 'pip install syqlorix[tailwind]'")

import tempfile
from pathlib import Path
from typing import Optional


class SyqlorixTailwindProcessor(TailwindProcessor):
    def _run_for_content(
        self,
        parent,
        content_path,
        tw_classes = None,
        input_path = None,
        config_path = None,
        output_path = None
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
            return "", Exception(f"Failed to read output file:\n{e}")

    def process(self, tailwind_classes: set[str], input_path = None, config_path=None) -> tuple[str, Optional[Exception]]: # type: ignore
        """
        Process Tailwind classes into CSS.

        Args:
            tailwind_classes - Classes to process

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
            return "", Exception(f"Failed to process tailwind classes:\n{e}")

tp = SyqlorixTailwindProcessor()
tp.process({"x"})

class TailwindScope:
    def __init__(self, name: str, input: None | str = None, config: str | None = None) -> None:
        if name in scopes:
            raise RuntimeError(f"Scope '{name}' is already defined. Access it using scope() method!")
        
        self.name: str = name
        self.css = ""
        self.changed = True
        self.input = input
        self.config = config
        self.data: set[str] = set()
        scopes[name] = self

    def add(self, *classes) -> None:
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

    def process(self, tp: SyqlorixTailwindProcessor = tp, input: None | str = None, config: str | None = None) -> str:
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
            print(f"\033[91m Error while generating CSS: {err}\n Defaulting to previous CSS!")
        else:
            self.css = out
            self.changed = False
        return self.css

scopes: dict[str, TailwindScope] = {}
current_scope = TailwindScope("global")

def scope(name = None):
    global current_scope
    if not name:
        return current_scope
    
    if name not in scopes:
        TailwindScope(name)

    current_scope = scopes[name]
    return current_scope


class tailwind(Node):
    def __init__(
        self,
        input: Optional[str] = None,
        config: Optional[str] = None,
        scope: str = "global",
        **kwargs
    ):
        self.input = input
        self.config = config
        self.scope = TailwindScope(scope) if scope not in scopes else scopes[scope]
        self.processor: SyqlorixTailwindProcessor = tp
        super().__init__(**kwargs)

    def render(self, indent=0, pretty=True):
        return style(self.scope.process(
            self.processor,
            self.input,
            self.config
        )).render(indent, pretty)


class TailwindPlugin(Plugin):
    def on_node_init(self, node: Node) -> None:
        current_scope.add({c for c in node.attributes.get('class',"").split(" ") if c})


def load_plugin():
    if not any(isinstance(plugin, TailwindPlugin) for plugin in plugins):
        plugins.append(TailwindPlugin())