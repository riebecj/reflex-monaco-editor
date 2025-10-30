"""Constants and configuration snippets for Monaco editor integration."""

from types import SimpleNamespace
from typing import Final


class CodeLensProviders(SimpleNamespace):
    """Constants containing JavaScript code snippets for registering CodeLens providers in Monaco editor."""

    TERRAFORM_RESOURCE_DOCS: Final = """const commandId = editor.addCommand(
        0,
        function (...args) {
            let [_, url] = args;
            window.open(url, '_blank').focus();
        },
    );
    vscode.languages.registerCodeLensProvider("terraform", {
        provideCodeLenses: async (document, _token) => {
            const providers = await getProviders();
            if (!providers) {
                return undefined;
            }
            const lines = [...Array(document.lineCount).keys()];
            const lenses = lines.filter(
                line => document.lineAt(line).text.startsWith("resource", 0)
            ).map(line => {
                let lineObj = document.lineAt(line);
                for (let key in providers) {
                    if (lineObj.text.includes(`${key}_`, 0)) {
                        const [_, resource, __] = lineObj.text.split(" ");
                        let urlResource = resource.replace(`${key}_`, "").replace(/"/g, '')
                        let url = `https://registry.terraform.io/providers/${providers[key]["owner"]}/${key}/${providers[key]["version"]}/docs/resources/${urlResource}`
                        let docString = urlResource.split("_").join(" ").toTitleCase();
                        return {
                            range: lineObj.range,
                            command: {
                                command: commandId,
                                title: docString,
                                arguments: [url],
                                tooltip: "Click to open documentation in new tab"
                            },
                        }
                    }
                }
            });
            return lenses;
        },
        resolveCodeLens: function (model, codeLens, token) {
            return codeLens;
        },
    });
    """


class FunctionConstants(SimpleNamespace):
    """Constants containing JavaScript functions and configuration snippets for Monaco editor integration."""

    CONTAINER_REF: Final = "const [container, setContainer] = useState(null);"
    WORKSPACE: Final = "const workspace = `${{{workspace_folder}}}`;"
    CODE_VALUE: Final = "const codeValue = `${{{value}}}`;"
    GET_PROVIDERS: Final = """const getProviders = async () => {
        const client = wrapper.getLanguageClient("terraform");
        const _providers = await client.sendRequest("workspace/executeCommand", {
            "command": 'terraform-ls.module.providers',
            "arguments": [`uri=${vscode.Uri.parse(workspace)}`],
        });
        let providerMap = {}
        for (let key in _providers["installed_providers"]) {
            const [registry, owner, provider] = key.split("/")
            if (registry == "registry.terraform.io") {
                providerMap[provider] = {
                    owner: owner,
                    registry: registry,
                    version: _providers["installed_providers"][key]
                }
            }
        }
        return providerMap || undefined
    };
    """
    USER_CONFIG: Final = """const userConfiguration = {{
        'workbench.colorTheme': {theme},
        'editor.guides.bracketPairsHorizontal': 'active',
        'editor.experimental.asyncTokenization': true,
    }};
    """
    REGISTER_COMMANDS: Final = """
    const registerCommand = async ({{language, type, name, method, params, restart_client}}) => {{
        const registered = await vscode.commands.getCommands(true);
        if (!registered.includes(name)) {{
            if (type === "request") {{
                vscode.commands.registerCommand(name, async () => {{
                    {on_command}
                    const languageClient = wrapper.getLanguageClient(language);
                    await languageClient.sendRequest(method, params);
                    if (restart_client) {{
                        {on_restart}
                        await wrapper.getLanguageClientWrapper(language).restartLanguageClient();
                    }};
                    {on_command_complete}
                }});
            }} else {{
                vscode.commands.registerCommand(name, async () => {{
                    {on_command}
                    const languageClient = wrapper.getLanguageClient(language);
                    await languageClient.sendNotification(method, params);
                    if (restart_client) {{
                        {on_restart}
                        await wrapper.getLanguageClientWrapper(language).restartLanguageClient();
                    }};
                    {on_command_complete}
                }});
            }}
        }}
    }};
    """


class UseEffects(SimpleNamespace):
    """Constants containing JavaScript useEffect hooks."""

    UPDATE_USER_CONFIG: Final = """useEffect(() => {
        if (wrapper.isStarted()) {
            (async() => {
                await updateUserConfiguration(JSON.stringify(userConfiguration));
            })();
        }
    }, [wrapper, userConfiguration]);
    """
    INIT_WRAPPER: Final = """useEffect(() => {{
        if (container && !wrapper.isStarted()) {{
            (async () => {{
                wrapperConfig.htmlContainer = container;
                await wrapper.init(wrapperConfig);
                {text_change_callback}
                await wrapper.start();
                const editor = wrapper.getEditor();
                {additional}
                setStarted(true);
            }})();
        }}
    }}, [wrapper, container, started]);
    """
    UPDATE_CODE: Final = """useEffect(() => {{
        (async () => {{
            await wrapper.updateCodeResources({{
                modified: {{
                    text: codeValue,
                    uri: `${{workspace}}/${{{filename}}}`,
                }}
            }});
        }})();
    }}, [codeValue]);
    """


class WrapperConfig(SimpleNamespace):
    """Configuration constants for initializing and customizing the Monaco editor wrapper."""

    BASE: Final = """const wrapperConfig = {{
        $type: 'extended',
        logLevel: LogLevel.{loglevel},
        vscodeApiConfig: {vscode_api_config},
        editorAppConfig: {editor_app_config},
        languageClientConfigs: {language_client_configs}
    }};
    """
    VSCODE_API_CONFIG: Final = """{
        viewsConfig: {
            viewServiceType: 'EditorService'
        },
        serviceOverrides: {
            ...getKeybindingsServiceOverride(),
            ...getExtensionServiceOverride(),
        },
        userConfiguration: {
            json: JSON.stringify(userConfiguration)
        },
    }"""
    EDITOR_APP_CONFIG: Final = """{{
        monacoWorkerFactory: configureDefaultWorkerFactory,
        codeResources: {{
            modified: {{
                text: codeValue,
                uri: `${{workspace}}/${{{filename}}}`,
            }}
        }}
    }}"""
