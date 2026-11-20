#!/opt/miniconda3/bin/python
"""Administra las cuentas Unix de JupyterHub y las guarda en un registro persistente.

Uso (siempre como root: en el build, en el arranque o con sudo desde la cuenta admin):

    crear_usuarios agregar ARCHIVO     crea las cuentas de ARCHIVO (usuario:contraseña[:rol])
    crear_usuarios clave USUARIO       cambia la contraseña de USUARIO
    crear_usuarios listar              muestra las cuentas del registro
    crear_usuarios restaurar           recrea las cuentas del registro (lo usa el arranque)

Roles: estudiante (por omisión), profesor y admin. Cada rol es un grupo Unix y
JupyterHub deja entrar a quien pertenezca a uno de esos grupos (allowed_groups),
por lo que una cuenta nueva puede iniciar sesión sin reiniciar el Hub.

Por qué hay un registro: las cuentas Unix viven en /etc/passwd y /etc/shadow, que son
parte del contenedor y se pierden al recrearlo. El registro guarda por cada cuenta
usuario:uid:rol:hash (la contraseña cifrada, nunca en texto plano) en un volumen, y
al arrancar el contenedor se recrean las cuentas con el MISMO UID, para que sigan
siendo dueñas de sus archivos en /home.
"""
import fcntl
import getpass
import os
import pwd
import re
import shutil
import subprocess
import sys

REGISTRO = os.environ.get("REGISTRO_USUARIOS", "/var/lib/usuarios-hub/usuarios.txt")
SKEL = "/etc/skel"
GRUPOS = {"estudiante": "estudiantes", "profesor": "profesores", "admin": "administradores"}
NOMBRE_VALIDO = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
UID_MINIMO = 1000          # mismo rango que useradd: el primer UID libre sobre el mayor en uso
UID_MAXIMO = 60000


def error(mensaje):
    sys.exit(f"error: {mensaje}")


def ejecutar(*comando, entrada=None):
    subprocess.run(comando, input=entrada, text=True, check=True)


# --- Registro -----------------------------------------------------------------

def leer_registro():
    """Devuelve {usuario: (uid, rol, hash)} en el orden del archivo."""
    cuentas = {}
    if not os.path.exists(REGISTRO):
        return cuentas
    with open(REGISTRO, encoding="utf-8") as f:
        for numero, linea in enumerate(f, start=1):
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            partes = linea.split(":")
            if len(partes) != 4:
                error(f"{REGISTRO}:{numero}: línea dañada")
            usuario, uid, rol, hash_clave = partes
            cuentas[usuario] = (int(uid), rol, hash_clave)
    return cuentas


def guardar_registro(cuentas):
    """Reescribe el registro completo de forma atómica (archivo temporal + rename)."""
    temporal = REGISTRO + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        f.write("# Generado por crear_usuarios. No editar a mano.\n")
        f.write("# usuario:uid:rol:hash de la contraseña\n")
        for usuario, (uid, rol, hash_clave) in cuentas.items():
            f.write(f"{usuario}:{uid}:{rol}:{hash_clave}\n")
    os.chmod(temporal, 0o600)
    os.replace(temporal, REGISTRO)


class Candado:
    """Evita que dos ejecuciones del script modifiquen el registro a la vez."""

    def __enter__(self):
        os.makedirs(os.path.dirname(REGISTRO), mode=0o700, exist_ok=True)
        self.archivo = open(REGISTRO + ".lock", "w")
        fcntl.flock(self.archivo, fcntl.LOCK_EX)
        return self

    def __exit__(self, *_):
        fcntl.flock(self.archivo, fcntl.LOCK_UN)
        self.archivo.close()


# --- Cuentas Unix ---------------------------------------------------------------

def existe_cuenta(usuario):
    try:
        pwd.getpwnam(usuario)
        return True
    except KeyError:
        return False


def hash_de(usuario):
    """Lee la contraseña cifrada de /etc/shadow (el módulo spwd ya no existe en Python 3.13)."""
    with open("/etc/shadow", encoding="utf-8") as f:
        for linea in f:
            campos = linea.split(":")
            if campos[0] == usuario:
                return campos[1]
    error(f"{usuario} no está en /etc/shadow")


def siguiente_uid(cuentas):
    usados = [uid for uid, _, _ in cuentas.values()]
    usados += [p.pw_uid for p in pwd.getpwall() if UID_MINIMO <= p.pw_uid < UID_MAXIMO]
    return max(usados + [UID_MINIMO]) + 1


def asegurar_grupos():
    for grupo in GRUPOS.values():
        ejecutar("groupadd", "-f", grupo)


def asegurar_home(usuario):
    """Crea /home/<usuario> desde /etc/skel si no existe (permisos 700)."""
    cuenta = pwd.getpwnam(usuario)
    if os.path.isdir(cuenta.pw_dir):
        return
    shutil.copytree(SKEL, cuenta.pw_dir, symlinks=True)
    for raiz, carpetas, archivos in os.walk(cuenta.pw_dir):
        os.chown(raiz, cuenta.pw_uid, cuenta.pw_gid)
        for nombre in carpetas + archivos:
            os.chown(os.path.join(raiz, nombre), cuenta.pw_uid, cuenta.pw_gid,
                     follow_symlinks=False)
    os.chmod(cuenta.pw_dir, 0o700)


