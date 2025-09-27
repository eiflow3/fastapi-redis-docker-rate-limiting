# 🚀 Common Docker Desktop & CLI Commands

## 1. Start Docker Desktop
```bash
open -a Docker
```
- Opens Docker Desktop on macOS.  
- Make sure Docker Desktop is running before using `docker` or `docker compose`.

---

## 2. Stop Docker Desktop
```bash
docker desktop stop
```
- Quits Docker Desktop.  
- Alternatively, you can click the Docker whale icon in the menu bar → **Quit Docker Desktop**.

---

## 3. Run containers with Docker Compose
```bash
docker compose up --build
```
- Starts containers defined in `docker-compose.yml`.  
- `--build` forces a rebuild of images before starting.  
- Run this command in the **directory where your `docker-compose.yml` file is located**.

---

## 4. Check Docker system info
```bash
docker info
```
- Shows overall system information (e.g., number of containers, images, storage driver, memory usage).  
- Use this to confirm Docker is running correctly.

---

## 5. List running containers
```bash
docker ps
```
- Displays currently running containers.  
- Add `-a` to see **all containers** (including stopped ones):
  ```bash
  docker ps -a
  ```

---

## 6. Access Redis CLI inside a container
```bash
docker exec -it <redis-container-name-from-yml> redis-cli
```
- Opens Redis CLI inside the Redis container.  
- Example commands inside Redis CLI:
  ```bash
  KEYS *       # Show all keys in Redis
  GET key_name # Get the value of a specific key
  ```

---

## 7. Clean up build cache
```bash
docker builder prune
```
- Removes unused build cache.  
- Add `--all` for a full cleanup (but it will make the next build slower):
  ```bash
  docker builder prune --all
  ```

---

## 8. Check disk usage
```bash
docker system df
```
- Displays disk usage by:
  - Images
  - Containers
  - Volumes
  - Build cache  
- Use this to monitor how much space Docker is consuming.
