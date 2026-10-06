# Guion de la demo

La demo es una sola página en la nube: David y Goliath traducen la misma frase al mismo tiempo, lado a lado,
entre la jerga de Gen Z y el español de los papás. Cada columna muestra su traducción y cuánto tardó. Unos
4 minutos. [English version](DEMO.en.md).

## Antes de la charla

Abre esta página en Chrome **unos diez minutos antes** y déjala abierta:

**https://genlingo-611681112050.us-central1.run.app**

![La página mientras se enciende David](demo/01-preparando-a-david.png)

Arriba a la derecha dice «Preparando a David…» con un reloj: se está encendiendo su servidor con GPU, que se
apaga solo cuando nadie lo usa. Tarda unos cuatro minutos. Cuando dice «David listo» ya está, y la página lo
mantiene encendido mientras siga abierta. Ponla a pantalla completa (`⌃⌘F`) y comprueba desde el fondo de la
sala que se lea.

## En escena

### 1 · La página (30 s)

Qué se ve: arriba la dirección, el cuadro de texto y los ejemplos; abajo, dos columnas, David a la izquierda y
Goliath a la derecha.

> A la izquierda, David: un modelo pequeño, ajustado con nuestros datos, en un servidor que es solo suyo. A la
> derecha, Goliath: Gemini, el modelo grande de Google. Los dos van a traducir la misma frase al mismo tiempo.

### 2 · De Gen Z a papás (1 min 30 s)

![David y Goliath traducen «esa tu tarea te quedó bien chafa»](demo/02-comparar-genz-a-papas.png)

Toca los tres ejemplos de «Gen Z → papás», uno por uno. Arriba aparece la traducción de referencia, hecha por
personas, con su fuente. Debajo de cada columna, cada término de jerga con ✓ o ✗.

| Ejemplo | David | Goliath |
| --- | --- | --- |
| esa tu tarea te quedó bien **chafa** | Esa tarea tuya te quedó muy mala | Esa tu tarea te quedó pura lata |
| No te creo vos, ¡ya sé que vos solo **pajas** sos! | No te creo vos, ¡ya sé que vos solo mentís! | No te creo vos, ¡si ya sé que pura casaca sos! |
| **Simón, de ley** llego al partido. | Sí, seguro llego al partido. | Cabal, sin falta llego al partido. |

Lo que dice Goliath varía un poco de una vez a otra; en todas las pruebas cambió la jerga por otra jerga en vez
de decirlo como un papá.

> «Chafa», «pajas», «simón, de ley»: David sabe qué significan y lo dice como lo diría tu mamá. Goliath cambia
> la jerga por más jerga. Y miren el tiempo: David responde en medio segundo.

### 3 · De papás a Gen Z (1 min)

![David y Goliath traducen «Voy a comprar algo de refacción para media mañana»](demo/03-comparar-papas-a-genz.png)

Toca el ejemplo de «Papás → Gen Z».

| Ejemplo | David | Goliath |
| --- | --- | --- |
| Voy a comprar algo de **refacción** para media mañana. | Voy a comprar algo de refa para media mañana. | Voy a conseguir un munchies para el bajón de media mañana. |

> La dirección difícil: hay que poner la jerga correcta de aquí. David dice «refa», como se dice en Guatemala;
> Goliath inventa «munchies».

### 4 · Una frase escrita (30 s, opcional)

Escribe en el cuadro una frase con jerga chapina y pulsa **Traducir**. En las frases escritas la página muestra
las dos traducciones y el tiempo, sin la revisión por término.

> Cualquier frase, en vivo.

Una frase escrita no está verificada de antemano: cualquiera de los dos puede equivocarse.

## De dónde salen los ejemplos

Los cuatro ejemplos están en `data/translate_examples.json`, con su fuente, su licencia, la razón por la que
están y las pruebas en vivo con los dos modelos. Son frases de jerga chapina del set de prueba: David nunca las
vio al entrenar. Se probaron las 51 frases chapinas cortas que la revisión término por término puede juzgar,
3 veces con cada modelo, y quedaron las que David tradujo bien y Goliath mal las 3 veces. Después de pasar a
David a la nube se volvieron a probar 3 veces cada una contra el David de Cloud Run: David acertó las 12 veces y
Goliath ninguna. Se eligieron de Guatemala porque ahí David acierta más jerga que Gemini (52 % contra 23 %,
[evals/niche_report.md](../evals/niche_report.md)).

## Si algo falla

| Síntoma | Qué hacer |
| --- | --- |
| Sigue en «Preparando a David…» después de 5 minutos | Recarga la página: vuelve a pedir que se encienda. |
| Arriba dice «David no respondió · reintentando» | La página reintenta sola cada pocos segundos; espera a «David listo». |
| La columna de David dice «No respondió» | Pulsa **Traducir** otra vez. |
| Goliath tarda mucho | Gemini está lento; la columna de David ya respondió. Sigue con el siguiente ejemplo. |
| En un ejemplo Goliath acierta | No pasó en ninguna prueba, pero Goliath varía. Sigue con otro ejemplo. |
