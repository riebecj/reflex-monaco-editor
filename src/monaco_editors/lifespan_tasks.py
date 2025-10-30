"""Async context managers for managing Terraform Language Server and LSP WebSocket proxy lifecycle."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from reflex.utils.processes import new_process

from .terraform import download_lsp_ws_proxy, download_terraform_ls, get_bin_dir


@asynccontextmanager
async def start_terraform_ls(port: int = 9999) -> AsyncGenerator[None, Any, None]:
    """Starts the Terraform Language Server and LSP WebSocket proxy as an async context manager.

    Args:
        port (int, optional): Port to bind the LSP WebSocket proxy. Defaults to 9999.

    Yields:
        None: Yields control while the server is running.
    """
    download_terraform_ls()
    download_lsp_ws_proxy()
    bin_dir = get_bin_dir()
    cmd = f"./lsp-ws-proxy -l 0.0.0.0:{port} -s -- ./terraform-ls serve"
    proc = new_process(cmd, show_logs=True, shell=True, cwd=bin_dir)  # noqa: S604
    yield
    proc.terminate()
    proc.wait()


__all__ = ("start_terraform_ls",)
