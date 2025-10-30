"""Models and configuration classes for Monaco editor integration with language servers."""

from typing import Annotated, Any, Literal, TypedDict

import reflex as rx
from pydantic import BaseModel, Field, PlainValidator


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
    restart_client: bool = False


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

    @property
    def formatted(self) -> str:
        """Return the formatted language server URL as a string."""
        schema = "wss" if self.secured else "ws"
        path = self.path
        if path and not path.startswith("/"):
            path = f"/{self.path}"
        return f"{schema}://{self.host}:{self.port}{path}"


def _var_validator(value: rx.Var) -> str:
    if not isinstance(value, rx.Var):
        msg = f"Value {value} must be passed as an rx.Var"
        raise TypeError(msg)
    return str(value)


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


class TextModel(TypedDict):
    """The response model sent by the editor's `onChange`.

    For standard (non-diff) editors, the updated code will be in the `modified` attribute.
    """

    modified: str
    original: str


__all__ = (
    "Command",
    "LanguageClientConfig",
    "LanguageServerUrl",
    "TextModel",
)
