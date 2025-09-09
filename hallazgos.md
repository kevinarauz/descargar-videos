# Hallazgos y Correcciones

## 2025-09-08: Error de Sintaxis en JavaScript (`Uncaught SyntaxError: Unexpected string`)

**Problema:** Se reportó un error de sintaxis de JavaScript en la consola del navegador. El análisis reveló que el error ocurría al generar una notificación de "descarga completada". Si el nombre del archivo descargado contenía una comilla simple (apóstrofo), rompía la cadena de texto de JavaScript, causando un error de sintaxis.

**Causa Raíz:** La función `sanitize_filename` en `app.py` no estaba saneando las comillas simples. Cuando un nombre de archivo como `it's_a_video.mp4` se pasaba al código JavaScript, la comilla en el nombre terminaba prematuramente la cadena de texto, resultando en un error.

**Solución:** Se modificó la función `sanitize_filename` en `app.py` para que reemplace las comillas simples (`'`) por guiones bajos (`_`).

**Estado:** Corregido.
