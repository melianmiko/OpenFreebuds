%global appname openfreebuds
%global appid pw.mmk.OpenFreebuds
%global wheelver 0.17.3

# Fallback when python-rpm-macros isn't available (e.g. building on Debian)
%{!?python3_sitelib: %global python3_sitelib %(python3 -c "import sysconfig; print(sysconfig.get_path('purelib'))")}

Name:           %{appname}
Version:        0.17.3.1
Release:        1%{?dist}
Summary:        FOSS client for HUAWEI FreeBuds headset series

License:        GPL-3.0-or-later
URL:            https://github.com/melianmiko/OpenFreebuds
Source0:        %{appname}-%{wheelver}-py3-none-any.whl

BuildArch:      noarch

# The wheel is prebuilt, nothing is compiled here
AutoReqProv:    no

Requires:       python3 >= 3.11
Requires:       python3dist(pyqt6)
Requires:       python3dist(dbus-next)
Requires:       python3dist(pillow)
Requires:       python3dist(qasync)
Requires:       python3dist(aiohttp)
Requires:       python3dist(psutil)
Requires:       python3dist(aiocmd)
Requires:       python3dist(pynput)

%description
Open-source client application for HUAWEI FreeBuds bluetooth headset series.

This application can view device info, change ANC settings, configure gestures
and more.

%prep
# Nothing to unpack: Source0 is a prebuilt wheel

%build
# Nothing to build: Source0 is a prebuilt wheel

%install
mkdir -p %{buildroot}%{python3_sitelib}
pip3 install -q --no-deps --no-compile --upgrade \
    --target "%{buildroot}%{python3_sitelib}" \
    "%{SOURCE0}"

# Console entry points are shipped inside the wheel
mkdir -p %{buildroot}%{_bindir}
install -m0755 %{buildroot}%{python3_sitelib}/bin/%{appname}_qt  %{buildroot}%{_bindir}/%{appname}_qt
install -m0755 %{buildroot}%{python3_sitelib}/bin/%{appname}_cmd %{buildroot}%{_bindir}/%{appname}_cmd
ln -sf ./%{appname}_qt %{buildroot}%{_bindir}/%{appname}
rm -rf %{buildroot}%{python3_sitelib}/bin

# Desktop integration
mkdir -p %{buildroot}%{_datadir}/applications \
         %{buildroot}%{_datadir}/metainfo \
         %{buildroot}%{_datadir}/icons/hicolor/256x256/apps
install -m0644 %{buildroot}%{python3_sitelib}/openfreebuds_qt/assets/%{appid}.desktop \
    %{buildroot}%{_datadir}/applications/
install -m0644 %{buildroot}%{python3_sitelib}/openfreebuds_qt/assets/%{appid}.metainfo.xml \
    %{buildroot}%{_datadir}/metainfo/
install -m0644 %{buildroot}%{python3_sitelib}/openfreebuds_qt/assets/%{appid}.png \
    %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/

%files
%{_bindir}/%{appname}
%{_bindir}/%{appname}_qt
%{_bindir}/%{appname}_cmd
%{python3_sitelib}/openfreebuds/
%{python3_sitelib}/openfreebuds_qt/
%{python3_sitelib}/openfreebuds_backend/
%{python3_sitelib}/openfreebuds_cmd/
%{python3_sitelib}/openfreebuds-%{wheelver}.dist-info/
%{_datadir}/applications/%{appid}.desktop
%{_datadir}/metainfo/%{appid}.metainfo.xml
%{_datadir}/icons/hicolor/256x256/apps/%{appid}.png

%changelog
* Thu Aug 06 2026 MelianMiko <support@mmk.pw> - 0.17.3.1-1
- Add HUAWEI FreeBuds 6 support
- Fix in-call long tap action being read from the wrong parameter
- Refuse remote RPC access when no secret key is set
