from setuptools import setup

setup(
    name="categoraize-docs-plugins",
    version="0.1.0",
    py_modules=["mkdocs_plugins"],
    entry_points={
        "mkdocs.plugins": [
            "escape-macros = mkdocs_plugins:EscapeMacrosInCodePlugin",
        ],
    },
)
