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
| `docker compose down` | Detiene y elimina el contenedor. Los usuarios y sus archivos se conservan en los volúmenes |
| `docker compose down -v` | Además elimina los volúmenes: **borra los archivos y la base de datos de todos los usuarios**. Al volver a levantar, solo quedan los de `users.txt` |

## Usuarios iniciales

`config/users.txt` tiene una línea por usuario: `usuario:contraseña[:rol]` (rol `estudiante`
por omisión, `profesor` o `admin`). Al levantar con `up -d --build` se agregan los usuarios nuevos
del archivo. Los que ya existen no cambian.

## Gestionar usuarios

Como admin, dentro del contenedor:

```
gestionar_usuarios agregar nuevos.txt      # crea los usuarios del archivo (usuario:contraseña[:rol])
gestionar_usuarios clave alumno3           # cambia la contraseña
gestionar_usuarios eliminar alumno3        # elimina al usuario y sus archivos (o un archivo con un usuario por línea)
gestionar_usuarios listar                  # muestra los usuarios
```

También se puede desde la máquina que ejecuta Docker:

```
docker compose exec jupyterhub gestionar_usuarios <opcion>
```

Desde la terminal de JupyterLab de la cuenta admin activando los permisos de admin `sudo su` o equivalentes.

## Pendiente (TODO)

- [ ] **Pasar lo de JAPPY a un repositorio propio.**

La imagen del entorno de programación deriva de JAPPY, de Gabriel Astudillo Muñoz
(<https://github.com/g-courses/jappy.rc>).
