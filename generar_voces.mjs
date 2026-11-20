// Genera las voces del guion "Lámparas Encendidas" con ElevenLabs (voces latinas de la biblioteca, plan Creator).
// Uso:  node --env-file=.env.local generar_voces.mjs   (si hay una variable ELEVENLABS_API_KEY en el sistema, tiene prioridad: quitarla)
// Uso:  node --env-file=.env.local generar_voces.mjs [--limit N] [--solo clave1,clave2]
// Guarda cada línea en "audios generados/<id>.mp3" + "<id>.json" (tiempos por palabra).
// Si el archivo ya existe NO se vuelve a generar (para no gastar caracteres).
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const KEY = process.env.ELEVENLABS_API_KEY;
const OUT = 'audios generados';
const MODEL = 'eleven_multilingual_v2'; // mejor calidad y expresividad (plan Creator)
fs.mkdirSync(OUT, { recursive: true });

// ---- Voces (biblioteca de ElevenLabs, español latinoamericano; plan Creator) ----
const V = {
  // adultos
  mondragon:  'iDEmt5MnqUotdwCIVplo', // Enrique Mondragón (MX)        -> Papá
  fruna:      '2CGcaXd1E04jesxY7nfq', // voz infantil                   -> Narrador (niño)
  lumina:     'x5IDPSl4ZUbhosMmVFTk', // femenina, clara y serena (CO)  -> Voz guía (acotaciones)
  camila:     'spPXlKT5a4JMfbhPRAzA', // Camila, cálida (MX)            -> Narradora
  gabiyoya:   'iBGVhgcEZS6A5gTOjqSJ', // Gabiyoya, cálida (MX)          -> Mamá
  jhenny:     '2Lb1en5ujrODDIqmp7F3', // Jhenny, suave y dulce          -> Profesora
  // villanos
  murdock:    'OLmSqlYzB06EIKJRy5b0', // grave, imponente               -> Ejército de Antíoco
  charlee:    'S3IzZfySI0ew2bHauy7G', // oscura, cinematográfica        -> Soldado 1
  santiago:   'VXZKNah1ssrzM8c81OiY', // áspera, autoritaria            -> Soldado 2
  // niños
  sebastian:  'p7cwnUviDFhhX9y8sG2Q', // adolescente enérgico           -> Judas
  tomas:      'gpNJzVUAYfxYn4LZQs0k', // aguda, amistosa                -> Juan
  leotimoteo: 'la6RPabI2cxKM6nIEr7B', // joven, cálida                  -> Simón
  thorthugo:  'WOY6pnQ1WCg0mrOZ54lM', // aguda, juguetona               -> Eleazar
  leo:        'ihKwLOjVUMG4lgUI6meZ', // infantil, curiosa              -> Jonatán
  arath:      'KaqDAydogRM91Fctgddi', // joven chilango                 -> Niño 2 / voz en la calle
  cuentacuentos:'A2ekoyYWxhBmOk8bT2mw', // joven, ligera                -> Matatías
  gaviria:    'DZlhGG8Tll3rs5TbKAe2', // Jorge Gaviria, grave y aireada -> Yeshúa (firme, suave, celestial)
  // niñas
  lizy:       'rrErIO88ehxTnspOjKvf', // dulce, no chillona             -> Niña 1
  gaby:       'yqTu7PvIL2rV3ubtjNlx', // cálida y tierna, no chillona   -> Niña 2
  lulu:       'CPv3Zr3CQCqE4ZzuCgBP', // aguda, adorable                -> Niña 3
};
// voz + ajustes por personaje (speed 0.7–1.2)
const ROLE = {
  narradora: { v: 'camila',     st: 0.5,  sp: 0.95, style: 0.3 },
  narrador:  { v: 'fruna',      st: 0.55, sp: 0.97, style: 0.3 },
  guia:      { v: 'lumina',     st: 0.75, sp: 1.0,  style: 0.1 }, // voz en off que lee las acotaciones
  papa:      { v: 'mondragon',  st: 0.55, sp: 0.95, style: 0.3 },
  mama:      { v: 'gabiyoya',   st: 0.55, sp: 0.95, style: 0.3 },
  profesora: { v: 'jhenny',     st: 0.65, sp: 0.92, style: 0.2 },
  ejercito:  { v: 'murdock',    st: 0.3,  sp: 0.95, style: 0.7 },
  soldado1:  { v: 'charlee',    st: 0.3,  sp: 1.0,  style: 0.7 },
  soldado2:  { v: 'santiago',   st: 0.3,  sp: 1.0,  style: 0.7 },
  judas:     { v: 'sebastian',  st: 0.4,  sp: 1.0,  style: 0.5 },
  juan:      { v: 'tomas',      st: 0.45, sp: 1.0,  style: 0.4 },
  simon:     { v: 'leotimoteo', st: 0.5,  sp: 0.97, style: 0.35 },
  eleazar:   { v: 'thorthugo',  st: 0.4,  sp: 1.05, style: 0.5 },
  jonatan:   { v: 'leo',        st: 0.4,  sp: 1.05, style: 0.5 },
  nino1:     { v: 'sebastian',  st: 0.4,  sp: 1.02, style: 0.5 },
  nino2:     { v: 'leo',        st: 0.4,  sp: 1.02, style: 0.45 }, // voz infantil
  calle:     { v: 'arath',      st: 0.3,  sp: 1.12, style: 0.6 },
  matatias:  { v: 'cuentacuentos', st: 0.55, sp: 0.92, style: 0.35 },
  // eco celestial: varias reflexiones suaves + un poco de reverberación
  yeshua:    { v: 'gaviria',    st: 0.75, sp: 0.88, style: 0.15, fx: 'aecho=0.85:0.8:60|130|220:0.32|0.22|0.12,aecho=0.9:0.9:400:0.12,volume=1.1' },
  nina1:     { v: 'lizy',       st: 0.55, sp: 1.0,  style: 0.3 },
  nina2:     { v: 'gaby',       st: 0.55, sp: 1.0,  style: 0.3 },
  nina3:     { v: 'lulu',       st: 0.45, sp: 1.0,  style: 0.4 },
};
// coros: se mezclan dos voces
const CHORUS = {
  boys:  [{ v: 'sebastian', st: 0.4, sp: 1.03, style: 0.5 }, { v: 'leo', st: 0.4, sp: 1.03, style: 0.5 }],
  girls: [{ v: 'lizy', st: 0.5, sp: 1.0, style: 0.35 }, { v: 'gaby', st: 0.5, sp: 1.0, style: 0.35 }],
  family:[{ v: 'sebastian', st: 0.4, sp: 1.0, style: 0.5 }, { v: 'lizy', st: 0.5, sp: 1.0, style: 0.35 }],
};
// coros especiales: cada personaje con su propia voz
const CORO_ESPECIAL = {
  // las tres niñas juntas
  '¡Yeshúa es nuestro Buen Pastor, y creemos en Él!': ['nina1', 'nina2', 'nina3'].map(r => ({ ...ROLE[r], st: 0.5, style: 0.45 })),
  // Niño 1, Niño 2, Papá y Mamá: muy alegres (modelo v3 con la etiqueta [excited])
  '¡Síííí!': ['nino1', 'nino2', 'papa', 'mama'].map(r => ({ ...ROLE[r], model: 'eleven_v3', st: 0.0, say: '[excited] ¡Síííí!' })),
};
// líneas con una emoción especial (modelo v3 con etiquetas de emoción)
const LINEA_ESPECIAL = {
  // Niño 1, desanimado
  'Papi, ¡uff! Hoy en la escuela todos se burlaron porque dije que sigo al Eterno. Dicen que la Biblia es una historia antigua.':
    { model: 'eleven_v3', st: 0.0, tag: '[sighs] [sad, discouraged]' },
  // Papá, firme pero con amor
  '¡Sé fuerte y valiente! Tu batalla hoy no es con espadas, sino con tus decisiones diarias en el colegio y en casa.':
    { model: 'eleven_v3', st: 0.5, tag: '[firmly, with warmth and love]' },
};
const BOYS = new Set(['juan', 'simon', 'judas', 'eleazar', 'jonatan', 'nino1', 'nino2']);

