# Nichos: David contra Goliath

Generado desde `evals/results/20261002-083923.json` (2026-10-02 08:39). Definiciones pre-registradas en [niche.md](niche.md). Métrica principal: jerga resuelta (`evals/term_accuracy.py`); IC 95 % por bootstrap pareado de la diferencia (10,000 remuestreos, semilla 2027). «Victorias de David»: frases donde solo David resuelve la jerga, sobre las frases donde la resuelve exactamente uno (entre paréntesis, solo David – solo el rival).

David: `genlingo-2026-10b-e2b + glosario`. Rival del nicho: `gemini-3.8-flash` (como en escena, sin glosario).

## Contra Goliath (rival del nicho)

| corte | n | David | rival | Δ (puntos) | IC 95 % | victorias de David | chrF++ David / rival | veredicto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Slang chapín (GT) | 115 | 78 % | 70 % | +7.8 | [+0.0, +15.7] | 70 % (16–7) | 61.2 / 51.4 | **empate estadístico** |
| Papás → Gen Z (GT/CO) | 106 | 65 % | 49 % | +16.0 | [+3.8, +28.3] | 68 % (32–15) | 47.1 / 41.8 | **gana David** |
| Todo el set | 398 | 82 % | 78 % | +3.8 | [-0.5, +8.0] | 60 % (46–31) | 56.6 / 53.1 | **empate estadístico** |
| País GT | 115 | 78 % | 70 % | +7.8 | [+0.0, +15.7] | 70 % (16–7) | 61.2 / 51.4 | **empate estadístico** |
| País MX | 78 | 79 % | 82 % | -2.6 | [-12.8, +7.7] | 44 % (8–10) | 50.9 / 51.3 | **empate estadístico** |
| País CO | 130 | 89 % | 82 % | +6.9 | [-0.8, +14.6] | 67 % (18–9) | 58.6 / 52.6 | **empate estadístico** |
| País LATAM | 75 | 77 % | 79 % | -1.3 | [-9.3, +6.7] | 44 % (4–5) | 52.0 / 57.7 | **empate estadístico** |

## Contra Goliath con el mismo glosario (referencia, no decide)

| corte | n | David | rival | Δ (puntos) | IC 95 % | victorias de David | chrF++ David / rival | veredicto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Slang chapín (GT) | 115 | 78 % | 77 % | +0.9 | [-7.8, +9.6] | 52 % (14–13) | 61.2 / 58.5 | **empate estadístico** |
| Papás → Gen Z (GT/CO) | 107 | 64 % | 60 % | +4.7 | [-6.5, +16.8] | 56 % (23–18) | 47.3 / 45.1 | **empate estadístico** |
| Todo el set | 399 | 82 % | 82 % | -0.8 | [-5.0, +3.5] | 48 % (36–39) | 56.6 / 56.5 | **empate estadístico** |
| País GT | 115 | 78 % | 77 % | +0.9 | [-7.8, +9.6] | 52 % (14–13) | 61.2 / 58.5 | **empate estadístico** |
| País MX | 78 | 79 % | 86 % | -6.4 | [-16.7, +3.8] | 35 % (6–11) | 50.9 / 51.6 | **empate estadístico** |
| País CO | 131 | 89 % | 84 % | +4.6 | [-1.5, +10.7] | 67 % (12–6) | 58.7 / 54.2 | **empate estadístico** |
| País LATAM | 75 | 77 % | 84 % | -6.7 | [-16.0, +2.7] | 31 % (4–9) | 52.0 / 62.6 | **empate estadístico** |

