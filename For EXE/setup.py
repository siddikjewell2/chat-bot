# setup.py - For PyInstaller configuration
import sys
from setuptools import setup

setup(
    name="RootTOP_Assistant",
    version="1.0.0",
    py_modules=["root_top_assistant"],
    install_requires=[
        "llama-cpp-python==0.2.83",
        "Pillow>=10.0.0",
        "psutil>=5.9.0",
    ],
)