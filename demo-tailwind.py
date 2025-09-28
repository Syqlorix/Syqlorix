# Import all the necessary components from syqlorix
from syqlorix import (
    Syqlorix, Component,
    head, body, title, meta, link, style, script,
    h1, p, div, a, img, br, code
)
from syqlorix.tailwind import tailwind, load_plugin, set_scope

# ---------------------------------------------------------
# 1.  Initialisation
# ---------------------------------------------------------

doc = Syqlorix()

load_plugin() # load tailwind plugin
set_scope("demo")

# ---------------------------------------------------------
# 2.  Re-usable Footer component
# ---------------------------------------------------------
class Footer(Component):
    def create(self, children=None):
        return div(
            p("Last Modified in v1.2.5 ✨"),
            a("Check out the source on GitHub",
              href="https://github.com/Syqlorix/Syqlorix",
              class_="text-[#feda6a] hover:text-white"),
            class_="text-center mt-12 font-sans text-[#aaa]"
        )

# ---------------------------------------------------------
# 3.  Embedded CSS (no external file needed for this demo)
# ---------------------------------------------------------


# ---------------------------------------------------------
# 4.  Tiny interactive JavaScript (embedded)
# ---------------------------------------------------------
interactive_js = """
document.addEventListener('DOMContentLoaded', () => {
    const heading = document.querySelector('h1');
    let clicks = 0;
    const originalText = heading.innerText;

    heading.addEventListener('click', () => {
        clicks++;
        heading.innerText = `${originalText} (Clicked ${clicks} times!)`;
    });

    console.log('Syqlorix page loaded and is interactive.');
});
"""

# ---------------------------------------------------------
# 5.  Build the page tree with the handy '/' operator
# ---------------------------------------------------------
doc / head(
    title("Syqlorix - The Future is Now"),
    meta(charset="UTF-8"),
    meta(name="viewport", content="width=device-width, initial-scale=1.0"),
    tailwind("demo.css", scope="demo")
) / body(
    div(
        img(
            src_="/syqlorix-logo.svg",
            alt="Syqlorix Logo",
            class_="block mx-auto max-w-[100px] mb-4"
        ),
        h1("Welcome to the Next Level", class_="text-3xl font-bold text-[#00a8cc] [text-shadow:0_0_5px_#00a8cc]"),
        p("Live reload and static file serving are fully operational."),
        p(
            "Try editing this file, or the CSS in ",
            code("static/custom.css"),
            " to see changes in real-time."
        ),
        class_="max-w-3xl mx-auto bg-[#16213e] p-8 rounded-xl shadow-2xl text-center"
    ),
    Footer(),
    script(interactive_js),
    class_="bg-[#1a1a2e] text-[#e0e0e0] font-sans leading-relaxed m-0 p-8"
)
set_scope("global")

# ---------------------------------------------------------
# 6.  EXPOSE the page on the root route so it actually renders
# ---------------------------------------------------------
@doc.route('/')
def home_page(request):
    return doc