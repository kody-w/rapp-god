#!/usr/bin/env python3
"""
RAPP Hub CLI - Setup script for pip installation

Install with: pip install -e .
Then use: rapp-hub <command>
"""

from setuptools import setup, find_packages

setup(
    name="rapp-hub",
    version="1.0.0",
    description="CLI for RAPP Hub - AI Implementation Registry",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="RAPP Hub",
    author_email="",
    url="https://github.com/kody-w/RAPP_Hub",
    license="Apache-2.0",
    py_modules=["rapp_hub_cli"],
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "rapp-hub=rapp_hub_cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="rapp ai agents skills registry hub",
)
