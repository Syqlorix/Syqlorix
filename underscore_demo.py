
from syqlorix.templating import *
from syqlorix import Syqlorix, head, body, title

doc = Syqlorix(
    head(
        title("Underscore Demo")
    ),
    body(
        _("div", class_="container")(
            _("h1")("This is a demo of the underscore function"),
            _("p")("You can use it to create any HTML element.")
        )
    )
)

@doc.route('/')
def home(request):
    return doc

if __name__ == "__main__":
    doc.run(file_path=__file__)
