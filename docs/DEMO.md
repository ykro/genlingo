# Guion de la demo

La demo es una sola página en la nube: David y Goliath traducen la misma frase al mismo tiempo, lado a lado,
entre la jerga de Gen Z y el español de los papás. Cada columna muestra su traducción, cuánto tardó y cuánto
costó, y debajo, cada palabra de jerga con ✓ o ✗. Unos 4 minutos. [English version](DEMO.en.md).

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

### 2 · De Gen Z a papás (1 min 30 s)

![David y Goliath traducen «esa tu tarea te quedó bien chafa»](demo/02-comparar-genz-a-papas.png)

Toca los dos ejemplos de «Gen Z → papás», uno por uno. Arriba aparece la traducción de referencia, hecha por
personas, con su fuente. Debajo de cada columna, cada término de jerga con ✓ o ✗.

| Ejemplo | David | Goliath |
| --- | --- | --- |
| esa tu tarea te quedó bien **chafa** | esa tu tarea te quedó bien mal hecha | Esa tu tarea te quedó pura lata. |
| **Simón, de ley** llego al partido. | Sí, seguro llego al partido. | Cabal, fijo llego al partido. |

Lo que dice Goliath varía un poco de una vez a otra; en todas las pruebas cambió la jerga por otra jerga en vez
de decirlo como un papá.

> «Chafa», «simón, de ley»: David sabe qué significan y lo dice como lo diría tu mamá. Goliath cambia
> la jerga por más jerga. Y miren el tiempo: David responde en medio segundo; Goliath, en varios.

El costo de cada columna es lo que costó esa traducción: Gemini cobra por tokens; David, por los segundos de su
GPU. Una sola frase puede salir más cara en David o en Goliath; el ahorro de David aparece con volumen (las
proyecciones están en el README). En la charla, lo que se dice del costo es eso: «con volumen, David cuesta una
fracción».

### 3 · De papás a Gen Z (1 min)

![David y Goliath traducen «Voy a comprar algo de refacción para media mañana»](demo/03-comparar-papas-a-genz.png)

Toca el ejemplo de «Papás → Gen Z».

| Ejemplo | David | Goliath |
| --- | --- | --- |
| Voy a comprar algo de **refacción** para media mañana. | Voy a comprar algo de refa para media mañana. | Voy a conseguir un moncheo para el bajón de media mañana. |

> La dirección difícil: hay que poner la jerga correcta de aquí. David dice «refa», como se dice en Guatemala;
> Goliath inventa «munchies».

### 4 · Una frase escrita (30 s, opcional)

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

Los tres ejemplos están en `data/translate_examples.json`, con su fuente, su licencia, la razón por la que
están y las pruebas en vivo con los dos modelos. Son frases de jerga chapina del set de prueba (David nunca las
vio al entrenar), de fuentes con licencia abierta (WikiLengua y diccionario-chapin): las de fuentes con todos los
derechos reservados no se pueden mostrar. Se probaron 3 veces cada una contra el David de la nube
(`genlingo-2026-10d-e2b`) y Gemini: David acertó las 9 veces y Goliath ninguna. Se eligieron de Guatemala porque
ahí David acierta más jerga que Gemini (50 % contra 20 %, [evals/niche_report.md](../evals/niche_report.md)).
También se probaron las 38 frases de fuentes abiertas de México, Colombia y español neutro: ninguna pasó todas
las pruebas (en Colombia y en español neutro Goliath tradujo igual o mejor; en México David ganó a ojo en 3, pero
la revisión ✓/✗ de la página no lo distingue). Con jerga Gen Z general («cringe», «random», «crush») los dos
aciertan igual: si alguien la escribe en vivo, esperen un empate.

## Si algo falla

| Síntoma | Qué hacer |
| --- | --- |
| Sigue en «Preparando a David…» después de 2 minutos | Recarga la página: vuelve a pedir que se encienda. |
| Arriba dice «David no respondió · reintentando» | La página reintenta sola cada pocos segundos; espera a «David listo». |
| La columna de David dice «No respondió» | Pulsa **Traducir** otra vez. |
| Goliath tarda mucho | Gemini está lento; la columna de David ya respondió. Sigue con el siguiente ejemplo. |
| En un ejemplo Goliath acierta | No pasó en ninguna prueba, pero Goliath varía. Sigue con otro ejemplo. |
