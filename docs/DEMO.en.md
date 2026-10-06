# Demo script

The demo is a single page: David (on the laptop) and Goliath (in the cloud) translate the same phrase at the
same time, side by side, between Gen Z slang and the way parents talk. Each column shows its translation, how
long it took and what it cost. About 4 minutes. [Versión en español](DEMO.md).

## Before the talk

An hour before, on the stage laptop (charged):

- [ ] `make up` in one terminal. It starts Ollama, loads David and the glossary model, brings up the service and
      opens the page `http://127.0.0.1:8787/traducir`.
- [ ] In another terminal:

      ```bash
      make stage-on && make warmup && make preflight
      ```

      `preflight` checks the models and the page, and translates every example live with both: David must get
      the slang right and Goliath must not. It must end with «preflight ok»; each `[FALLA]` says how to fix it.
- [ ] Chrome full screen on the page. Check from the back of the room that it reads.
- [ ] Tap one example once, so the first translation on stage isn't the slowest.
- [ ] No-Wi-Fi test: turn it off, wait for «Sin internet · David sigue» at the top right, tap an example and check
      that David translates and Goliath says «Sin conexión». Turn it back on and wait for «En línea».

After the talk: `make stage-off`.

## On stage

### 1 · The page (30 s)

What you see: at the top, the direction, the text box and the examples; below, two columns, David on the left
and Goliath on the right.

> On the left, David: a small model running on this laptop, without internet. On the right, Goliath: Gemini,
> in the cloud. Both will translate the same phrase at the same time.

### 2 · Gen Z to parents (1 min 30 s)

![David and Goliath translate «esa tu tarea te quedó bien chafa»](demo/10-comparar-genz-a-papas.png)

Tap the three "Gen Z → papás" examples, one by one. The human reference translation shows at the top, with its
source. Under each column, each slang term with ✓ or ✗.

| Example | David | Goliath |
| --- | --- | --- |
| esa tu tarea te quedó bien **chafa** | Esa tarea tuya te quedó muy mala | Esa tu tarea te quedó bien pura lata |
| No te creo vos, ¡ya sé que vos solo **pajas** sos! | No te creo vos, ¡ya sé que vos solo mentís! | No te creo vos, ¡ya sé que sos pura casaca! |
| **Simón, de ley** llego al partido. | Sí, seguro llego al partido. | Cabal, fijo llego al partido. |

Goliath's wording varies a little from one call to the next; in the live tests, every time it swapped the slang
for more slang instead of saying it the way a parent would.

> "Chafa", "pajas", "simón, de ley": David knows what they mean and says it the way your mom would. Goliath
> swaps slang for more slang. And look at the time and cost: David, under a second and zero dollars.

### 3 · Parents to Gen Z (1 min)

![David and Goliath translate «Voy a comprar algo de refacción para media mañana»](demo/11-comparar-papas-a-genz.png)

Tap the "Papás → Gen Z" example.

| Example | David | Goliath |
| --- | --- | --- |
| Voy a comprar algo de **refacción** para media mañana. | Voy a comprar algo de refa para media mañana. | Voy a conseguir un munchies para el bajón de media mañana. |

> The hard direction: it has to add the right local slang. David says "refa", as it's said in Guatemala;
> Goliath makes up "munchies".

### 4 · No internet (45 s)

![No internet: Goliath says «Sin conexión» and David translates](demo/12-sin-internet.png)

Turn the laptop's Wi-Fi off, wait for «Sin internet · David sigue» and tap an example.

> Without a network, Goliath doesn't exist. David carries on: the model, the glossary and the page live on this
> laptop.

Turn the Wi-Fi back on.

### 5 · A typed phrase (30 s, optional)

Type a phrase with Guatemalan slang in the box and press **Traducir**. For typed phrases the page shows both
translations, the time and the cost, without the term check.

> Any phrase, live.

A typed phrase is not verified in advance: either model can get it wrong.

## Where the examples come from

The four examples live in `data/translate_examples.json`, with their source, license, the reason each is there
and the 3 live runs with both models. They are Guatemalan slang phrases from the test set: David never saw them
in training. The 51 short Guatemalan phrases the term-by-term check can judge were run 3 times with each model;
the ones kept are those David got right and Goliath wrong all 3 times, where a person sees the same as the
check. They are Guatemalan because that is where David gets more slang right than Gemini (52 % vs 23 %,
[evals/niche_report.md](../evals/niche_report.md)).

## If something fails

| Symptom | What to do |
| --- | --- |
| The page doesn't open | `make up` in a terminal; the page is at `http://127.0.0.1:8787/traducir`. |
| The top says «El servicio no responde» | The service went down: `Ctrl+C` in the `make up` terminal and `make up` again. |
| David's column says «No respondió» | Ollama isn't running or doesn't have David: `ollama ps` and `make up` again. |
| Goliath says «Sin conexión» with Wi-Fi on | The venue's network blocks Vertex AI. Use it as the no-internet moment. |
| Goliath takes long | The network is slow; David's column already answered. Go on to the next example. |
| Goliath gets an example right | Rare (it didn't happen in the tests), but Goliath varies. Go on to another example. |
