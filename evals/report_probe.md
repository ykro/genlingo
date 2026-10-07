# Sonda Gen Z general (fuera de Guatemala)

Generado por `make eval-probe` el 2026-10-07 22:24. 64 frases reales de la web (32 oraciones, cada una en las dos direcciones), preguntadas con el país en LATAM y en GT. Juicio determinista, igual para todos los modelos (`evals/probe_report.py`): de Gen Z a papás, la jerga desaparece y la salida dice el significado; de papás a Gen Z, la salida usa la jerga de la frase.

| modelo | país | Gen Z → papás | papás → Gen Z | total | IC 95 % (total) |
| --- | --- | --- | --- | --- | --- |
| genlingo-2026-10e-e2b + léxico | LATAM | 28/32 | 28/32 | **88 %** | [77, 94] |
| genlingo-2026-10e-e2b + léxico | GT | 25/32 | 19/32 | **69 %** | [57, 79] |
| genlingo-2026-10d-e2b + léxico | LATAM | 31/32 | 27/32 | **91 %** | [81, 96] |
| genlingo-2026-10d-e2b + léxico | GT | 26/32 | 21/32 | **73 %** | [62, 83] |
| gemini-3.8-flash | LATAM | 31/32 | 29/32 | **94 %** | [85, 98] |
| gemini-3.8-flash | GT | 14/32 | 30/32 | **69 %** | [57, 79] |

## Frase por frase (país LATAM)

| # | jerga | dirección | genlingo-2026-10e-e2b + léxico | genlingo-2026-10d-e2b + léxico | gemini-3.8-flash |
| --- | --- | --- | --- | --- | --- |
| 001 | slay | Gen Z → papás | ✓ | ✓ | ✓ |
| 001 | slay | papás → Gen Z | ✓ | ✓ | ✓ |
| 002 | slay | Gen Z → papás | ✗ | ✓ | ✓ |
| 002 | slay | papás → Gen Z | ✓ | ✗ | ✓ |
| 003 | funaron, funar, funa | Gen Z → papás | ✓ | ✗ | ✓ |
| 003 | funaron, funar, funa | papás → Gen Z | ✓ | ✗ | ✓ |
| 004 | stalk, crush | Gen Z → papás | ✗ | ✓ | ✓ |
| 004 | stalk, crush | papás → Gen Z | ✓ | ✓ | ✓ |
| 005 | hype | Gen Z → papás | ✓ | ✓ | ✓ |
| 005 | hype | papás → Gen Z | ✓ | ✓ | ✓ |
| 006 | beef | Gen Z → papás | ✓ | ✓ | ✓ |
| 006 | beef | papás → Gen Z | ✗ | ✗ | ✓ |
| 007 | vibe | Gen Z → papás | ✓ | ✓ | ✓ |
| 007 | vibe | papás → Gen Z | ✓ | ✓ | ✓ |
| 008 | cringe | Gen Z → papás | ✓ | ✓ | ✓ |
| 008 | cringe | papás → Gen Z | ✓ | ✓ | ✓ |
| 009 | aesthetic | Gen Z → papás | ✓ | ✓ | ✓ |
| 009 | aesthetic | papás → Gen Z | ✓ | ✓ | ✓ |
| 010 | fomo | Gen Z → papás | ✗ | ✓ | ✓ |
| 010 | fomo | papás → Gen Z | ✓ | ✓ | ✓ |
| 011 | random | Gen Z → papás | ✓ | ✓ | ✓ |
| 011 | random | papás → Gen Z | ✓ | ✗ | ✗ |
| 012 | cringe | Gen Z → papás | ✓ | ✓ | ✓ |
| 012 | cringe | papás → Gen Z | ✓ | ✓ | ✓ |
| 013 | random | Gen Z → papás | ✓ | ✓ | ✗ |
| 013 | random | papás → Gen Z | ✗ | ✓ | ✗ |
| 014 | cringe | Gen Z → papás | ✓ | ✓ | ✓ |
| 014 | cringe | papás → Gen Z | ✓ | ✓ | ✓ |
| 015 | bro | Gen Z → papás | ✓ | ✓ | ✓ |
| 015 | bro | papás → Gen Z | ✓ | ✓ | ✓ |
| 016 | funar, funa | Gen Z → papás | ✗ | ✓ | ✓ |
| 016 | funar, funa | papás → Gen Z | ✓ | ✗ | ✓ |
| 017 | prime | Gen Z → papás | ✓ | ✓ | ✓ |
| 017 | prime | papás → Gen Z | ✗ | ✓ | ✓ |
| 018 | shippe, crush, stalk, red flag | Gen Z → papás | ✓ | ✓ | ✓ |
| 018 | shippe, crush, stalk, red flag | papás → Gen Z | ✓ | ✓ | ✓ |
| 019 | prime, peak | Gen Z → papás | ✓ | ✓ | ✓ |
| 019 | prime, peak | papás → Gen Z | ✓ | ✓ | ✓ |
| 020 | prime | Gen Z → papás | ✓ | ✓ | ✓ |
| 020 | prime | papás → Gen Z | ✗ | ✓ | ✓ |
| 021 | cringe | Gen Z → papás | ✓ | ✓ | ✓ |
| 021 | cringe | papás → Gen Z | ✓ | ✓ | ✓ |
| 022 | cringe | Gen Z → papás | ✓ | ✓ | ✓ |
| 022 | cringe | papás → Gen Z | ✓ | ✓ | ✓ |
| 023 | cringe | Gen Z → papás | ✓ | ✓ | ✓ |
| 023 | cringe | papás → Gen Z | ✓ | ✓ | ✓ |
| 024 | cringe | Gen Z → papás | ✓ | ✓ | ✓ |
| 024 | cringe | papás → Gen Z | ✓ | ✓ | ✓ |
| 025 | delulu | Gen Z → papás | ✓ | ✓ | ✓ |
| 025 | delulu | papás → Gen Z | ✓ | ✓ | ✗ |
| 026 | delulu | Gen Z → papás | ✓ | ✓ | ✓ |
| 026 | delulu | papás → Gen Z | ✓ | ✓ | ✓ |
| 027 | mid | Gen Z → papás | ✓ | ✓ | ✓ |
| 027 | mid | papás → Gen Z | ✓ | ✓ | ✓ |
| 028 | mid | Gen Z → papás | ✓ | ✓ | ✓ |
| 028 | mid | papás → Gen Z | ✓ | ✓ | ✓ |
| 029 | mood | Gen Z → papás | ✓ | ✓ | ✓ |
| 029 | mood | papás → Gen Z | ✓ | ✓ | ✓ |
| 030 | mood | Gen Z → papás | ✓ | ✓ | ✓ |
| 030 | mood | papás → Gen Z | ✓ | ✓ | ✓ |
| 031 | basado | Gen Z → papás | ✓ | ✓ | ✓ |
| 031 | basado | papás → Gen Z | ✓ | ✓ | ✓ |
| 032 | rizz | Gen Z → papás | ✓ | ✓ | ✓ |
| 032 | rizz | papás → Gen Z | ✓ | ✓ | ✓ |
