# Generative AI prototypes

Collection of generative AI prototypes, mainly using LLMs.

- [Generative AI prototypes](#generative-ai-prototypes)
  - [Setup](#setup)
    - [Generic setup for working with `pyenv` and `poetry`](#generic-setup-for-working-with-pyenv-and-poetry)
    - [How to install this project](#how-to-install-this-project)
  - [TODO](#todo)

## Setup


### Generic setup for working with `pyenv` and `poetry`
Assuming you work on a Mac, you can use the following commands to setup your environment from scratch with `pyenv` and `poetry`. Please deactivate any anaconda environments you might have activated before the setup.

1. [Install brew](https://brew.sh/). Confirm you've installed it correctly by running:

```bash
brew --version
``````

2. Install `pyenv`
```bash
brew install pyenv
```

At the end of the installation, `pyenv` will advise you to add the following lines to your `.bash_profile` (or `.zshrc` if you use `zsh`). Do that, save the file and restart your terminal.

```bash
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

3. Install Python

Install/update a few dependencies

```
brew install openssl readline sqlite3 xz zlib
```

Install Python 3.9.17

```bash
pyenv install 3.9.17
```

Confirm you've installed it correctly by running:

```bash
pyenv versions
```

Run the following commands to set the global Python version to 3.9.17.

```bash
pyenv global 3.9.17
```

Close and reopen your terminal so that the changed take effect.

4. Install `poetry`

You can use the [official installer](https://python-poetry.org/docs/master/#installing-with-the-official-installer):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Add poetry to your PATH:

```bash
export PATH="/Users/<MYUSERNAME>/.local/bin:$PATH"
```

Confirm your poetry installation:

```bash
poetry --version
```

### How to install this project
Assuming you have installed `pyenv` and `poetry` as described above, you can now install this project:

```bash
make init
```

## TODO

- Write setup instructions
