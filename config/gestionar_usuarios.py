#!/opt/miniconda3/bin/python
"""Uso:
    gestionar_usuarios agregar ARCHIVO           crea las cuentas de ARCHIVO (usuario:contraseña[:rol])
    gestionar_usuarios clave USUARIO             cambia la contraseña de USUARIO
    gestionar_usuarios eliminar USUARIO|ARCHIVO  elimina al usuario, o a los de ARCHIVO, con sus archivos
    gestionar_usuarios listar                    muestra usuarios, UID, rol, origen y fecha

Roles: estudiante (por omisión), profesor y admin.
"""
import os
import sys

# usuarios.py se instala en /usr/local/lib/usuarios-hub. La segunda ruta permite
# ejecutar el script desde config/ durante las pruebas.
sys.path[:0] = ["/usr/local/lib/usuarios-hub", os.path.dirname(os.path.realpath(__file__))]
import usuarios  # noqa: E402


def main():
    usuarios.exigir_root()
    args = sys.argv[1:]
    match args:
        case ["agregar", archivo]:
            usuarios.agregar(archivo)
        case ["clave", usuario]:
            usuarios.cambiar_clave(usuario)
        case ["eliminar", origen]:
            usuarios.eliminar(origen)
        case ["listar"]:
            usuarios.listar()
        case _:
            sys.exit(__doc__)


if __name__ == "__main__":
    main()
