from syqlorix import Page, start_dev_server, Route
import os

example_router = Route("/")

@example_router.route("/")
def my_page_callable() -> Page:
    my_page = Page(title="Syqlorix Dev Server Example")

    with my_page.body:
        my_page.h1("Welcome to Syqlorix Dev Server!")
        my_page.p("This page is served directly from your Python script using `syqlorix.start_dev_server()`.")
        my_page.div("Explore the power of Syqlorix.", _class="info-box")
        my_page.button("Click Me!", id="devBtn")

    my_page.style("""
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 50px; background: #f4f7f6; color: #333; }
        h1 { color: #2c3e50; }
        .info-box { background: #e0f2f7; padding: 20px; border-left: 5px solid #3498db; margin-top: 20px; border-radius: 4px; }
        button { background: #28a745; color: white; border: none; padding: 12px 25px; border-radius: 5px; cursor: pointer; font-size: 1.1em; transition: background 0.3s ease; }
        button:hover { background: #218838; }
    """)

    my_page.script("""
        document.getElementById('devBtn').onclick = function() {
            alert('Dev server click detected!');
        };
    """)
    return my_page

if __name__ == "__main__":
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_for_example = os.path.dirname(current_script_dir) 

    start_dev_server(example_router, port=8000, project_root=project_root_for_example)