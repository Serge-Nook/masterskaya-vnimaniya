# Сборка на Debian 11 (glibc 2.31): бинарник запускается на Debian 11+, Ubuntu 22.04+ и SteamOS 3.x
FROM python:3.11-slim-bullseye
# bullseye снят с основных зеркал — берём пакеты из archive.debian.org
RUN printf 'deb http://archive.debian.org/debian bullseye main\ndeb http://archive.debian.org/debian bullseye-updates main\ndeb http://archive.debian.org/debian-security bullseye-security main\n' \
      > /etc/apt/sources.list && rm -f /etc/apt/sources.list.d/* \
    && apt-get -o Acquire::Check-Valid-Until=false update && apt-get install -y --no-install-recommends \
      binutils file curl ca-certificates dpkg-dev desktop-file-utils patchelf \
      libgl1 libegl1 libglib2.0-0 libfontconfig1 libfreetype6 libdbus-1-3 \
      libxkbcommon0 libxkbcommon-x11-0 libx11-xcb1 libxcb1 libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
      libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0 libxcb-xinerama0 \
      libxcb-xkb1 libxcb-sync1 libxcb-shm0 libxrender1 libxrandr2 libatomic1 libxi6 libsm6 libice6 \
      libwayland-client0 libwayland-cursor0 libwayland-egl1 \
      libpulse0 libasound2 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt pyinstaller==6.22.3
WORKDIR /src
