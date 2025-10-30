import importlib
import os
from pathlib import Path
import pytest
import reflex as rx

from reflex.testing import AppHarness
import reflex.config
from playwright.sync_api import Page, expect

from monaco_editors import base
from monaco_editors.models import LanguageClientConfig, LanguageServerUrl


class MonacoBaseTestState(rx.State):
    register_commands = {"foo", "bar"}
    initialization_options = {"bar", "baz"}

@pytest.mark.parametrize("clients,expected", [
    ([        
        LanguageClientConfig(
            language_id="terraform",
            url=LanguageServerUrl(host="localhost", port=9999, secured=False),
            register_commands=MonacoBaseTestState.register_commands
        )
    ], ["startOptions:", "await registerCommand(params);"]),
    ([
        LanguageClientConfig(
            language_id="terraform",
            url=LanguageServerUrl(host="0.0.0.0", port=1234),
            initialization_options=MonacoBaseTestState.initialization_options
        )
    ], ["connection", "clientOptions"]),
    ([], ["undefined"])
])
def test_configure_language_clients(clients, expected):
    result = base.configure_language_clients(clients)
    for client in clients:
        assert client.language_id in result
        assert client.url.formatted in result
    for expected_string in expected:
        assert expected_string in result


# Upper-casing to have it stand out from test functions
# Must be a function and include all imports for AppHarness to generate the app correctly
def EditorApp(): 
    import reflex as rx
    from monaco_editors import monaco_editor

    def index():
        return rx.vstack(
            monaco_editor(
                filename="test.txt",
                data_testid="basic_monaco_editor"
            )
        )

    app = rx.App()
    app.add_page(index)


def test_editor_render(create_app_harness: AppHarness, page: Page):
    os.environ.setdefault("HOME", str(Path.cwd()))
    with create_app_harness.create(EditorApp) as editor_app:
        assert editor_app.frontend_url is not None
        page.goto(editor_app.frontend_url)
        page.bring_to_front
        expect(page.get_by_test_id("basic_monaco_editor")).to_be_visible()
