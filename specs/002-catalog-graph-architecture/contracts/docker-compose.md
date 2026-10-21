# Contract: Local Disposable PostgreSQL Container (`docker-compose.yml`)

**Purpose**: Servicio PostgreSQL 17 desechable y aislado para desarrollo local y pruebas de integridad sin alterar datos ni paquetes del sistema operativo.

---

## 1. Configuración de Servicio (`docker-compose.yml`)

```yaml
services:
  db:
    image: postgres:17-alpine
    container_name: electrical_cpq_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: electrical_cpq
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres_dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d electrical_cpq"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
    driver: local
```

---

## 2. Variables de Conexión en `.env`

```ini
DATABASE_URL="postgres://postgres:postgres_dev_password@localhost:5432/electrical_cpq"
```

---

## 3. Ciclo de Vida y Manipulación Desechable

- **Iniciar base de datos**: `docker compose up -d db`
- **Verificar estado de salud**: `docker compose ps`
- **Resetear datos completamente (limpieza limpia)**:
  ```bash
  docker compose down -v
  docker compose up -d db
  uv run python manage.py migrate
  ```
- **Detener base de datos**: `docker compose down`
