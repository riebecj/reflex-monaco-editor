"""Reflex Monaco Editor Demo."""

import pathlib

import reflex as rx

from monaco_editors import TextModel, monaco_editor, start_terraform_ls


class EditorState(rx.State):
    """State management for the Monaco Editor demo."""

    editor_type: str = "text"
    value: str = "This is a basic text editor."
    workspace: str | None = None
    filename: str = "demo.txt"
    commands: dict = rx.field(default_factory=dict)
    init_options: dict = rx.field(default_factory=dict)

    @rx.event
    async def set_editor(self, editor: str) -> None:
        """Sets the editor type and updates the value and filename.

        Args:
            editor (str): The type of editor to set.
        """
        self.editor_type = editor
        match editor:
            case "text":
                self.workspace = None
                self.value = "This is a basic text editor."
                self.filename = "demo.txt"
                self.init_options = {}
                self.commands = {}
            case "terraform-simple":
                self.workspace = None
                self.value = '# This is a comment\nresource "aws_s3_bucket" "my_bucket" {\n  bucket = "my-bucket"\
                    \n  acl    = "private"\n}\n'
                self.filename = "main.tf"
                self.init_options = {}
                self.commands = {}
            case "terraform-advanced":
                self.workspace = str(pathlib.Path().cwd() / "demo_workspace")
                self.value = 'resource "aws_s3_bucket" "my_bucket" {\n  bucket = "my-bucket"\
                    \n  acl    = "private"\n}\n'
                self.filename = "main.tf"
                self.init_options = {
                    "validation": {"enableEnhancedValidation": True},
                    "experimentalFeatures": {"prefillRequiredFields": True},
                }
                self.commands = {
                    "terraform.init": monaco_editor.command(
                        type="request",
                        method="workspace/executeCommand",
                        params={
                            "command": "terraform-ls.terraform.init",
                            "arguments": [f"uri=file://{self.workspace!s}"],
                        },
                        restart_client=True,
                    ),
                    "terraform.initCurrent": monaco_editor.command(
                        type="request",
                        method="workspace/executeCommand",
                        params={
                            "command": "'terraform-ls.terraform.init'",
                            "arguments": [f"uri=file://{self.workspace!s}"],
                        },
                        restart_client=True,
                    ),
                    "terraform.validate": monaco_editor.command(
                        type="request",
                        method="workspace/executeCommand",
                        params={
                            "command": "'terraform-ls.terraform.validate'",
                            "arguments": [f"uri=file://{self.workspace!s}"],
                        },
                    ),
                }

    @rx.event
    async def on_change(self, text: TextModel) -> None:
        """Handle changes in the editor's text model.

        Args:
            text (TextModel): The updated text model containing the modified value.
        """
        self.value = text["modified"]

    @rx.event
    async def on_command(self, command: str) -> rx.event.EventSpec:
        """Handle execution of a command and display an informational toast.

        Args:
            command (str): The command to be executed.

        Returns:
            rx.event.EventSpec: An event specification for displaying the toast.
        """
        return rx.toast.info(f"Running {command}...")

    @rx.event
    async def on_command_complete(self, command: str) -> rx.event.EventSpec:
        """Handle completion of a command and display a success toast.

        Args:
            command (str): The command that was completed.

        Returns:
            rx.event.EventSpec: An event specification for displaying the success toast.
        """
        return rx.toast.success(f"{command} succeeded!")

    @rx.event
    async def on_restart(self, client: str) -> rx.event.EventSpec:
        """Handle restart of a language client and display a warning toast.

        Args:
            client (str): The name of the language client to restart.

        Returns:
            rx.event.EventSpec: An event specification for displaying the warning toast.
        """
        return rx.toast.warning(f"Restarting language client {client}")


class HeaderState(rx.State):
    """State management for the header section, including language selection button states."""

    @rx.var
    async def basic_disabled(self) -> bool:
        """Determine if the 'Basic' language menu item should be disabled.

        Returns:
            bool: True if the current editor type is 'text', otherwise False.
        """
        return await self.get_var_value(EditorState.editor_type) == "text"

    @rx.var
    async def terraform_simple_disabled(self) -> bool:
        """Determine if the 'Terraform' language menu item should be disabled.

        Returns:
            bool: True if the current editor type is 'terraform', otherwise False.
        """
        return await self.get_var_value(EditorState.editor_type) == "terraform-simple"

    @rx.var
    async def terraform_advanced_disabled(self) -> bool:
        """Determine if the 'Terraform' language menu item should be disabled.

        Returns:
            bool: True if the current editor type is 'terraform', otherwise False.
        """
        return await self.get_var_value(EditorState.editor_type) == "terraform-advanced"


@rx.page("/")
def index() -> rx.Component:
    """Render the main page of the Monaco Editor demo.

    Returns:
        rx.Component: The root component for the demo page.
    """
    return rx.vstack(
        rx.hstack(
            rx.heading("Monaco Editor Demo", size="5"),
            rx.button("Toggle Theme", on_click=rx.toggle_color_mode),
            rx.menu.root(
                rx.menu.trigger(
                    rx.button("Languages", variant="soft"),
                ),
                rx.menu.content(
                    rx.menu.item(
                        "Plaintext",
                        disabled=HeaderState.basic_disabled,
                        on_click=EditorState.set_editor("text"),
                    ),
                    rx.menu.item(
                        "Terraform (Simple)",
                        disabled=HeaderState.terraform_simple_disabled,
                        on_click=EditorState.set_editor("terraform-simple"),
                    ),
                    rx.menu.item(
                        "Terraform (Advanced)",
                        disabled=HeaderState.terraform_advanced_disabled,
                        on_click=EditorState.set_editor("terraform-advanced"),
                    ),
                ),
            ),
            rx.button(
                "Restart Language Client",
                on_click=rx.call_function(
                    "wrapper.getLanguageClientWrapper(wrapper.getEditor().getModel().getLanguageId())?.restartLanguageClient()"
                ),
            ),
            class_name="w-full m-2 items-center",
        ),
        monaco_editor(
            filename=EditorState.filename,
            value=EditorState.value,
            on_change=EditorState.on_change,
            on_command=EditorState.on_command,
            on_command_complete=EditorState.on_command_complete,
            on_restart=EditorState.on_restart,
            workspace_folder=EditorState.workspace,
            language_clients=[
                monaco_editor.language_client(
                    language_id="terraform",
                    url=monaco_editor.server_url(host="localhost", port=9999, secured=False),
                    initialization_options=EditorState.init_options,
                    register_commands=EditorState.commands,
                ),
            ],
            class_name="w-full h-3/4",
        ),
        class_name="w-full h-screen",
    )


app = rx.App()
app.register_lifespan_task(start_terraform_ls)
