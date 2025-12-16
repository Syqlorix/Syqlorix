
import os
import shutil
from click.testing import CliRunner
from syqlorix.cli import main

def test_init_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init', 'test_app.py'])
        assert result.exit_code == 0
        assert 'Created a new Syqlorix project' in result.output
        assert os.path.exists('test_app.py')

def test_init_command_with_trailing_slash():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.makedirs('my_project_dir')
        result = runner.invoke(main, ['init', 'my_project_dir/'])
        assert result.exit_code == 0
        assert 'Created a new Syqlorix project in my_project_dir/app.py' in result.output
        assert os.path.exists('my_project_dir/app.py')

def test_init_command_creates_file_in_current_dir_by_default():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0
        assert 'Created a new Syqlorix project in app.py' in result.output
        assert os.path.exists('app.py')

def test_init_command_with_path_no_trailing_slash():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # This should create 'my_app.py' directly, not 'my_app/app.py'
        result = runner.invoke(main, ['init', 'my_app'])
        assert result.exit_code == 0
        assert 'Created a new Syqlorix project in my_app.py' in result.output
        assert os.path.exists('my_app.py')
        assert not os.path.exists('my_app/app.py') # Ensure it doesn't create a directory and then app.py

def test_run_command():
    runner = CliRunner()
    # This is a bit tricky to test as it starts a server.
    # I will just check if the command can be invoked without errors.
    result = runner.invoke(main, ['run', '--help'])
    assert result.exit_code == 0
    assert 'Usage: main run [OPTIONS] FILE' in result.output

def test_build_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('app.py', 'w') as f:
            f.write('from syqlorix import Syqlorix, h1\ndoc = Syqlorix(h1("Hello"))\n@doc.route("/")\ndef home(req):\n    return doc')
        
        result = runner.invoke(main, ['build', 'app.py'])
        assert result.exit_code == 0
        assert 'Build successful' in result.output
        assert os.path.exists('dist/index.html')