def crear_cuenta(usuario, uid, rol, hash_clave=None):
    """Crea la cuenta con UID y grupo propio fijos. Si se da hash_clave, se usa tal cual."""
    comando = ["useradd", "--uid", str(uid), "--user-group", "--groups", GRUPOS[rol],
               "--no-create-home", "--home-dir", f"/home/{usuario}", "--shell", "/bin/bash"]
    if hash_clave:
        comando += ["--password", hash_clave]
    ejecutar(*comando, usuario)
    asegurar_home(usuario)


# --- Comandos ---------------------------------------------------------------------

def leer_archivo_usuarios(archivo):
    """Lee usuario:contraseña[:rol] y valida TODO antes de crear nada."""
    nuevos = []
    with open(archivo, encoding="utf-8") as f:
        for numero, linea in enumerate(f, start=1):
            linea = linea.strip()            # también quita el \r de archivos de Windows
            if not linea or linea.startswith("#"):
                continue
            partes = linea.split(":")
            if len(partes) not in (2, 3) or not partes[1]:
                error(f"{archivo}:{numero}: se esperaba usuario:contraseña[:rol]")
            usuario, clave = partes[0], partes[1]
            rol = partes[2] if len(partes) == 3 else "estudiante"
            if not NOMBRE_VALIDO.match(usuario):
                error(f"{archivo}:{numero}: nombre no válido: {usuario!r} "
                      "(solo minúsculas, números, - y _)")
            if rol not in GRUPOS:
                error(f"{archivo}:{numero}: rol no válido: {rol!r} "
                      f"(use {', '.join(GRUPOS)})")
            if usuario in [u for u, _, _ in nuevos]:
                error(f"{archivo}:{numero}: usuario repetido: {usuario}")
            nuevos.append((usuario, clave, rol))
    if not nuevos:
        error(f"{archivo}: no hay ningún usuario")
    return nuevos


def agregar(archivo):
    nuevos = leer_archivo_usuarios(archivo)
    with Candado():
        cuentas = leer_registro()
        asegurar_grupos()
        for usuario, clave, rol in nuevos:
            if usuario in cuentas:
                print(f"ya existe, se omite: {usuario}")
                continue
            if existe_cuenta(usuario):
                error(f"{usuario} es una cuenta del sistema, no se puede usar")
            uid = siguiente_uid(cuentas)
            crear_cuenta(usuario, uid, rol)
            ejecutar("chpasswd", entrada=f"{usuario}:{clave}\n")
            cuentas[usuario] = (uid, rol, hash_de(usuario))
            guardar_registro(cuentas)       # se guarda después de cada cuenta
            print(f"usuario creado: {usuario} (uid {uid}, rol {rol})  ->  /home/{usuario}")


def cambiar_clave(usuario):
    with Candado():
        cuentas = leer_registro()
        if usuario not in cuentas:
            error(f"{usuario} no está en el registro")
        if sys.stdin.isatty():
            clave = getpass.getpass(f"Nueva contraseña para {usuario}: ")
            if clave != getpass.getpass("Repetir contraseña: "):
                error("las contraseñas no coinciden")
        else:
            clave = sys.stdin.readline().strip()
        if not clave or ":" in clave:
            error("contraseña vacía o con ':'")
        ejecutar("chpasswd", entrada=f"{usuario}:{clave}\n")
        uid, rol, _ = cuentas[usuario]
        cuentas[usuario] = (uid, rol, hash_de(usuario))
        guardar_registro(cuentas)
        print(f"contraseña actualizada: {usuario}")


def listar():
    cuentas = leer_registro()
    print(f"{'usuario':<20} {'uid':>6}  rol")
    for usuario, (uid, rol, _) in cuentas.items():
        print(f"{usuario:<20} {uid:>6}  {rol}")


def restaurar():
    """Deja /etc/passwd, /etc/shadow y /etc/group como dice el registro."""
    with Candado():
        cuentas = leer_registro()
        asegurar_grupos()
        for usuario, (uid, rol, hash_clave) in cuentas.items():
            if not existe_cuenta(usuario):
                crear_cuenta(usuario, uid, rol, hash_clave)
                print(f"usuario restaurado: {usuario} (uid {uid}, rol {rol})")
                continue
            if pwd.getpwnam(usuario).pw_uid != uid:
                error(f"{usuario} existe con otro UID; revise la imagen o el registro")
            ejecutar("usermod", "--password", hash_clave, "--groups", GRUPOS[rol], usuario)
            asegurar_home(usuario)
        print(f"{len(cuentas)} cuentas en el registro")


def main():
    if os.geteuid() != 0:
        error("debe ejecutarse como root (use sudo)")
    argumentos = sys.argv[1:]
    if argumentos[:1] == ["agregar"] and len(argumentos) == 2:
        agregar(argumentos[1])
    elif argumentos[:1] == ["clave"] and len(argumentos) == 2:
        cambiar_clave(argumentos[1])
    elif argumentos == ["listar"]:
        listar()
    elif argumentos == ["restaurar"]:
        restaurar()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
