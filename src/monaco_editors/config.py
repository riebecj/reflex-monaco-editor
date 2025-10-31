"""Plugins for integrating Monaco Editor with VSCode extensions in Reflex.

This module provides configuration classes and Vite plugin definitions
to enable Monaco Editor with VSCode language extensions and services.
"""

from vite_config_plugin import RawJS, ViteConfig


class MonacoEditorsReflexConfig:
    """A Reflex plugin for integrating Monaco Editor with VSCode extensions.

    This plugin provides the necessary Vite configuration and dependencies
    to use Monaco Editor with various VSCode language extensions and services
    in a Reflex application.
    """

    @classmethod
    def get_dependencies(cls) -> list[str]:
        """Return a list of dependencies required for the Monaco Editor Reflex plugin."""
        return [
            "@codingame/esbuild-import-meta-url-plugin@1.0.3",
            "@codingame/monaco-vscode-rollup-vsix-plugin@20.2.1",
        ]

    @classmethod
    def get_imports(cls) -> list[str]:
        """Return a list of custom import statements for the Monaco Editor Reflex plugin."""
        return [
            "import importMetaUrlPlugin from '@codingame/esbuild-import-meta-url-plugin';",
            "import vsixPlugin from '@codingame/monaco-vscode-rollup-vsix-plugin';",
        ]

    @classmethod
    def get_vite_config(cls) -> ViteConfig:
        """Return the Vite configuration for integrating Monaco Editor with VSCode extensions.

        Returns:
            The configuration dictionary for Vite.
        """
        return {
            "worker": {"format": "es"},
            "optimizeDeps": {
                "include": [
                    "@codingame/monaco-vscode-api",
                    "@codingame/monaco-vscode-configuration-service-override",
                    "@codingame/monaco-vscode-editor-api",
                    "@codingame/monaco-vscode-editor-service-override",
                    "@codingame/monaco-vscode-extension-api",
                    "@codingame/monaco-vscode-extensions-service-override",
                    "@codingame/monaco-vscode-java-default-extension",
                    "@codingame/monaco-vscode-javascript-default-extension",
                    "@codingame/monaco-vscode-json-default-extension",
                    "@codingame/monaco-vscode-languages-service-override",
                    "@codingame/monaco-vscode-localization-service-override",
                    "@codingame/monaco-vscode-model-service-override",
                    "@codingame/monaco-vscode-monarch-service-override",
                    "@codingame/monaco-vscode-textmate-service-override",
                    "@codingame/monaco-vscode-theme-defaults-default-extension",
                    "@codingame/monaco-vscode-theme-service-override",
                    "@codingame/monaco-vscode-views-service-override",
                    "@codingame/monaco-vscode-workbench-service-override",
                    "vscode/localExtensionHost",
                    "vscode-textmate",
                    "vscode-oniguruma",
                ],
                "rollupOptions": {
                    "plugins": [RawJS("importMetaUrlPlugin")],
                },
            },
            "plugins": [RawJS("vsixPlugin()")],
        }
