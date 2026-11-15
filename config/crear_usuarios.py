#!/usr/bin/env python3
"""Crea una cuenta Unix por cada línea de users.txt (formato usuario:contraseña).

Lo ejecuta el Dockerfile del Hub durante el build, por lo que los usuarios quedan
dentro de la imagen. Cada cuenta recibe su propio directorio /home/<usuario>,
copiado desde /etc/skel y visible solo para ese usuario (permisos 700).
"""
import os
import re
import subprocess
import sys

archivo = sys.argv[1]
lista_permitidos = "/etc/jupyterhub/usuarios_permitidos.txt"
nombre_valido = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")

usuarios = []
with open(archivo, encoding="utf-8") as f:
    for numero, linea in enumerate(f, start=1):
        linea = linea.strip()            # también quita el \r de archivos guardados en Windows
        if not linea or linea.startswith("#"):
            continue
        usuario, separador, clave = linea.partition(":")
        if not separador or not clave:
            sys.exit(f"{archivo}:{numero}: se esperaba usuario:contraseña")
        if not nombre_valido.match(usuario):
            sys.exit(f"{archivo}:{numero}: nombre de usuario no válido: {usuario!r} "
                     "(solo minúsculas, números, - y _)")
        if usuario in [u for u, _ in usuarios]:
            sys.exit(f"{archivo}:{numero}: usuario repetido: {usuario}")
        usuarios.append((usuario, clave))

if not usuarios:
    sys.exit(f"{archivo}: no hay ningún usuario")

for usuario, clave in usuarios:
    subprocess.run(["useradd", "--create-home", "--shell", "/bin/bash", usuario], check=True)
    subprocess.run(["chpasswd"], input=f"{usuario}:{clave}\n", text=True, check=True)
    os.chmod(f"/home/{usuario}", 0o700)
    print(f"usuario creado: {usuario}  ->  /home/{usuario}")

# Solo los nombres (sin contraseñas): JupyterHub usa esta lista para decidir quién puede entrar.
with open(lista_permitidos, "w", encoding="utf-8") as f:
    f.writelines(f"{usuario}\n" for usuario, _ in usuarios)
