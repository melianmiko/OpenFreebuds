# Build everything
build: qt_i18n
    pdm run pyuic6 ./openfreebuds_qt/designer/
    pdm build --no-clean

# Compile Qt Linguist translation files
[script]
qt_i18n:
    import subprocess
    from pathlib import Path
    files_to_compile = []
    command = [r"{{lrelease}}"]
    for translation in Path("openfreebuds_qt/assets/i18n").iterdir():
        if translation.name.endswith(".ts"):
            command.append(str(translation))
    print("{{BOLD}}" + ' '.join(command) + "{{NORMAL}}")
    subprocess.run(command)

# Check that all build requirements are resolved
[private,script]
build_check:
    assert "{{pdm}}" != "", "PDM not found"
    assert "{{lrelease}}" != "", "Qt lrelease not found"
