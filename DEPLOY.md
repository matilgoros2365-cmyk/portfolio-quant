# Publicar PortfolioQuant (deploy privado para compartir)

Guía para dejar la app online y compartir el link. Stack gratuito:

- **Frontend (la web):** Vercel
- **Backend (la API):** Render
- **Base de datos:** Neon (PostgreSQL) — para que los perfiles no se borren

Necesitás crear cuenta (gratis) en: GitHub, Neon, Render y Vercel. No hace falta
tarjeta para el plan gratis de ninguno (Render/Vercel/Neon free no la piden).

> Aviso: los perfiles no tienen login. Cualquiera con el link verá la lista de
> perfiles. Está bien para compartir entre amigos; para separar por usuario se
> agrega un login después.

---

## Paso 1 — Subir el código a GitHub

1. Creá un repositorio **privado** en https://github.com/new (ej: `portfolio-quant`). No agregues README.
2. En tu compu, desde `C:\dev\portfolio-quant`:

```bash
git remote add origin https://github.com/TU_USUARIO/portfolio-quant.git
git branch -M main
git push -u origin main
```

(Si te pide login, GitHub abre una ventana para autorizar.)

---

## Paso 2 — Base de datos (Neon, PostgreSQL)

1. Entrá a https://neon.tech y creá un proyecto (gratis).
2. Copiá el **connection string** (empieza con `postgresql://...`). Guardalo para el Paso 3.

---

## Paso 3 — Backend en Render

1. Entrá a https://render.com → **New +** → **Web Service** → conectá tu repo de GitHub.
2. Configuración:
   - **Root Directory:** `backend`
   - **Runtime:** Docker (detecta el `Dockerfile` solo)
   - **Instance Type:** Free
3. En **Environment**, agregá estas variables:
   - `FRED_API_KEY` = tu key de FRED
   - `OPENROUTER_API_KEY` = tu key de OpenRouter
   - `OPENROUTER_MODEL` = `nvidia/nemotron-3-super-120b-a12b:free`
   - `DATABASE_URL` = el connection string de Neon (Paso 2)
   - `CORS_ORIGINS` = lo completás en el Paso 5 (por ahora dejalo vacío o `*`)
4. Deploy. Cuando termine, copiá la URL del backend (ej: `https://portfolio-quant-api.onrender.com`).

> Nota: en el plan Free el backend "se duerme" tras ~15 min sin uso; la primera
> consulta después de dormir tarda ~1 minuto en despertar. Es normal.

---

## Paso 4 — Frontend en Vercel

1. Entrá a https://vercel.com → **Add New** → **Project** → importá tu repo.
2. Configuración:
   - **Root Directory:** `frontend`
   - Framework: Next.js (lo detecta solo)
3. En **Environment Variables**, agregá:
   - `NEXT_PUBLIC_API_URL` = la URL del backend + `/api/v1`
     (ej: `https://portfolio-quant-api.onrender.com/api/v1`)
4. Deploy. Cuando termine, copiá la URL del frontend (ej: `https://portfolio-quant.vercel.app`).

---

## Paso 5 — Conectar los dos (CORS)

1. Volvé a Render → tu servicio → Environment → editá `CORS_ORIGINS` y poné la URL
   del frontend (sin barra final):
   `https://portfolio-quant.vercel.app`
2. Guardá (Render redeploya solo).

Listo: compartí la URL de Vercel con tus amigos.

---

## Actualizar la app más adelante

Cada vez que hagas `git push` a `main`, Render y Vercel redeployan automáticamente.
