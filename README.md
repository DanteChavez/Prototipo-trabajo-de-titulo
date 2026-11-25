# Prototipo: sistema web de apoyo a la práctica de programación

JupyterHub en un solo contenedor de Docker. Cada usuario inicia sesión desde el navegador y
trabaja en su propio JupyterLab (Python, C++ y Java), con sus archivos en `/home/<usuario>`.
Los usuarios y sus roles (estudiante, profesor y admin) se guardan en una base de datos SQLite.

## Levantar el contenedor

Desde la raíz del repositorio:

```
docker compose up -d --build
```

Luego abrir <http://localhost:8000> e ingresar con una cuenta de `config/users.txt`.

| Comando | Qué hace |
|---|---|
| `docker compose up -d` | Levanta el contenedor en segundo plano con la imagen ya construida |
| `docker compose up -d --build` | Reconstruye la imagen antes de levantarlo. Usarlo la primera vez y después de cambiar un Dockerfile, `config/` o `users.txt` |
| `docker compose logs -f` | Muestra los mensajes del contenedor (con `-d` no aparecen en la terminal). Se sale con Ctrl+C |
| `docker compose down` | Detiene y elimina el contenedor. Los usuarios y sus archivos se conservan en los volúmenes |
| `docker compose down -v` | Además elimina los volúmenes: **borra los archivos y la base de datos de todos los usuarios**. Al volver a levantar, solo quedan los de `users.txt` |

## Usuarios iniciales

`config/users.txt` tiene una línea por usuario: `usuario:contraseña[:rol]` (rol `estudiante`
por omisión, `profesor` o `admin`). Al levantar con `up -d --build` se agregan los usuarios nuevos
del archivo. Los que ya existen no cambian.

## Gestionar usuarios

Con el contenedor en funcionamiento, desde la máquina que ejecuta Docker:

```
docker compose exec jupyterhub gestionar_usuarios agregar /tmp/nuevos.txt   # crea los usuarios del archivo
docker compose exec jupyterhub gestionar_usuarios clave alumno3              # cambia la contraseña
docker compose exec jupyterhub gestionar_usuarios eliminar alumno3           # elimina al usuario y sus archivos
docker compose exec jupyterhub gestionar_usuarios eliminar /tmp/bajas.txt    # elimina a los usuarios del archivo
docker compose exec jupyterhub gestionar_usuarios listar                     # muestra los usuarios
```

Para usar un archivo, primero se copia al contenedor:

```
docker compose cp nuevos.txt jupyterhub:/tmp/nuevos.txt
```

El archivo de `agregar` usa el mismo formato que `users.txt`. El de `eliminar` puede tener solo
nombres, uno por línea. Los cambios rigen de inmediato, sin reiniciar el Hub.

## Pendiente (TODO)

- [ ] **Pasar lo de JAPPY a un repositorio propio.** Hoy los Dockerfiles `base`, `kernels` y
  `latest` descargan archivos de <https://github.com/g-courses/jappy.rc> durante el build
  (`ARG IMAGE_DIR=https://raw.githubusercontent.com/g-courses/jappy.rc/...` y
  `/opt/libs/jappy.d/jappy_utils.py`), y la imagen `hub` parte de
  `dantechavez0/entorno-programacion:latest`. Si ese repositorio cambia o deja de estar
  disponible, la imagen no se puede reconstruir igual. Pasos:
  1. Copiar a este repositorio (o a uno propio) la carpeta `image_dir` que usan los Dockerfiles.
  2. Cambiar `IMAGE_DIR` para que apunte a la copia propia, o usar `COPY` desde el repositorio.
  3. Reconstruir la cadena `base` → `kernels` → `latest` y publicar la imagen propia.
  4. Mantener el crédito a JAPPY y revisar su licencia.

La imagen del entorno de programación deriva de JAPPY, de Gabriel Astudillo Muñoz
(<https://github.com/g-courses/jappy.rc>).
