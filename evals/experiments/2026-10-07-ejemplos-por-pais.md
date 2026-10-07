# Ejemplos de la página por país (México, Colombia, español neutro y Guatemala)

**Para qué:** la página solo tiene ejemplos chapines. Antes de agregar ejemplos de otros países, se prueban
candidatos en vivo con la revisión ✓/✗ corregida (2026-10-07: en Gen Z → papás la jerga tiene que dejar su lugar
al significado llano, sin otra jerga; en papás → Gen Z solo cuenta la jerga del país de la frase;
`duel/genlingo_duel/term_check.py`).

**Regla para que un candidato califique:**

- 3 de 3 veces en vivo, David saca ✓ en todos los términos y Goliath saca ✗ en al menos uno;
- la referencia humana que muestra la página es correcta (`reference_ok`, revisada por una persona);
- es texto que la página puede mostrar (fuente abierta o frase escrita por el curador, nunca la cita de una
  fuente cerrada) y una frase de prueba con la que David no entrenó (el script lo comprueba contra los pares de
  entrenamiento y el set de chat del último entrenamiento).

**Candidatos** (`2026-10-07-ejemplos-por-pais.json`): los pares de prueba que cumplen lo anterior y que en las
salidas guardadas del eval del 2026-10-07 (`evals/results/20261007-053721-merged.json`) David traduce con todo ✓ y
Goliath con algún ✗ (52), más «Tengo un chingo de chamba…» (`test-w2-0384`), el caso que motivó el arreglo.
Tres referencias se marcaron como incorrectas (la nota dice por qué); esos candidatos no califican aunque pasen.

**Cómo correrlo otra vez** (por ejemplo con el David reentrenado, después de cambiar `DAVID_MODEL_TAG` en `.env`):

```bash
make check-candidates                 # todos, 3 vueltas; despierta a David si está apagado
make check-candidates ONLY=MX,CO      # solo esos países
```

Llama a David (GPU privada en Cloud Run, con token de identidad) y a Gemini como lo hace la página, con el mismo
código (`genlingo_duel.arena`), pero pasando el país de cada frase (la página en vivo solo traduce texto escrito con
jerga chapina). Escribe las respuestas en `2026-10-07-ejemplos-por-pais.live.json` y la tabla de abajo. Nada se
agrega a `data/translate_examples.json` sin revisar a mano que la traducción de David diga lo mismo que la frase
(la revisión automática solo mira los términos del banco).

## Resultados en vivo

<!-- live:start -->

En vivo el 2026-10-07 11:17: David `genlingo-2026-10d-e2b`, Goliath `gemini-3.8-flash`, 3 vueltas cada uno.

### México: 5 de 10 pasan

