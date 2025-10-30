from collections.abc import Callable
import functools
from pathlib import Path
import re
import types
from typing import Any

import pytest

from reflex.testing import AppHarness


TEST_CONFIG = """
import reflex as rx
from vite_config_plugin import ViteConfigPlugin
from monaco_editors.config import MonacoEditorsReflexConfig

config = rx.Config(
    app_name="{test_app_name}",
    plugins=[
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.SitemapPlugin(),
        ViteConfigPlugin(
            MonacoEditorsReflexConfig.get_vite_config(),
            imports=MonacoEditorsReflexConfig.get_imports(),
            dependencies=MonacoEditorsReflexConfig.get_dependencies(),
        )
    ]
)
"""


@pytest.fixture
def create_app_harness(tmp_path_factory) -> Callable[[Callable], AppHarness]:
    class CreateTestApp(AppHarness):
        @classmethod
        def create(cls, app_source: Callable[[], None] | types.ModuleType | functools.partial[Any]) -> AppHarness:
            if isinstance(app_source, functools.partial):
                keywords = app_source.keywords
                slug_suffix = "_".join([str(v) for v in keywords.values()])
                func_name = app_source.func.__name__
                app_name = f"{func_name}_{slug_suffix}"
                app_name = re.sub(r"[^a-zA-Z0-9_]", "_", app_name)
            else:
                app_name = app_source.__name__

            app_name = app_name.lower()
            root = tmp_path_factory.mktemp("app_harness")
            app_module_path = root / app_name / f"{app_name}.py"
            app_module_path.parent.mkdir(parents=True, exist_ok=True)
            cls._add_custom_config(root, app_name)
            return cls(
                app_name=app_name,
                app_source=app_source,
                app_path=root,
                app_module_path=app_module_path,
            )

        @classmethod
        def _add_custom_config(cls, root: Path, app_name: str) -> None:
            name = "rxconfig.py"
            with (root / name).open("wt+") as test_config:
                test_config.write(TEST_CONFIG.format(test_app_name=app_name))

    return CreateTestApp
