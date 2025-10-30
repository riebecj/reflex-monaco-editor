"""Base module for Monaco editor integration with Reflex."""

from typing import Literal

import reflex as rx

from monaco_editors import constants

from .models import Command, LanguageClientConfig, LanguageServerUrl, TextModel


def generate_start_options(config: LanguageClientConfig) -> str:
    """Generates the JS `onCall` start options for the language client, if commands are configured for the editor.

    Args:
        config (LanguageClientConfig): The language client config object.

    Returns:
        The configured `startOptions` for the language client as a JS object string.
    """
    if config.register_commands:
        commands = f"""Object.entries({config.register_commands}).map(async ([name, params]) => {{
            params["name"] = name
            params["language"] = '{config.language_id}'
            await registerCommand(params);
        }})"""
        return f"""startOptions: {{
            onCall: async () => {{
                {commands}
            }}
        }}
        """
    return ""


def configure_language_clients(language_clients: list[LanguageClientConfig]) -> str:
    """Configures all language clients as JS objects.

    Args:
        language_clients (list[LanguageClientConfig]): The list of lanaguge clients to configure for the editor.

    Returns:
        The language client configs JS object string.
    """
    if language_clients:
        config_string = ""
        for config in language_clients:
            config_string += f"""{config.language_id}: {{
                name: "{config.language_id} client",
                connection: {{
                    options: {{
                        $type: "WebSocketUrl",
                        url: "{config.url.formatted}",
                        {generate_start_options(config=config)}
                    }}
                }},
                clientOptions: {{
                    documentSelector: {config.document_selector or [config.language_id]},
                    workspaceFolder: {{
                        index: 0,
                        name: "workspace",
                        uri: vscode.Uri.parse(`${{workspace}}`)
                    }},
                    initializationOptions: {config.initialization_options or "{}"}
                }}
            }},
            """
        return f"""{{
            configs: {{
                {config_string}
            }}
        }}"""
    return "undefined"


