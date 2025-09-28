from syqlorix.core import Syqlorix, body, h1, h2, p, a, div, style, head, code, pre, Component

# --- Page Styles ---
# A more sophisticated stylesheet for a portfolio/docs look
page_styles = """
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        line-height: 1.6;
        background-color: #f8f9fa;
        color: #212529;
        margin: 0;
        padding: 0 2rem;
    }
    .container {
        max-width: 960px;
        margin: 2rem auto;
        padding: 2rem;
        background-color: #ffffff;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    h1, h2 {
        color: #343a40;
        border-bottom: 2px solid #dee2e6;
        padding-bottom: 0.5rem;
    }
    h1 { font-size: 2.5rem; }
    h2 { font-size: 2rem; margin-top: 2.5rem; }
    .card {
        border: 1px solid #e9ecef;
        border-radius: 5px;
        padding: 1.5rem;
        margin-top: 1rem;
        background-color: #fff;
    }
    pre {
        background-color: #e9ecef;
        padding: 1rem;
        border-radius: 5px;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    code { font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace; }
"""

# --- Component Definitions ---

# 1. A basic component
class BasicCard(Component):
    def create(self, children=None):
        return div(
            h2("Basic Component"),
            p("This is the simplest form of a component."),
            class_="card"
        )

# 2. A component that accepts props and children
class PropCard(Component):
    def create(self, children=None):
        title = self.props.get("title", "Default Title")
        return div(
            h2(title),
            *(children or []),
            class_="card"
        )

# 3. A component with scoped styles
class ScopedCssCard(Component):
    def create(self, children=None):
        scoped_style = f"""
            div[{self.scope_attr}] p {{
                color: #007bff;
                font-weight: bold;
            }}
        """
        return div(
            style(scoped_style),
            h2("Scoped CSS"),
            p("This text is styled with scoped CSS and should be blue and bold."),
            *(children or []),
            class_="card"
        )

# 4. A component demonstrating lifecycle methods
class LifecycleCard(Component):
    def before_render(self):
        self.title_from_lifecycle = self.props.get("title", "Default").upper()

    def create(self, children=None):
        return div(
            h2(self.title_from_lifecycle),
            p("This title was converted to uppercase in the `before_render` lifecycle method."),
            *(children or []),
            class_="card"
        )

# --- App Definition ---

doc = Syqlorix()

@doc.route('/')
def home(request):
    return Syqlorix(
        head(
            style(page_styles)
        ),
        body(
            div(
                h1("Syqlorix Component Features"),
                
                # Showcase Basic Component
                BasicCard(),

                # Showcase Component with Props and Children
                PropCard(
                    p("This component demonstrates accepting props for the title and children for the content."),
                    title="Component with Props & Children"
                ),

                # Showcase Scoped CSS
                ScopedCssCard(),

                # Showcase Lifecycle Methods
                LifecycleCard(title="Lifecycle Methods"),

                class_="container"
            )
        )
    )

@doc.route('/about')
def about(request):
    return Syqlorix(
        head(
            style(page_styles)
        ),
        body(
            div(
                h1("About Syqlorix"),
                p("This is a demonstration of the static site generation feature."),
                class_="container"
            )
        )
    )