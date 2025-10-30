from monaco_editors import constants

def test_code_lens_providers_constant():
    assert hasattr(constants.CodeLensProviders, "TERRAFORM_RESOURCE_DOCS")
    assert "vscode.languages.registerCodeLensProvider" in constants.CodeLensProviders.TERRAFORM_RESOURCE_DOCS

def test_function_constants():
    assert hasattr(constants.FunctionConstants, "CONTAINER_REF")
    assert "useState" in constants.FunctionConstants.CONTAINER_REF
