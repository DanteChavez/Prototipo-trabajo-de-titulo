# Spec: JupyterHub base con pods efímeros  (RF-06 / RNF-01 / RNF-05)

Estado: borrador
Hito: H0

## Problema y objetivo

El prototipo necesita un entorno donde cada estudiante ejecute código Python en un
contenedor aislado que se crea al hacer login y se destruye automáticamente por
inactividad. Este hito establece la infraestructura mínima: clúster k3d +
JupyterHub con KubeSpawner, sin persistencia ni autenticación real aún.

## Comportamiento esperado

1. Un usuario inicia sesión en JupyterHub con el autenticador simple (usuario/contraseña
   configurados en el values de Helm).
2. KubeSpawner crea un pod con la imagen `jupyter/scipy-notebook` (o equivalente
   ligera) en el namespace `jhub`.
3. El usuario trabaja en su notebook. Si cierra el navegador y no hay actividad
   durante **10 minutos**, el pod se destruye automáticamente (culling).
4. Al volver a ingresar, se le crea un pod nuevo (sin datos persistentes en este hito).
5. Un usuario no puede ver ni acceder al pod de otro usuario.

## Criterios de aceptación (cada uno debe tener una prueba)

- [ ] Dado un clúster k3d vacío, cuando se ejecuta el script de instalación, entonces
      JupyterHub queda disponible en `http://localhost` (o un puerto local definido).
- [ ] Dado un usuario válido del autenticador simple, cuando hace login, entonces se
      crea un pod en el namespace `jhub` (verificable con `kubectl get pods -n jhub`).
- [ ] Dado un pod activo, cuando han pasado 10 minutos sin actividad del kernel,
      entonces el pod es eliminado automáticamente (culling configurado).
- [ ] Dado dos usuarios distintos, cuando ambos tienen pods activos, entonces cada pod
      corre en su propio namespace de red y no puede alcanzar el pod del otro.
- [ ] Dado el clúster corriendo, cuando se ejecuta el script de smoke-test, entonces
      retorna exit 0 y muestra el estado de los pods.

## Fuera de alcance

- Volúmenes persistentes (eso es H1).
- Carga de usuarios reales desde CSV (eso es H2).
- Microsoft SSO / autenticación institucional.
- Múltiples nodos o alta disponibilidad.
- Imagen de notebook personalizada con librerías del curso.

## Diseño propuesto

### Archivos a crear

```
scripts/
  setup-cluster.sh      # crea clúster k3d, instala JupyterHub con Helm
  teardown-cluster.sh   # destruye el clúster k3d
  smoke-test.sh         # verifica que JupyterHub responde y el spawner funciona
infra/
  helm/
    jhub-values.yaml    # values de Helm para Zero to JupyterHub
```

### Configuración clave en `jhub-values.yaml`

```yaml
hub:
  config:
    DummyAuthenticator:
      password: "test1234"
    Authenticator:
      allowed_users:
        - alumno1
        - alumno2
        - profesor1

singleuser:
  image:
    name: jupyter/scipy-notebook
    tag: latest
  storage:
    type: none          # sin PVC en H0

cull:
  enabled: true
  timeout: 600          # 10 minutos de inactividad
  every: 60             # chequeo cada 60 s
```

### Clúster k3d

- Nombre: `jhub-dev`
- Puerto local mapeado: `80:80` (o `8080:80` si hay conflicto)
- Versión de k3s: la estable al momento de instalación (fijar en el script)

### Pruebas

`scripts/smoke-test.sh` hace:
1. `kubectl get pods -n jhub` — espera que el hub esté en Running.
2. `curl -s -o /dev/null -w "%{http_code}" http://localhost/hub/login` — espera 200.
3. Login programático con `curl` y credenciales de `alumno1` — espera redirección al
   spawner.

## Riesgos y preguntas abiertas

- **Puerto 80 ocupado en WSL2**: puede necesitar `8080:80`; decidir antes de instalar.
- **Tamaño de imagen**: `jupyter/scipy-notebook` es ~3 GB; evaluar usar
  `jupyter/base-notebook` para acelerar la demo.
- **Versión de Helm chart**: Zero to JupyterHub tiene versiones que rompen
  compatibilidad; fijar la versión en el script.
- **Culling en entorno de demo**: 10 min puede ser molesto durante la demostración;
  considerar un valor configurable por variable de entorno.

