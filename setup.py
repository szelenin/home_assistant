#!/usr/bin/env python3
"""
Setup script for Home Assistant package
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements(filename):
    with open(filename, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="home-assistant",
    version="1.0.0",
    author="Home Assistant Team",
    author_email="team@homeassistant.com",
    description="Voice-controlled home automation system",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/szelenin/home_assistant",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Home Automation",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "full": read_requirements("requirements-full.txt"),
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "home-assistant=home_assistant.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "home_assistant": ["*.yaml", "*.yml"],
    },
    keywords="home automation voice speech recognition tts",
    project_urls={
        "Bug Reports": "https://github.com/szelenin/home_assistant/issues",
        "Source": "https://github.com/szelenin/home_assistant",
        "Documentation": "https://github.com/szelenin/home_assistant#readme",
    },
) 