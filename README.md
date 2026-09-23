# PortfolioQuant Engine

Motor cuantitativo de gestión de carteras. El usuario ingresa supuestos
mínimos (capital, aporte, horizonte, perfil de riesgo, objetivo) y el
sistema obtiene los datos de mercado/macro, calcula todo y recomienda
carteras según el riesgo elegido.

> **Estado:** Fase 1 (MVP) — cimientos: modelos de datos, ingesta,
> cálculo de retornos/volatilidad/riesgo y API básica.

## Plan por fases

1. **Fase 1 (actual):** ingesta y almacenamiento de datos, cálculo de
   retornos, volatilidad, covarianzas, correlaciones, drawdown, Sharpe y
   Sortino. API y dashboard básicos.
2. **Fase 2:** optimización de carteras (frontera eficiente, mínima
   varianza, máximo Sharpe, risk parity) y generador de propuestas.
3. **Fase 3:** riesgo avanzado (VaR, CVaR, solapamiento de ETFs, concentración).
4. **Fase 4:** simulación y pronóstico (Monte Carlo, probabilidad de meta,
   stress tests, escenarios históricos).
5. **Fase 5:** análisis de factores, Black-Litterman y estabilidad.

## Arranque liviano (decisión de la Fase 1)

Para poder correr en la máquina local desde el día uno:

- **Base de datos:** SQLite (archivo local, sin instalar nada).
- **Sin** Redis / Celery / Docker todavía; se suman cuando se necesiten.
- **Sin** Alembic todavía; las tablas se crean solas (`init_db`).

La capa de datos está abstraída, así que migrar a PostgreSQL más adelante
no obliga a reescribir el código.

## Cómo correr el backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt

# Levantar la API:
uvicorn app.main:app --reload
# -> http://127.0.0.1:8000/health   y   /docs (Swagger)

# Correr los tests:
pytest
```

## Estructura

```
portfolio-quant/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # Endpoints (Tarea 5)
│   │   ├── core/          # Config y conexión a la DB
│   │   ├── models/        # Modelos ORM (SQLAlchemy)
│   │   ├── schemas/       # Contratos de API (Pydantic)
│   │   ├── services/      # Proveedores de datos (Tarea 2)
│   │   └── quant/         # Motor de cálculo (Tarea 3)
│   ├── tests/             # Tests (unitarios + integración)
│   └── requirements.txt
└── frontend/              # Next.js (fase posterior)
```
