import pytest
from monaco_editors import lifespan_tasks

@pytest.mark.asyncio
async def test_start_terraform_ls(monkeypatch):
    called = {}
    def fake_download_terraform_ls():
        called['terraform_ls'] = True
    def fake_download_lsp_ws_proxy():
        called['lsp_ws_proxy'] = True
    def fake_get_bin_dir():
        return "."
    class FakeProc:
        def terminate(self):
            called['terminated'] = True
        def wait(self):
            called['waited'] = True
    def fake_new_process(cmd, show_logs, shell, cwd):
        called['new_process'] = cmd
        return FakeProc()
    monkeypatch.setattr(lifespan_tasks, "download_terraform_ls", fake_download_terraform_ls)
    monkeypatch.setattr(lifespan_tasks, "download_lsp_ws_proxy", fake_download_lsp_ws_proxy)
    monkeypatch.setattr(lifespan_tasks, "get_bin_dir", fake_get_bin_dir)
    monkeypatch.setattr(lifespan_tasks, "new_process", fake_new_process)
    async with lifespan_tasks.start_terraform_ls(port=1234):
        pass
    assert called['terraform_ls']
    assert called['lsp_ws_proxy']
    assert called['new_process']
    assert called['terminated']
    assert called['waited']
