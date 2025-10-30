from monaco_editors import models
import reflex as rx

def test_command_model():
    cmd = models.Command(type="notification", method="test", params={"foo": "bar"})
    assert cmd.type == "notification"
    assert cmd.method == "test"
    assert cmd.params["foo"] == "bar"
    assert not cmd.restart_client

def test_language_server_url():
    url = models.LanguageServerUrl(host="localhost", port=9999, secured=True, path="/ws")
    assert url.formatted == "wss://localhost:9999/ws"
    url2 = models.LanguageServerUrl(host="localhost", port=9999, secured=False, path="ws")
    assert url2.formatted == "ws://localhost:9999/ws"

def test_var_validator():
    var = rx.Var.create("foo")
    assert models._var_validator(var) == '"foo"'

    try:
        models._var_validator("not_a_var")
    except TypeError as e:
        assert "must be passed as an rx.Var" in str(e)

def test_language_client_config():
    url = models.LanguageServerUrl(host="localhost", port=9999, secured=True)
    config = models.LanguageClientConfig(language_id="terraform", url=url)
    assert config.language_id == "terraform"
    assert config.url == url