class MonacoEditorReactComp(rx.Component):
    """Monaco Editor with configurable langauage clients."""

    library = "monaco-languageclient@9.11.0"
    lib_dependencies = [  # noqa: RUF012
        "monaco-editor-wrapper@6.12.0",
        "@codingame/monaco-vscode-api@20.2.1",
        "@codingame/monaco-vscode-all-language-default-extensions@20.2.1",
    ]

    def add_imports(self) -> dict:
        """Add imports."""
        return {
            "@codingame/monaco-vscode-api": rx.ImportVar("LogLevel", is_default=False, install=False),
            "monaco-editor-wrapper": [
                rx.ImportVar("MonacoEditorLanguageClientWrapper", is_default=False, install=False),
                rx.ImportVar(
                    "configureDefaultWorkerFactory",
                    is_default=False,
                    install=False,
                    package_path="/workers/workerLoaders",
                ),
            ],
            "vscode": rx.ImportVar("*", alias="vscode", is_default=True, install=False),
            "@codingame/monaco-vscode-keybindings-service-override": rx.ImportVar(
                "getKeybindingsServiceOverride", is_default=True, install=False
            ),
            "@codingame/monaco-vscode-extensions-service-override": rx.ImportVar(
                "getExtensionServiceOverride", is_default=True, install=False
            ),
            "@codingame/monaco-vscode-configuration-service-override": rx.ImportVar(
                "updateUserConfiguration", is_default=False, install=False
            ),
            "": [
                "@" + rx.asset("hashicorp-terraform.vsix", shared=True),
            ],
        }

    def add_hooks(self) -> list:
        """Add component function hooks."""
        # Internal Hooks - Does not have SELF access, so can only be static strings.
        internal = [
            rx.vars.base.Var(
                constants.FunctionConstants.CONTAINER_REF,
                _var_data=rx.vars.base.VarData(
                    imports={"react": ["useState"]}, position=rx.constants.Hooks.HookPosition.INTERNAL
                ),
            ),
            rx.vars.base.Var(
                "const [started, setStarted] = useState(false);",
                _var_data=rx.vars.base.VarData(
                    imports={"react": ["useState"]}, position=rx.constants.Hooks.HookPosition.INTERNAL
                ),
            ),
        ]

        # Pre-Trigger Hooks - mostly function `const` definitions.
        on_command = (
            f"{rx.vars.LiteralVar.create(self.event_triggers['on_command'])._js_expr}(name);"  # noqa: SLF001
            if self.event_triggers.get("on_command")
            else ""
        )
        on_command_complete = (
            f"{rx.vars.LiteralVar.create(self.event_triggers['on_command_complete'])._js_expr}(name);"  # noqa: SLF001
            if self.event_triggers.get("on_command_complete")
            else ""
        )
        on_restart = (
            f"{rx.vars.LiteralVar.create(self.event_triggers['on_restart'])._js_expr}(language);"  # noqa: SLF001
            if self.event_triggers.get("on_restart")
            else ""
        )

        if isinstance(self.workspace_folder, type(None)):  # noqa: FURB168
            self.workspace_folder = "/workspace"

        pre_triggers = [
            rx.vars.base.Var(
                pre_trigger,
                _var_data=rx.vars.base.VarData(position=rx.constants.Hooks.HookPosition.PRE_TRIGGER),
            )
            for pre_trigger in (
                constants.FunctionConstants.WORKSPACE.format(
                    workspace_folder=(
                        rx.Var.create(self.workspace_folder)
                        if isinstance(self.workspace_folder, str)
                        else self.workspace_folder
                    )
                ),
                constants.FunctionConstants.CODE_VALUE.format(
                    value=rx.Var.create(self.value) if isinstance(self.value, str) else self.value,
                ),
                constants.FunctionConstants.USER_CONFIG.format(theme=self.theme),
                constants.FunctionConstants.GET_PROVIDERS,
                constants.FunctionConstants.REGISTER_COMMANDS.format(
                    on_command=on_command, on_command_complete=on_command_complete, on_restart=on_restart
                ),
            )
        ]

        # Post-Trigger hooks - mostly `useEffect` functions to dynamically configure editor

        text_change_callback = (
            f"wrapper.registerTextChangedCallback({rx.vars.LiteralVar.create(self.event_triggers['on_change'])._js_expr})"  # noqa: SLF001
            if self.event_triggers.get("on_change")
            else ""
        )
        additional = f"{constants.CodeLensProviders.TERRAFORM_RESOURCE_DOCS}"

        post_triggers = [
            rx.vars.base.Var(
                post_trigger,
                _var_data=rx.vars.base.VarData(
                    imports={"react": ["useEffect"]}, position=rx.constants.Hooks.HookPosition.POST_TRIGGER
                ),
            )
            for post_trigger in (
                constants.WrapperConfig.BASE.format(
                    loglevel=self.loglevel,
                    vscode_api_config=constants.WrapperConfig.VSCODE_API_CONFIG,
                    editor_app_config=constants.WrapperConfig.EDITOR_APP_CONFIG.format(
                        filename=rx.Var.create(self.filename)
                    ),
                    language_client_configs=configure_language_clients(self.language_clients),
                ),
                constants.UseEffects.UPDATE_USER_CONFIG,
                constants.UseEffects.INIT_WRAPPER.format(
                    text_change_callback=text_change_callback, additional=additional
                ),
                constants.UseEffects.UPDATE_CODE.format(filename=rx.Var.create(self.filename)),
            )
        ]

        return [*internal, *pre_triggers, *post_triggers]

    def add_custom_code(self) -> list:
        """Returns custom JavaScript code snippets required for the Monaco editor component."""
        return [
            # Wrapper must be created once in the file rather than inside the
            # component function or the universe will explode.
            "const wrapper = new MonacoEditorLanguageClientWrapper();",
            # Adds a file-level String prototype function to title-case strings
            """String.prototype.toTitleCase = function () {
                return this.replace(
                    /\w\S*/g,
                    function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();}
                );
            };
            """,  # noqa: W605
        ]

    def render(self) -> dict:
        """Render the Monaco editor component as a div with appropriate props.

        Returns:
            dict: A dictionary containing the component name and filtered props.
        """
        self.ref = self._ref
        rendered = super().render()
        forbidden_props = (
            "filename",
            "theme",
            "value",
            "workspaceFolder",
            "languageClients",
            "loglevel",
            "onChange",
            "onCommand",
            "onRestart",
            "onCommandComplete",
        )
        props = [prop for prop in rendered["props"] if not any(prop.startswith(i) for i in forbidden_props)]
        return {"name": '"div"', "props": props}

    # Reference used to pass to the monaco wrapper.
    _ref = rx.Var("setContainer")

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


class Monaco(rx.ComponentNamespace):
    """Namespace for Monaco editor components and configuration."""

    __call__ = MonacoEditorReactComp.create
    language_client = LanguageClientConfig
    server_url = LanguageServerUrl
    command = Command


monaco_editor = Monaco()
