# PortfolioQuant — Diseño del onboarding y perfilado (para revisar antes de implementar)

> Estado: PROPUESTA para revisión. No implementar hasta aprobación.
> Objetivo: que alguien que no sabe nada de inversiones pueda usar PortfolioQuant
> como si hablara con un asesor. El usuario aporta contexto humano; el sistema
> traduce eso a parámetros cuantitativos, de forma **auditable**.

---

## 1. Cómo encaja con el código actual

El onboarding es una **capa nueva por delante** del motor. Casi todo lo que
infiere ya lo consume el backend.

| El onboarding infiere | Alimenta (ya existe) |
|---|---|
| horizonte | `investment_horizon_years` |
| capital / aportes / estabilidad | `initial_capital`, `monthly_contribution` (con *haircut* si la estabilidad es baja) |
| objetivo | `target_wealth` |
| capacidad + tolerancia → **nivel continuo [0,1]** | reemplaza `risk_profile` → `portfolio_for_risk_level(mu, cov, level, max_weight)` |
| exclusiones | filtro sobre el **universo por defecto** → `custom_asset_universe` |
| umbral de incomodidad | señal para elegir zona de la frontera (no límite matemático exacto) |

**Cambio mínimo en el motor:** hoy `RISK_PROFILE_LEVELS` (optimizer.py:43) mapea
5 enums a 5 niveles. Se centraliza la conversión en una función
`risk_level_from_profile(...)` y se permite pasar un **nivel continuo** directo.
El enum de 5 valores se conserva solo como **etiqueta legible** derivada por bandas.

---

## 2. Perfiles locales (estilo "¿Quién está usando PortfolioQuant?")

Sin cuentas, sin mail, sin contraseña. Al abrir: selector de perfiles + "Nuevo perfil".

**Modelos nuevos:**

- `User`: `id (UUID)`, `name`, `avatar_color`, `created_at`.
- `Assessment` (cuestionario respondido): `id`, `user_id`, `created_at`, `answers (JSON)`,
  `dimensions (JSON: score+confidence+evidence por dimensión)`, `derived (JSON: nivel,
  restricciones, universo, etiqueta)`, `is_current (bool)`.
- Agregar `user_id` a `AnalysisRun` (y opcionalmente `assessment_id`).

**Reglas:**
- Todo (assessments, carteras, análisis, historial) se asocia a `user_id`.
- Al cambiar de perfil se cambia **todo el contexto** (cartera, historial, objetivo).
- No se borran assessments viejos: se guardan como histórico; el más reciente es `is_current`.
- Nada sensible: son perfiles locales de conveniencia, no autenticación.

**Endpoints nuevos:** `GET/POST /users`, `GET /users/{id}`, `POST /users/{id}/assessments`,
`GET /users/{id}/assessments`, `GET /users/{id}/current`.

---

## 3. Dimensiones internas del perfil

Cada dimensión guarda **score (0–100)**, **confidence (0–1)** y **evidence_count**.

| Dim | Nombre | Qué mide | De qué preguntas sale |
|---|---|---|---|
| D1 | horizonte | cuándo podría necesitar el dinero | Q3 (+Q2 timing) |
| D2 | liquidez / capacidad financiera | qué tan atado está a este dinero | Q4 + Q5 |
| D3 | aportes | capital y flujo futuro | Q6 + Q7 + Q8 |
| D4 | tolerancia emocional | cómo reacciona ante caídas | Q9 + Q10 (+QB) |
| D5 | prioridad del objetivo | qué tan crítico es la meta | Q11 |
| D6 | experiencia / detalle UI | cuánto explicar y con qué profundidad | Q12 (no afecta el riesgo) |

**Principio rector (capacidad manda):**
```
techo_capacidad = min(horizonte, liquidez)         # capacidad financiera real
deseo_tolerancia = tolerancia_emocional
nivel_final = min(deseo_tolerancia, techo_capacidad)
```
Una alta tolerancia psicológica **nunca** elimina una restricción financiera real.

---

## 4. Cuestionario (8–12 preguntas, adaptativo)

Una pregunta por pantalla. Sin jerga. Con “No sé” donde corresponde. Barra
"Pregunta N de M". Cada pantalla explica en una línea por qué se pregunta.

| # | Pregunta (resumen) | Dimensión / uso | "No sé" |
|---|---|---|---|
| Q1 | ¿Qué querés conseguir con este dinero? (+nombre opcional) | contexto/D5, `goal_type` | — |
| Q2 | ¿Hay una cantidad a la que querés llegar? (monto+moneda) | `target_wealth` | Sí |
| Q3 | ¿Cuándo podrías necesitar este dinero? | D1 | "sin fecha" |
| Q4 | Si mañana lo necesitaras para otra cosa, ¿qué tan complicado sería? | D2 | — |
| Q5 | Si aparece un gasto inesperado, ¿tenés dinero separado? | D2 | Sí |
| Q6 | ¿Con cuánto querés empezar? (monto+moneda) | `initial_capital` | — |
| Q7 | ¿Pensás agregar dinero regularmente? (+monto) | `monthly_contribution` | Sí |
| Q8 | ¿Qué tan seguro/a de mantener ese aporte? | D3 (haircut MC) | — |
| Q9 | Escenario: $10.000 → $8.500, no lo necesitás. ¿Qué harías? | D4 | Sí |
| Q10 | ¿A partir de qué caída empezarías a sentirte incómodo/a? | D4 | Sí |
| Q11 | ¿Qué tan importante es alcanzar tu objetivo? | D5 | — |
| Q12 | ¿Invertiste antes? + ¿cuánto detalle querés ver? | D6 / UI | — |
| Q13 | ¿Algo que NO quieras en tu cartera? (cripto, etc.) | restricciones | Sí |
| QB  | (branch) Opción A estable vs. B variable | D4, solo si Q9/Q10 = "No sé" | Sí |

