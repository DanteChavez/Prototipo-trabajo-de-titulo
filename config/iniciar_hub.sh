#!/bin/bash
# Arranque del contenedor del Hub.
#
# /etc/passwd y /etc/shadow vienen de la imagen y no traen a los usuarios. Los usuarios
# están en la base de datos del volumen /var/lib/usuarios-hub: restaurar_usuarios suma
# los nuevos de users.txt (usuarios de la imagen) y crea sus cuentas, con su mismo UID, antes de
# abrir el Hub.
set -euo pipefail

/usr/local/sbin/restaurar_usuarios

exec /opt/miniconda3/bin/jupyterhub -f /etc/jupyterhub/jupyterhub_config.py
