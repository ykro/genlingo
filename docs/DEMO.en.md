# Demo script

The demo is a single page: David translates between Gen Z slang and the way parents talk, on the
laptop and without internet. Pick the direction, type a phrase or tap an example, and press
**Traducir**. About 3 minutes.

[Versión en español](DEMO.md)

## Before the talk

An hour before, on the stage laptop (charged):

- [ ] `make up` in one terminal. It starts Ollama, loads David and the glossary model, and serves the
      page.
- [ ] In another terminal:

      ```bash
      make stage-on && make warmup && make preflight
      ```

      `preflight` checks the models and the page, and translates every example live: all six must
      come out as they did when they were verified. It must end with «preflight ok»; each `[FALLA]`
      says how to fix it.
- [ ] Open `http://127.0.0.1:8787/traducir` in Chrome, full screen, and check it reads from the back
      of the room.
- [ ] Tap one example once so the first translation on stage isn't the slowest.

After the talk: `make stage-off`.

## On stage

### 1 · The page (30 s)

![The translation page](demo/10-traducir-genz-a-papas.png)

> This is David: a small model running on this laptop, without internet. We trained it on real
> Guatemalan slang.

### 2 · Gen Z to parents (1 min)

Tap two "Gen Z → papás" examples:

| Example | David's answer |
| --- | --- |
| Agarrá tus chivas y nos vamos al partido de fut. | Agarrá tus cosas y nos vamos al partido de fútbol. |
| Hacé eso al chilazo antes de que llegue tu mamá. | Hacé eso rapidito antes de que llegue tu mamá. |
| El chonte nos ayudó a encontrar la dirección. | El policía nos ayudó a encontrar la dirección. |

> "Chivas", "al chilazo", "chonte": David knows what they mean and says it the way your mom would,
> in under a second and for free.

### 3 · Parents to Gen Z (1 min)

![Parents to Gen Z](demo/11-traducir-papas-a-genz.png)

Tap two "Papás → Gen Z" examples:

| Example | David's answer |
| --- | --- |
| ¡Épale, cuidado con el carro! | ¡Trucha, maje, cuidado con el carro! |
| Voy a comprar algo de refacción para media mañana. | Voy a comprar algo de refa para media mañana. |
| No seas tan mashcuil, ya aceptá la verdad. | No seas tan necio, maje, ya aceptá la verdad. |

> The hard direction: removing slang isn't enough, it has to add the right local slang.

### 4 · A typed phrase (30 s, optional)

Type a phrase with Guatemalan slang in the box and press **Traducir**.

> Any phrase, live, on the laptop.

## Where the examples come from

The six examples live in `data/translate_examples.json`, with their source and license. They are
Guatemalan slang phrases from the test set: David never saw them in training. Each one was
translated four times live with the stage David (`genlingo-2026-10c-e2b-nomulti`) and all four came
out right. They are Guatemalan because that is where David gets more slang right than Gemini (52 %
vs 23 %, [evals/report.md](../evals/report.md)).

A phrase typed live is not verified in advance: David can get slang he doesn't know wrong.

## If something fails

| Symptom | What to do |
| --- | --- |
| The page doesn't open | `make up` in a terminal; the page is at `http://127.0.0.1:8787/traducir`. |
| "David no respondió" | Ollama isn't running or doesn't have David: `ollama ps` and `make up` again. |
| The first translation takes over 2 s | The model had been unloaded: tap an example and go on. |
| An example answers differently from the table | `make preflight` flags it; check that `LOCAL_MODEL_TAG` in `.env` is `genlingo-2026-10c-e2b-nomulti`. |
