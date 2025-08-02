from syqlorix import *

doc = Syqlorix()

# This now correctly accepts the 'request' object, even if it's unused.
@doc.route('/')
def home(request):
    return h1("Welcome Home!")

@doc.route('/user/<username>')
def user_profile(request):
    name = request.path_params.get('username')
    return p(f"Profile of {name}")

@doc.route('/login', methods=['POST'])
def login(request):
    username = request.form_data.get('username', 'guest')
    return f"Logged in as {username}"

# This also now correctly accepts the 'request' object.
@doc.route('/old-path')
def old_path(request):
    return redirect('/user/redirected')