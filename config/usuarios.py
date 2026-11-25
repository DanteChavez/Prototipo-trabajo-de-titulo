"""Gestión de las cuentas de JupyterHub y de su base de datos persistente.

Módulo común de tres scripts, uno por cada momento del ciclo de vida:

    cargar_usuarios_iniciales   build de la imagen: convierte users.txt en los usuarios de la imagen
    restaurar_usuarios          cada arranque del contenedor: regenera las cuentas desde la BD
    gestionar_usuarios          administrador, con sudo: agregar, cambiar contraseña, eliminar y listar

Ubicación de los datos:

    Base de datos          /var/lib/usuarios-hub/usuarios.db (volumen usuarios_hub, SQLite).
                           Fuente oficial: nombre, UID, rol y contraseña cifrada de cada usuario.
    Usuarios de la imagen  /etc/usuarios-hub/usuarios_imagen.txt (dentro de la imagen).
                           Contenido de users.txt en el último build, con las contraseñas cifradas.
    Cuentas Unix           /etc/passwd, /etc/shadow y /etc/group (dentro del contenedor).
                           Las usan PAM, el lanzador de sesiones y los permisos de /home. Se
                           pierden al recrear el contenedor y se regeneran desde la BD.

Cada rol es un grupo Unix. JupyterHub admite a los miembros de esos grupos, por lo que los
cambios de usuarios rigen sin reiniciar el Hub.
"""
import contextlib
import getpass
import grp
import os
import pwd
import re
import shutil
import sqlite3
import subprocess
import sys
import time

BD = os.environ.get("BD_USUARIOS", "/var/lib/usuarios-hub/usuarios.db")
USUARIOS_IMAGEN = os.environ.get("USUARIOS_IMAGEN", "/etc/usuarios-hub/usuarios_imagen.txt")
SKEL = "/etc/skel"
GRUPOS = {"estudiante": "estudiantes", "profesor": "profesores", "admin": "administradores"}
NOMBRE_VALIDO = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
UID_MINIMO = 1000
UID_MAXIMO = 60000

ESQUEMA = """
CREATE TABLE IF NOT EXISTS rol (
    id          INTEGER PRIMARY KEY,
    nombre      TEXT NOT NULL UNIQUE,
    grupo_unix  TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS usuario (
    id                 INTEGER PRIMARY KEY,
    nombre             TEXT    NOT NULL UNIQUE,
    uid                INTEGER NOT NULL UNIQUE CHECK (uid >= 1000 AND uid < 60000),
    rol_id             INTEGER NOT NULL REFERENCES rol(id),
    hash_clave         TEXT    NOT NULL,
    home               TEXT    NOT NULL UNIQUE,
    origen             TEXT    NOT NULL CHECK (origen IN ('users.txt', 'admin')),
    creado_en          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    clave_cambiada_en  TEXT
);
"""


# --- Utilidades ------------------------------------------------------------------------

def error(mensaje):
    """Muestra el mensaje y termina con código de salida 1."""
    sys.exit(f"error: {mensaje}")


def ejecutar(*comando, entrada=None):
    """Ejecuta un comando del sistema y termina con un mensaje claro si falla."""
    resultado = subprocess.run(comando, input=entrada, text=True, capture_output=True)
    if resultado.returncode != 0:
        error(f"falló {comando[0]}: {resultado.stderr.strip()}")


def exigir_root():
    """Termina si el proceso no se ejecuta como root."""
    if os.geteuid() != 0:
        error("debe ejecutarse como root (use sudo)")


def pedir_clave(usuario):
    """Pide la contraseña dos veces en la terminal, o la lee de la entrada estándar."""
    if sys.stdin.isatty():
        clave = getpass.getpass(f"Nueva contraseña para {usuario}: ")
        if clave != getpass.getpass("Repetir contraseña: "):
            error("las contraseñas no coinciden")
    else:
        clave = sys.stdin.readline().strip()
    if not clave or ":" in clave:
        error("la contraseña no puede estar vacía ni contener ':'")
    return clave


# --- Base de datos ---------------------------------------------------------------------

def conectar():
    """Abre la base de datos, creando las tablas y los roles si no existen."""
    os.makedirs(os.path.dirname(BD), mode=0o700, exist_ok=True)
    con = sqlite3.connect(BD, timeout=30, isolation_level=None)
    os.chmod(BD, 0o600)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(ESQUEMA)
    con.executemany("INSERT OR IGNORE INTO rol (nombre, grupo_unix) VALUES (?, ?)",
                    GRUPOS.items())
    return con


