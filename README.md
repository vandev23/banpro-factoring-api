# 🏦 BANPRO Factoring – API de Gestión de Operaciones de Factoring

API REST desarrollada en **Python + Django REST Framework** para la gestión de **Clientes**, **Facturas** y **Operaciones de Cesión**, implementando reglas de negocio reales del dominio de factoring, con trazabilidad, validaciones financieras y documentación OpenAPI.

---

## 🎯 Objetivo del proyecto

Este proyecto fue desarrollado como **prueba técnica** para BANPRO Factoring, priorizando:

- Correcta **modelación del dominio**
- Implementación explícita de **reglas de negocio**
- **Consistencia transaccional**
- **Trazabilidad** de operaciones
- Manejo consistente de errores
- Código claro, testeado y documentado

---

## 🏗️ Arquitectura general

- **Framework**: Django + Django REST Framework  
- **Base de datos**: PostgreSQL  
- **Infraestructura local**: Docker + docker-compose  
- **Documentación API**: OpenAPI 3 (drf-spectacular)  
- **Tests**: pytest + pytest-django + coverage  

Estructura por dominios:

```
core/           # utilidades transversales (errores, RUT, logging, middleware)
clientes/       # dominio clientes
facturas/       # dominio facturas
operaciones/    # dominio operaciones de cesión
config/         # settings y urls
```

---

## ⚙️ Requisitos

- Docker
- Docker Compose

---

## 🚀 Levantar el proyecto

```bash
git clone https://github.com/vandev23/banpro-factoring-api.git
cd banpro-factoring-api
cp .env.example .env
docker compose up --build -d
docker compose exec api python manage.py migrate
```

---

## 🌱 Datos de prueba

```bash
docker compose exec api python manage.py seed_clientes
docker compose exec api python manage.py seed_facturas --solo-disponibles
```

---

## 🧪 Tests

```bash
docker compose run --rm api pytest
```

Coverage mínimo configurado: **80%**

---

## 📚 Documentación API

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- OpenAPI JSON: http://localhost:8000/api/schema/

Los endpoints están etiquetados por dominio:
- Clientes
- Facturas
- Operaciones

---

## ❗ Manejo de errores (Error Wrapper)

La API implementa un **wrapper de errores estandarizado** para garantizar respuestas consistentes, claras y fáciles de consumir por clientes frontend o integraciones externas.

Todas las respuestas de error siguen la estructura:

```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "message": "La solicitud contiene datos inválidos",
  "errors": {
    "campo": "Descripción del error"
  }
}
```

### Tipos de errores manejados

- **VALIDATION_ERROR (400)**  
  Errores de reglas de negocio o validaciones de dominio  
  Ejemplo:
  - intento de desembolsar una operación no aprobada
  - línea de crédito insuficiente

- **NOT_FOUND (404)**  
  Recurso inexistente (cliente, factura u operación)

- **CONFLICT (409)**  
  Conflictos de estado o transiciones inválidas

- **INTERNAL_ERROR (500)**  
  Errores inesperados del sistema (registrados solo en logs)

### Diseño
- Los errores de negocio retornan códigos HTTP adecuados + mensajes explícitos
- Los errores técnicos se registran únicamente en logs
- El wrapper se implementa mediante un **exception handler global** en DRF
- Las respuestas evitan filtrar detalles internos del sistema

Este enfoque separa claramente:
- **Errores técnicos** → logging y monitoreo
- **Errores de negocio** → respuesta API y auditoría cuando aplica

---

## 🔎 Trazabilidad

- Logging técnico con `request_id` propagado por middleware
- Auditoría de negocio persistida por operación
- Cada evento de operación almacena:
  - estado anterior / nuevo
  - snapshot de datos relevantes
  - `request_id` asociado
- Historial consultable vía endpoint:

```http
GET /api/operaciones/{id}/eventos/
```

---

## 🧠 Decisiones técnicas destacadas

- Separación por dominios para facilitar escalabilidad
- Servicios transaccionales con `atomic` y `select_for_update`
- Acciones explícitas de dominio en lugar de PATCH genérico
- Wrapper de errores consistente y centralizado
- Auditoría desacoplada de logging técnico
- OpenAPI como contrato de integración

---

## 🧩 Bonus – Diseño futuro (no implementado)

### 🔔 Notificaciones asíncronas al aprobar una operación (AWS)

**Objetivo**  
Al aprobar una operación, disparar notificaciones (email y webhook) de forma **asíncrona**, **resiliente** y **sin impactar** la latencia de la API.

**Diseño propuesto (alineado a backend Django + AWS)**  
1. **Transacción de negocio (Django + PostgreSQL)**  
   En `aprobar_operacion()` se actualiza el estado y se registra un evento en una tabla `outbox_event` dentro de la misma transacción.

2. **Dispatcher asíncrono**  
   Un worker liviano (Celery/RQ o comando programado) lee eventos pendientes y los publica en un **Amazon SNS Topic** (`factoring-operaciones-topic`).

3. **Fan-out por consumidores (SNS → SQS)**  
   SNS distribuye el evento a colas SQS por tipo de consumidor:
   - `factoring-email-queue`
   - `factoring-webhook-queue`

4. **Procesamiento (AWS Lambda)**  
   - Lambda `email_notifier`: consume SQS y envía correos vía **Amazon SES**
   - Lambda `webhook_notifier`: consume SQS y ejecuta HTTP POST a endpoints externos

**Consistencia – Outbox Pattern**  
Garantiza que la operación aprobada y el evento de notificación sean consistentes, evitando pérdidas de eventos.

**Payload sugerido**
```json
{
  "event_id": "uuid",
  "type": "operacion.aprobada",
  "operacion_id": 123,
  "cliente_id": 45,
  "monto_a_desembolsar": "298000.00",
  "tasa_descuento": "2.00",
  "request_id": "..."
}
```

---

### 🗓️ Procesamiento batch de facturas vencidas

- Job diario (cron / Celery Beat / EventBridge Scheduler)
- Marca facturas vencidas según fecha y estado
- Procesamiento en batch para grandes volúmenes

---

### 🛠️ Migración desde stored procedures

- Identificación de SPs y reglas
- Tests de caracterización
- Implementación en servicios de dominio
- Ejecución paralela (dual-run)
- Cutover gradual con feature flags

---

## 👤 Vanessa Pacheco

Prueba técnica – Febrero 2026
