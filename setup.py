from setuptools import setup, find_packages
try:
    import tomllib
except ImportError:
    import tomli as tomllib

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("pyproject.toml", "rb") as f:
    pyproject = tomllib.load(f)
    version = pyproject["project"]["version"]

setup(
    name="tonic-fabricate",
    version=version,
    author="Fabricate Tools",
    description="The official Fabricate client for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fabricate-tools/client-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "python-dotenv>=0.19.0",
        ],
    },
) 