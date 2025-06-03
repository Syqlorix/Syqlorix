from syqlorix import Page, component, css
from typing import List

from syqlorix import Page, component, css
from typing import List

@component
def SimpleAlert(page_instance: Page, message: str, type: str = "info"):
    alert_rules = {
        ".alert-box": {
            "padding": "15px",
            "margin": "10px 0",
            "border_radius": "4px",
            "font_weight": "bold",
            "opacity": "0.95"
        },
        ".alert-info": {
            "background_color": "#d9edf7",
            "color": "#31708f",
            "border": "1px solid #bce8f1"
        },
        ".alert-success": {
            "background_color": "#dff0d8",
            "color": "#3c763d",
            "border": "1px solid #d6e9c6"
        },
        ".alert-warning": {
            "background_color": "#fcf8e3",
            "color": "#8a6d3b",
            "border": "1px solid #faebcc"
        },
        ".alert-error": {
            "background_color": "#f2dede",
            "color": "#a94442",
            "border": "1px solid #ebccd1"
        }
    }
    alert_styles = css(**alert_rules)
    page_instance.style(alert_styles)

    page_instance.div(message, _class=f"alert-box alert-{type}")

@component
def ImageGallery(page_instance: Page, images: List[str], _class: str = "", **attrs): # fixed for ver 3.8 
    gallery_rules = {
        ".image-gallery": {
            "display": "grid",
            "grid_template_columns": "repeat(auto-fit, minmax(150px, 1fr))",
            "gap": "10px",
            "margin_top": "20px"
        },
        ".image-gallery img": {
            "width": "100%",
            "height": "auto",
            "border_radius": "5px",
            "box_shadow": "0 2px 5px rgba(0,0,0,0.1)",
            "object_fit": "cover"
        }
    }
    gallery_styles = css(**gallery_rules)
    page_instance.style(gallery_styles)

    with page_instance.div(_class=f"image-gallery {_class}" if _class else "image-gallery", **attrs):
        for img_src in images:
            page_instance.img(src=img_src, alt="Gallery Image")