@contextlib.contextmanager
def transaccion(con):
    """Agrupa las operaciones en una transacción exclusiva. Si algo falla, se deshace."""
    con.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        con.execute("ROLLBACK")
        raise
    con.execute("COMMIT")


def leer_usuarios(con):
    """Devuelve {nombre: (uid, rol, hash)} en orden de creación."""
    filas = con.execute("""SELECT u.nombre, u.uid, r.nombre, u.hash_clave
                           FROM usuario u JOIN rol r ON r.id = u.rol_id
                           ORDER BY u.id""")
    return {nombre: (uid, rol, hash_clave) for nombre, uid, rol, hash_clave in filas}


def insertar_usuario(con, nombre, uid, rol, hash_clave, origen):
    """Inserta un usuario. La base rechaza nombres, UID o directorios repetidos."""
    con.execute("""INSERT INTO usuario (nombre, uid, rol_id, hash_clave, home, origen)
                   VALUES (?, ?, (SELECT id FROM rol WHERE nombre = ?), ?, ?, ?)""",
                (nombre, uid, rol, hash_clave, f"/home/{nombre}", origen))


# --- Usuarios de la imagen -------------------------------------------------------------

def generar_usuarios_imagen(archivo):
    """Escribe los usuarios de la imagen (usuario:rol:hash) a partir de users.txt.

    Se ejecuta en el build, cuando el volumen de la base de datos aún no existe.
    """
    nuevos = leer_archivo_usuarios(archivo)
    lineas = [f"{usuario}:{rol}:{cifrar(clave)}\n" for usuario, clave, rol in nuevos]
    os.makedirs(os.path.dirname(USUARIOS_IMAGEN), mode=0o700, exist_ok=True)
    temporal = USUARIOS_IMAGEN + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        f.write("# Usuarios de users.txt del último build. Generado, no editar.\n")
        f.writelines(lineas)
    os.chmod(temporal, 0o600)
    os.replace(temporal, USUARIOS_IMAGEN)
    for usuario, _, rol in nuevos:
        print(f"en los usuarios de la imagen: {usuario} (rol {rol})")


def cifrar(clave):
    """Devuelve el hash de la contraseña con el mismo formato de /etc/shadow.

    Python 3.13 ya no incluye el módulo crypt, por lo que se usa chpasswd sobre una
    cuenta temporal sin inicio de sesión.
    """
    temporal = "cifrado-tmp"
    ejecutar("useradd", "--no-create-home", "--shell", "/usr/sbin/nologin", temporal)
    try:
        ejecutar("chpasswd", entrada=f"{temporal}:{clave}\n")
        return hash_de(temporal)
    finally:
        subprocess.run(["userdel", temporal], capture_output=True)


def incorporar_usuarios_imagen(con):
    """Agrega a la base de datos los usuarios de la imagen que aún no tiene.

    No modifica a los usuarios existentes. El UID se elige contra la base para no
    repetir uno ya asignado.
    """
    if not os.path.exists(USUARIOS_IMAGEN):
        return
    with open(USUARIOS_IMAGEN, encoding="utf-8") as f:
        de_la_imagen = [l.strip().split(":") for l in f if l.strip() and not l.startswith("#")]
    with transaccion(con):
        cuentas = leer_usuarios(con)
        for usuario, rol, hash_clave in de_la_imagen:
            if usuario in cuentas:
                continue
            uid = siguiente_uid(cuentas)
            insertar_usuario(con, usuario, uid, rol, hash_clave, "users.txt")
            cuentas[usuario] = (uid, rol, hash_clave)
            print(f"nuevo en users.txt, se agrega a la BD: {usuario} (uid {uid}, rol {rol})")


# --- Cuentas Unix ----------------------------------------------------------------------

def existe_cuenta(usuario):
    """True si el usuario está en /etc/passwd."""
    try:
        pwd.getpwnam(usuario)
        return True
    except KeyError:
        return False


def existe_grupo(nombre):
    """True si el grupo está en /etc/group."""
    try:
        grp.getgrnam(nombre)
        return True
    except KeyError:
        return False


def hash_de(usuario):
    """Devuelve el hash de la contraseña del usuario guardado en /etc/shadow."""
    with open("/etc/shadow", encoding="utf-8") as f:
        for linea in f:
            campos = linea.split(":")
            if campos[0] == usuario:
                return campos[1]
    error(f"{usuario} no está en /etc/shadow")


