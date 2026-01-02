from syqlorix.core import Syqlorix, body, h1, p, button, div, style, head, Component, form

# --- Page Styles ---
page_styles = """
    body { 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        display: grid; place-content: center; height: 100vh; text-align: center; 
        background-color: #f8f9fa;
    }
    .counter-card {
        background-color: #fff;
        padding: 2rem 4rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    h1 { font-size: 4rem; margin: 0; }
    button { 
        font-size: 1.5rem; padding: 0.5rem 1.5rem; margin: 0.5rem; 
        border-radius: 5px; border: 1px solid #dee2e6; cursor: pointer;
    }
"""

# --- Counter Component ---
class Counter(Component):
    def __init__(self, *children, **props):
        super().__init__(*children, **props)
        # Initialize state from props (e.g., from request query params)
        try:
            count = int(self.props.get("initial_count", 0))
        except ValueError:
            count = 0
        self.set_state({"count": count})

    def create(self, children=None):
        count = self.state.get("count", 0)

        return div(
            h1(count),
            # A form submission will trigger a page reload, sending the new count
            form(
                button("-", name="count", value=count - 1),
                button("+", name="count", value=count + 1),
                method="get",
                action="/"
            ),
            class_="counter-card"
        )

# --- App Definition ---
doc = Syqlorix()

@doc.route('/')
def home(request):
    # Get the count from the URL query parameters (e.g., /?count=5)
    initial_count = request.query_params.get("count", 0)
    
    return Syqlorix(
        head(
            style(page_styles)
        ),
        body(
            # Pass the count from the request to the component
            Counter(initial_count=initial_count)
        )
    )
