# Demo script

The demo is a single page in the cloud: David and Goliath translate the same phrase at the same time, side by
side, between Gen Z slang and parents' Spanish. Each column shows its translation, how long it took and what it
cost, and under it, each slang word with ✓ or ✗. About 5 minutes. [Versión en español](DEMO.md). The page and the talk are in Spanish.

## Before the talk

Open this page in Chrome **a few minutes before** and leave it open:

**https://genlingo-611681112050.us-central1.run.app**

![The page while David starts](demo/01-preparando-a-david.png)

The top right says «Preparando a David…» with a clock: his GPU server is starting (it shuts down on its own when
nobody uses it). It takes under a minute (about 35 seconds). Once it says «David listo» he's ready, and the page keeps him on
while it stays open. Go full screen (`⌃⌘F`) and check from the back of the room that it reads.

## On stage

### 1 · The page (30 s)

What you see: the direction, the text box and the examples at the top; two columns below, David on the left and
Goliath on the right. At the bottom, «¿Cómo se lee esta página?» explains ✓/✗, time and cost in a line each.

> On the left, David: a small model, tuned with our data, on a server of his own. On the right, Goliath:
> Gemini, Google's big model. Both will translate the same phrase at the same time.

### 2 · First, slang from all over the internet: a tie (30 s)

Type in the box, with «Gen Z → papás», and press **Traducir**:

```
Qué cringe tu foto de perfil
```

Both answer «Qué pena ajena tu foto de perfil», with ✓ (tried 3 times with each on 2026-10-07).

> «Cringe» is all over the internet and Goliath knows it: here they tie. With general Gen Z slang
> David gets 88 % right and Goliath 94 %: that's a tie. David wins with something else.

### 3 · Local slang and combinations: David wins (1 min 30 s)

![David and Goliath translate «No tengo pisto, préstame unas baras»](demo/02-comparar-genz-a-papas.png)

Tap the «Gen Z → papás» examples, one by one: the two-term ones first. The human reference translation appears
at the top, with its source. Under each column, each slang term with ✓ or ✗.

| Example | David | Goliath (in the tests) |
| --- | --- | --- |
| No tengo **pisto**, préstame unas **baras**. | No tengo dinero, préstame unos quetzales. | No tengo pisto, prestame unos lenes / pesos. |
| Ese **maje** está bien **engasado** con ella. | Ese muchacho está muy enamorado de ella. | Ese patojo está bien enculado con ella. / Aquel pizado está bien clavado con ella. |
| **Simón, de ley** llego al partido. | Sí, seguro llego al partido. | Cabal, fijo llego al partido. |
| Ese concierto estuvo de **partir la madre**. (Mexico) | Ese concierto estuvo buenísimo. | Ese concierto estuvo de poca madre / a toda madre. |

Goliath's wording varies a little from one run to the next; in every test it kept the slang or swapped it for
other slang instead of saying it the way a parent would.

> A phrase with two Guatemalan terms at once: David translates both; Goliath keeps «pisto» and swaps «baras» for
> «lenes». In phrases like this, with several terms from one country, David gets 62 % right and Goliath 45 %. And
> look at the time: David answers in half a second; Goliath, in several.

Each column's cost is what that translation cost: Gemini bills by token; David, by his GPU's seconds. A single
phrase may come out cheaper on either side; David's savings show up with volume (the projections are in the
README). What the talk says about cost is just that: «at volume, David costs a fraction».

### 4 · Parents to Gen Z (1 min)

![David and Goliath translate «Voy a comprar algo de refacción para media mañana»](demo/03-comparar-papas-a-genz.png)

Tap the «Papás → Gen Z» example.

| Example | David | Goliath (in the tests) |
| --- | --- | --- |
| Voy a comprar algo de **refacción** para media mañana. | Voy a comprar algo de refa para media mañana. | Voy a conseguir un munchies / algo de moncha para el bajón de media mañana. |

> The hard direction: you have to produce the right local slang. David says «refa», as they say in Guatemala;
> Goliath makes up «munchies».

### 5 · A typed phrase (30 s, optional)

![A typed phrase: «Tengo un clavo: no traigo pisto para el bus»](demo/04-frase-escrita.png)

Type a phrase with Guatemalan slang in the box and press **Traducir**, for example:

```
Tengo un clavo: no traigo pisto para el bus
```

The top line says which slang in the phrase the bank knows («clavo», «pisto»), and each column marks it with ✓ or
✗, just like the examples. If the phrase has no slang the bank knows, the page says so: there's nothing to check
automatically.

> Any phrase, live.

A typed phrase isn't checked in advance: either side can get it wrong.

## Where the examples come from

The five examples are in `data/translate_examples.json`, with their source, license, why they're there and the
live runs with both models. They're phrases from the test set (David never saw them in training), from openly
licensed sources (diccionario-chapin, WikiLengua, Wiktionary) or written by the curator from them: sentences from
all-rights-reserved sources can't be shown. On 2026-10-07 the 96 showable test phrases were each run 3 times with
the page's David (`genlingo-2026-10e-e2b`) and Gemini (`make check-candidates`, [evals/experiments/2026-10-07-ejemplos-ronda5.md](../evals/experiments/2026-10-07-ejemplos-ronda5.md)):
18 passed the automatic check (Mexico 6, Colombia 3, neutral Spanish 1, Guatemala 8) and, read one by one, 5 hold
up. Colombia and neutral Spanish have no example: in the ones that passed, Goliath said something correct that
the bank doesn't recognize («qué vaina», «acuerpado», «se le van a ir encima»). In the eval David does win in
Colombia (53 % vs 28 %); in neutral Spanish they tie (55 % vs 52 %).

## If something fails

| Symptom | What to do |
| --- | --- |
| Still «Preparando a David…» after 2 minutes | Reload the page: it asks him to start again. |
| The top says «David no respondió · reintentando» | The page retries on its own every few seconds; wait for «David listo». |
| David's column says «No respondió» | Press **Traducir** again. |
| Goliath takes long | Gemini is slow; David's column already answered. Move on to the next example. |
| Goliath gets an example right | It didn't happen in any test, but Goliath varies. Move on to another example. |
| Goliath's column says it didn't answer | Gemini didn't reply within 30 s (it happened several times on 2026-10-07). Press **Traducir** again or move on. |
