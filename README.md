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
| `config/users.txt` | Usuarios iniciales (`usuario:contraseña[:rol]`), leídos solo al construir |
| `config/crear_usuarios.py` | Crea, lista y restaura las cuentas Unix y las guarda en el registro persistente |
| `config/iniciar_hub.sh` | Arranque del contenedor: restaura las cuentas del registro y abre JupyterHub |
| `config/jupyterhub_config.py` | Configuración de JupyterHub |
| `config/personalizacion/` | Logos y plantillas HTML con la identidad visual de la UV |
| `logos/` | Logos originales (UV, Facultad de Ingeniería, Escuela de Ingeniería Informática) y *Manual de Normas UV 2023* |
| `docker-compose.yml` | Levanta JupyterHub con sus volúmenes persistentes |
| `docker-compose.entorno.yml` | Levanta la imagen `latest` sola (Jupyter Lab sin login, etapa anterior) |

Cadena de imágenes: `base` → `kernels` → `latest` → `hub`.

## Cómo levantar JupyterHub

Desde la raíz del repositorio:

```
docker compose up --build
```

Luego abrir <http://localhost:8000> e ingresar con una cuenta de `config/users.txt`
(por ejemplo `alumno1`).

La imagen `hub` parte de `dantechavez0/entorno-programacion:latest`. Si esa imagen no
está en el Docker local, se descarga de Docker Hub. Para usar otra imagen de partida:

```
docker compose build --build-arg IMAGEN_ENTORNO=entorno-programacion:latest
```

## Cómo funciona

- **Usuarios iniciales.** `users.txt` se lee al construir la imagen: por cada línea se
  crea una cuenta Unix con su directorio `/home/<usuario>` (permisos 700). El archivo
  se monta solo durante ese paso del build, así que no queda copiado en la imagen.
- **Registro persistente.** Cada cuenta se anota en `/var/lib/usuarios-hub/usuarios.txt`
  como `usuario:uid:rol:hash` (contraseña cifrada, nunca en texto plano). Esa carpeta es
  el volumen `usuarios_hub`: en el primer `docker compose up` Docker copia ahí el
  registro de la imagen, y desde entonces cada arranque lee **solo el volumen**.
- **Arranque.** `iniciar_hub.sh` ejecuta `crear_usuarios restaurar`, que recrea las
  cuentas del registro con su mismo UID (así siguen siendo dueñas de sus archivos en
  `/home`), y luego abre JupyterHub.
- **Roles.** `estudiante`, `profesor` y `admin`, cada uno un grupo Unix (`estudiantes`,
  `profesores`, `administradores`). Solo `administradores` puede usar `sudo` (con su
  propia contraseña) y ve el panel de administración del Hub. Por ahora el profesor
  tiene los mismos permisos que un estudiante.
- **Autenticación.** JupyterHub valida usuario y contraseña contra las cuentas Unix
  del contenedor (PAM). Solo entran las cuentas de los tres grupos de rol; la
  pertenencia se revisa en cada inicio de sesión, así que una cuenta nueva entra sin
  reiniciar el Hub.
- **Contraseñas.** Estudiantes y profesores no pueden cambiarla (`passwd` no tiene el
  bit setuid). Solo el admin las cambia, con el script.
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
- `config/personalizacion/*.png`: logos recortados desde los originales de `logos/`.
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

Usuarios y roles:

1. Como `admin`, en una terminal: `sudo whoami` pide la contraseña y responde `root`.
2. Como `admin`: `echo "alumno6:1234" > /tmp/n.txt && sudo crear_usuarios agregar /tmp/n.txt`.
   Sin reiniciar, `alumno6` puede iniciar sesión.
3. `docker compose down` y `docker compose up`: `alumno6` sigue pudiendo entrar, con sus
   archivos, y `docker compose exec jupyterhub crear_usuarios listar` muestra su mismo UID.
4. Como `alumno1` o `profesor1`: `sudo whoami` es rechazado, `passwd` falla y
   `/hub/admin` no está disponible.

## Agregar o cambiar usuarios

Con el Hub encendido, desde la terminal de JupyterLab de la cuenta `admin`:

```
sudo crear_usuarios agregar nuevos.txt     # nuevos.txt: usuario:contraseña[:rol]
sudo crear_usuarios clave alumno3          # cambia la contraseña
sudo crear_usuarios listar                 # usuarios, UID y rol
```

O desde la máquina que corre Docker, sin iniciar sesión:

```
docker compose cp nuevos.txt jupyterhub:/tmp/nuevos.txt
docker compose exec jupyterhub crear_usuarios agregar /tmp/nuevos.txt
```

Las cuentas nuevas pueden iniciar sesión de inmediato y se mantienen después de
`docker compose down` / `up`. Si un usuario ya existe, se omite. Conviene borrar el
archivo con las contraseñas después de usarlo.

`users.txt` solo se usa para la **primera** carga: cambiarlo después no tiene efecto
mientras exista el volumen `usuarios_hub`. Para partir de cero con los usuarios de
`users.txt` hay que borrar los volúmenes (**elimina los archivos de todos los usuarios**):

```
docker compose down -v
docker compose up --build
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
- Las contraseñas iniciales están en texto plano en `config/users.txt` (en el
  repositorio), aunque no en la imagen. Sirven solo para pruebas.
- El rol profesor todavía no tiene funciones propias (seguimiento de estudiantes).
- Las cuentas son locales; el inicio de sesión institucional (Microsoft) queda para
  una etapa futura.
- Un admin con `sudo` es root dentro del contenedor y puede leer los archivos de todos.

## Origen

Los Dockerfiles `base`, `kernels` y `latest` derivan de JAPPY, de Gabriel Astudillo
Muñoz (<https://github.com/g-courses/jappy.rc>), y descargan archivos de ese repositorio
durante el build.