def siguiente_uid(cuentas):
    """Primer UID libre: no lo usa la base, ni una cuenta, ni un directorio de /home."""
    usados = [uid for uid, _, _ in cuentas.values()]
    usados += [p.pw_uid for p in pwd.getpwall()]
    if os.path.isdir("/home"):
        usados += [os.stat(os.path.join("/home", n)).st_uid for n in os.listdir("/home")]
    usados = [uid for uid in usados if UID_MINIMO <= uid < UID_MAXIMO]
    return max(usados + [UID_MINIMO]) + 1


def asegurar_grupos():
    """Crea los grupos de rol que falten."""
    for grupo in GRUPOS.values():
        ejecutar("groupadd", "-f", grupo)


def asegurar_home(usuario):
    """Crea /home/<usuario> desde /etc/skel si no existe, con permisos 700."""
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


def corregir_dueno_home(usuario):
    """Asigna /home/<usuario> a su UID si pertenece a otro (por ejemplo, tras recrear la cuenta)."""
    cuenta = pwd.getpwnam(usuario)
    datos = os.stat(cuenta.pw_dir)
    if (datos.st_uid, datos.st_gid) == (cuenta.pw_uid, cuenta.pw_gid):
        return
    ejecutar("chown", "-R", f"{cuenta.pw_uid}:{cuenta.pw_gid}", cuenta.pw_dir)
    print(f"dueño corregido: {cuenta.pw_dir}  (uid {datos.st_uid} -> {cuenta.pw_uid})")


def crear_cuenta(usuario, uid, rol, hash_clave=None):
    """Crea la cuenta Unix con UID y grupo de rol fijos, y su directorio personal."""
    comando = ["useradd", "--uid", str(uid), "--user-group", "--groups", GRUPOS[rol],
               "--no-create-home", "--home-dir", f"/home/{usuario}", "--shell", "/bin/bash"]
    if hash_clave:
        comando += ["--password", hash_clave]
    ejecutar(*comando, usuario)
    asegurar_home(usuario)
    corregir_dueno_home(usuario)


def detener_procesos(usuario, espera=10):
    """Termina los procesos del usuario, incluida su sesión de JupyterLab."""
    subprocess.run(["pkill", "-KILL", "-u", usuario], capture_output=True)
    limite = time.monotonic() + espera
    while subprocess.run(["pgrep", "-u", usuario], capture_output=True).returncode == 0:
        if time.monotonic() > limite:
            error(f"no se pudieron detener los procesos de {usuario}")
        time.sleep(0.2)


def eliminar_cuenta(usuario):
    """Elimina la cuenta Unix, su grupo personal y su directorio /home/<usuario>."""
    if existe_cuenta(usuario):
        home = pwd.getpwnam(usuario).pw_dir
        detener_procesos(usuario)
        ejecutar("userdel", usuario)
    else:
        home = f"/home/{usuario}"
    if os.path.isdir(home):
        shutil.rmtree(home)


# --- Operaciones del administrador -----------------------------------------------------

def leer_archivo_usuarios(archivo):
    """Lee y valida un archivo usuario:contraseña[:rol]. Devuelve [(usuario, clave, rol)].

    Valida el archivo completo antes de devolver nada, para no crear solo una parte.
    """
    nuevos = []
    with open(archivo, encoding="utf-8") as f:
        for numero, linea in enumerate(f, start=1):
            linea = linea.strip()
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
    """Crea las cuentas del archivo y las registra en la base. Omite las que ya existen."""
    nuevos = leer_archivo_usuarios(archivo)
    con = conectar()
    asegurar_grupos()
    cuentas = leer_usuarios(con)
    ocupados = [u for u, _, _ in nuevos
                if u not in cuentas and (existe_cuenta(u) or existe_grupo(u))]
    if ocupados:
        error("estos nombres ya los usa el sistema (cuenta o grupo): "
              f"{', '.join(ocupados)}. No se creó ninguna cuenta")
    for usuario, clave, rol in nuevos:
        with transaccion(con):
            cuentas = leer_usuarios(con)
            if usuario in cuentas:
                print(f"ya existe, se omite: {usuario}")
                continue
            uid = siguiente_uid(cuentas)
            crear_cuenta(usuario, uid, rol)
            ejecutar("chpasswd", entrada=f"{usuario}:{clave}\n")
            insertar_usuario(con, usuario, uid, rol, hash_de(usuario), "admin")
        print(f"usuario creado: {usuario} (uid {uid}, rol {rol})  ->  /home/{usuario}")


