from unittest.mock import patch, MagicMock

import pytest
from monaco_editors import terraform


@patch("monaco_editors.terraform.get_backend_dir")
def test_get_bin_dir(mock_get_backend_dir: MagicMock, tmp_path):
    mock_get_backend_dir.return_value = tmp_path
    bin_dir = terraform.get_bin_dir()
    assert bin_dir == tmp_path / "bin"
    assert bin_dir.exists()


@pytest.mark.parametrize("purpose", ["terraform-ls", "lsp-ws-proxy"])
@pytest.mark.parametrize("system_type", ["Darwin", "Windows", "Linux"])
@patch("monaco_editors.terraform.platform")
def test_get_platform(mock_platform: MagicMock, purpose: str, system_type: str):
    mock_platform.system.return_value = system_type
    expected = system_type.lower()
    if purpose == "lsp-ws-proxy" and system_type == "Darwin":
        expected = "macos"
    assert terraform.get_platform(purpose) == expected
    mock_platform.system.assert_called_once()
    terraform.get_platform.cache_clear()


@pytest.mark.parametrize(
    "machine,expected",
    [
        ("x86_64", "amd64"),
        ("i386", "386"),
        ("armv7l", "arm"),
        ("aarch64", "arm64"),
        ("arm64", "arm64"),
        ("arm", "arm"),
        ("386", "386"),
    ],
)
@patch("monaco_editors.terraform.platform")
def test_get_architecture_valid(mock_platform: MagicMock, machine, expected):
    mock_platform.machine.return_value = machine
    assert terraform.get_architecture() == expected

@patch("monaco_editors.terraform.platform")
def test_get_architecture_invalid(mock_platform: MagicMock):
    mock_platform.machine.return_value = "mips"
    with pytest.raises(ValueError, match="Unsupported machine architecture: mips"):
        terraform.get_architecture()


@pytest.mark.parametrize("exists", [False, True])
@patch("monaco_editors.terraform.zipfile")
@patch("monaco_editors.terraform.get_bin_dir")
@patch("monaco_editors.terraform.get")
def test_download_terraform_ls(mock_get: MagicMock, mock_get_bin_dir: MagicMock, mock_zip: MagicMock, tmp_path, exists):
    mock_get_bin_dir.return_value = tmp_path
    terraform_bin = (tmp_path / "terraform-ls")
    
    mock_json_response = MagicMock()
    mock_json_response.json.return_value = {"langServer": {"version": "1.2.3"}}
    mock_bin_response = MagicMock()
    mock_bin_response.content = b"test bytes"
    mock_get.side_effect = [mock_json_response, mock_bin_response]

    mock_file = MagicMock()
    mock_file.filename = "terraform-ls"
    other_mock_file = MagicMock()
    other_mock_file.filename = "foobar"
    mock_archive = mock_zip.ZipFile.return_value.__enter__.return_value
    mock_archive.filelist = [other_mock_file, mock_file]

    def mock_extract(member = None, path = None):
        terraform_bin.touch()
    
    if exists:
        mock_extract()
    else:
        mock_archive.extract.side_effect = mock_extract

    terraform.download_terraform_ls()

    if not exists:
        mock_archive.extract.assert_called_once()
        assert mock_get.call_count == 2
        assert oct(terraform_bin.stat().st_mode & 0o777) == "0o755"
    else:
        mock_archive.extract.assert_not_called()
        mock_get.assert_not_called()


@pytest.mark.parametrize("exists", [False, True])
@patch("monaco_editors.terraform.tarfile")
@patch("monaco_editors.terraform.get_bin_dir")
@patch("monaco_editors.terraform.get")
def test_download_lsp_ws_proxy(mock_get: MagicMock, mock_get_bin_dir: MagicMock, mock_tar: MagicMock, tmp_path, exists):
    mock_get_bin_dir.return_value = tmp_path
    proxy_bin = (tmp_path / "lsp-ws-proxy")

    mock_bin_response = MagicMock()
    mock_bin_response.content = b"test bytes"
    mock_get.return_value = mock_bin_response

    mock_file = MagicMock()
    mock_file.name = "lsp-ws-proxy"
    other_mock_file = MagicMock()
    other_mock_file.name = "foobar"
    mock_tarball = mock_tar.open.return_value.__enter__.return_value
    mock_tarball.getmembers.return_value = [other_mock_file, mock_file]

    def mock_extract(*args):
        proxy_bin.touch()
    
    if exists:
        mock_extract()
    else:
        mock_tarball.extract.side_effect = mock_extract

    terraform.download_lsp_ws_proxy()

    if not exists:
        mock_tarball.extract.assert_called_once()
        mock_get.assert_called_once()
    else:
        mock_tarball.extract.assert_not_called()
        mock_get.assert_not_called()
