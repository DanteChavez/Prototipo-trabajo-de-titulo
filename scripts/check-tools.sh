#!/usr/bin/env bash
# Verifica que el entorno esté listo. Termina con código 1 si algo falta.
export PATH="$HOME/.local/bin:$PATH"
fail=0
check() {  # check "nombre" comando...
  local name="$1"; shift
  if out=$("$@" 2>&1 | head -n1); then printf 'OK    %-10s %s\n' "$name" "$out"
  else printf 'FALLA %-10s\n' "$name"; fail=1; fi
}

check systemd  bash -c '[ "$(ps -p 1 -o comm=)" = systemd ] && echo systemd'
check git      git --version
check docker   docker --version
check "docker (permisos)" docker info --format '{{.ServerVersion}}'
check k3d      k3d version
check kubectl  kubectl version --client
check helm     helm version --short
check uv       uv --version

case "$PWD" in /mnt/*) echo "AVISO  el proyecto está en /mnt/ (disco de Windows): muévelo a ~/proyectos";; esac
mem_gb=$(awk '/MemTotal/ {printf "%.0f", $2/1024/1024}' /proc/meminfo)
echo "INFO   RAM visible para WSL: ${mem_gb} GB"
exit $fail