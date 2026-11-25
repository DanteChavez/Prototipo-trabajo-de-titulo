#!/opt/miniconda3/bin/python
"""Genera los usuarios de la imagen durante el build.

Lo ejecuta el Dockerfile del hub, con users.txt montado solo durante ese paso:

    cargar_usuarios_iniciales /tmp/users.txt

Escribe /etc/usuarios-hub/usuarios_imagen.txt (usuario:rol:contraseña cifrada). No crea
cuentas ni escribe en la base de datos, porque el volumen no existe durante el build.
restaurar_usuarios incorpora estos usuarios en el arranque.
"""
import os
import sys

# usuarios.py se instala en /usr/local/lib/usuarios-hub. La segunda ruta permite
# ejecutar el script desde config/ durante las pruebas.
sys.path[:0] = ["/usr/local/lib/usuarios-hub", os.path.dirname(os.path.realpath(__file__))]
import usuarios  # noqa: E402


def main():
    usuarios.exigir_root()
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    usuarios.generar_usuarios_imagen(sys.argv[1])


if __name__ == "__main__":
    main()