**Branching:**
- Horizonte < 1 año (Q3) → se saltea profundidad de comportamiento; el techo por
  capacidad ya restringe. Q10 pasa a opcional.
- Q9 o Q10 = "No sé" → se hace QB (A vs B) como respaldo concreto.
- Objetivo muy ambicioso vs. capital/aportes → no se sube el riesgo: se activa la
  **reconciliación** (sección 7).

---

## 5. Scoring auditable (respuesta → puntos)

Las tablas viven en **configuración editable** (archivo/DB), no hardcodeadas. Cada
`Assessment` guarda cuánto sumó **cada respuesta** por dimensión (reconstruible).

### D1 — horizonte (base del techo)
| Respuesta Q3 | score | confidence |
|---|---|---|
| < 1 año | 10 | 1.0 |
| 1–3 años | 30 | 1.0 |
| 3–5 años | 50 | 1.0 |
| 5–10 años | 75 | 1.0 |
| > 10 años | 95 | 1.0 |
| sin fecha | 55 | 0.5 |

### D2 — liquidez / capacidad (impone tope, se toma el mínimo)
| Q4 importancia | tope |
|---|---|
| tengo otros ahorros | 100 |
| podría manejarlo | 80 |
| me complicaría bastante | 45 |
| lo necesito para gastos importantes | 25 |

| Q5 fondo emergencia | tope |
|---|---|
| varios meses | 100 |
| algo, no demasiado | 80 |
| no | 40 |
| no estoy seguro/a | 60 (conf 0.5) |

`techo_capacidad = min(D1, tope_Q4, tope_Q5)`

### D4 — tolerancia emocional
| Q9 (caída -15%) | score |
|---|---|
| sacaría todo | 10 |
| sacaría una parte | 30 |
| esperaría | 55 |
| lo dejaría | 78 |
| agregaría más | 92 |
| no sé | (no puntúa; conf↓ → QB) |

| Q10 (umbral incomodidad) | score |
|---|---|
| a -5% | 20 |
| a -10% | 40 |
| a -20% | 65 |
| a -30% | 85 |
| no sé | (no puntúa; conf↓) |

| QB (A/B, solo branch) | score |
|---|---|
| definitivamente A | 15 |
| probablemente A | 35 |
| no estoy seguro/a | 50 (conf 0.4) |
| probablemente B | 70 |
| definitivamente B | 90 |

`tolerancia = promedio ponderado de las respondidas (Q9=0.6, Q10=0.4; si ambas "no sé" → QB)`

### D3 — aportes (no cambia el nivel de riesgo; ajusta Monte Carlo)
| Q8 estabilidad | factor sobre aporte futuro en MC |
|---|---|
| muy seguro/a | 1.00 |
| bastante seguro/a | 0.90 |
| puede variar | 0.70 |
| probablemente no siempre | 0.50 |

### D5 — prioridad (afecta cómo se evalúa la meta, no el riesgo)
imprescindible / muy importante / flexible / solo hacer crecer → se usa en la sección 7.

---

## 6. Del score a la cartera

```
nivel_final_0_100 = min(tolerancia, techo_capacidad)
nivel = nivel_final_0_100 / 100        # → portfolio_for_risk_level(mu, cov, nivel, max_weight)
etiqueta = banda(nivel)                # solo para mostrar
```
Bandas para la etiqueta: 0–0.20 muy conservador · 0.20–0.40 conservador ·
0.40–0.60 moderado · 0.60–0.80 agresivo · 0.80–1.0 muy agresivo.

**Restricciones derivadas:**
- `max_weight` según diversificación deseada (p. ej. tope 35–40% por activo por defecto).
- Exclusiones de Q13 → se filtran del universo por defecto.
- Horizonte corto → tope adicional de riesgo (ya vía capacidad).

**Universo por defecto** (porque el principiante no da tickers): una canasta chica,
amplia y barata. **Definido:**
- **Global (default):** `VT` (acciones mundo) · `BND` (bonos globales/US) · `GLD` (oro).
- **Argentina (opción, no default):** `ARGT` (ETF MSCI Argentina, en USD) y, para quien
  quiera, ADRs argentinos (GGAL, YPF, PAM, BMA…). Se ofrece como alternativa explícita
  con aviso de que concentrar en Argentina implica **riesgo alto** (volatilidad + riesgo
  país); no se recomienda por defecto a un principiante.

