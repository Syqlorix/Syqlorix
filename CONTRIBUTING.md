# Contributing to Syqlorix

We welcome contributions from the community! By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Bug Reports

If you find a bug, please open an issue on our [GitHub Issue Tracker](https://github.com/Syqlorix/Syqlorix/issues).

When reporting a bug, please include:
*   A clear and concise description of the bug.
*   Steps to reproduce the behavior.
*   Expected behavior.
*   Actual behavior.
*   Screenshots or error messages if applicable.
*   Your Python version and Syqlorix version.

### Feature Requests

We love new ideas! If you have a feature in mind, please open an issue on our [GitHub Issue Tracker](https://github.com/Syqlorix/Syqlorix/issues).

When suggesting a feature, please describe:
*   What problem does this feature solve?
*   How would it be used?
*   Any alternative solutions you've considered.

### Code Contributions (Pull Requests)

We appreciate code contributions that help make Syqlorix better!

1.  **Fork the repository.**
2.  **Clone your forked repository locally:**
    ```bash
    git clone https://github.com/your-username/Syqlorix.git
    cd Syqlorix
    ```
3.  **Create a new branch** for your feature or bug fix:
    ```bash
    git checkout -b feature/your-feature-name-here
    ```
    (For bug fixes, use  or .)
4.  **Install development dependencies:**
    ```bash
    pip install -e .[dev]
  Installing build dependencies: started
  Installing build dependencies: finished with status 'done'
  Checking if build backend supports build_editable: started
  Checking if build backend supports build_editable: finished with status 'done'
  Getting requirements to build editable: started
  Getting requirements to build editable: finished with status 'done'
  Preparing editable metadata (pyproject.toml): started
  Preparing editable metadata (pyproject.toml): finished with status 'done'
Building wheels for collected packages: syqlorix
  Building editable for syqlorix (pyproject.toml): started
  Building editable for syqlorix (pyproject.toml): finished with status 'done'
  Created wheel for syqlorix: filename=syqlorix-0.0.2.5-0.editable-py3-none-any.whl size=6820 sha256=55de61840ee6e724a109f317808cf0202d6645991840f98714c201bdc5661847
  Stored in directory: /tmp/pip-ephem-wheel-cache-tgkybufs/wheels/63/c4/4b/705019e491ee601ccf51b70849f9c17c35d23d641be7f6590b
Successfully built syqlorix
Installing collected packages: syqlorix
  Attempting uninstall: syqlorix
    Found existing installation: syqlorix 0.0.2.4
    Uninstalling syqlorix-0.0.2.4:
      Successfully uninstalled syqlorix-0.0.2.4
Successfully installed syqlorix-0.0.2.5
    ```
5.  **Make your changes.**
6.  **Write tests** for your changes. Ensure existing tests still pass.
    ```bash
    pytest tests/
    ```
7.  **Format your code** (e.g., with Black, Flake8 - if you configure them later).
8.  **Commit your changes** with a clear and concise commit message.
    ```bash
    git commit -m "feat: Add new feature"
    ```
    (See [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for best practices.)
9.  **Push your branch** to your forked repository:
    ```bash
    git push origin feature/your-feature-name-here
    ```
10. **Open a Pull Request** against the  branch of the [original Syqlorix repository](https://github.com/Syqlorix/Syqlorix).

## Questions?

If you have any questions about contributing, feel free to open an issue or reach out to the maintainers.
