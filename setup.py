#!/usr/bin/env python
from setuptools import setup, find_packages

# Read the contents of README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="laneswap",
    version="0.1.2",
    description="A heartbeat monitoring system for distributed services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="LaneSwap Team",
    author_email="laneswap@example.com",
    url="https://github.com/laneswap/laneswap",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.95.0",
        "uvicorn>=0.21.0",
        "pydantic>=2.0.0",
        "motor>=3.1.0",
        "aiohttp>=3.8.0",
        "tabulate>=0.9.0",
        "requests>=2.28.0",  # For web monitor HTTP requests
        "python-dateutil>=2.8.2",  # For date handling in web monitor
        "keyboard>=0.13.5",  # For keyboard event handling in terminal monitor
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
        ],
        "all": [
            "fastapi>=0.95.0",
            "uvicorn>=0.21.0",
            "pydantic>=2.0.0",
            "motor>=3.1.0",
            "aiohttp>=3.8.0",
            "tabulate>=0.9.0",
            "requests>=2.28.0",
            "python-dateutil>=2.8.2",
            "keyboard>=0.13.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "laneswap=laneswap.cli.commands:main",
            "laneswap-web=laneswap.examples.web_monitor.launch:main",
            "laneswap-term=laneswap.cli.terminal_monitor:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Monitoring",
    ],
    project_urls={
        "Documentation": "https://github.com/laneswap/laneswap#readme",
        "Issues": "https://github.com/laneswap/laneswap/issues",
    },
)