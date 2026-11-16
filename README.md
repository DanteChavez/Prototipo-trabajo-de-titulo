# Prototipo: entorno de programación con JupyterHub

Prototipo del trabajo de título *Desarrollo de un software de apoyo a la práctica de
programación en laboratorios docentes*. En esta etapa **no hay Kubernetes ni un
contenedor por usuario**: un solo contenedor ejecuta JupyterHub y cada estudiante
trabaja con su propia cuenta Unix.

## Estructura

| Ruta | Contenido |
|---|---|
| `imagenes/Dockerfile_entornoProgramacion_base` | Ubuntu 24.04 + miniconda + Jupyter + librerías de Python |
| `imagenes/Dockerfile_entornoProgramacion_kernels` | Agrega los kernels de C++ y Java |
| `imagenes/Dockerfile_entornoProgramacion_latest` | Librerías extra y Jupyter Lab de un solo usuario |
| `imagenes/Dockerfile_entornoProgramacion_hub` | **JupyterHub + usuarios de prueba** (parte de `latest`) |
| `config/users.txt` | Usuarios de prueba (`usuario:contraseña`) |
| `config/crear_usuarios.py` | Crea las cuentas Unix a partir de `users.txt` durante el build |
| `config/jupyterhub_config.py` | Configuración de JupyterHub |
| `config/personalizacion/` | Logos y plantillas HTML con la identidad visual de la UV |
| `docker-compose.yml` | Levanta JupyterHub con sus volúmenes persistentes |
| `docker-compose.entorno.yml` | Levanta la imagen `latest` sola (Jupyter Lab sin login, etapa anterior) |

Cadena de imágenes: `base` → `kernels` → `latest` → `hub`.

## Cómo levantar JupyterHub

Desde la raíz del repositorio:

```
docker compose up --build
```

Luego abrir <http://localhost:8000> e ingresar con una cuenta de `config/users.txt`
(por ejemplo `alumno01` / `clave01`).

La imagen `hub` parte de `dantechavez0/entorno-programacion:latest`. Si esa imagen no
está en el Docker local, se descarga de Docker Hub. Para usar otra imagen de partida:

```
docker compose build --build-arg IMAGEN_ENTORNO=entorno-programacion:latest
```

## Cómo funciona

- **Usuarios.** `users.txt` se lee al construir la imagen: por cada línea se crea una
  cuenta Unix con su directorio `/home/<usuario>` (permisos 700). Los usuarios quedan
  dentro de la imagen, no se leen al arrancar.
- **Autenticación.** JupyterHub valida usuario y contraseña contra las cuentas Unix
  del contenedor (PAM). Solo pueden entrar las cuentas de `users.txt`.
- **Sesiones.** Al iniciar sesión, el Hub (que corre como root) lanza un servidor
  Jupyter como proceso del usuario autenticado. La raíz del explorador de archivos es
  `/home/<usuario>` y un usuario no puede leer el directorio de otro.
- **Persistencia.** `/home` es el volumen `homes_estudiantes`. Los archivos sobreviven
  a `docker compose down` y a la reconstrucción de la imagen.

## Apariencia

Las páginas del Hub (inicio de sesión, inicio y espera mientras arranca el entorno)
usan la identidad visual de la Universidad de Valparaíso según el *Manual de Normas
UV 2023*: azul institucional `#003c58`, azul oscuro `#002e38` y turquesa `#06717e`,
con los logos de la UV y de la Escuela de Ingeniería Informática.

- `config/personalizacion/templates/`: plantillas que heredan de las originales de
  JupyterHub y solo cambian colores, textos (en español) y logos.
  `page.html` es la base de todas las páginas (barra superior, colores y pie de página),
  y `login.html`, `home.html` y `spawn_pending.html` cambian cada página.
- `config/personalizacion/*.png`: logos recortados desde los originales de la UV.
- Se activan en `jupyterhub_config.py` (`template_paths`, `logo_file`, `template_vars`).

Esto solo afecta a las páginas de JupyterHub; JupyterLab mantiene su apariencia.

## Comprobaciones

Con el contenedor arriba y dos usuarios con sesión iniciada:

```
docker compose exec jupyterhub ps -eo user,pid,cmd
```

Debe mostrar `jupyterhub` como root y un `jupyterhub-singleuser` por cada usuario, con
su nombre. En una terminal de JupyterLab, `whoami` y `pwd` deben mostrar el usuario y
su `/home/<usuario>`, y `ls /home/<otro usuario>` debe dar `Permission denied`.

Persistencia: crear un archivo, ejecutar `docker compose down`, luego
`docker compose up` y comprobar que el archivo sigue ahí.

## Agregar o cambiar usuarios

1. Editar `config/users.txt` (agregar los usuarios nuevos **al final**).
2. `docker compose up --build`

Si se cambia el orden o se eliminan usuarios, los UID cambian y dejan de coincidir con
los archivos del volumen. En ese caso, o para partir de cero, borrar los volúmenes
(**elimina los archivos de todos los usuarios**):

```
docker compose down -v
```

## Construir la cadena completa (opcional)

Solo hace falta si se modifican `base`, `kernels` o `latest`. Desde la raíz, en este orden:

```
docker build --platform linux/amd64 -f imagenes/Dockerfile_entornoProgramacion_base    -t entorno-programacion:base    .
docker build --platform linux/amd64 -f imagenes/Dockerfile_entornoProgramacion_kernels -t entorno-programacion:kernels .
docker build --platform linux/amd64 -f imagenes/Dockerfile_entornoProgramacion_latest  -t entorno-programacion:latest -t dantechavez0/entorno-programacion:latest .
```

## Limitaciones conocidas de esta etapa

- Todas las sesiones comparten un contenedor: no hay límites de CPU ni memoria por
  usuario, y un proceso de un estudiante puede afectar a los demás.
- Las contraseñas de prueba están en texto plano en `users.txt` y en el historial de
  capas de la imagen. Sirven solo para pruebas.
- No hay usuarios profesor ni administrador.

## Origen

Los Dockerfiles `base`, `kernels` y `latest` derivan de JAPPY, de Gabriel Astudillo
Muñoz (<https://github.com/g-courses/jappy.rc>), y descargan archivos de ese repositorio
durante el build.