| | frase | referencia | David | Goliath | por qué |
| --- | --- | --- | --- | --- | --- |
| — | Güey, le mandé el mensaje a mi ex por error, qué oso. <br>`test-w-0038` Gen Z → papás | Oye, le mandé el mensaje a mi ex por equivocación, qué vergüenza. | Amigo, le mandé el mensaje a mi ex por error, ¡trágame tierra! ✓ ×3 | Híjole, mano, le mandé el recado a mi ex por equivocación, qué pena me dio. ✗<br>Mano, le mandé el mensaje a mi ex por equivocación, qué pena me dio. ✗<br>Oye, le mandé el mensaje a mi ex por equivocación, qué pena me dio. ✓ | David 3/3 todo ✓ · Goliath falla 2/3 |
| ✅ | Me agüité porque el examen estuvo cañón. <br>`test-w-0040` Gen Z → papás | Me desanimé porque el examen estuvo muy difícil. | Me arrastré la cobija porque el examen estuvo difícil. ✓ ×3 | Me achicopalé porque el examen estuvo pesadísimo. ✗<br>Me achicopalé porque el examen estuvo en chino. ✗<br>Me achicopalé porque el examen estuvo bien canijo. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Mis compas me traen de carrilla por mi corte de pelo. <br>`test-w-0041` Gen Z → papás | Mis amigos no dejan de burlarse de mi corte de pelo. | Mis amigos me hacen burla por mi corte de pelo. ✓ ×3 | Mis amigos me están agarrando de su puerquito por mi corte de pelo. ✗<br>Mis amigos me traen de bajada por mi corte de pelo. ✗<br>Mis cuates me están agarrando de bajada por mi corte de pelo. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Oye, qué padre te quedó el cuarto, está a todo dar. <br>`test-w-0086` papás → Gen Z | Güey, tu cuarto quedó bien chido, está bien aesthetic. | Oye, qué chingón te quedó el cuarto, está a todo dar. ✓ ×3 | Oye, qué chido te quedó el cuarto, está bien perro. ✗ ×2<br>Oye, qué perro te quedó el cuarto, está bien god. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| — | la marmaja la quiero en efectivo no me vayas a salir que solo tienes cheques te lo advierto. <br>`test-w2-0377` papás → Gen Z | La feria la quiero en efectivo, güey, no me salgas con que solo traes cheques. | La feria la quiero en efectivo, no me vayas a salir que solo tienes cheques, te lo advierto. ✓<br>La feria la quiero en efectivo, no me vayas a salir que solo tienes cheques, la neta. ✓ ×2 | La feria la quiero en cash, no me vayas a salir con que pura transferencia, neta te aviso. ✓<br>El varo lo quiero en cash, no me vayas a salir con que pura transferencia, te estoy avisando. ✗<br>La feria la quiero en cash, no me vayas a salir con que pura transferencia, te lo juro. ✓ | David 3/3 todo ✓ · Goliath falla 1/3 |
| — | En suma, no me es posible encontrar un solo defecto en La llegada. Es la neta del planeta. <br>`test-w2-0380` papás → Gen Z | No le encuentro ni un defecto a La llegada. Está bien chingona, neta. | En suma, no me es posible encontrar un solo defecto en La llegada. Es god. ✓ ×3 | Literal no le encuentro ni un solo pero a La llegada. Es cine, está god. ✓<br>En resumen, cero quejas con La llegada, es una joya total y devoró durísimo. ✗<br>En resumen, literal no le encuentro ni un solo fallo a La llegada. Es cine, está god. ✓ | David 3/3 todo ✓ · Goliath falla 1/3 |
| ✅ | Ese vato te va a madrear si le sigues echando carrilla. <br>`test-w2-0382` Gen Z → papás | Ese muchacho te va a dar una golpiza si lo sigues molestando. | Ese muchacho te va a golpear si le sigues haciendo burla. ✓ ×3 | Ese tipo te va a acomodar unos trancazos si lo sigues toreando. ✗<br>Ese tipo te va a poner una friega si le sigues picando la cresta. ✗<br>Ese muchacho te va a poner unos trancazos si lo sigues toreando. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Ese concierto estuvo de partir la madre. <br>`test-w2-0383` Gen Z → papás | Ese concierto estuvo buenísimo. | Ese concierto estuvo a todo dar. ✓ ×3 | Ese concierto estuvo a toda madre. ✗ ×2<br>Ese concierto estuvo de poca madre. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| — | Güey, ¿nos echamos la pinta y vamos al cine? <br>`test-w2-0385` Gen Z → papás | Oye, ¿nos saltamos la clase y vamos al cine? | Amigo, ¿nos ponemos de acuerdo y vamos al cine? ✓ ×3 | Oye, ¿nos vamos de pinta y nos lanzamos al cine? ✓<br>Mano, ¿nos vamos de pinta y nos lanzamos al cine? ✗<br>Güey, ¿nos vamos de pinta y nos lanzamos al cine? ✗ | David 3/3 todo ✓ · Goliath falla 2/3 · la revisión solo mira «güey»; «echarse la pinta» (irse de pinta) no está en el banco: revisar a mano que David no cambie el sentido |
| — | Tengo un chingo de chamba y no salgo hasta las nueve. <br>`test-w2-0384` Gen Z → papás | Tengo muchísimo trabajo y no salgo hasta las nueve. | Tengo un montón de trabajo y no salgo hasta las nueve. ✗ ×3 | Tengo un friego de trabajo y no salgo hasta las nueve. ✗ ×2<br>Tengo un montón de trabajo y no salgo hasta las nueve. ✗ | David 0/3 todo ✓ · Goliath falla 3/3 · el caso del arreglo: Goliath dijo «un friego de trabajo» (otra jerga) y la revisión anterior lo daba por bueno |

