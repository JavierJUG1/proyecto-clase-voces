# Quita las respiraciones de las voces generadas y deja todas al mismo volumen.
# Uso:  python -I limpiar_respiraciones.py      (después de generar_voces.mjs y antes de construir_modulo.py)
#
# Cómo funciona: pide a ElevenLabs (forced alignment) el inicio y fin exacto de cada palabra y baja el
# volumen casi a cero en las pausas entre palabras, que es donde están las respiraciones. La voz no se toca.
# Guarda el original en "respaldo/audios_con_respiraciones" y recuerda qué archivos ya limpió,
# así que se puede volver a correr sin limpiar dos veces (y limpia solo los audios nuevos o regenerados).
import glob, hashlib, json, os, re, shutil, subprocess, sys, urllib.request, uuid
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(BASE, 'audios generados')
ALI = os.path.join(AUD, 'alineacion')            # alineaciones + registro de limpieza
RAW = os.path.join(BASE, 'respaldo', 'audios_con_respiraciones')
SALTAR = {'l1b28bv5'}                             # Yeshúa: su eco vive en las pausas, no se limpia
SR = 44100
PISO = 0.03      # volumen en las pausas (≈ -30 dB)
ANTES, DESPUES = 0.04, 0.08   # margen que se respeta alrededor de cada palabra (s)
PAUSA_MIN = 0.15              # solo se limpian pausas más largas que esto (s)
RAMPA = 0.025                 # fundido para que no haya clics (s)
LUFS = -18                    # volumen igual para todas las voces (la guía un poco más bajo)
LUFS_GUIA = -20
VERSION = 2                   # subir si cambia el proceso, para rehacer todo desde los originales

os.makedirs(ALI, exist_ok=True); os.makedirs(RAW, exist_ok=True)
KEY = next(l.split('=', 1)[1].strip().strip('"\'') for l in open(os.path.join(BASE, '.env.local'), encoding='utf-8')
           if l.startswith('ELEVENLABS_API_KEY='))
md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
hablado = lambda t: re.sub(r'\s+', ' ', re.sub(r'\([^)]*\)', ' ', t)).strip()

def alinear(mp3, texto):
    b = uuid.uuid4().hex
    body = (f'--{b}\r\nContent-Disposition: form-data; name="text"\r\n\r\n{texto}\r\n'
            f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n').encode()
    body += open(mp3, 'rb').read() + f'\r\n--{b}--\r\n'.encode()
    req = urllib.request.Request('https://api.elevenlabs.io/v1/forced-alignment', body,
                                 {'xi-api-key': KEY, 'Content-Type': f'multipart/form-data; boundary={b}'})
    w = json.load(urllib.request.urlopen(req, timeout=120))['words']
    return [(x['start'], x['end']) for x in w if x['text'].strip()]

def limpiar(src, dst, palabras, lufs):
    x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                                     capture_output=True, check=True).stdout, np.float32)
    dur = len(x) / SR
    if palabras is None: palabras = [(0, dur)]          # sin limpieza de pausas (Yeshúa)
    voz = [(max(0, s - ANTES), min(dur, e + DESPUES)) for s, e in palabras]
    huecos = [(0, voz[0][0])] + [(a[1], b[0]) for a, b in zip(voz, voz[1:])] + [(voz[-1][1] + 0.1, dur)]
    g = np.ones(len(x), np.float32); n = 0
    for a, b in huecos:
        if b - a < PAUSA_MIN: continue
        i, j, r = int(a * SR), int(b * SR), int(RAMPA * SR)
        g[i:j] = PISO
        if i > 0: g[i:i + r] = np.linspace(1, PISO, min(r, j - i))[:len(g[i:i + r])]
        if j < len(g): g[max(i, j - r):j] = np.linspace(PISO, 1, j - max(i, j - r))
        n += 1
    y = (x * g).astype(np.float32)
    med = subprocess.run(['ffmpeg', '-hide_banner', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-af', 'ebur128', '-f', 'null', '-'],
                         input=y.tobytes(), capture_output=True).stderr.decode('utf-8', 'ignore')
    actual = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', med)[-1])
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-',
                    '-af', f'volume={lufs - actual:.2f}dB,alimiter=limit=0.95:level=disabled', '-b:a', '64k', dst],
                   input=y.tobytes(), check=True)
    return n

hechos = 0
for j in sorted(glob.glob(os.path.join(AUD, '*.json'))):
    id_ = os.path.basename(j)[:-5]; mp3 = j[:-5] + '.mp3'; reg = os.path.join(ALI, id_ + '.json'); raw = os.path.join(RAW, id_ + '.mp3')
    r = json.load(open(reg, encoding='utf-8')) if os.path.exists(reg) else {}
    nuevo = r.get('limpio') != md5(mp3) or not os.path.exists(raw)      # audio recién generado (o regenerado)
    if not nuevo and r.get('v') == VERSION: continue                   # ya está listo
    if nuevo: shutil.copy2(mp3, raw); r = {}                           # guardar el original
    d = json.load(open(j, encoding='utf-8')); clave = d['key']
    texto = d.get('text') or hablado(clave.split('|', 1)[1] if re.match(r'^(narradora|narrador|guia)\|', clave) else clave)
    if id_ in SALTAR or d.get('coro'): palabras = None    # coros: varias voces a destiempo, no se cortan pausas
    else: palabras = r.get('palabras') or alinear(raw, texto)
    if d.get('sync'):   # modelo v3: sus tiempos por palabra son aproximados -> usar la alineación real del audio
        reales = palabras or alinear(raw, texto)
        if len(reales) == len(d['t']):
            d['t'] = [round(s_, 2) for s_, e_ in reales]
            json.dump(d, open(j, 'w', encoding='utf-8'), ensure_ascii=False)
        else: print(f'{id_}: no coincide el número de palabras ({len(reales)} vs {len(d["t"])}), se dejan los tiempos')
    n = limpiar(raw, mp3, palabras, LUFS_GUIA if clave.startswith('guia|') else LUFS)
    json.dump({'palabras': palabras, 'limpio': md5(mp3), 'v': VERSION}, open(reg, 'w', encoding='utf-8'))
    hechos += 1
print('listo:', hechos, 'audios limpiados y nivelados')
