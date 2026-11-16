# Configuración de JupyterHub para la prueba de concepto con usuarios locales.
# Sin Kubernetes y sin un contenedor por usuario: el Hub y todas las sesiones
# viven en un mismo contenedor, y cada sesión es un proceso de la cuenta Unix
# del usuario que inició sesión.
import os
import pwd
import shutil

c = get_config()  # noqa: F821

# --- Red -------------------------------------------------------------------
c.JupyterHub.bind_url = "http://0.0.0.0:8000"

# El proxy vive en su propio entorno conda (ver Dockerfile_entornoProgramacion_hub).
# Se llama con el node de ese entorno porque el script empieza con "#!/usr/bin/env node",
# que buscaría node en el PATH en vez de usar el del entorno "proxy".
ENTORNO_PROXY = "/opt/miniconda3/envs/proxy/bin"
c.ConfigurableHTTPProxy.command = [
    f"{ENTORNO_PROXY}/node",
    f"{ENTORNO_PROXY}/configurable-http-proxy",
]

# --- Autenticación: cuentas Unix del contenedor (PAM) -----------------------
# Usuario y contraseña se validan contra /etc/passwd y /etc/shadow, que se
# llenaron al construir la imagen a partir de config/users.txt.
c.JupyterHub.authenticator_class = "jupyterhub.auth.PAMAuthenticator"
c.PAMAuthenticator.open_sessions = False  # las sesiones PAM no funcionan bien dentro de Docker

# Solo pueden entrar las cuentas de users.txt (no root, ni devuser, ni cuentas del sistema).
with open("/etc/jupyterhub/usuarios_permitidos.txt", encoding="utf-8") as f:
    c.Authenticator.allowed_users = {linea.strip() for linea in f if linea.strip()}

# --- Sesiones: un proceso Jupyter por usuario, con su UID -------------------
c.JupyterHub.spawner_class = "jupyterhub.spawner.LocalProcessSpawner"
c.Spawner.default_url = "/lab"         # se mantiene JupyterLab como interfaz
c.Spawner.notebook_dir = "~"           # la raíz del explorador de archivos es /home/<usuario>
c.Spawner.http_timeout = 120
c.Spawner.start_timeout = 120

# Variables de la imagen que el servidor de cada usuario también necesita.
c.Spawner.env_keep.extend([
    "LD_LIBRARY_PATH", "TZ", "LANGUAGE", "JUPYTER_NO_ANNOUNCEMENTS",
])


def asegurar_home(spawner):
    """Crea /home/<usuario> si no existe.

    Los homes se crean al construir la imagen, pero /home es un volumen
    persistente: si más adelante se agregan usuarios a users.txt y se
    reconstruye, el volumen antiguo no tiene sus carpetas.
    """
    cuenta = pwd.getpwnam(spawner.user.name)
    if os.path.isdir(cuenta.pw_dir):
        return
    shutil.copytree("/etc/skel", cuenta.pw_dir, symlinks=True)
    os.chown(cuenta.pw_dir, cuenta.pw_uid, cuenta.pw_gid)
    for raiz, carpetas, archivos in os.walk(cuenta.pw_dir):
        for nombre in carpetas + archivos:
            os.chown(os.path.join(raiz, nombre), cuenta.pw_uid, cuenta.pw_gid, follow_symlinks=False)
    os.chmod(cuenta.pw_dir, 0o700)


c.Spawner.pre_spawn_hook = asegurar_home

# --- Apariencia (identidad visual de la Universidad de Valparaíso) ----------
# Plantillas propias en /etc/jupyterhub/personalizacion/templates: heredan de las
# originales de JupyterHub y cambian colores, textos (en español) y logos.
import base64

PERSONALIZACION = "/etc/jupyterhub/personalizacion"
c.JupyterHub.template_paths = [f"{PERSONALIZACION}/templates"]
c.JupyterHub.logo_file = f"{PERSONALIZACION}/logo_uv_blanco.png"


def imagen_incrustada(nombre):
    """Devuelve el PNG como data URI para incrustarlo en el HTML.

    Así los logos viajan dentro de la página: no hace falta publicar archivos
    estáticos y el navegador no puede mostrar un logo antiguo guardado en caché
    (con /hub/logo seguía apareciendo el logo de JupyterHub de pruebas anteriores).
    """
    with open(f"{PERSONALIZACION}/{nombre}", "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


c.JupyterHub.template_vars = {
    "logo_barra": imagen_incrustada("logo_uv_blanco.png"),                  # barra superior
    "logo_login": imagen_incrustada("logo_informatica_azul.png"),          # login, modo claro
    "logo_login_oscuro": imagen_incrustada("logo_informatica_blanco.png"), # login, modo oscuro
}

# --- Estado del Hub ---------------------------------------------------------
# jupyterhub.sqlite y jupyterhub_cookie_secret quedan en el directorio de
# trabajo (/srv/jupyterhub), que el compose monta como volumen persistente.