### Colombia: 5 de 6 pasan

| | frase | referencia | David | Goliath | por qué |
| --- | --- | --- | --- | --- | --- |
| ✅ | Paila, se acabaron las polas. <br>`test-w-0134` Gen Z → papás | Qué pesar, se acabaron las cervezas. | Ni modo, se acabaron las cervezas. ✓ ×3 | Qué vaina, se acabaron las cervezas. ✗ ×3 | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Parce, me piso, que mi cucha me está llamando. <br>`test-w2-0345` Gen Z → papás | Amigo, me voy, que mi mamá me está llamando. | Amigo, me voy, que mi mamá me está llamando. ✓ ×3 | Hermano, me voy yendo que mi mamá me está llamando. ✗<br>Hermano, me voy yendo, que mi mamá me está llamando. ✗<br>Hermano, me abro, que mi mamá me está llamando. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| — | Desde que terminó con la novia anda con una tusa terrible. <br>`test-w2-0348` Gen Z → papás | Desde que terminó con la novia anda muy triste y despechado. | Desde que terminó con la novia anda con un guayabo terrible. ✓ ×3 | Desde que terminó con la novia anda con un despecho terrible. ✓<br>Desde que terminó con la novia anda con un despecho tremendo. ✓<br>Desde que terminó con la novia anda con una dicha de despecho tenaz. ✗ | David 3/3 todo ✓ · Goliath falla 1/3 |
| ✅ | Mi hermano está mera viga desde que entró al gimnasio. <br>`test-w2-0353` Gen Z → papás | Mi hermano está muy musculoso desde que entró al gimnasio. | Mi hermano está muy musculoso desde que entró al gimnasio. ✓ ×3 | Mi hermano se puso acuerpadísimo desde que se metió al gimnasio. ✗<br>Mi hermano está todo acuerpado desde que se metió al gimnasio. ✗<br>Mi hermano se puso acuerpadísimo desde que entró al gimnasio. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Ese sardino no sabe ni manejar todavía. <br>`test-w2-0364` papás → Gen Z | Ese pelado es un buñuelo, todavía no sabe ni manejar. | Ese man no sabe ni manejar todavía. ✓ ×3 | Ese pelao no sabe ni manejar todavía. ✗ ×2<br>Ese pelao ni sabe manejar todavía. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Deje de darme la lata con ese celular nuevo. <br>`test-w2-0365` papás → Gen Z | Deje de ser tan cansón con ese cel nuevo, parce. | Deje de hablarme de ese celular nuevo, parce. ✓ ×3 | Deje de intensiar con ese cel nuevo. ✗<br>Deje de rayarme tanto con ese cel nuevo. ✗<br>Deje de chimbar con ese cel nuevo. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |

### español neutro: 1 de 4 pasan

