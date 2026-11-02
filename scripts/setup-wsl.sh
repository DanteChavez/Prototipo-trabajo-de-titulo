#!/usr/bin/env bash
# Instala las herramientas del proyecto dentro de WSL2 (Ubuntu). Es seguro ejecutarlo varias veces.
set -euo pipefail

K3D_VERSION="v5.9.0"
KUBECTL_VERSION="v1.35.5"   # misma versión menor que k3s del ADR 0003
HELM_VERSION="v3.22.1"

have() { command -v "$1" >/dev/null 2>&1; }

echo "==> Paquetes base"
sudo apt-get update -y
sudo apt-get install -y curl git unzip ca-certificates

if ! have docker; then
  echo "==> Docker Engine"
  curl -fsSL https://get.docker.com | sudo sh
fi
sudo systemctl enable --now docker || echo "AVISO: no se pudo iniciar docker con systemd (revisa /etc/wsl.conf)"
if ! id -nG "$USER" | grep -qw docker; then
  sudo usermod -aG docker "$USER"
  NEED_RESTART=1
fi

if ! have k3d; then
  echo "==> k3d $K3D_VERSION"
  curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | TAG="$K3D_VERSION" bash
fi

if ! have kubectl; then
  echo "==> kubectl $KUBECTL_VERSION"
  curl -fsSLo /tmp/kubectl "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl"
  sudo install -m 0755 /tmp/kubectl /usr/local/bin/kubectl
  rm -f /tmp/kubectl
fi

if ! have helm; then
  echo "==> Helm $HELM_VERSION"
  curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash -s -- --version "$HELM_VERSION"
fi

if ! have uv && [ ! -x "$HOME/.local/bin/uv" ]; then
  echo "==> uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo
echo "Instalación terminada."
if [ "${NEED_RESTART:-0}" = "1" ]; then
  echo "IMPORTANTE: ejecuta 'wsl --shutdown' en PowerShell y abre Ubuntu de nuevo (grupo docker)."
fi
echo "Luego verifica con: bash scripts/check-tools.sh"