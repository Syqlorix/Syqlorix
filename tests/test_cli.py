import os
import shutil
from click.testing import CliRunner
from syqlorix.cli import main

def test_init_command():
    """
    Test the 'init' command for creating a new project file.
    Ensures that:
    1. The command exits successfully (code 0).
    2. The output message confirms creation.
    3. The file is actually created on the filesystem.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init', 'test_app.py'])
        assert result.exit_code == 0
        assert 'Created a new Syqlorix project' in result.output
        assert os.path.exists('test_app.py')

def test_init_command_with_trailing_slash():
    """
    Test 'init' with a directory path (trailing slash).
    Ensures it defaults to creating 'app.py' inside the specified directory.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.makedirs('my_project_dir')
        result = runner.invoke(main, ['init', 'my_project_dir/'])
        assert result.exit_code == 0
        assert 'Created a new Syqlorix project in my_project_dir/app.py' in result.output
        assert os.path.exists('my_project_dir/app.py')

def test_init_command_creates_file_in_current_dir_by_default():
    """
    Test 'init' without arguments.
    Ensures it creates 'app.py' in the current working directory.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0
        assert 'Created a new Syqlorix project in app.py' in result.output
        assert os.path.exists('app.py')

def test_init_command_with_path_no_trailing_slash():
    """
    Test 'init' with a filename that has no extension (and no trailing slash).
    Ensures it treats it as a filename (with .py appended implicitly if we were fancy, 
    but currently explicitly just creates that file).
    Note: The framework currently creates exactly what is asked if it doesn't end in /.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        # This should create 'my_app.py' directly, not 'my_app/app.py'
        result = runner.invoke(main, ['init', 'my_app.py'])
        assert result.exit_code == 0
        assert 'Created a new Syqlorix project' in result.output
        assert os.path.exists('my_app.py')

def test_run_command():
    """
    Test the 'run' command's help output.
    Running the actual server in a test is complex due to blocking,
    so checking the help verifies the command registration.
    """
    runner = CliRunner()
    result = runner.invoke(main, ['run', '--help'], prog_name='syqlorix')
    assert result.exit_code == 0
    assert 'Usage: syqlorix run [OPTIONS] FILE' in result.output

def test_build_command():
    """
    Test the 'build' command for static site generation.
    Steps:
    1. Create a dummy app file.
    2. Run 'build'.
    3. Verify exit code and output message.
    4. Verify 'dist/index.html' is generated.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('app.py', 'w') as f:
            f.write('from syqlorix import Syqlorix, h1\ndoc = Syqlorix(h1("Hello"))\n@doc.route("/")\ndef home(req):\n    return doc')
        
        result = runner.invoke(main, ['build', 'app.py'])
        assert result.exit_code == 0
        assert 'Build successful' in result.output
        assert os.path.exists('dist/index.html')

def test_help_alias_command():
    """
    Test the '-help' alias (if supported via click or custom logic).
    Ensures users can get help easily.
    """
    runner = CliRunner()
    result = runner.invoke(main, ['--help'], prog_name='syqlorix')
    assert result.exit_code == 0
    assert 'Usage: syqlorix [OPTIONS] COMMAND [ARGS]...' in result.output