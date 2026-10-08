# Guion de la demo

La demo es una sola página en la nube: David y Goliath traducen la misma frase al mismo tiempo, lado a lado,
entre la jerga de Gen Z y el español de los papás. Cada columna muestra su traducción, cuánto tardó y cuánto
costó, y debajo, cada palabra de jerga con ✓ o ✗. Unos 5 minutos. [English version](DEMO.en.md).

## Antes de la charla

Abre esta página en Chrome **unos minutos antes** y déjala abierta:

**https://genlingo-611681112050.us-central1.run.app**

![La página mientras se enciende David](demo/01-preparando-a-david.png)

Arriba a la derecha dice «Preparando a David…» con un reloj: se está encendiendo su servidor con GPU, que se
apaga solo cuando nadie lo usa. Tarda menos de un minuto (unos 35 segundos). Cuando dice «David listo» ya está, y la página lo
mantiene encendido mientras siga abierta. Ponla a pantalla completa (`⌃⌘F`) y comprueba desde el fondo de la
sala que se lea.

## En escena

### 1 · La página (30 s)

Qué se ve: arriba la dirección, el cuadro de texto y los ejemplos; abajo, dos columnas, David a la izquierda y
Goliath a la derecha. Al final, «¿Cómo se lee esta página?» explica en una línea qué es ✓/✗, el tiempo y el
costo.

> A la izquierda, David: un modelo pequeño, ajustado con nuestros datos, en un servidor que es solo suyo. A la
> derecha, Goliath: Gemini, el modelo grande de Google. Los dos van a traducir la misma frase al mismo tiempo.

### 2 · Primero, jerga de todo internet: empate (30 s)

Escribe en el cuadro, con «Gen Z → papás», y pulsa **Traducir**:

```
Qué cringe tu foto de perfil
```

Los dos responden «Qué pena ajena tu foto de perfil», con ✓ (probado 3 veces con cada uno el 2026-10-07).

> «Cringe» está en todo internet y Goliath lo conoce: aquí empatan. Con jerga Gen Z general
> David acierta el 88 % y Goliath el 94 %: es un empate. David gana con otra cosa.

### 3 · Jerga local y combinaciones: gana David (1 min 30 s)

![David y Goliath traducen «No tengo pisto, préstame unas baras»](demo/02-comparar-genz-a-papas.png)

Toca los ejemplos de «Gen Z → papás», uno por uno: primero los de dos términos. Arriba aparece la traducción de
referencia, hecha por personas, con su fuente. Debajo de cada columna, cada término de jerga con ✓ o ✗.

| Ejemplo | David | Goliath (en las pruebas) |
| --- | --- | --- |
| No tengo **pisto**, préstame unas **baras**. | No tengo dinero, préstame unos quetzales. | No tengo pisto, prestame unos lenes / pesos. |
| Ese **maje** está bien **engasado** con ella. | Ese muchacho está muy enamorado de ella. | Ese patojo está bien enculado con ella. / Aquel pizado está bien clavado con ella. |
| **Simón, de ley** llego al partido. | Sí, seguro llego al partido. | Cabal, fijo llego al partido. |
| Ese concierto estuvo de **partir la madre**. (México) | Ese concierto estuvo buenísimo. | Ese concierto estuvo de poca madre / a toda madre. |

Lo que dice Goliath varía un poco de una vez a otra; en todas las pruebas dejó la jerga o la cambió por otra
jerga en vez de decirlo como un papá.

> Una frase con dos términos chapines a la vez: David traduce los dos; Goliath deja «pisto» y cambia «baras» por
> «lenes». En frases así, con varios términos de un mismo país, David acierta el 62 % y Goliath el 45 %. Y miren
> el tiempo: David responde en medio segundo; Goliath, en varios.

El costo de cada columna es lo que costó esa traducción: Gemini cobra por tokens; David, por los segundos de su
GPU. Una sola frase puede salir más cara en David o en Goliath; el ahorro de David aparece con volumen (las
proyecciones están en el README). En la charla, lo que se dice del costo es eso: «con volumen, David cuesta una
fracción».

### 4 · De papás a Gen Z (1 min)

![David y Goliath traducen «Voy a comprar algo de refacción para media mañana»](demo/03-comparar-papas-a-genz.png)

Toca el ejemplo de «Papás → Gen Z».

| Ejemplo | David | Goliath (en las pruebas) |
| --- | --- | --- |
| Voy a comprar algo de **refacción** para media mañana. | Voy a comprar algo de refa para media mañana. | Voy a conseguir un munchies / algo de moncha para el bajón de media mañana. |

> La dirección difícil: hay que poner la jerga correcta de aquí. David dice «refa», como se dice en Guatemala;
> Goliath inventa «munchies».

### 5 · Una frase escrita (30 s, opcional)

![Una frase escrita: «Tengo un clavo: no traigo pisto para el bus»](demo/04-frase-escrita.png)

Escribe en el cuadro una frase con jerga chapina y pulsa **Traducir**, por ejemplo:

```
Tengo un clavo: no traigo pisto para el bus
```

Arriba dice qué jerga de la frase conoce el banco («clavo», «pisto»), y cada columna la marca con ✓ o ✗, igual
que en los ejemplos. Si la frase no tiene jerga que el banco conozca, la página lo dice: no hay nada que revisar
automáticamente.

> Cualquier frase, en vivo.

Una frase escrita no está verificada de antemano: cualquiera de los dos puede equivocarse.

## De dónde salen los ejemplos

Los cinco ejemplos están en `data/translate_examples.json`, con su fuente, su licencia, la razón por la que
están y las pruebas en vivo con los dos modelos. Son frases del set de prueba (David nunca las vio al entrenar),
de fuentes con licencia abierta (diccionario-chapin, WikiLengua, Wikcionario) o escritas por el curador sobre
ellas: las de fuentes con todos los derechos reservados no se pueden mostrar. El 2026-10-07 se probaron 3 veces
cada una, con el David de la página (`genlingo-2026-10e-e2b`) y Gemini, las 96 frases de prueba que se pueden
mostrar (`make check-candidates`, [evals/experiments/2026-10-07-ejemplos-ronda5.md](../evals/experiments/2026-10-07-ejemplos-ronda5.md)):
pasaron la revisión automática 18 (México 6, Colombia 3, español neutro 1, Guatemala 8) y, leídas una por una,
se sostienen 5. Colombia y español neutro no tienen ejemplo: en las que pasaban, Goliath dijo algo correcto que el
banco no reconoce («qué vaina», «acuerpado», «se le van a ir encima»). En el eval David sí gana en Colombia (53 %
contra 28 %); en español neutro empatan (55 % contra 52 %).

## Si algo falla

| Síntoma | Qué hacer |
| --- | --- |
| Sigue en «Preparando a David…» después de 2 minutos | Recarga la página: vuelve a pedir que se encienda. |
| Arriba dice «David no respondió · reintentando» | La página reintenta sola cada pocos segundos; espera a «David listo». |
| La columna de David dice «No respondió» | Pulsa **Traducir** otra vez. |
| Goliath tarda mucho | Gemini está lento; la columna de David ya respondió. Sigue con el siguiente ejemplo. |
| En un ejemplo Goliath acierta | No pasó en ninguna prueba, pero Goliath varía. Sigue con otro ejemplo. |
| La columna de Goliath dice que no respondió | Gemini no contestó en 30 s (pasó varias veces el 2026-10-07). Pulsa **Traducir** otra vez o sigue. |
