import html
import urllib.parse
from typing import Dict, Union, List

def escape_html(text: str) -> str:
    return html.escape(text)

def format_attrs(attrs: dict) -> str:
    attr_parts = []
    for key, value in attrs.items():
        if key == '_class':
            key = 'class'
        
        if isinstance(value, bool):
            if value:
                attr_parts.append(escape_html(key))
        elif value is not None:
            attr_parts.append(f'{escape_html(key)}="{escape_html(str(value))}"')
    return " ".join(attr_parts)

def parse_form_urlencoded(data: str) -> Dict[str, Union[str, List[str]]]:
    parsed_data = urllib.parse.parse_qs(data)
    result = {}
    for key, values in parsed_data.items():
        if len(values) == 1:
            result[key] = values[0]
        else:
            result[key] = values
    return result