// ---- Guion (se lee del módulo) ----
const html = fs.readFileSync('clase de niños/index.html', 'utf8');
const a = html.indexOf('/* =================== SCRIPT'), b = html.indexOf('SCR.forEach((x,i)=>x.i=i);');
const SCR = [];
new Function('SCR', html.slice(a, b).replace('const SCR=[];', ''))(SCR);
const spokenText = t => t.replace(/\([^)]*\)/g, ' ').replace(/\s+/g, ' ').trim();

const jobs = [];
for (const x of SCR) {
  if (x.k !== 'L' || (x.w.length === 1 && x.w[0] === 'antioco')) continue;
  const text = spokenText(x.t);
  if (x.w.length === 1 && x.w[0] === 'narr') {
    for (const r of ['narradora', 'narrador']) jobs.push({ key: r + '|' + x.t, text, parts: [ROLE[r]] });
  } else if (x.w.length === 1) {
    const e = LINEA_ESPECIAL[x.t];
    jobs.push({ key: x.t, text, parts: [e ? { ...ROLE[x.w[0]], ...e, say: e.tag + ' ' + text } : ROLE[x.w[0]]] });
  } else {
    const kind = x.w.every(w => BOYS.has(w)) ? 'boys' : x.w.every(w => w.startsWith('nina')) ? 'girls' : 'family';
    jobs.push({ key: x.t, text, parts: CORO_ESPECIAL[x.t] || CHORUS[kind] });
  }
}
// voz guía: lee las acotaciones (sin emojis)
const guiaTexto = t => t.replace(/[\p{Extended_Pictographic}️‍]/gu, '').replace(/\s*·\s*/g, ', ').replace(/\s+/g, ' ').trim();
const guias = new Set();
for (const x of SCR) {
  if (x.k === 'S') guias.add(x.t);
  if (x.k === 'L' && x.d) guias.add(x.d);
  if (x.k === 'L') for (const m of x.t.matchAll(/\(([^)]*)\)/g)) guias.add(m[1]);
}
for (const g of guias) { const text = guiaTexto(g); if (text) jobs.push({ key: 'guia|' + g, text, parts: [ROLE.guia] }); }
const idOf = k => 'l' + [...k].reduce((h, c) => (h * 31 + c.codePointAt(0)) >>> 0, 7).toString(36);

