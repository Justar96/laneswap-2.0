#!/usr/bin/env python
from setuptools import setup, find_packages

# Read the contents of README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="laneswap",
    version="2.0.0",
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
        "keyboard>=0.13.5",  # For keyboard event handling in terminal monitor
        "python-dotenv>=1.0.0",  # For loading .env files
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
        ]
    },
    # console_scripts entry updated: only terminal dashboard
    entry_points={
        "console_scripts": [
            "laneswap=laneswap.cli.terminal_monitor:main",
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