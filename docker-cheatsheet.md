Here’s an updated, more visual and task-oriented Docker cheat-sheet in Markdown. I’ve grouped commands into clear “workflows,” added icons for quick scanning, and highlighted key tips and “stop” actions where appropriate.

---

## 🚀 Setup & Iteration

> **Goal:** Quickly tear down any running containers, rebuild images, and spin up a fresh local environment.

```powershell
# 1. Ensure all containers are stopped and removed
docker-compose down

# 2. Build images and start services in detached mode
docker-compose up -d --build
```

> 🔑 **Tip:** Use `docker-compose down` instead of `stop`+`rm` so networks and volumes from your Compose project are cleaned up too.

---
## 🐍 Virtual Environments

| Command                                    | What it does                                |
|--------------------------------------------|---------------------------------------------|
| .\.venv\Scripts\Activate.ps1               | Activate the virtualenv (Windows PowerShell)|
| `deactivate`                               | Deactivate the current virtualenv           |



## 🔍 Status & Inspection

### List Services & Containers

```powershell
# Show running Compose services
docker-compose ps

# Show all containers (running + stopped)
docker ps -a
```

### Inspect Details

```powershell
# Detailed JSON info on a running container
docker inspect <container_name>
```

---

## 🛠️ Building & Updating

```powershell
# Rebuild images from Dockerfiles in your Compose file
docker-compose build

# Pull latest images from the registry
docker-compose pull

# Combine build + start
docker-compose up -d --build
```

---

## 📋 Logging & Debugging

### Viewing Logs

```powershell
# Show logs for all Compose services
docker-compose logs

# Follow all logs in real time
docker-compose logs -f

# Tail logs for one container
docker logs -f <container_name>
```

❓ **Stop “follow” mode:**  
Press <kbd>Ctrl</kbd>+<kbd>C</kbd> to exit any “-f” (follow) log command.

### Interactive Shell

```powershell
# Open a Bash shell inside the 'web' service container
docker-compose exec web bash
```

❓ **Exit the shell:**  
Type `exit` or press <kbd>Ctrl</kbd>+<kbd>D</kbd>.

---

## 📂 In-Container File Ops

```powershell
# Copy a file from container to host
docker cp <container>:/path/in/container ./local/path

# Copy a file from host into container
docker cp ./local/path <container>:/path/in/container
```

---

## 🧹 Cleaning Up

```powershell
# Stop and remove containers, networks, volumes created by Compose
docker-compose down

# Prune all unused Docker objects (containers, images, networks, build cache)
docker system prune
```

> ⚠️ **Warning:** `docker system prune` is *destructive*—it will remove any stopped containers, dangling images, unused networks, and build cache.

---

## ⚙️ Advanced Compose Usage

```powershell
# Use an alternate Compose file
docker-compose -f docker-compose.override.yml up -d

# Override the project name (default is folder name)
docker-compose -p myapp up
```

---

> **Pro Tip:**  
> - During development, mount your code into the container (`.:/app`) so edits appear instantly.  
> - In production, omit the volume mount to use the code baked into the image.