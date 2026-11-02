# Spec: JupyterHub base con pods efímeros  (RF-06 / RNF-01 / RNF-05)

Estado: borrador
Hito: H0

## Problema y objetivo

El prototipo necesita un entorno donde cada estudiante ejecute código Python en un
contenedor aislado que se crea al hacer login y se destruye automáticamente por
inactividad. Este hito establece la infraestructura mínima: clúster k3d +
JupyterHub con KubeSpawner, sin persistencia ni autenticación real aún.

## Comportamiento esperado

1. Un usuario inicia sesión en JupyterHub en `http://localhost:8000` con el
   autenticador simple (DummyAuthenticator).
2. KubeSpawner crea un pod con la imagen
   `quay.io/jupyter/base-notebook:2024-08-26` en el namespace `jhub`.
3. El usuario trabaja en su notebook. Si no hay actividad del kernel durante
   **10 minutos** (configurable), el pod se destruye automáticamente (culling).
4. Al volver a ingresar, se le crea un pod nuevo (sin datos persistentes en este hito).
5. Cada pod corre sujeto a límites de recursos (memoria y CPU) compatibles con un
   equipo de 16 GB de RAM.
6. El tráfico de red entre pods de distintos usuarios queda bloqueado por
   NetworkPolicy; un pod no puede alcanzar a otro.
7. Los contenedores corren sin privilegios de root (`runAsNonRoot` a nivel de pod)
   ni escalación de privilegios (`allowPrivilegeEscalation: false` a nivel de
   contenedor).

## Criterios de aceptación (cada uno debe tener una prueba)

- [ ] **CA-1 Disponibilidad**: dado un clúster k3d vacío, cuando se ejecuta el
      script de instalación, entonces
      `curl http://localhost:8000/hub/login` retorna HTTP 200.
- [ ] **CA-2 Spawner**: dado un usuario válido del autenticador simple, cuando se
      crea su pod mediante la API de JupyterHub, entonces aparece un pod en
      el namespace `jhub` con estado `Running`.
- [ ] **CA-3 Culling**: dado un pod activo, cuando han pasado `$CULL_TIMEOUT`
      segundos (defecto 600) sin actividad del kernel, entonces el pod es eliminado
      automáticamente y `kubectl get pods -n jhub` deja de mostrarlo.
- [ ] **CA-4 Aislamiento de red**: dados dos pods activos (`alumno1` y `alumno2`),
      cuando se ejecuta `kubectl exec` en el pod de `alumno1` e intenta conectar al
      IP del pod de `alumno2` en el puerto 8888, entonces la conexión es rechazada o
      agota el tiempo (la NetworkPolicy la bloquea).
- [ ] **CA-5 Límites de recursos**: dado un pod recién creado, cuando se consultan
      sus recursos con `kubectl get pod <nombre> -n jhub -o jsonpath=...`, entonces
      `resources.limits.memory` = `512Mi` y `resources.limits.cpu` = `500m`
      (Kubernetes normaliza `0.5` → `500m` y `512M` → `512Mi`).
- [ ] **CA-6 Seguridad de contenedor**: dado un pod activo, cuando se consulta
      `.spec.securityContext` del pod, entonces contiene `runAsNonRoot: true`; y
      cuando se consulta `.spec.containers[0].securityContext`, entonces contiene
      `allowPrivilegeEscalation: false`.
- [ ] **CA-7 Idempotencia**: dado que el script de instalación ya fue ejecutado,
      cuando se ejecuta una segunda vez, entonces termina sin error (no falla por
      recursos ya existentes).

### Tabla criterio → prueba

Los pods de prueba para CA-2..CA-6 se crean sin navegador: el script usa la API
REST de JupyterHub (`POST /hub/api/users/<user>/server` con el token de admin)
para iniciar los pods de `alumno1` y `alumno2` de forma programática.

| Criterio | Script / comando de prueba |
|---|---|
| CA-1 Disponibilidad | `smoke-test.sh` → `curl -sf http://localhost:8000/hub/login` retorna 200 |
| CA-2 Spawner | `smoke-test.sh` → `POST /hub/api/users/alumno1/server` y luego `kubectl get pod jupyter-alumno1 -n jhub` muestra `Running` |
| CA-3 Culling | `smoke-test.sh` → espera `$CULL_TIMEOUT` + margen sin actividad y verifica que `kubectl get pod jupyter-alumno1 -n jhub` retorna `NotFound` |
| CA-4 Aislamiento | `smoke-test.sh` → crea pods de `alumno1` y `alumno2`, obtiene el IP del pod de `alumno2`, ejecuta `kubectl exec jupyter-alumno1 -n jhub -- timeout 5 bash -c "echo > /dev/tcp/<IP>/8888"` y verifica exit ≠ 0 |
| CA-5 Límites | `smoke-test.sh` → `kubectl get pod jupyter-alumno1 -n jhub -o jsonpath='{.spec.containers[0].resources.limits}'` y compara con `{"cpu":"500m","memory":"512Mi"}` |
| CA-6 Seguridad | `smoke-test.sh` → verifica `jsonpath='{.spec.securityContext.runAsNonRoot}'` = `true` y `jsonpath='{.spec.containers[0].securityContext.allowPrivilegeEscalation}'` = `false` |
| CA-7 Idempotencia | Ejecutar `setup-cluster.sh` dos veces seguidas; la segunda debe terminar con exit 0 |

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
  setup-cluster.sh      # crea clúster k3d (idempotente) e instala JupyterHub con Helm
  teardown-cluster.sh   # destruye el clúster k3d
  smoke-test.sh         # verifica criterios CA-1..CA-7