| | frase | referencia | David | Goliath | por qué |
| --- | --- | --- | --- | --- | --- |
| — | No entendí el mensaje y preparé la cena porque flasheé que venías hoy. <br>`test-w-0280` Gen Z → papás | No entendí el recado y preparé la cena porque creí que venías hoy. | No entendí el mensaje y preparé la cena porque me imaginé que venías hoy. ✓ ×3 | No entendí bien el mensaje y preparé la cena porque me hice la idea de que venías hoy. ✗<br>No entendí el mensaje y preparé la cena porque me imaginé que venías hoy. ✓<br>No entendí el mensaje y preparé la cena porque me hice la idea de que venías hoy. ✗ | David 3/3 todo ✓ · Goliath falla 2/3 |
| — | Me la pasé stalkeando a mi crush toda la noche, qué cringe. <br>`test-w-0287` Gen Z → papás | Me pasé la noche espiando las fotos del muchacho que me gusta, qué vergüenza. | Me la pasé revisándole el perfil a escondidas a mi persona favorita toda la noche, qué pena ajena. ✓ ×3 | Me la pasé espiando a la persona que me gusta toda la noche, qué pena ajena. ✓<br>Me la pasé espiando las redes de la persona que me gusta toda la noche, qué vergüenza. ✓<br>Me la pasé espiando a mi amor platónico toda la noche, qué pena ajena. ✗ | David 3/3 todo ✓ · Goliath falla 1/3 |
| ✅ | No te sulfures, que no es para tanto. <br>`test-w-0312` papás → Gen Z | Relax, no te ataques, cero drama. | Cero drama, que no es para tanto. ✓<br>Cero drama, bro, que no es para tanto. ✓ ×2 | No te ataques, que ni es para tanto. ✗ ×2<br>No te ataques, ni es para tanto. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 · «no te ataques» suena más mexicano que neutro |
| — | ¡Qué barbaridad! ¿Ya viste a qué hora llegaste? <br>`test-w2-0413` papás → Gen Z | Bro, ¿ya viste la hora a la que llegaste? Cero drama, pero literal es tardísimo. | Literal, ¿ya viste a qué hora llegaste? ✓ ×3 | No manches, ¿ya viste la hora a la que llegas? ✗<br>¡Te pasas, literal! ¿Ya viste a qué hora caes? ✓<br>Qué onda, te pasaste, ¿ya viste la hora a la que llegas? ✗ | David 3/3 todo ✓ · Goliath falla 2/3 · referencia incorrecta · la referencia agrega «cero drama, pero literal es tardísimo», que no está en la frase |

### Guatemala: 22 de 34 pasan

