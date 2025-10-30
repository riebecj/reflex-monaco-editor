pex_binary(
    name="playwright",
    entry_point="playwright",
    dependencies=["//:pyproject#pytest-playwright"],
)

adhoc_tool(
    name="playwright-browsers",
    runnable=":playwright",
    args=["install"],
    execution_dependencies=[":playwright"],
    log_output=True,
)

python_test_utils(
    name="test_utils",
    dependencies=[
        ":playwright-browsers",
        "//:pyproject",
    ]
)

python_tests(
    name="tests",
    dependencies=["src/monaco_editors:monaco_editors", "//:rxconfig"],
)
