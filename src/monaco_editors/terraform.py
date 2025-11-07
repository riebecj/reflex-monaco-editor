"""Functions for downloading and managing Terraform language server and LSP WebSocket proxy binaries.

This module provides utilities to fetch, extract, and prepare the necessary binaries for Terraform language server
and LSP WebSocket proxy, supporting multiple platforms and architectures.
"""

import functools
import io
import pathlib
import platform
import tarfile
import zipfile
from typing import Final, Literal

from reflex.utils import console, path_ops
from reflex.utils.decorator import once
from reflex.utils.net import get
from reflex.utils.prerequisites import get_backend_dir

TERRAFORM_EXTENSION_VERSION: Final = "v2.34.5"
LSP_WS_PROXY_VERSION: Final = "v0.8.0"


def get_bin_dir() -> pathlib.Path:
    """Returns the path to the binary directory, creating it if it does not exist.

    Returns:
        pathlib.Path: Path to the binary directory.
    """
    bin_dir = get_backend_dir() / "bin"
    path_ops.mkdir(bin_dir)
    return bin_dir


@once
def get_vscode_extension_package_json() -> dict:
    """Fetches the package.json for the HashiCorp Terraform VSCode Extension.

    Returns:
        dict: The parsed JSON content of the package.json file.
    """
    console.debug(f"Getting Package JSON for HashiCorp Terraform VSCode Extenstion {TERRAFORM_EXTENSION_VERSION}")
    response = get(
        f"https://raw.githubusercontent.com/hashicorp/vscode-terraform/refs/tags/{TERRAFORM_EXTENSION_VERSION}/package.json"
    )
    return response.json()


@functools.lru_cache(maxsize=2)
def get_platform(purpose: Literal["terraform-ls", "lsp-ws-proxy"]) -> str:
    """Determines the platform string for downloading binaries based on the system and purpose.

    Args:
        purpose (Literal["terraform-ls", "lsp-ws-proxy"]): The intended binary ("terraform-ls" or "lsp-ws-proxy").

    Returns:
        str: The platform identifier string used in download URLs.
    """
    match platform.system():
        case "Darwin":
            return "darwin" if purpose == "terraform-ls" else "macos"
        case "Windows":
            return "windows"
        case _:
            return "linux"


def get_architecture() -> str:
    """Determines the machine architecture string for downloading binaries.

    Returns:
        str: The architecture identifier string used in download URLs.

    Raises:
        ValueError: If the machine architecture is unsupported.
    """
    arch = platform.machine()
    if "x86" in arch:
        return "amd64"
    if "arm" in arch or "aarch" in arch:
        if "64" in arch:
            return "arm64"
        return "arm"
    if "386" in arch:
        return "386"

    msg = f"Unsupported machine architecture: {arch}"
    raise ValueError(msg)


def download_terraform_ls() -> None:
    """Downloads and extracts the Terraform language server binary if not already present.

    This function determines the correct version and platform, fetches the binary archive,
    and extracts the executable to the bin directory.
    """
    bin_dir = get_bin_dir()
    terraform_ls_bin = bin_dir / "terraform-ls"
    if not terraform_ls_bin.exists():
        package_json = get_vscode_extension_package_json()
        terraform_ls_version = package_json["langServer"]["version"]
        os = get_platform("terraform-ls")
        arch = get_architecture()
        console.debug(f"Downloading terraform-ls v{terraform_ls_version} for {os} {arch}")
        base_url = "https://releases.hashicorp.com/terraform-ls/0.36.5/terraform-ls"
        response = get(f"{base_url}_{terraform_ls_version}_{os}_{arch}.zip")
        terraform_ls_zip = io.BytesIO(response.content)
        with zipfile.ZipFile(terraform_ls_zip, "r") as archive:
            for file in archive.filelist:
                if file.filename == "terraform-ls":
                    archive.extract(member=file, path=bin_dir)
        terraform_ls_bin.chmod(0o755)


def download_lsp_ws_proxy() -> None:
    """Downloads and extracts the LSP WebSocket proxy binary if not already present.

    This function determines the correct platform, fetches the binary archive,
    and extracts the executable to the bin directory.
    """
    bin_dir = get_bin_dir()
    if not (bin_dir / "lsp-ws-proxy").exists():
        os = get_platform("lsp-ws-proxy")
        console.debug(f"Downloading lsp-ws-proxy v{LSP_WS_PROXY_VERSION} for {os}")
        base_url = "https://github.com/qualified/lsp-ws-proxy/releases/download"
        response = get(f"{base_url}/{LSP_WS_PROXY_VERSION}/lsp-ws-proxy_{os}.tar.gz", follow_redirects=True)
        lsp_ws_proxy_tar = io.BytesIO(response.content)
        with tarfile.open(fileobj=lsp_ws_proxy_tar, mode="r:gz") as tarball:
            for file in tarball.getmembers():
                if file.name == "lsp-ws-proxy":
                    tarball.extract(file, bin_dir)