| | frase | referencia | David | Goliath | por qué |
| --- | --- | --- | --- | --- | --- |
| ✅ | esa tu tarea te quedó bien chafa <br>`test-w-0179` Gen Z → papás | esa tarea te quedó muy mal hecha | esa tu tarea te quedó bien mal hecha ✓ ×3 | Esa tu tarea te quedó bien pura lata. ✗<br>Esa tu tarea te quedó pura lata. ✗<br>Esa tu tarea te quedó bien garra. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Chish, huele horrible aquí. <br>`test-w-0182` Gen Z → papás | ¡Púchica, qué feo huele aquí! | ¡Qué asco, huele mal aquí! ✓ ×3 | Fuchi, qué gran tufo hay aquí. ✗<br>Fuchi, qué peste hay aquí. ✗<br>Fuchi, qué tufo se siente aquí. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| — | Ese patojo es bien chispudo para las matemáticas. <br>`test-w-0185` Gen Z → papás | Ese muchacho es muy listo para las matemáticas. | Ese muchacho es muy listo para las matemáticas. ✓ ×3 | Ese patojo es bien abusado para las matemáticas. ✗<br>Ese muchacho es bien abusado para las matemáticas. ✓<br>Ese patojo es bien pilas para las matemáticas. ✗ | David 3/3 todo ✓ · Goliath falla 2/3 |
| — | Qué buena onda sos, me llegas. <br>`test-w-0186` Gen Z → papás | Qué buena persona sos, me caés muy bien. | Qué chilero sos, me caes muy bien. ✓ ×3 | Qué bien me caés, de verdad qué calidad de persona sos. ✓<br>Qué de a huevo sos, me caés bien. ✗<br>Qué de a huevo sos, me caés re bien. ✗ | David 3/3 todo ✓ · Goliath falla 2/3 |
| ✅ | Ese maje está bien engasado con ella. <br>`test-w-0188` Gen Z → papás | Ese muchacho está muy enamorado de ella. | Ese muchacho está muy enamorado de ella. ✓ ×3 | Aquel pisado está bien clavado con ella. ✗<br>Ese chavo está bien clavado con ella. ✗<br>Aquel cuatio está bien enculado con ella. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Estas muy engasado, no es para tanto. <br>`test-w-0189` Gen Z → papás | Estás muy entusiasmado, no es para tanto. | Estás muy entusiasmado, no es para tanto. ✓ ×3 | Estás muy clavado, no es para tanto. ✗ ×3 | David 3/3 todo ✓ · Goliath falla 3/3 |
| — | Agarrá tus chivas y nos vamos al partido de fut. <br>`test-w-0191` Gen Z → papás | Agarrá tus cosas y nos vamos al partido de fútbol. | Agarrá tus cosas y nos vamos al partido de fútbol. ✓ ×3 | Agarrá tus chunches y nos vamos a la chamusca. ✗ ×2<br>Agarrá tus tiliches y nos vamos al partido de fútbol. ✓ | David 3/3 todo ✓ · Goliath falla 2/3 |
| — | No quiero manejar bolo, mejor me voy en taxi. <br>`test-w-0197` Gen Z → papás | No quiero manejar tomado, mejor me voy en taxi. | No quiero manejar borracho, mejor me voy en taxi. ✓ ×3 | No quiero manejar tomado, mejor me voy en taxi. ✓<br>No quiero manejar tomado, mejor agarro un taxi. ✓<br>No quiero manejar bolo, mejor me voy en taxi. ✗ | David 3/3 todo ✓ · Goliath falla 1/3 |
| — | Hacé eso al chilazo antes de que llegue tu mamá. <br>`test-w-0198` Gen Z → papás | Hacé eso rapidito antes de que llegue tu mamá. | Hacé eso de inmediato antes de que llegue tu mamá. ✓ ×3 | Hacé eso rapidito antes de que venga tu mamá. ✓<br>Hacé eso a la carrera antes de que venga tu mamá. ✗ ×2 | David 3/3 todo ✓ · Goliath falla 2/3 |
| — | Terminá al chilazo tu tarea para que podamos salir. <br>`test-w-0199` Gen Z → papás | Terminá pronto tu tarea para que podamos salir. | Terminá rápido tu tarea para que podamos salir. ✓ ×3 | Apurate a terminar la tarea para que podamos salir. ✗<br>Terminá rápido tu tarea para que podamos salir. ✓ ×2 | David 3/3 todo ✓ · Goliath falla 1/3 |
| — | ¡Puchis! Qué caro está todo. <br>`test-w-0201` Gen Z → papás | ¡Qué barbaridad! Qué caro está todo. | ¡Púchica! Qué caro está todo. ✓ ×3 | ¡Púchica! Todo está por las nubes. ✓<br>¡Ala gran chucha! Qué caro está todo. ✗<br>¡Dios guarde! Qué caro está todo. ✗ | David 3/3 todo ✓ · Goliath falla 2/3 |
| ✅ | No te creo vos, ¡ya sé que vos solo pajas sos! <br>`test-w-0202` Gen Z → papás | No te creo, ¡ya sé que vos solo mentiras decís! | No te creo vos, ¡ya sé que vos solo mentís sos! ✓ ×3 | No te creo, mano, ¡ya sé que vos sos pura casaca! ✗<br>No te creo mano, ¡ya sé que vos pura casaca sos! ✗<br>No sea casaquero mano, ¡si bien sé que puras mentiras son las suyas! ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Simón, de ley llego al partido. <br>`test-w-0206` Gen Z → papás | Sí, seguro que llego al partido. | Sí, seguro llego al partido. ✓ ×3 | Cabal, sin falta llego al partido. ✗<br>Va, seguro que llego a la chamusca. ✗<br>Va pues, sin falta llego al partido. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | El viaje estuvo chilero, lo volvería a hacer. <br>`test-w-0210` papás → Gen Z | El viaje estuvo calidá, maje, de ley lo repito. | El viaje estuvo nítido, lo volvería a hacer. ✓ ×3 | El viaje estuvo bien god, lo repetiría mil veces. ✗ ×2<br>El viaje estuvo god, fijo lo repetiría. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | ¡Púchica, qué bonita tu casa! <br>`test-w-0214` papás → Gen Z | ¡Puchis, qué calidá tu casa! | ¡Puchis, qué bonita tu casa! ✓ ×3 | Ala madre, qué de ahuevo tu chante. ✗<br>Ala gran, qué chilera tu choza. ✗<br>¡A la gran, qué aesthetic tu chante! ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| — | Qué chulo tu chucho, colocho. <br>`test-w-0237` papás → Gen Z | Qué calidá tu perro, colocho. | Qué nítido tu chucho, maje. ✓ ×3 | Qué cool tu chucho, bro. ✗<br>Qué chilero tu chucho, colocho. ✗<br>Qué lindo tu perro, bro. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 · referencia incorrecta · la referencia cambia «chucho» por «perro»: no es más Gen Z, y el chucho sigue siendo chapín |
| ✅ | Mi burra me ha llevado a todos lados <br>`test-w2-0007` Gen Z → papás | Mi camioneta vieja me ha llevado a todos lados. | Mi camioneta me ha llevado a todos lados ✓ ×3 | Mi nave me ha llevado a todos lados ✗<br>Mi carcachita me ha llevado a todos lados ✗ ×2 | David 3/3 todo ✓ · Goliath falla 3/3 · «burra»: carro o camioneta vieja (diccionario chapín) |
| ✅ | No me vengás con casacas. <br>`test-w2-0010` Gen Z → papás | No me vengás con mentiras. | No me vengas con tus mentiras. ✓ ×3 | No me vengás con cuentos. ✗ ×3 | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Chotea bien la comida, no vaya a ser que se queme. <br>`test-w2-0012` Gen Z → papás | Vigilá bien la comida, no vaya a ser que se queme. | Vigile bien la comida, no vaya a ser que se queme. ✓ ×3 | Echale un ojo a la comida, no vaya a ser que se queme. ✗ ×2<br>Echale un buen ojo a la comida, no vaya a ser que se queme. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Esa canche canta muy bonito. <br>`test-w2-0026` Gen Z → papás | Esa muchacha rubia canta muy bonito. | Esa muchacha rubia canta muy bonito. ✓ ×3 | Esa chelita canta bien rebonito. ✗<br>Esa güera canta bien chulo. ✗<br>Esa canche canta bien chulo. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | No tengo pisto para salir este fin <br>`test-w2-0040` Gen Z → papás | No tengo dinero para salir este fin de semana. | No tengo dinero para salir este fin ✓ ×3 | No tengo pisto para salir este fin de semana ✗<br>No tengo pisto para salir este fin de semana. ✗ ×2 | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Épale, que se te va a caer. <br>`test-w2-0044` papás → Gen Z | ¡Trucha, maje, que lo vas a botar! | Trucha, maje, que se te va a caer. ✓ ×3 | Pilas, que se te va a caer. ✗<br>Aguas, que se te va a caer. ✗ ×2 | David 3/3 todo ✓ · Goliath falla 3/3 |
| — | Llegaste cabal a la hora. <br>`test-w2-0046` papás → Gen Z | Llegaste de ley a la hora, maje. | Llegaste literal a la hora. ✓ ×3 | Caíste en punto, literal. ✓<br>Caíste al toque a la hora. ✗<br>Llegaste en el mero punto. ✗ | David 3/3 todo ✓ · Goliath falla 2/3 · referencia incorrecta · «cabal» es «exacto»; la referencia usa «de ley» («seguro»), que no significa lo mismo |
| ✅ | El tata de Juan es carpintero. <br>`test-w2-0062` papás → Gen Z | El papá de Juan es carpintero, maje. | El papá de Juan es carpintero, maje. ✓ ×3 | El jefe de Juan es carpintero. ✗ ×2<br>El ruco de Juan es carpintero. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| — | Aquél le dio un talegazo con el palo. <br>`test-w2-0064` papás → Gen Z | Aquel maje le dio un golpazo con el palo. | Él lo somató con el palo, maje. ✓ ×3 | Ese chavo le sampó un riendazo con el palo. ✗<br>Ese pisado le metió un vergazo con el palo. ✗<br>Ese maje le sampó un vergazo con el palo. ✓ | David 3/3 todo ✓ · Goliath falla 2/3 |
| ✅ | Voy a comprar algo de refacción para media mañana. <br>`test-w2-0066` papás → Gen Z | Voy a comprar algo de refa para media mañana. | Voy a comprar algo de refa para media mañana. ✓ ×3 | Voy a conseguirme un moncheo para el bajón de media mañana. ✗<br>Voy a conseguir un munchies para el bajón de media mañana. ✗<br>Voy a ir a traer un bajón para el moncheo de media mañana. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Solo quiero un cachito de tu tiempo. <br>`test-w2-0067` papás → Gen Z | Maje, solo quiero un ratito de tu tiempo. | Solo te pido un poquito de tu tiempo, maje. ✓ ×3 | Solo te robo un toque de tu tiempo. ✗ ×2<br>Solo dame un toque de tu tiempo. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | ¿Puedes darme un cachito de queso? <br>`test-w2-0068` papás → Gen Z | ¿Me regalás un poquito de queso, maje? | ¿Me podés regalar un pedacito de queso, maje? ✓ ×3 | ¿Me tirás una nada de queso? ✗<br>¿Me tirás un pedacito de queso? ✗<br>¿Me pasás un cacho de queso, porfa? ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Ya te colgaste de esa patoja, se te nota. <br>`test-w2-0133` Gen Z → papás | Ya te enamoraste de esa muchacha, se te nota. | Ya te cantineaste de esa muchacha, se te nota. ✓ ×3 | Ya te tragaste de esa patoja, se te nota. ✗<br>Ya te clavaste con esa patoja, se te nota. ✗<br>Ya estás bien tragado de esa patoja, se te nota. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | ¿Vamos por una refa? Yo pongo el pisto. <br>`test-w2-0140` Gen Z → papás | ¿Vamos a comer algo? Yo pago. | ¿Vamos por una refacción? Yo pongo el dinero. ✓ ×3 | ¿Vamos a echarnos una refacción? Yo disparo. ✗<br>¿Vamos a refaccionar? Yo disparo. ✗ ×2 | David 3/3 todo ✓ · Goliath falla 3/3 |
| ✅ | Chotealo, que ese maje se quiere colar. <br>`test-w2-0145` Gen Z → papás | Vigilalo, que ese muchacho se quiere colar. | Vigílalo, que ese muchacho se quiere meter. ✓ ×3 | Miralo, que ese pizado se quiere meter a la brava. ✗<br>Miralo bien, que ese chato se quiere meter a la brava. ✗<br>Échale el ojo, que ese cuate se quiere meter. ✗ | David 3/3 todo ✓ · Goliath falla 3/3 |
| — | ¿Cachaste lo que dijo el profe, maje? <br>`test-w2-0151` Gen Z → papás | ¿Entendiste lo que dijo el profesor? | ¿Entendiste lo que dijo el profesor? ✓ ×3 | ¿Le entendiste a lo que dijo el profesor, vos? ✓ ×3 | David 3/3 todo ✓ · Goliath falla 0/3 |
| ✅ | Haceme la campaña de ir a traer las tortillas, mijo. <br>`test-w2-0156` papás → Gen Z | Maje, ¿me echás la mano y vas por las tortillas? | Haceme la pala de ir a traer las tortillas, maje. ✓ ×3 | Haceme paro de ir a traer las tortillas, bro. ✗<br>Haceme la segunda de ir por las tortillas, bro. ✗ ×2 | David 3/3 todo ✓ · Goliath falla 3/3 |
| — | Ese muchacho la anda cantineando desde el año pasado. <br>`test-w2-0157` papás → Gen Z | Ese maje anda casaqueando a la patoja desde el año pasado. | Ese chavo la anda colgando desde el año pasado. ✓ ×3 | Ese chavo le anda tirando la onda desde el año pasado. ✗<br>Ese chavo le anda tirando casaca desde el año pasado. ✓<br>Ese pizado le anda tirando la onda desde el año pasado. ✗ | David 3/3 todo ✓ · Goliath falla 2/3 |

