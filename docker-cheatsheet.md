## Getting Started
- **Start all services** (in the foreground):  
  ```bash
  docker-compose up
  ```
- **Start in detached mode** (background):  
  ```bash
  docker-compose up -d
  ```

## Common Status & Inspection
- **List running services** defined in your Compose file:  
  ```bash
  docker-compose ps
  ```
- **List all containers** (including stopped):  
  ```bash
  docker ps -a
  ```
- **Inspect a live container** (detailed JSON):  
  ```bash
  docker inspect <container_name>
  ```

## Stopping & Restarting
- **Stop services** (graceful):  
  ```bash
  docker-compose stop
  ```
- **Start previously stopped services**:  
  ```bash
  docker-compose start
  ```
- **Restart services** (stop + start):  
  ```bash
  docker-compose restart
  ```
- **Restart a single container**:  
  ```bash
  docker restart <container_name>
  ```

## Debugging & Logs
- **Show logs for all services**:  
  ```bash
  docker-compose logs
  ```
- **Follow logs in real time**:  
  ```bash
  docker-compose logs -f
  ```
- **Tail logs of a single container**:  
  ```bash
  docker logs -f <container_name>
  ```

## Rebuilding & Updating
- **Build (or rebuild) images** defined in Compose:  
  ```bash
  docker-compose build
  ```
- **Rebuild and (re)create containers** in one go:  
  ```bash
  docker-compose up -d --build
  ```
- **Pull fresh versions of images** from registry:  
  ```bash
  docker-compose pull
  ```

## Advanced Compose Flags
- **Specify an alternate Compose file**:  
  ```bash
  docker-compose -f docker-compose.override.yml up -d
  ```
- **Set a custom project name**:  
  ```bash
  docker-compose -p myapp up
  ```

## In-Container Operations
- **Execute a shell** inside a running service container:  
  ```bash
  docker-compose exec web bash
  ```
- **Copy files between host and container**:  
  ```bash
  docker cp <container>:/path/in/container ./local/path
  ```

## Cleaning Up
- **Stop and remove all containers, networks, volumes** created by Compose:  
  ```bash
  docker-compose down
  ```
- **Prune unused Docker objects** (containers, networks, images, build cache):  
  ```bash
  docker system prune
  ```

---

> **Tip:** For local development you often mount your code (`.:/app`), but remember this overrides what’s baked into the image. In production, drop the volume mount to use the image’s built-in files.
