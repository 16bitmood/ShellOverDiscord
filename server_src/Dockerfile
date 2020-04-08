FROM archlinux

COPY ./pacman.conf /etc/pacman.conf
RUN pacman --noconfirm -Sy reflector
RUN reflector --latest 100 --protocol http --protocol https --sort rate --save /etc/pacman.d/mirrorlist

RUN pacman --noconfirm -Syu
RUN pacman --noconfirm -S python python-pip sudo

RUN pip install --upgrade pip

# Required for Server
RUN pip install --no-cache-dir flask flask-socketio aiohttp eventlet watchdog

# Optional packages
RUN pacman --noconfirm -S vim grep lsof lua gcc gdb man-db man-pages util-linux cowsay nano

# Finishing
COPY . /app
EXPOSE 5000
CMD ["python", "-u", "/app/server.py"]
