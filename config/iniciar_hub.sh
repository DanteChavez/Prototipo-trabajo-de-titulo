#!/bin/bash
# Arranque del contenedor del Hub.
#
# /etc/passwd y /etc/shadow vienen de la imagen, así que solo traen los usuarios
# iniciales. Las cuentas que el admin agregó después están en el registro del volumen
# /var/lib/usuarios-hub: se recrean aquí, con su mismo UID, antes de abrir el Hub.
set -euo pipefail

/usr/local/sbin/crear_usuarios restaurar

exec /opt/miniconda3/bin/jupyterhub -f /etc/jupyterhub/jupyterhub_config.py
