import "../build.just"

pyinstaller_builddir := join(build_dir, "pyinstaller")
pyinstaller_distdir := join(build_dir, "pyinstaller_dist")
pyinstaller := "pdm run pyinstaller -y" + \
    " --workpath " + pyinstaller_builddir + \
    " --distpath " + pyinstaller_distdir

nsis_builddir := join(build_dir, "makensis")

icuuc_nuget_url := if env("WINE", "") != "/usr/bin/wine-arm64" {
    "https://www.nuget.org/api/v2/package/Microsoft.ICU.ICU4C.Runtime.win-x64/72.1.0.3"
} else {
    "https://www.nuget.org/api/v2/package/Microsoft.ICU.ICU4C.Runtime.win-arm64/72.1.0.3"
}
