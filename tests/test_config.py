from monaco_editors import config

def test_get_dependencies():
    deps = config.MonacoEditorsReflexConfig.get_dependencies()
    assert isinstance(deps, list)
    assert "@codingame/esbuild-import-meta-url-plugin@1.0.3" in deps
    assert "@codingame/monaco-vscode-rollup-vsix-plugin@20.2.1" in deps

def test_get_imports():
    imports = config.MonacoEditorsReflexConfig.get_imports()
    assert isinstance(imports, list)
    assert "import importMetaUrlPlugin from '@codingame/esbuild-import-meta-url-plugin';" in imports
    assert "import vsixPlugin from '@codingame/monaco-vscode-rollup-vsix-plugin';" in imports

def test_get_vite_config():
    vite_config = config.MonacoEditorsReflexConfig.get_vite_config()
    assert vite_config["worker"]["format"] == "es"
    assert len(vite_config["optimizeDeps"]["include"]) == 23
    meta_url_plugin = vite_config["optimizeDeps"]["esbuildOptions"]["plugins"][0]
    assert isinstance(meta_url_plugin, config.RawJS)
    assert meta_url_plugin.code == "importMetaUrlPlugin"
    vsix_plugin = vite_config["plugins"][0]
    assert isinstance(vsix_plugin, config.RawJS)
    assert vsix_plugin.code == "vsixPlugin()"
