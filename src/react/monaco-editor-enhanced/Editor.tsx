import * as monaco from "monaco-editor";
import * as vscode from "vscode"; // pants: no-infer-dep
import { loader, Editor, Monaco } from "@monaco-editor/react";
import React from "react";
import { language, conf } from "./hcl.tsx";
import {
  CloseAction,
  ErrorAction,
  MessageTransports,
  ExecuteCommandParams,
  ExecuteCommandRequest,
  State,
} from "vscode-languageclient"; // pants: no-infer-dep
import { MonacoLanguageClient } from "monaco-languageclient";
import {
  toSocket,
  WebSocketMessageReader,
  WebSocketMessageWriter,
} from "vscode-ws-jsonrpc";
import initializeTerraformFeatures from "./terraformFeatures.tsx";
import normalizeUrl from "normalize-url";

type ClientAction = {
  name: string;
  order?: number;
  groupId?: string;
  keyBindings?: monaco.KeyCode[];
  command: string;
  arguments?: string[];
  params?: object;
  reloadClient?: boolean;
};

type ClientOptions = {
  documentSelector?: string[];
  initializationOptions?: any | (() => any);
  workspaceFolder?: string;
  languageServerUrl?: string;
  actions?: ClientAction[];
};

interface EnhancedEditorProps {
  // language client options
  clientOptions?: ClientOptions;
  // React Monaco Editor props we expose
  defaultValue?: string;
  defaultLanguage?: string;
  defaultPath?: string;
  value?: string;
  language?: string;
  path?: string;
  theme?: string;
  line?: number;
  width?: number | string;
  height?: number | string;
  className?: string;
  wrapperProps?: object;
  onChange?: (value: string) => void;
  onClientStateChange?: (state: string) => void;
  onClientClose?: () => void;
  onError?: (error: Error) => void;
  onValidate?: (markers: monaco.editor.IMarker[]) => void;
}

interface LanguageServerConnection {
  client: MonacoLanguageClient;
  reader: WebSocketMessageReader;
}

const registerUncommonLanguages = (_monaco: typeof monaco): void => {
  // Register Terraform for terraform-ls
  _monaco.languages.register({
    id: "terraform",
    extensions: [".tf", ".tfvars"],
    aliases: ["Terraform", "terraform", "tf", "HCL", "hcl"],
  });
  _monaco.languages.setLanguageConfiguration("terraform", conf);
  _monaco.languages.setMonarchTokensProvider("terraform", language);
};

window.MonacoEnvironment = {
  getWorker(_moduleId, label) {
    switch (label) {
      case "javascript":
      case "typescript":
        return new Worker(
          new URL(
            "monaco-editor/esm/vs/language/typescript/ts.worker",
            import.meta.url,
          ),
        );
      default:
        return new Worker(
          new URL("monaco-editor/esm/vs/editor/editor.worker", import.meta.url),
        );
    }
  },
};
loader.config({ monaco });
loader.init().then((monaco) => {
  registerUncommonLanguages(monaco);
});

