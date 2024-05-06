# AI for Software Engineering

Generate source code mutations for python using a LLM.

## Installation and Usage

Install the requirement dependencies:

```sh
# Dependencies required to run the program
pip install .
```

The program can be executed using the following command:

```sh
mutator -h
```

## Development

> This section contains tools used and the recommended project setup for development.
> It is not mandatory for running the tool.

Required tools:

- [pyright](https://github.com/microsoft/pyright) for type checking
- [ruff](https://github.com/astral-sh/ruff) for linting

Install required dependencies:

```sh
# Create a venv
python3 -m venv venv
# Activate venv
source ./venv/bin/activate
# Install package dependencies
pip install -e .
```
