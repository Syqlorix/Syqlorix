from flask import Flask, render_template_string
from syqlorix import Page

app = Flask(__name__)

@app.route('/')
def home():
    page = Page(title="Syqlorix with Flask")

    with page.body:
        page.h1("Hello from Flask and Syqlorix!")
        page.p("This page was generated entirely using Syqlorix within a Flask app.")
        page.div("No separate HTML templates needed!", _class="flask-info")
        page.button("Click me!", id="flaskBtn")

    page.style("""
        body { font-family: 'Arial', sans-serif; margin: 60px; background: #f8f9fa; color: #495057; text-align: center; }
        h1 { color: #6f42c1; margin-bottom: 20px; }
        .flask-info { background: #e9ecef; padding: 25px; border-radius: 8px; margin: 30px auto; max-width: 600px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        button { background: #007bff; color: white; border: none; padding: 15px 30px; border-radius: 25px; cursor: pointer; font-size: 1.2em; transition: background 0.3s ease; }
        button:hover { background: #0056b3; }
    """)

    page.script("""
        document.getElementById('flaskBtn').onclick = function() {
            alert('Flask page clicked via Syqlorix JS!');
        };
    """)

    html_output = page.render()

    return render_template_string(html_output)

if __name__ == '__main__':
    print("\n" + "="*50)
    print(" Flask App with Syqlorix ")
    print(" Open your browser to: http://127.0.0.1:5000/ ")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)