function EnhancedEditor(props: EnhancedEditorProps): React.JSX.Element {
  const [connection, setConnection] = React.useState<
    LanguageServerConnection | undefined
  >(undefined);
  const [editor, setEditor] = React.useState<
    monaco.editor.IStandaloneCodeEditor | undefined
  >(undefined);
  const [registered, setRegistered] = React.useState<boolean>(false);
  const clientOptions = props.clientOptions || undefined;

  React.useEffect(() => {
    if (editor && connection && !registered) {
      registerActions(editor, connection);
      setRegistered(true);
    }
  }, [editor, connection, registered]);

  React.useEffect(() => {
    if (editor && clientOptions?.languageServerUrl && !connection) {
      connectToLanguageServer()
        .then((conn) => {
          setConnection(conn);
        })
        .catch((error) => {
          throw error;
        });
    }
  }, [editor, clientOptions, connection]);

  const registerActions = (
    editor: monaco.editor.IStandaloneCodeEditor,
    connection: LanguageServerConnection,
  ) => {
    if (clientOptions?.actions) {
      for (const action of clientOptions.actions) {
        const actionId = action.name.replace(/\s+/g, "-").toLowerCase();
        editor.addAction({
          id: actionId,
          label: action.name,
          keybindings: action.keyBindings || undefined,
          contextMenuGroupId: action.groupId || "default",
          contextMenuOrder: action.order || 1,
          run: async () => {
            if (action.command.startsWith("terraform-ls.")) {
              await execWorkspaceLSCommand(
                connection,
                action.command,
                action.arguments,
              );
            } else {
              await connection.client.sendNotification(
                action.command,
                action.params || {},
              );
            }
            if (action.reloadClient) {
              editor.setModel(editor.getModel());
            }
          },
        });
      }
    }
  };

  const createLanguageClient = async (
    transports: MessageTransports,
  ): Promise<MonacoLanguageClient> => {
    const options = {
      initializationOptions: clientOptions?.initializationOptions,
      documentSelector: clientOptions?.documentSelector,
      errorHandler: {
        error: () => ({ action: ErrorAction.Shutdown }),
        closed: () => ({ action: CloseAction.DoNotRestart }),
      },
      workspaceFolder: clientOptions?.workspaceFolder
        ? {
            uri: vscode.Uri.parse(`file://${clientOptions?.workspaceFolder}`),
            name: "Workspace",
            index: 0,
          }
        : undefined,
    };

    return new MonacoLanguageClient({
      name: `${crypto.randomUUID()} client`,
      clientOptions: options,
      connectionProvider: {
        get: () => Promise.resolve(transports),
      },
    });
  };

  const connectToLanguageServer = (): Promise<{
    client: MonacoLanguageClient;
    reader: WebSocketMessageReader;
  }> => {
    return new Promise((resolve, reject) => {
      // Handle the WebSocket opening event
      const websocket = new WebSocket(
        normalizeUrl(clientOptions.languageServerUrl),
      );
      websocket.onopen = async () => {
        const socket = toSocket(websocket);
        const reader = new WebSocketMessageReader(socket);
        const writer = new WebSocketMessageWriter(socket);

        try {
          const languageClient = await createLanguageClient({ reader, writer });
          languageClient.onDidChangeState((event) =>
            props.onClientStateChange?.(State[event.newState]),
          );
          registerFeatures(languageClient);
          // Start the language client
          await languageClient.start();
          websocket.onerror = (error) => {
            reject(error);
          };
          // return the client
          resolve({ client: languageClient, reader: reader });
        } catch (error) {
          reject(error);
        }
      };
    });
  };

  const registerFeatures = (client: MonacoLanguageClient): void => {
    if (props.language === "terraform") {
      // Register any Terraform specific features here
      for (const feature of initializeTerraformFeatures(client)) {
        client.registerFeature(feature);
      }
    }
  };

  const execWorkspaceLSCommand = async (
    conn: LanguageServerConnection,
    command: string,
    args?: any[],
  ): Promise<void> => {
    const params: ExecuteCommandParams = {
      command: command,
      arguments: args || undefined,
    };
    await conn.client.sendRequest<ExecuteCommandParams, any, void>(
      ExecuteCommandRequest.type,
      params,
    );
  };

  return (
    <Editor
      language={props.language}
      defaultLanguage={props.defaultLanguage}
      value={props.value}
      defaultPath={props.defaultPath}
      path={props.path}
      theme={props.theme}
      line={props.line}
      width={props.width}
      height={props.height}
      className={props.className}
      wrapperProps={props.wrapperProps}
      onMount={(
        editor: monaco.editor.IStandaloneCodeEditor,
        _monaco: Monaco,
      ) => {
        setEditor(editor);
      }}
      onChange={(value: string | undefined) => {
        if (value && props.onChange) {
          props.onChange(value);
        }
      }}
    />
  );
}

export default EnhancedEditor;
