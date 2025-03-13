# Setting Up a LaneSwap Development Environment

This guide will walk you through the process of setting up a development environment for working with LaneSwap. Whether you're contributing to the core LaneSwap project or building applications that integrate with LaneSwap, this guide will help you get started.

## Prerequisites

Before setting up your development environment, ensure you have the following installed:

- **Python 3.7+**: LaneSwap is built with Python and requires version 3.7 or higher.
- **Git**: For version control and cloning the repository.
- **pip**: The Python package installer (usually comes with Python).
- **virtualenv** or **conda**: For creating isolated Python environments.

## Step 1: Clone the Repository

First, clone the LaneSwap repository to your local machine:

```bash
git clone https://github.com/yourusername/laneswap.git
cd laneswap
```

## Step 2: Create a Virtual Environment

It's recommended to use a virtual environment to avoid conflicts with other Python projects:

### Using virtualenv

```bash
# Install virtualenv if you don't have it
pip install virtualenv

# Create a virtual environment
virtualenv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### Using conda

```bash
# Create a conda environment
conda create -n laneswap python=3.9

# Activate the conda environment
conda activate laneswap
```

## Step 3: Install Dependencies

Install the required dependencies:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Or install just the basic package
pip install -e .
```

## Step 4: Configure Development Settings

Create a local configuration file for development:

```bash
# Copy the example configuration
cp config/config.example.yaml config/config.dev.yaml

# Edit the configuration file with your preferred editor
# For example:
nano config/config.dev.yaml
```

Update the configuration file with your development settings, such as:

- API endpoints
- Database connection strings
- Logging settings
- Authentication settings

## Step 5: Set Up the Database

LaneSwap uses a database to store service information, messages, and other data. Set up the database:

```bash
# Run database migrations
python -m laneswap.tools.db_setup
```

## Step 6: Run Tests

Verify your setup by running the tests:

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_core.py

# Run tests with coverage
pytest --cov=laneswap
```

## Step 7: Start the Development Server

Start the LaneSwap API server in development mode:

```bash
python -m laneswap.api.server --config config/config.dev.yaml
```

The server should now be running at `http://localhost:8000` (or the port specified in your configuration).

## Development Workflow

Here's a typical workflow for developing with LaneSwap:

1. **Create a Feature Branch**: Always create a new branch for your changes.
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**: Implement your changes, following the project's coding standards.

3. **Run Tests**: Ensure your changes don't break existing functionality.
   ```bash
   pytest
   ```

4. **Format Code**: Format your code according to the project's style guide.
   ```bash
   black laneswap
   isort laneswap
   ```

5. **Run Linters**: Check for code quality issues.
   ```bash
   flake8 laneswap
   mypy laneswap
   ```

6. **Commit Changes**: Commit your changes with a descriptive message.
   ```bash
   git add .
   git commit -m "Add feature: your feature description"
   ```

7. **Push Changes**: Push your changes to the remote repository.
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a Pull Request**: Create a pull request to merge your changes into the main branch.

## Development Tools

LaneSwap development can be enhanced with the following tools:

### IDE Integration

- **VS Code**: Recommended extensions:
  - Python
  - Pylance
  - Black Formatter
  - isort
  - GitLens

- **PyCharm**: Professional edition has built-in support for most Python development tools.

### Debugging

- Use the built-in debugger in your IDE.
- For debugging the API server, you can use tools like Postman or curl to send requests.

### Documentation

- Generate documentation locally:
  ```bash
  # Install documentation dependencies
  pip install -e ".[docs]"

  # Generate documentation
  cd docs
  make html
  ```

- View the documentation in your browser by opening `docs/_build/html/index.html`.

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure your virtual environment is activated and all dependencies are installed.

2. **Database Connection Issues**: Check your database configuration and ensure the database server is running.

3. **Port Already in Use**: If the API server fails to start because the port is in use, change the port in your configuration file.

4. **Permission Issues**: Ensure you have the necessary permissions to access files and directories.

### Getting Help

If you encounter issues not covered in this guide:

- Check the [project documentation](https://laneswap.readthedocs.io/)
- Open an issue on the [GitHub repository](https://github.com/yourusername/laneswap/issues)
- Join the community chat on [Discord](https://discord.gg/laneswap)

## Next Steps

Now that you have set up your development environment, you can:

- Explore the [API documentation](../api/README.md)
- Check out the [example applications](./examples/README.md)
- Learn about the [core concepts](../core/README.md)
- Contribute to the project by fixing bugs or implementing new features

Happy coding! 