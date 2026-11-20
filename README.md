# Lámparas Encendidas: El Legado de Modín

Módulo de ensayo para la obra de Janucá de la clase de niños (5 a 11 años). Cada niño elige su personaje,
escucha la obra con voces y practica sus líneas; con cada misión enciende una vela de la menorá.

**Ver en línea:** https://javierjug1.github.io/proyecto-clase-voces/

## Contenido
- `Lamparas_Encendidas_Ensayo.html`: el módulo completo (un solo archivo, funciona sin internet).
- `Lamparas_Encendidas_SCORM.zip`: el mismo módulo como paquete SCORM para subir a una plataforma de cursos.
- `clase de niños/`: el módulo SCORM descomprimido (`index.html` + `imsmanifest.xml`).
- `audios generados/`: las voces de cada línea (ElevenLabs, español latinoamericano) y sus tiempos por palabra.
- `musica/`: música de fondo (ElevenLabs Music).

## Cómo se rehace
1. `node --env-file=.env.local generar_voces.mjs`: genera las voces que falten (necesita `ELEVENLABS_API_KEY` en `.env.local`).
2. `python -I limpiar_respiraciones.py`: quita respiraciones y deja todas las voces al mismo volumen.
3. `python -I construir_modulo.py`: inserta voces y música en el módulo y rehace el HTML y el SCORM.
