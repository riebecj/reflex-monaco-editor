# reflex-monaco-editor

[![PyPI Version](https://img.shields.io/pypi/v/reflex-monaco-editor)](https://pypi.org/project/reflex-monaco-editor/)
[![Python Versions](https://img.shields.io/pypi/pyversions/reflex-monaco-editor)](https://pypi.org/project/reflex-monaco-editor/)
[![License](https://img.shields.io/github/license/riebecj/reflex-monaco-editor)](https://github.com/riebecj/reflex-monaco-editor/blob/main/LICENSE)

## Overview

`reflex-monaco-editor` provides integration of the Monaco Editor with support for Terraform syntax highlighting and language features via `terraform-ls`. This project enables embedding a powerful code editor in Python web applications, with extensible language support.

> NOTE: This has not been fully tested in a compiled Reflex app for production. If there are any bugs or issues, please report them.

---

## Table of Contents

- [Getting Started](#getting-started)
  - [Demo](#demo)
- [Built-In Language Clients](#available-built-in-language-clients)
- [API Documentation](#api-documentation)
- [Contributing](#how-to-contribute)

---

## Getting Started

### 1. Installation

Install the package

```bash
pip install reflex-monaco-editor
```

### 2. Apply Config

If you're not using any other custom Vite config, you can do this in your `rxconfig.py`:

```python
import reflex as rx
from vite_config_plugin import ViteConfigPlugin
from monaco_editors.config import MonacoEditorsReflexConfig

config = rx.Config(
    ...
    plugins=[
        ...
        ViteConfigPlugin(
            MonacoEditorsReflexConfig.get_vite_config(),
            imports=MonacoEditorsReflexConfig.get_imports(),
            dependencies=MonacoEditorsReflexConfig.get_dependencies(),
        )
    ]
)
```

If you need other custom configurations, do this instead:

```python
import reflex as rx
from vite_config_plugin import ViteConfigPlugin
from monaco_editors.config import MonacoEditorsReflexConfig

config = rx.Config(
    ...
    plugins=[
        ...
        ViteConfigPlugin(
            ..., # your custom vite config for your project
            imports=[
                ..., # your other custom imports
                *MonacoEditorsReflexConfig.get_imports(),
            ],
            dependencies=[
                ..., # your other frontend dependencies
                *MonacoEditorsReflexConfig.get_dependencies()
            ],
            extra_configs=[
                ..., # Any other Vite configs you're merging in your project config
                MonacoEditorsReflexConfig.get_vite_config()
            ]
        )
    ]
)
```

The imports, dependencies, and config ensure that Vite handles the necessary libraries correctly.

### 3. Creating a Basic Editor

The minimum required keywork argument is `filename`.

```python
import reflex as rx
from reflex_monaco_editor import monaco_editor

@rx.page("/")
def home() -> rx.Component:
    return rx.flex(
        monaco_editor(filename="demo.txt")
    )
```

> For advanced configuration, see the [API documentation](#api-documentation).

---

## Demo

To run the demo, just clone the repository and either do:

```
pants lock
pants run demo
```

If you have `pants` installed, or:

```
pip install .
reflex run
```

---

## Available Built-In Language Clients

### Terraform

To provide Terraform/HCL language client integration, a VSIX file is included as a shared `rx.asset()` to the editor component and imported by it, and the
`@codingame/monaco-vscode-rollup-vsix-plugin` vite plugin handles the asset loading. This provides the editor with syntax highlighting and other VSCode
editor features, but it does not work with web workers (blame HashiCorp). To get around this, there's a Reflex app lifespan task called `start_terraform_ls`
that you can import and pass to your app on start-up. This will download [lsp-ws-proxy](https://github.com/qualified/lsp-ws-proxy) and
[terraform-ls](https://github.com/hashicorp/terraform-ls) binaries from GitHub to your `.web/backend/bin` directory.

#### Lifespan Task

It's not ***required** to use this lifespan task. You can download them yourself, but you will need to ensure they're listening on your specified port
before starting the editor or the language client won't connect.

To use the lifespan task just import and register like this:

```python
from monaco_editors import start_terraform_ls

app = rx.App()
app.register_lifespan_task(start_terraform_ls)
```

#### Editor + Language Client Config

Assuming your `terraform-ls` server is listening on port 9999 on the localhost, here's how you'd need to configure the editor at a minimum:

```python
from monaco_editors import monaco_editor

def editor():
    return monaco_editor(
        filename="main.tf",  # needs to be a standard Terraform/HCL file type.
        language_clients=[
            monaco_editor.language_client(
                language_id="terraform",  # Must be 'terraform'
                url=monaco_editor.server_url(host="localhost", port=9999, secured=False), # configure as needed. The default for `secured` is `True`.
            ),
        ],
    )
```

> See API Documentation for more information on available configurations.

---

# API Documentation

## Monaco Editor

The `monaco_editor` has the available configuration:

```python
class MonacoEditorReactComp(rx.Component):
    ...
    ###### Required Attributes ######
    # The name of the 'file' to open in the editor.
    filename: str | rx.Var[str]

    ###### Optional Attributes ######
    # Theme configured based on Reflex color mode condition.
    theme = rx.color_mode_cond(dark="Default Dark Modern", light="Default Light Modern")
    # The editor code content of the 'file'
    value: str | rx.Var[str] = ""
    # The name of the worspace/folder/directory of the 'file'.
    workspace_folder: str | rx.Var[str] | None = None
    # Any configured language clients for the editor.
    language_clients: list[LanguageClientConfig] = []  # noqa: RUF012
    # The monaco editor log level (logs to browser console).
    loglevel: Literal["Off", "Trace", "Debug", "Info", "Warning", "Error"] = "Info"
    # The HTML class of the editor window.
    class_name: str = "w-full h-full"

    ###### Configurable Event Handlers ######
    # Fires on editor code content change. Returns the contant as a TextModel object.
    on_change: rx.EventHandler[rx.event.passthrough_event_spec(TextModel)]
    # Fires when an user-registered editor command executes. Returns the name of the registered command.
    on_command: rx.EventHandler[rx.event.passthrough_event_spec(str)]
    # Fires when a language client is restarted. Returns the name of the editor langauge client that restarts.
    on_restart: rx.EventHandler[rx.event.passthrough_event_spec(str)]
    # Fires when an user-registered editor command finishes. Returns the name of the registered command.
    on_command_complete: rx.EventHandler[rx.event.passthrough_event_spec(str)]
```


## Language Client Configs

The `LanguageClientConfig` is a Pydantic model that provides a configured language client to the monaco editor.

```python
class LanguageClientConfig(BaseModel):
    """The Monaco Language Client Config.

    Params:
        language_id (str): The language ID registered with the editor.
        url (LanguageServerUrl): The langauge server URL object.
        register_commands (dict[str, Command]): The mapping of command names and configs to register wuth the editor.
        document_selector (list[str | dict[str, str]] | None): The optional document selector for the LSP.
        initialization_options (dict): The language-specific LSP opts to provide the language server upon connection.
    """
    language_id: str
    url: LanguageServerUrl
    register_commands: Annotated[str, PlainValidator(_var_validator), Field(default="")]
    document_selector: Annotated[list[str | dict[str, str]] | None, Field(default=None)]
    initialization_options: Annotated[str, PlainValidator(_var_validator), Field(default="")]
```

While the `register_commands` and `initialization_options` say the type should be a `str`, it actually accepts an `rx.Var[dict[str, Command]]` and raises a `TypeError`
if the value isn't a Reflex var. This is by design.

> See more about [`register_commands`](#registered-editor-command). The `initialization_options` are LSP or Language Server specific.

## Registered Editor Command

The `Command` Pydantic model helps to register a command between the Monaco editor and the language server, allowing the editor to perform actions
and tasks avaiable to your language server. 

```python
class Command(BaseModel):
    """Language Servers Commands.

    Used to register Monaco editor commands with the language client.

    Params:
        type (Literal["notification", "request"]): The type of LSP command to execute.
        method (str): The LSP method to send (based on the specific language server).
        params (dict[str, Any]): The parameters to send.
        restart_client: (bool): If the editor's language client should be restarted after command completion.
    """
    type: Literal["notification", "request"]
    method: str
    params: dict[str, Any]
    restart_client: Annotated[bool, Field(default=False)]
```

### Example:

How this is configured will be dependant on your LSP's documentation. I'll use [`terraform.init`](https://github.com/hashicorp/terraform-ls/blob/main/docs/commands.md#terraforminit)
as an example. 

More often than not, the `type` of request commands use are **request**. This is true for `terraform-ls`. The `method` is the LSP method, in this case it's `workspace/executeCommand`. Based on the [documentation](https://github.com/hashicorp/terraform-ls/blob/main/docs/commands.md#arguments) for `terraform-ls`, we know the `params` it expects is:

```
{
	"command": "command-name",
	"arguments": [ "key=value" ]
}
```

And `terraform.init` expects an argument of `uri` set to the directory in which to run `init`; making it `[ "uri=file:///path/to/my/dir" ]`. And if a restart of the client is
necessary or benficial, you can set `restart_client` to `True`. This would be the entire `Command` config you'd add to your dict of commands looks like this:

```python
"terraform.init": Command(
    type="request",
    method="workspace/executeCommand",
    params={
        "command": "terraform-ls.terraform.init",
        "arguments": ["uri=file:///path/to/my/dir"]
    },
    restart_client=True
)
```

## Language Server URL

The only currently available method for connecting to a language server is via websocket URL. The `LanguageServerUrl` model
helps specify and format the URL correctly.

```python
class LanguageServerUrl(BaseModel):
    """The language server URL.

    Params:
        host (str): The hostname with a language server websocket.
        port (int): The host's websocket port number.
        secured (bool): Whether the connection is secure (use `wss` instead of `ws`)
        path (str): Additional path URI for the langauge server.
    """
    host: str
    port: int
    secured: Annotated[bool, Field(default=True)]
    path: Annotated[str, Field(default="")]
```

## Namespace

To make it easier (and less imports), all of the major moving parts are grouped into an `rx.ComponentNamespace` for convenient configuration and importing.

```python
class Monaco(rx.ComponentNamespace):
    """Namespace for Monaco editor components and configuration."""

    __call__ = MonacoEditorReactComp.create
    language_client = LanguageClientConfig
    server_url = LanguageServerUrl
    command = Command


monaco_editor = Monaco()
```

So, in your code, all you need to do is:

```python
from monaco_editors import monaco_editor

def my_editor():
    return monaco_editor(
        filename="foo.txt",
        language_clients=[
            monaco_editor.language_client(
                language_id="my-lang",
                url=monaco_editor.server_url(...),
                register_commands={
                    "my-lsp.command": monaco_editor.command(...),
                    ... # other commands
                },
                ... # other options
            )
        ],
        ... # other settings or event handlers
    )
```

## How to Contribute

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Prereuisites

This repository builds with [pantsbuild](https://www.pantsbuild.org/) which requires Linux or Mac. If you're on a Windows, you can use WSL.
Install `pants` using the [provided instructions](https://www.pantsbuild.org/stable/docs/getting-started/installing-pants) for your OS.

### Development Setup

1. Fork the repository and clone.
2. Install dependencies: `pants lock`
3. *Optionally* export a venv: `pants venv`. Creates `dist/export/python/virtualenvs/python-default/3.X.Y`.
4. If you run `pants venv` you can update your IDE interpreter using the available venv.

Now you can make code changes as necessary.

### Submitting a PR

Before you submit a PR, ensure the following run without errors:

1. Run tests: `pants test all`
2. Format code: `pants fmt all`
3. Lint code: `pants lint all`

---

## License

See [LICENSE](LICENSE) for details.
