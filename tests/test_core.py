import pytest
from syqlorix.core import Syqlorix, Component, div, h1, p, body, head, style

def test_component_rendering():
    """Test that a basic component renders correctly."""

    class SimpleCard(Component):
        def create(self, children=None):
            title = self.props.get("title", "Default Title")
            return div(
                h1(title),
                p("This is a simple card.")
            )

    app = Syqlorix()

    @app.route('/')
    def home(request):
        return SimpleCard(title="Test Title")

    client = app.test_client()
    response = client.get('/')

    assert response.status_code == 200
    assert "<h1>\n        Test Title\n      </h1>" in response.text
    assert "<p>\n        This is a simple card.\n      </p>" in response.text

def test_component_default_props():
    """Test that a component renders with default properties."""

    class SimpleCard(Component):
        def create(self, children=None):
            title = self.props.get("title", "Default Title")
            return div(
                h1(title),
                p("This is a simple card.")
            )

    app = Syqlorix()

    @app.route('/')
    def home(request):
        return SimpleCard()

    client = app.test_client()
    response = client.get('/')

    assert response.status_code == 200
    assert "<h1>\n        Default Title\n      </h1>" in response.text


def test_component_not_implemented():
    """Test that a component without a create method raises an error."""

    class BadComponent(Component):
        pass

    app = Syqlorix()

    @app.route('/')
    def home(request):
        return BadComponent()

    client = app.test_client()
    with pytest.raises(NotImplementedError):
        client.get('/')

def test_component_with_children():
    """Test that a component can render children."""

    class Container(Component):
        def create(self, children=None):
            return div(
                h1("Container Title"),
                *(children or [])
            )

    app = Syqlorix()

    @app.route('/')
    def home(request):
        return Container(
            p("This is a child paragraph.")
        )

    client = app.test_client()
    response = client.get('/')

    assert response.status_code == 200
    assert "<h1>\n        Container Title\n      </h1>" in response.text
    assert "<p>\n        This is a child paragraph.\n      </p>" in response.text

def test_component_scoped_css():
    """Test that component styles are scoped and do not conflict."""

    class BlueComponent(Component):
        def create(self, children=None):
            scoped_styles = f"""
                div[{self.scope_attr}] h1 {{ color: blue; }}
            """
            return div(
                style(scoped_styles),
                h1("Blue Title"),
            )

    class RedComponent(Component):
        def create(self, children=None):
            scoped_styles = f"""
                div[{self.scope_attr}] h1 {{ color: red; }}
            """
            return div(
                style(scoped_styles),
                h1("Red Title"),
            )

    app = Syqlorix()

    @app.route('/')
    def home(request):
        return body(
            BlueComponent(),
            RedComponent(),
        )

    client = app.test_client()
    response = client.get('/')

    assert response.status_code == 200
    assert "div[data-syq-" in response.text
    assert "{ color: blue; }" in response.text
    assert "{ color: red; }" in response.text
    assert response.text.count("<style>") == 2

def test_component_lifecycle_methods():
    """Test that component lifecycle methods are called correctly."""

    class LifecycleComponent(Component):
        def __init__(self, *children, **props):
            super().__init__(*children, **props)
            self.after_render_called = False

        def before_render(self):
            self.internal_title = self.props.get("title", "Default").upper()

        def after_render(self, node):
            self.after_render_called = True

        def create(self, children=None):
            return h1(self.internal_title)

    app = Syqlorix()
    component_instance = LifecycleComponent(title="Test")

    @app.route('/')
    def home(request):
        return component_instance

    client = app.test_client()
    response = client.get('/')

    assert response.status_code == 200
    assert ">\n      TEST\n    </h1>" in response.text
    assert component_instance.after_render_called is True
