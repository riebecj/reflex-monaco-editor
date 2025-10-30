python_requirements(
    name="pyproject",
    source="pyproject.toml",
)

pex_binary(
    name="demo",
    entry_point="reflex",
    args=["run"],
    dependencies=[":pyproject", "src/demo:demo"],
)

python_source(name="rxconfig", source="rxconfig.py")

files(
    name="build_files",
    sources=["pyproject.toml", "README.md", "LICENSE"],
)

python_distribution(
    name="reflex-monaco-editor",
    dependencies=[
        ":build_files",
        "src/monaco_editors:monaco_editors",
    ],
    provides=python_artifact(),
    generate_setup = False,
)
