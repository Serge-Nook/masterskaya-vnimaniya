#!/usr/bin/env bash
# Сборка AppImage и .deb. Запуск:  packaging/build.sh            — в Docker (Debian 11)
#                                  packaging/build.sh --native   — в текущем окружении
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
APP=masterskaya-vnimaniya
VERSION="$(python3 -c 'import re;print(re.search(r"__version__ = \"(.+?)\"", open("mv/__init__.py").read())[1])')"
ARCH="$(uname -m)"

if [[ "${1:-}" != "--native" ]]; then
  docker build -t "$APP-build" -f packaging/Dockerfile .
  docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$ROOT:/src" "$APP-build" bash packaging/build.sh --native
  exit 0
fi

rm -rf build dist/$APP dist/AppDir dist/deb
python3 -m PyInstaller --noconfirm --clean --distpath dist --workpath build packaging/$APP.spec
BUNDLE="dist/$APP"
# Лишние модули Qt, которые PyInstaller мог захватить транзитивно
# (libQt6Quick/Qml не трогаем: от них зависит FFmpeg-плагин QtMultimedia)
find "$BUNDLE" \( -name 'libQt6WebEngine*' -o -name 'libQt63D*' \
  -o -name 'libQt6Pdf*' -o -name 'libQt6Designer*' -o -name 'libQt6VirtualKeyboard*' -o -name 'libqgtk3.so' \
  -o -name 'libqpdf.so' -o -name 'libqtvirtualkeyboardplugin.so' \) -delete
# Приложение офлайн: сетевые плагины Qt не нужны
rm -rf "$BUNDLE/_internal/PySide6/Qt/plugins/tls" "$BUNDLE/_internal/PySide6/Qt/plugins/networkinformation"
find "$BUNDLE" -path '*/mv/i18n/*.ts' -delete
QT_QPA_PLATFORM=offscreen "$BUNDLE/$APP" --version
test -f "$BUNDLE/_internal/sdl2dll/dll/libSDL2-2.0.so"

install_shared() {  # $1 = корень (usr)
  install -Dm644 packaging/$APP.desktop "$1/share/applications/$APP.desktop"
  install -Dm644 packaging/ru.nookbat.masterskaya_vnimaniya.metainfo.xml \
    "$1/share/metainfo/ru.nookbat.masterskaya_vnimaniya.metainfo.xml"
  for d in packaging/icons/*; do
    install -Dm644 "$d/$APP.png" "$1/share/icons/hicolor/$(basename "$d")/apps/$APP.png"
  done
}

# AppImage
APPDIR=dist/AppDir
mkdir -p "$APPDIR/usr/lib"
cp -a "$BUNDLE" "$APPDIR/usr/lib/$APP"
install_shared "$APPDIR/usr"
cp packaging/$APP.desktop "$APPDIR/$APP.desktop"
cp packaging/icons/256x256/$APP.png "$APPDIR/$APP.png"
ln -sf $APP.png "$APPDIR/.DirIcon"
cat > "$APPDIR/AppRun" <<'RUN'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/lib/masterskaya-vnimaniya/masterskaya-vnimaniya" "$@"
RUN
chmod +x "$APPDIR/AppRun"
mkdir -p .cache && TOOL=".cache/appimagetool-$ARCH.AppImage"
if [[ ! -x "$TOOL" ]]; then
  curl -fsSL --retry 5 --retry-delay 5 --retry-all-errors -o "$TOOL" "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$ARCH.AppImage"
  chmod +x "$TOOL"
fi
RUNTIME=".cache/runtime-$ARCH"
if [[ ! -s "$RUNTIME" ]]; then
  curl -fsSL --retry 5 --retry-delay 5 --retry-all-errors -o "$RUNTIME" "https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-$ARCH"
fi
APPIMAGE_EXTRACT_AND_RUN=1 ARCH="$ARCH" "$TOOL" --no-appstream --runtime-file "$RUNTIME" "$APPDIR" "dist/Masterskaya-vnimaniya-$VERSION-$ARCH.AppImage"

# .deb
DEBARCH=$([[ "$ARCH" == "aarch64" ]] && echo arm64 || echo amd64)
PKG=dist/deb
mkdir -p "$PKG/DEBIAN" "$PKG/opt" "$PKG/usr/bin" "$PKG/usr/share/doc/$APP"
cp -a "$BUNDLE" "$PKG/opt/$APP"
ln -sf /opt/$APP/$APP "$PKG/usr/bin/$APP"
install_shared "$PKG/usr"
cp LICENSE "$PKG/usr/share/doc/$APP/copyright"
SIZE=$(du -sk "$PKG" | cut -f1)
cat > "$PKG/DEBIAN/control" <<CTRL
Package: $APP
Version: $VERSION
Architecture: $DEBARCH
Maintainer: Горшков Сергей Владимирович <nookbat@gmail.com>
Installed-Size: $SIZE
Depends: libc6 (>= 2.31), libgl1, libegl1, libfontconfig1, libfreetype6, libxkbcommon0, libdbus-1-3
Recommends: libpulse0 | libasound2
Section: education
Priority: optional
Homepage: https://nookbat.ru
Description: Мастерская внимания — тренажёр внимания для детей 6–7 лет
 Короткие игровые занятия с енотом Тихоном: внимание, усидчивость, спокойствие.
 Работает без интернета, не собирает данные. Не заменяет консультацию специалиста.
CTRL
cat > "$PKG/DEBIAN/postinst" <<'POST'
#!/bin/sh
set -e
command -v update-desktop-database >/dev/null && update-desktop-database -q /usr/share/applications || true
command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
POST
cp "$PKG/DEBIAN/postinst" "$PKG/DEBIAN/postrm"
chmod 755 "$PKG/DEBIAN/postinst" "$PKG/DEBIAN/postrm"
dpkg-deb --root-owner-group -Zxz --build "$PKG" "dist/${APP}_${VERSION}_${DEBARCH}.deb"
ls -la dist/*.AppImage dist/*.deb
