# Bump application version
[group("manage"),positional-arguments]
bump_version code:
    {{python}} ./scripts/bump_version.py {{code}}

# Bump application version to git commit identifier
[group("manage")]
bump_version_git:
    {{python}} ./scripts/bump_version.py git

# Sync Qt Linguist translation files
[group("manage"), script]
sync_qt_translations:
    import subprocess
    from pathlib import Path
    for ts_file in Path("./openfreebuds_qt/assets/i18n").iterdir():
        if not ts_file.name.endswith(".ts"):
            continue
        print(f"Sync {ts_file}")
        result = subprocess.run([r"{{pdm}}", "run", "pylupdate6",
                                 "--no-obsolete",
                                 "--exclude", "scripts",
                                 "--exclude", "debian",
                                 "--ts", ts_file, "."])
        if result.returncode != 0:
            print("-- pylupdate6 failed")
            raise SystemExit(1)

# Lock dependencies in PDM for two platforms
[group("manage")]
pdm_lock:
    rm pdm.lock
    pdm lock
    pdm lock --platform=windows_amd64 --append
    pdm lock --platform=windows_arm64 --append
