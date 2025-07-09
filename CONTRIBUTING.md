# Contributing to Syqlorix

We welcome contributions from the community! By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Bug Reports & Feature Requests

If you find a bug or have an idea for a new feature, please open an issue on our [GitHub Issue Tracker](https://github.com/Syqlorix/Syqlorix/issues). Please check to see if a similar issue already exists before creating a new one.

### Code Contributions (Pull Requests)

We actively welcome your pull requests.

1.  **Fork the repository.**
2.  **Clone your forked repository locally:**
    ```bash
    git clone https://github.com/your-username/Syqlorix.git
    cd Syqlorix
    ```
3.  **Create a new branch** for your feature or bug fix:
    *   For features: `git checkout -b feature/your-feature-name`
    *   For bug fixes: `git checkout -b fix/bug-description`

4.  **Set up your development environment:**
    It's recommended to use a virtual environment.
    ```bash
    # Create and activate a virtual environment
    python3 -m venv venv
    source venv/bin/activate

    # Install the package in editable mode with all dependencies
    pip install -e .
    ```

5.  **Make your changes** to the source code in the `syqlorix/` directory.

6.  **Commit your changes** with a clear and concise commit message.
    ```bash
    git commit -m "feat: Add a new component for alerts"
    git commit -m "fix: Correctly handle content-type for JSON responses"
    ```
    (Using a convention like this helps keep the project history clean.)

7.  **Push your branch** to your forked repository:
    ```bash
    git push origin feature/your-feature-name
    ```
8.  **Open a Pull Request** against the `main` branch of the original Syqlorix repository. Provide a clear description of the changes you have made.

## Questions?

If you have any questions about contributing, feel free to open an issue. Thank you for your interest in making Syqlorix better!