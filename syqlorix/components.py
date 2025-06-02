from typing import Callable, Any

def component(func: Callable[..., Any]) -> Callable[..., Any]:
    func._is_syqlorix_component = True
    return func