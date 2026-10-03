import "../build.just"

pyinstaller_builddir := join(build_dir, "pyinstaller")
pyinstaller_distdir := join(build_dir, "pyinstaller_dist")
# The build tree usually lives under the user's home, whose path contains
# spaces on Windows. Without quoting, PowerShell splits the path into two
# arguments and pyinstaller dies with "unrecognized arguments".
pyinstaller := "pdm run pyinstaller -y" + \
    " --workpath " + quote(pyinstaller_builddir) + \
    " --distpath " + quote(pyinstaller_distdir)

nsis_builddir := join(build_dir, "makensis")

# makensis is looked up on PATH instead of being hardcoded to one machine's
# install location; override with NSIS=/path/to/makensis when needed.
nsis := env("NSIS", if os_family() == "windows" { "makensis.exe" } else { "makensis" })

icuuc_nuget_url := if env("WINE", "") != "/usr/bin/wine-arm64" {
    "https://www.nuget.org/api/v2/package/Microsoft.ICU.ICU4C.Runtime.win-x64/72.1.0.3"
} else {
    "https://www.nuget.org/api/v2/package/Microsoft.ICU.ICU4C.Runtime.win-arm64/72.1.0.3"
}
