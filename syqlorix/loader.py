import importlib.util
import os
from typing import Callable, Any

def load_component(file_path: str, component_name: str = None) -> Callable[..., Any]:
    """
    Loads a Syqlorix component function from a Python file.

    Args:
        file_path (str): The absolute or relative path to the Python file containing the component.
        component_name (str, optional): The name of the component function within the file.
                                        If None, it tries to find a function decorated with `@component`.
                                        If only one such function exists, it returns that.
                                        Raises error if multiple or none found.

    Returns:
        Callable: The loaded component function.

    Raises:
        FileNotFoundError: If the file_path does not exist.
        ValueError: If component_name is not specified and no or multiple @component functions are found.
        TypeError: If the loaded function is not a valid Syqlorix component.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Component file not found: {file_path}")

    module_name = f"syqlorix_component_loaded_{os.path.basename(file_path).replace('.', '_')}_{os.urandom(4).hex()}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Could not load module spec for component file: {file_path}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    found_components = []
    if component_name:
        if hasattr(module, component_name):
            func = getattr(module, component_name)
            if callable(func) and hasattr(func, '_is_syqlorix_component') and func._is_syqlorix_component:
                return func
            else:
                raise TypeError(f"'{component_name}' in '{file_path}' is not a valid Syqlorix component function.")
        else:
            raise ValueError(f"Component '{component_name}' not found in file '{file_path}'.")
    else:
        for name in dir(module):
            func = getattr(module, name)
            if callable(func) and hasattr(func, '_is_syqlorix_component') and func._is_syqlorix_component:
                found_components.append(func)
        
        if not found_components:
            raise ValueError(f"No @component decorated functions found in file '{file_path}'.")
        if len(found_components) > 1:
            raise ValueError(f"Multiple @component decorated functions found in '{file_path}'. Please specify 'component_name'.")
        
        return found_components[0]