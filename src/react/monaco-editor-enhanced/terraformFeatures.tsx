import * as vscode from "vscode";  // pants: no-infer-dep
import {
  ClientCapabilities,
  FeatureState,
  ReferencesRequest,
  ServerCapabilities,
  StaticFeature,
} from "vscode-languageclient";  // pants: no-infer-dep
import { MonacoLanguageClient } from "monaco-languageclient";
import { WorkspaceFoldersFeature } from "vscode-languageclient/lib/common/workspaceFolder.js";  // pants: no-infer-dep

interface Position {
  line: number;
  character: number;
}

interface RefContext {
  includeDeclaration: boolean;
}

const CLIENT_CMD_ID = "client.showReferences";
const VSCODE_SHOW_REFERENCES = "editor.action.showReferences";

class ShowReferencesFeature implements StaticFeature {
  private registeredCommands: vscode.Disposable[] = [];
  private isEnabled = true;

  constructor(private _client: MonacoLanguageClient) {}

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  clear(): void {}

  getState(): FeatureState {
    return {
      kind: "static",
    };
  }

  public fillClientCapabilities(
    capabilities: ClientCapabilities & ExperimentalClientCapabilities,
  ): void {
    if (!this.isEnabled) {
      return;
    }
    if (!capabilities.experimental) {
      capabilities.experimental = {};
    }
    capabilities.experimental.showReferencesCommandId = CLIENT_CMD_ID;
  }

  public initialize(capabilities: ServerCapabilities): void {
    if (!capabilities.experimental?.referenceCountCodeLens) {
      return;
    }

    if (!this.isEnabled) {
      return;
    }

    const showRefs = vscode.commands.registerCommand(
      CLIENT_CMD_ID,
      async (pos: Position, refCtx: RefContext) => {
        const client = this._client;
        const doc = vscode.window.activeTextEditor?.document;
        if (!doc) {
          console.error("No active editor found");
          return;
        }

        const position = new vscode.Position(pos.line, pos.character);
        const context: vscode.ReferenceContext = {
          includeDeclaration: refCtx.includeDeclaration,
        };

        const provider = client
          .getFeature(ReferencesRequest.method)
          .getProvider(doc);
        if (!provider) {
          return;
        }

        const tokenSource = new vscode.CancellationTokenSource();
        const locations = await provider.provideReferences(
          doc,
          position,
          context,
          tokenSource.token,
        );

        await vscode.commands.executeCommand(
          VSCODE_SHOW_REFERENCES,
          doc.uri,
          position,
          locations,
        );
      },
    );

    this.registeredCommands.push(showRefs);
  }

  public dispose(): void {
    this.registeredCommands.forEach(function (cmd, index, commands) {
      cmd.dispose();
      commands.splice(index, 1);
    });
  }
}

interface ExperimentalClientCapabilities {
  experimental: {
    telemetryVersion?: number;
    showReferencesCommandId?: string;
    refreshModuleProvidersCommandId?: string;
    refreshModuleCallsCommandId?: string;
    refreshTerraformVersionCommandId?: string;
  };
}

export default function initializeTerraformFeatures(
  client: MonacoLanguageClient,
): any[] {
  return [
    new ShowReferencesFeature(client),
    new WorkspaceFoldersFeature(client),
  ];
}
