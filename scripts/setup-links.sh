#!/usr/bin/env bash
# Crea los enlaces para que Claude Code reutilice lo que vive en .agents/
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p .claude
ln -sfn ../.agents/skills    .claude/skills
ln -sfn ../.agents/workflows .claude/commands

# Copia del PDF de análisis si existe en la raíz del repo
[ -f Trabajo_Titulo.pdf ] && mv Trabajo_Titulo.pdf docs/Trabajo_Titulo.pdf || true

echo "Listo:"
ls -l .claude
