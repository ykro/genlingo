# Créditos y procedencia

De dónde salen los datos de Genlingo y con qué licencia se usan. Volver al [README](../README.md). [English version](CREDITOS.en.md).

## Procedencia de los datos y licencias

| Datos | Origen | Licencia / uso |
| --- | --- | --- |
| `data/terms.jsonl` (734 términos) y `data/raw/web_usage*.jsonl` (1,435 oraciones) | 133 fuentes web de MX, GT, CO y Latinoamérica (más frases de jerga panhispana de Argentina, Chile, Perú, Venezuela y España, etiquetadas como español neutro), consultadas del 2026-09-30 al 2026-10-07 ([SOURCES.md](../data/SOURCES.md)); un corpus de habla general (S63) solo para contar términos ambiguos | WikiLengua (CC BY-SA 3.0), Wikcionario (CC BY-SA 4.0) y diccionario-chapin (MIT) se reutilizan bajo su licencia con atribución por registro. De las fuentes con todos los derechos reservados solo se toman hechos (término y significado, parafraseado) y una cita breve atribuida por entrada, con fines de investigación y educación; esas citas no están en el repo, viven en un bucket privado (`make data-pull`). |
| `data/pairs/test_web.jsonl` (522 pares, 399 `auto_validated`) y `data/pairs/real_train.jsonl` (334 pares) | Oraciones reales de esas fuentes; la referencia es reescritura del curador (menos de 30 % son oraciones escritas por el curador, marcadas `example_origin=curator`) | Igual que la fuente; los pares que citan ejemplos CC BY-SA heredan share-alike para ese texto. |
| `data/pairs/synthetic.jsonl` y `synthetic_multi.jsonl` (pares sintéticos) | `gemini-3.8-flash`, contrapartes validadas por significado (`data/counterparts.jsonl`), semilla base 2027; solo entrenamiento | Cada par registra modelo, versión de prompt, semilla y los ids de término de los que salió. |
| `data/eval/combos.jsonl` (174 pares) | Nicho de combinaciones: frases del set de prueba con 2 o más términos y oraciones reales de la ronda 5 (publicaciones de X, Bluesky, reseñas de Steam, comentarios de blogs y foros), apartadas antes de entrenar; la referencia es del curador | Como el set de prueba: las citas de fuentes cerradas viven en el bucket privado; nunca se usan para entrenar ni en la página. |
| `data/pairs/synthetic_combo.jsonl` y `synthetic_p2g.jsonl` (ronda 5) | `gemini-3.8-flash`, versiones de prompt `synthetic-combo-2026-10e` (semilla 6067) y `synthetic-2026-10b` (semilla 5051); solo entrenamiento | Cada par registra modelo, versión de prompt y semilla; cada término se valida por significado contra el banco. |

Limitaciones conocidas (del datasheet): la jerga juvenil guatemalteca está poco documentada en línea; la jerga envejece rápido; las referencias son de una sola persona, así que chrF++ subestima traducciones alternativas válidas.

Detalle por fuente y recuentos: [data/SOURCES.md](../data/SOURCES.md) y [data/DATASHEET.md](../data/DATASHEET.md).
