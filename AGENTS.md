# AGENTS.md

## Context
Sistema web asistido por motor de reglas de compatibilidad eléctrica para la configuración de tableros, recomendación de piezas compatibles y generación de Lista de Materiales (BOM) sin errores para ejecutivos comerciales e ingenieros integradores de ABV ELECTRIC SUPPLY (Morelia, Michoacán).

- **Proyecto**: Sistema Web de Selección Basado en Reglas para la Recomendación de Piezas Compatibles y Armado de Tableros Eléctricos (CPQ)
- **Residente**: Joel Josafat Hernández Saucedo
- **Asesor Externo**: Ing. Octavio Trinidad Rodríguez Ramírez (Encargado de TI de ABV)
- **Periodo**: 01 de Agosto de 2026 – 18 de Diciembre de 2026

## Stack
- **Backend**: Python 3.12, Django 5, Django Ninja (API REST / OpenAPI)
- **Frontend**: Django Templates + Tailwind CSS + Alpine.js
- **Base de Datos**: PostgreSQL 17 (Docker Compose para desarrollo, SQLite como fallback en tests unitarios)
- **Calidad y Herramientas**: Ruff (linter y formateador), uv (gestor de paquetes), pre-commit
- **Despliegue Staging**: VPS Ubuntu 24.04 LTS con Systemd, Gunicorn, Nginx y Let's Encrypt SSL

## Expensive Decisions
- **Multi-tenant / Multi-org**: Ninguno. Monolito corporativo dedicado para ABV Electric Supply.
- **Modelo de Permisos y Roles**: Tres perfiles operativos:
  1. *Ejecutivo Comercial / Ventas*: Búsqueda rápida, recomendación inmediata de accesorios obligatorios y venta cruzada (*cross-selling*).
  2. *Ingeniero Integrador*: Armado asistido de tableros, verificación física de polos/ranuras/amperaje y despiece de materiales (*BOM*).
  3. *Administrador Técnico*: Gestión de familias, productos y reglas relacionales desde Django Admin.
  *Nota*: La consulta y configuración básica opera en autoservicio sin barreras de autenticación forzada.
- **Offline / Sincronización**: Ninguno. Sistema web en línea con validación centralizada en el servidor.
- **Multi-moneda / Facturación**: Ninguno. Cero precios monetarios en base de datos; la plataforma no procesa pagos, carritos de compra ni timbrado fiscal CFDI/SAT.

## Reglas de Arquitectura y Negocio
1. **Cero Precios en BD**: El sistema resuelve precisión de ingeniería y despiece (BOM); no compite ni se sincroniza con sistemas ERP contables en esta etapa.
2. **Autoridad Absoluta en el Backend**: Toda regla física (polos, ranuras, amperajes y compatibilidades) se valida en el motor del servidor.
3. **Grafo Dirigido Asimétrico**: Relaciones modeladas en `ProductCompatibility` con semántica explícita (`COMPATIBLE_WITH`, `REQUIRES`, `COMPLEMENT_OF`, `ALTERNATIVE_TO`).
4. **Consultas O(1)**: La resolución del árbol de compatibilidad debe operar en máximo 2 consultas SQL fijas (evitar antipatrón N+1).
5. **Sesión en Vivo / Desechable**: Las cotizaciones y la Lista de Materiales (BOM) se gestionan reactivamente en la sesión viva del cliente en el navegador, ofreciendo impresión directa (`window.print()`) sin ensuciar la base de datos con cotizaciones borrador.

## Comandos Esenciales
```bash
# Ejecutar suite de pruebas completa (37 tests)
uv run python manage.py test src.catalog.tests tests

# Formateo y revisión de código
uv run ruff check .
uv run ruff format --check .

# Servidor de base de datos Postgres de desarrollo
./scripts/db_dev.sh up
./scripts/db_dev.sh status

# Verificaciones de fase
./scripts/check_phase2.sh --local
./scripts/check_phase3.sh
```
