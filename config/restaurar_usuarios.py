#!/opt/miniconda3/bin/python
"""Sincroniza la base de datos y las cuentas del contenedor en cada arranque.

Lo ejecuta iniciar_hub.sh antes de abrir JupyterHub:

    restaurar_usuarios

1. Abre la base de datos del volumen (la crea vacía la primera vez).
2. Agrega los usuarios de la imagen que aún no están.
3. Regenera las cuentas Unix desde la base y sincroniza contraseña, rol y dueño de cada home.
"""
import os
import sys

# usuarios.py se instala en /usr/local/lib/usuarios-hub. La segunda ruta permite
# ejecutar el script desde config/ durante las pruebas.
sys.path[:0] = ["/usr/local/lib/usuarios-hub", os.path.dirname(os.path.realpath(__file__))]
import usuarios  # noqa: E402


def main():
    usuarios.exigir_root()
    if len(sys.argv) != 1:
        sys.exit(__doc__)
    con = usuarios.conectar()
    usuarios.incorporar_usuarios_imagen(con)
    usuarios.restaurar(con)


if __name__ == "__main__":
    main()