def cambiar_clave(usuario):
    """Cambia la contraseña de un usuario en su cuenta y en la base."""
    con = conectar()
    if usuario not in leer_usuarios(con):
        error(f"{usuario} no está en la base de datos")
    clave = pedir_clave(usuario)
    with transaccion(con):
        ejecutar("chpasswd", entrada=f"{usuario}:{clave}\n")
        con.execute("""UPDATE usuario SET hash_clave = ?,
                              clave_cambiada_en = datetime('now', 'localtime')
                       WHERE nombre = ?""", (hash_de(usuario), usuario))
    print(f"contraseña actualizada: {usuario}")


def leer_nombres(origen):
    """Devuelve los nombres a eliminar: el de ORIGEN o los de un archivo, uno por línea.

    Del archivo se toma lo que está antes del primer ':', por lo que sirve el mismo
    archivo usado para agregar.
    """
    if not os.path.isfile(origen):
        return [origen]
    nombres = []
    with open(origen, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea and not linea.startswith("#"):
                nombre = linea.split(":")[0]
                if nombre not in nombres:
                    nombres.append(nombre)
    if not nombres:
        error(f"{origen}: no hay ningún usuario")
    return nombres


def eliminar(origen):
    """Elimina usuarios: su registro en la base, su cuenta Unix y su directorio personal.

    ORIGEN es un nombre de usuario o un archivo con un usuario por línea. Las
    restricciones se revisan para todos antes de eliminar a alguno. Un usuario
    eliminado puede volver a agregarse.
    """
    nombres = leer_nombres(origen)
    con = conectar()
    cuentas = leer_usuarios(con)
    for usuario in [n for n in nombres if n not in cuentas]:
        print(f"no está en la base de datos, se omite: {usuario}")
    nombres = [n for n in nombres if n in cuentas]
    if os.environ.get("SUDO_USER") in nombres:
        error("un administrador no puede eliminar su propia cuenta. No se eliminó ninguno")
    admins = [n for n, (_, rol, _) in cuentas.items() if rol == "admin"]
    if admins and all(a in nombres for a in admins):
        error("no se puede eliminar a todos los administradores. No se eliminó ninguno")
    for usuario in nombres:
        with transaccion(con):
            origen_usuario = con.execute("SELECT origen FROM usuario WHERE nombre = ?",
                                         (usuario,)).fetchone()[0]
            con.execute("DELETE FROM usuario WHERE nombre = ?", (usuario,))
            eliminar_cuenta(usuario)
        print(f"usuario eliminado: {usuario} (base de datos, cuenta y /home/{usuario})")
        if origen_usuario == "users.txt":
            print(f"  aviso: {usuario} viene de users.txt y se volverá a crear en el próximo "
                  "arranque si sigue en ese archivo")


def listar():
    """Muestra usuario, UID, rol, origen y fecha de creación."""
    con = conectar()
    filas = con.execute("""SELECT u.nombre, u.uid, r.nombre, u.origen, u.creado_en
                           FROM usuario u JOIN rol r ON r.id = u.rol_id ORDER BY u.id""")
    print(f"{'usuario':<20} {'uid':>6}  {'rol':<11} {'origen':<10} creado")
    for nombre, uid, rol, origen, creado in filas:
        print(f"{nombre:<20} {uid:>6}  {rol:<11} {origen:<10} {creado}")


# --- Arranque --------------------------------------------------------------------------

def restaurar(con):
    """Deja /etc/passwd, /etc/shadow y /etc/group como indica la base de datos.

    Crea las cuentas que faltan con su UID y contraseña de la base (al recrear el
    contenedor no existe ninguna) y sincroniza contraseña, rol y dueño del directorio
    de las que ya existen.
    """
    with transaccion(con):
        cuentas = leer_usuarios(con)
        asegurar_grupos()

        for usuario, (uid, rol, hash_clave) in cuentas.items():
            if not existe_cuenta(usuario):
                try:
                    ocupado = pwd.getpwuid(uid).pw_name
                except KeyError:
                    ocupado = None
                if ocupado:
                    error(f"el UID {uid} de {usuario} lo usa la cuenta {ocupado}")
                crear_cuenta(usuario, uid, rol, hash_clave)
                print(f"usuario restaurado: {usuario} (uid {uid}, rol {rol})")
                continue
            if pwd.getpwnam(usuario).pw_uid != uid:
                error(f"la cuenta {usuario} tiene otro UID que la base de datos")
            ejecutar("usermod", "--password", hash_clave, "--groups", GRUPOS[rol], usuario)
            asegurar_home(usuario)
            corregir_dueno_home(usuario)
        print(f"{len(cuentas)} usuarios en la base de datos")