Las exclusiones de Q13 aplican sobre la canasta elegida. Todos los instrumentos cotizan
en USD en mercados de EE.UU. (que yfinance cubre).

---

## 7. Reconciliación honesta del objetivo

El objetivo **no** sube el riesgo. Tras construir la cartera al `nivel_final`, se
corre Monte Carlo y:
- Si `prob_meta` es alta → se comunica con tranquilidad.
- Si `prob_meta` es baja → **no se fuerza riesgo**; se muestran palancas que el
  usuario controla:
  - aportar $X más por mes,
  - esperar N años más,
  - ajustar la meta a $Y (la que sí tiene ~70% de probabilidad).
- La **prioridad (D5)** modula el tono y el umbral de alarma, no el riesgo.

---

## 8. Manejo de casos difíciles

- **Contradicción** (tolerancia >> capacidad): gana capacidad; se marca
  `capacity_binding = true` y se explica en el resumen humano ("aunque las subidas
  y bajadas no te preocupan, como podrías necesitar el dinero pronto, elegimos algo
  más estable"). Caso inverso (capacidad >> tolerancia): gana tolerancia; se respeta
  la comodidad del usuario.
- **"No sé"**: nunca se interpreta como "conservador". No puntúa esa respuesta, baja
  la confidence de la dimensión; si la dimensión queda con confidence baja se dispara
  una pregunta alternativa (branching). Solo ante falta real de datos de **capacidad**
  se cae del lado prudente (seguridad), nunca por "no sé" de tolerancia.
- **Confidence** por dimensión = `evidencia_respondida / evidencia_esperada`, penalizada
  por "no sé". Se guarda `score`, `confidence`, `evidence_count` por dimensión.

---

## 9. Resultado en lenguaje humano + revelación progresiva

**Al terminar** (no un número frío): "Así entendemos tu situación" en prosa,
**editable** ("¿es correcto? ajustalo"). Botón "Ver mi propuesta". El score existe
internamente y aparece en "Ver detalles".

**La cartera** se presenta en tres bloques: *Qué buscamos · Qué podría pasar · Tu
objetivo (prob. de alcanzarlo)*. Luego "Ver análisis avanzado".

| Nivel | Qué se muestra |
|---|---|
| 1 | qué recomendamos, por qué, qué podría pasar, prob. de objetivo |
| 2 | retorno esperado, riesgo, caídas históricas, escenarios |
| 3 | Sharpe, Sortino, VaR, CVaR, covarianzas, factores, Black-Litterman, robustez, fórmulas |

El motor sigue igual de cuantitativo; la interfaz oculta la complejidad hasta que
el usuario la pida. Disclaimer visible: no es asesoramiento financiero personalizado.

---

## 10. Explicabilidad

Cada assessment permite reconstruir:
`respuestas → dimensiones (score+confidence) → nivel → restricciones → zona de la
frontera → pesos`. Para el usuario, en criollo ("elegimos algo más estable porque
podrías necesitar parte del dinero en 3 años"); en "Ver cálculo", toda la matemática.

---

## 11. Plan de implementación por fases (después del OK)

1. **Datos + scoring auditable:** modelos `User`/`Assessment`, `user_id` en `AnalysisRun`,
   motor de scoring con tablas en config, endpoints de perfiles. Tests unitarios del scoring
   (incluyendo contradicciones y "No sé").
2. **Universo por defecto + restricciones:** canasta base + filtro de exclusiones.
3. **UI del cuestionario:** selector de perfiles, preguntas con branching, barra de progreso.
4. **Resumen humano + revelación progresiva:** las 3 capas sobre lo ya construido.
5. **Reconciliación del objetivo:** palancas cuando la probabilidad es baja.

---

## 12. Decisiones tomadas

1. **Universo:** default global `VT + BND + GLD`; universo argentino (`ARGT` + ADRs) como
   opción con aviso de riesgo. (Confirmado.)
2. **Moneda:** se pregunta moneda de referencia al inicio (Q0: USD / ARS). Contexto argentino:
   los instrumentos son USD-denominados (cobertura natural ante inflación/deval). Vista
   "real vs nominal" con IPC queda para una fase posterior (dato de IPC argentino limitado
   en FRED; se implementa con aviso). (Confirmado.)
3. **Cantidad de preguntas:** ~12 con branching, priorizando que se entienda. (Confirmado.)
4. **Nivel de riesgo:** continuo interno `[0,1]`; la etiqueta (conservador/moderado/…) es
   solo para mostrar. (Confirmado.)
5. **Implementación:** se arranca por la Fase 1 (modelos `User`/`Assessment` + motor de
   scoring auditable + tests). (Confirmado.)

### Q0 — Moneda de referencia (nueva, va primero)
Pregunta: "¿En qué moneda querés pensar tus objetivos?" → USD / ARS. Nota: se invierte en
instrumentos en dólares; para un usuario argentino eso funciona como cobertura. La vista
ajustada por inflación (IPC) llega más adelante.
