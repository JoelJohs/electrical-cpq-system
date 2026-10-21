# Contract: Health Check API Endpoint

**Interface**: HTTP REST Service  
**Path**: `/health/`  
**Method**: `GET`  
**Protocol**: HTTP/1.1, HTTP/2 via HTTPS (Port 443)  

---

## 1. Request Contract

### Headers
No se requieren cabeceras especiales de autenticación o cuerpo de petición.

```http
GET /health/ HTTP/1.1
Host: tu-dominio.com
User-Agent: curl/8.5.0
Accept: */*
```

---

## 2. Response Contract

### Success Response (200 OK)
Retornado cuando el proxy inverso Nginx, el socket Unix de Gunicorn y la aplicación Django están completamente operativos.

- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Max Latency**: `< 2000ms`

#### Payload Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "HealthCheckSuccessResponse",
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["ok"]
    }
  },
  "required": ["status"],
  "additionalProperties": false
}
```

#### Example Response Body
```json
{"status": "ok"}
```

---

## 3. Failure Response Contracts

### 502 Bad Gateway
Ocurre si Nginx no puede comunicarse con `/run/gunicorn.sock` (Gunicorn detenido o socket con permisos incorrectos).

- **Status Code**: `502 Bad Gateway`
- **Content-Type**: `text/html`
- **Interpretación por `check_phase2.sh`**: FAIL

### 504 Gateway Timeout
Ocurre si la aplicación Django no responde dentro del tiempo límite de proxy.

- **Status Code**: `504 Gateway Time-out`
- **Content-Type**: `text/html`
- **Interpretación por `check_phase2.sh`**: FAIL
