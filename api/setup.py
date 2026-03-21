import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "requirements.txt")) as f:
    requirements = f.read().splitlines()

setup(
    name="chesspunk",
    version="0.1.0",
    description="Chess Community Manager API POC",
    author="Chesspunk",
    packages=find_packages(where="python"),
    package_dir={"": "python"},
    install_requires=requirements,
    python_requires=">=3.11",
)