from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vscode_theme_generator",
    version="0.1.0",
    author="Chris Watkins",
    author_email="chris@watkinslabs.com",
    description="Automated VS Code theme generator with AI enhancement",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/watkinslabs/vscode_theme_generator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "jinja2>=3.0",
        "click>=8.0",
        "colorama>=0.4",
        "wl_ai_manager",
        "wl_config_manager",
    ],
    entry_points={
        "console_scripts": [
            "vstg=theme_generator.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "vscode_theme_generator": ["templates/*.j2"],
    },
)