<!-- live:end -->

## Revisión a ojo de los que pasaron (2026-10-07, David `genlingo-2026-10d-e2b`)

La revisión automática solo conoce los términos del banco. Leídas las respuestas de los que pasaron 3 de 3, varios no
sirven para la página porque Goliath dijo algo que un papá (o un Gen Z del país) sí diría, pero que el banco no conoce,
o porque la frase de David suena rara:

| país | sirve para la página | no sirve (y por qué) |
| --- | --- | --- |
| México | `test-w-0041` («me traen de carrilla» → «me hacen burla»; Goliath: «agarrando de su puerquito», «de bajada»), `test-w2-0383` («de partir la madre» → «a todo dar»; Goliath: «a toda madre», «de poca madre»), `test-w2-0382` (David: «golpear… haciendo burla»; Goliath: «trancazos… toreando»: más de papás que Gen Z, discutible) | `test-w-0040`: «me achicopalé» de Goliath es habla de papás mexicana y «me arrastré la cobija» de David suena raro. `test-w-0086`: Goliath dice «qué chido… está bien perro», jerga Gen Z mexicana correcta; David deja «a todo dar» |
| Colombia | ninguno | `test-w-0134`: «qué vaina» (Goliath) lo dicen los papás. `test-w2-0345`: «Hermano, me voy yendo» también. `test-w2-0353`: «acuerpado» es español colombiano común. `test-w2-0364`: Goliath dice «pelao», la misma palabra que la referencia («pelado»), escrita como se pronuncia. `test-w2-0365`: David solo agrega «parce» («deje de hablarme de…») y Goliath usa jerga Gen Z («intensiar», «rayarme») |
| español neutro | ninguno | `test-w-0312`: Goliath dice «no te ataques», lo mismo que la referencia |
| Guatemala | los 3 de hoy (`test-w-0179`, `test-w-0206`, `test-w2-0066`) y `test-w-0188`, `test-w-0189`, `test-w-0182`, `test-w2-0026`, `test-w2-0040`, `test-w2-0044`, `test-w2-0062`, `test-w2-0067`, `test-w2-0068`, `test-w2-0140`, `test-w2-0145`, `test-w2-0156`; `test-w2-0007` si «burra» es un carro viejo | `test-w-0202` y `test-w2-0133`: la frase de David no es buen español («solo mentís sos», «te cantineaste de»). `test-w-0210`: «estuvo bien god» (Goliath) es jerga Gen Z panhispana correcta. `test-w-0214`: Goliath («qué chilera tu choza», «tu chante») es más chapín Gen Z que David («qué bonita tu casa»). `test-w2-0010` y `test-w2-0012`: «cuentos» y «échale un ojo» son habla de papás |

Lo que enseña: con el arreglo la revisión ya no da por buena otra jerga en lugar de la jerga, pero sigue sin conocer
todo el español llano («cuentos», «hermano», «acuerpado») ni las grafías de lo hablado («pelao»), así que a veces marca
✗ a un Goliath que está bien. Por eso cada ejemplo nuevo se lee antes de ponerlo en la página.
