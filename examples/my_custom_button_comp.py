from syqlorix import Page, component

@component
def CustomButtonComponent(page_instance: Page, text: str = "Loaded Button", **attrs):
    page_instance.button(text, _class="custom-loaded-btn", **attrs)