infra/
  helm/
    jhub-values.yaml    # values de Helm para Zero to JupyterHub
```

### Versiones fijadas (ADR 0003)

| Componente | Valor |
|---|---|
| Helm chart | `jupyterhub/jupyterhub` versión `4.4.4` (JupyterHub 5.5.4) |
| Imagen notebook | `quay.io/jupyter/base-notebook:2024-08-26` |
| k3s | `v1.35.5-k3s1` |

### Cómo llega el tráfico a localhost:8000

k3d crea el clúster con el flag `--port 8000:80@loadbalancer`, que mapea el
puerto 8000 del host al puerto 80 del contenedor del load balancer de k3d.
Dentro del clúster, el chart de JupyterHub crea el Service `proxy-public` de tipo
`LoadBalancer` en el namespace `jhub`, que expone el puerto 80. El load balancer
de k3d (ServiceLB / Klipper) enruta el tráfico entrante en su puerto 80 al
Service `proxy-public`, completando la cadena:

```
navegador → localhost:8000 → k3d LB (:80) → proxy-public Service (:80) → proxy pod → hub
```

### Configuración clave en `jhub-values.yaml`

```yaml
hub:
  config:
    JupyterHub:
      authenticator_class: dummy
    DummyAuthenticator:
      password: "test1234"
    Authenticator:
      allowed_users:
        - alumno1
        - alumno2
        - profesor1

singleuser:
  image:
    name: quay.io/jupyter/base-notebook
    tag: "2024-08-26"
  storage:
    type: none                  # sin PVC en H0
  memory:
    limit: 512M
    guarantee: 256M
  cpu:
    limit: 0.5
    guarantee: 0.1
  extraPodConfig:
    securityContext:
      runAsNonRoot: true        # a nivel de pod
  containerSecurityContext:
    allowPrivilegeEscalation: false  # a nivel de contenedor
  networkPolicy:
    enabled: true               # usa la NetworkPolicy del chart

cull:
  enabled: true
  timeout: 600                  # sobrescribible con CULL_TIMEOUT en el script
  every: 60
```

### Clúster k3d

- Nombre: `jhub-dev` (único nombre en todos los scripts)
- Puerto local: `8000:80@loadbalancer`
- Versión de k3s: `v1.35.5-k3s1`
- Los scripts son idempotentes: comprueban si el clúster ya existe antes de crearlo.

### NetworkPolicy

Se usa la NetworkPolicy integrada en el chart de Zero to JupyterHub
(`singleuser.networkPolicy.enabled: true`). Esta política restringe el tráfico
de entrada a los pods singleuser.

La prueba de aislamiento (CA-4) verifica empíricamente que un pod no puede
conectarse a otro. Si la política del chart resulta insuficiente, se agrega una
NetworkPolicy propia en `infra/k8s/network-policy.yaml` que **permita** tráfico
desde el proxy y el hub y bloquee el resto (deny-by-default para singleuser con
excepciones explícitas).

### Scripts (comportamiento esperado, sin código aún)

**`setup-cluster.sh`**
1. Si el clúster `jhub-dev` no existe, lo crea con
   `k3d cluster create jhub-dev --image rancher/k3s:v1.35.5-k3s1 -p 8000:80@loadbalancer`.
2. Agrega el repo Helm de JupyterHub si no está presente.
3. Ejecuta `helm upgrade --install jupyterhub jupyterhub/jupyterhub
   --namespace jhub --create-namespace --version 4.4.4
   --values infra/helm/jhub-values.yaml`.
4. Espera a que el pod del hub esté en `Running`.

**`smoke-test.sh`**
1. Verifica disponibilidad (CA-1).
2. Crea pods de prueba vía API de JupyterHub (CA-2).
3. Verifica límites (CA-5), seguridad (CA-6), aislamiento de red (CA-4).
4. Retorna `exit 0` si todo pasa, `exit 1` con mensaje descriptivo si algo falla.

## Riesgos y preguntas abiertas

- **Culling en demo**: el timeout de 10 min por defecto puede interrumpir la
  demostración; el script debe permitir sobreescribirlo con `CULL_TIMEOUT=<seg>`.
- **NetworkPolicy y k3s**: k3s trae un controlador de políticas de red integrado
  (basado en kube-router). Debería funcionar sin instalar nada adicional, pero
  hay que verificar empíricamente con la prueba de aislamiento (CA-4). Solo si
  la prueba falla se evaluaría instalar un CNI alternativo.
