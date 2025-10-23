
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