const args = process.argv.slice(2);
const limit = args.includes('--limit') ? +args[args.indexOf('--limit') + 1] : Infinity;
let todo = jobs.filter(j => !fs.existsSync(path.join(OUT, idOf(j.key) + '.json')));
if (args.includes('--plan')) { console.log('líneas', jobs.length, 'pendientes', todo.length, 'caracteres', todo.reduce((s, j) => s + j.text.length * j.parts.length, 0)); process.exit(0); }
todo = todo.slice(0, limit);

async function tts(text, p) {
  const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${V[p.v]}/with-timestamps?output_format=mp3_44100_64`, {
    method: 'POST',
    headers: { 'xi-api-key': KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text, model_id: p.model || MODEL,
      voice_settings: { stability: p.st, similarity_boost: 0.8, style: p.style, use_speaker_boost: true, speed: p.sp },
    }),
  });
  if (!r.ok) throw new Error(r.status + ' ' + (await r.text()).slice(0, 300));
  return r.json();
}
// tiempo de inicio (s) de cada palabra de text.split(' ')
function wordTimes(text, al, say) {
  const starts = al.character_start_times_seconds, out = [];
  const base = say ? Math.max(0, say.indexOf(text)) : 0; // si se mandó con etiqueta ([excited] …), saltarla
  let i = 0;
  for (const w of text.split(' ').filter(Boolean)) {
    const at = text.indexOf(w, i);
    out.push(+(starts[base + at] ?? starts[starts.length - 1] ?? 0).toFixed(2));
    i = at + w.length;
  }
  return out;
}

for (const j of todo) {
  const id = idOf(j.key);
  const res = [];
  for (const p of j.parts) res.push(await tts(p.say || j.text, p));
  const mp3 = path.join(OUT, id + '.mp3');
  if (res.length === 1 && j.parts[0].fx) {
    const raw = path.join(OUT, id + '_raw.mp3'); fs.writeFileSync(raw, Buffer.from(res[0].audio_base64, 'base64'));
    execFileSync('ffmpeg', ['-y', '-v', 'error', '-i', raw, '-af', j.parts[0].fx, '-b:a', '64k', mp3]); fs.unlinkSync(raw);
  } else if (res.length === 1) fs.writeFileSync(mp3, Buffer.from(res[0].audio_base64, 'base64'));
  else {
    const tmp = res.map((r, k) => { const f = path.join(OUT, `${id}_${k}.mp3`); fs.writeFileSync(f, Buffer.from(r.audio_base64, 'base64')); return f; });
    execFileSync('ffmpeg', ['-y', '-v', 'error', ...tmp.flatMap(f => ['-i', f]), '-filter_complex', `amix=inputs=${tmp.length}:normalize=0,volume=0.8`, '-b:a', '64k', mp3]);
    tmp.forEach(f => fs.unlinkSync(f));
  }
  fs.writeFileSync(path.join(OUT, id + '.json'), JSON.stringify({ key: j.key, text: j.text, coro: j.parts.length > 1, t: wordTimes(j.text, res[0].alignment, j.parts[0].say) }));
  console.log('OK', id, j.parts.map(p => p.v).join('+'), j.text.slice(0, 60));
}
console.log('listo:', todo.length, 'líneas');
