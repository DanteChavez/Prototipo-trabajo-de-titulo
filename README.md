## Preparar el entorno (Windows 10 + WSL2)

Todo el proyecto se ejecuta dentro de WSL2 con Docker Engine (sin Docker Desktop), de modo que el
PC de desarrollo y el de la demostración se comporten igual.

### 1. En Windows (PowerShell como administrador, una sola vez)
```powershell
wsl --install -d Ubuntu
```
Reinicia si lo pide y crea tu usuario de Linux. Luego limita la memoria de WSL2:
```powershell
notepad $env:USERPROFILE\.wslconfig
```
Contenido (para un PC de 16 GB; en uno de 32 GB puedes subir `memory`):
```ini
[wsl2]
memory=8GB
processors=4
swap=2GB
```
El archivo debe llamarse exactamente `.wslconfig`, sin `.txt`.

### 2. Activar systemd (dentro de Ubuntu)
```bash
sudo nano /etc/wsl.conf
```
Debe contener:
```ini
[boot]
systemd=true
```
Guarda (`Ctrl+O`, `Enter`, `Ctrl+X`) y reinicia WSL desde PowerShell:
```powershell
wsl --shutdown
```

### 3. Instalar las herramientas (dentro de Ubuntu)
Clona o copia el proyecto en el disco de Linux, **no** en `/mnt/c/`:
```bash
mkdir -p ~/proyectos && cd ~/proyectos
# (descomprime o clona aquí el proyecto) y entra en su carpeta
bash scripts/setup-wsl.sh
```
Si el script indica que se cambió el grupo `docker`, ejecuta `wsl --shutdown` en PowerShell y abre
Ubuntu de nuevo.

Versiones fijadas: k3d v5.9.0, kubectl v1.35.5, Helm v3.22.1 (ver `docs/adr/0003-versiones-jupyterhub.md`).
Docker y uv se instalan en su última versión.

### 4. Verificar
```bash
bash scripts/check-tools.sh
docker run --rm hello-world
```
Todas las líneas deben decir `OK`. Si Docker Desktop está instalado, mantenlo cerrado mientras trabajas.

### Problemas frecuentes
| Síntoma | Solución |
|---|---|
| `permission denied ... docker.sock` | Tu usuario no está en el grupo `docker`: `sudo usermod -aG docker $USER`, luego `wsl --shutdown` y abre Ubuntu de nuevo. |
| `uv: command not found` | `source ~/.bashrc` o abre una terminal nueva (uv queda en `~/.local/bin`). |
| `ps -p 1` no responde `systemd` | Revisa `/etc/wsl.conf` y ejecuta `wsl --shutdown`. |
| Docker no arranca | `sudo systemctl start docker` y `systemctl status docker`. |
| `free -h` muestra más RAM de la esperada | `.wslconfig` mal nombrado o sin `wsl --shutdown` posterior. |
| Todo va lento | El proyecto está en `/mnt/c/`: muévelo a `~/proyectos`. |