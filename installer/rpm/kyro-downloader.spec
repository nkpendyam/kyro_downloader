Name:           kyro-downloader
Version:        1.0.0
Release:        1%{?dist}
Summary:        Production-grade media downloader with 4 UI modes
License:        MIT
URL:            https://github.com/nkpendyam/kyro_downloader
Source0:        %{name}-%{version}.tar.gz

BuildArch:      x86_64
Requires:       python3 >= 3.9
Requires:       ffmpeg

%description
Kyro Downloader is a cross-platform media downloader supporting 20+ platforms
with CLI, TUI, Web UI, and Desktop GUI. Features include 8K/4K HDR video,
Dolby Atmos audio, parallel downloads, queue management, and more.

%prep
%setup -q

%build
# No build step needed for Python app

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/kyro-downloader
cp -r * %{buildroot}/opt/kyro-downloader/

# Create wrapper script
mkdir -p %{buildroot}/usr/bin
cat > %{buildroot}/usr/bin/kyro << 'WRAPPER'
#!/bin/bash
exec /opt/kyro-downloader/venv/bin/python -m src.cli "$@"
WRAPPER
chmod 755 %{buildroot}/usr/bin/kyro

# Desktop entry
mkdir -p %{buildroot}/usr/share/applications
cat > %{buildroot}/usr/share/applications/kyro-downloader.desktop << EOF
[Desktop Entry]
Name=Kyro Downloader
Comment=Production-grade media downloader
Exec=/opt/kyro-downloader/src/main.py
Icon=/opt/kyro-downloader/resources/icon.png
Terminal=false
Type=Application
Categories=Network;FileTransfer;
EOF

%files
/opt/kyro-downloader
/usr/bin/kyro
/usr/share/applications/kyro-downloader.desktop

%post
update-desktop-database /usr/share/applications >/dev/null 2>&1 || true

%postun
update-desktop-database /usr/share/applications >/dev/null 2>&1 || true

%changelog
* Sat Apr 04 2026 nkpendyam - 1.0.0-1
- Initial package release
