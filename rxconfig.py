"""Configuration for the Reflex Monaco Editor demo application."""

import sys

import reflex as rx

sys.path.append("src")

from vite_config_plugin import ViteConfigPlugin

from monaco_editors.config import MonacoEditorsReflexConfig

config = rx.Config(
    app_module_import="demo.main",
    app_name="demo",
    plugins=[
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.SitemapPlugin(),
        ViteConfigPlugin(
            MonacoEditorsReflexConfig.get_vite_config(),
            imports=MonacoEditorsReflexConfig.get_imports(),
            dependencies=MonacoEditorsReflexConfig.get_dependencies(),
        ),
    ],
)
