# Inserta las voces de "audios generados" en el módulo y rehace el HTML y el paquete SCORM.
# Uso:  python construir_modulo.py
# Toma como base "respaldo/index_sin_voces.html" (la versión original), así se puede repetir sin duplicar nada.
import base64, glob, json, os, shutil, sys, zipfile

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.join(BASE, 'clase de niños')
SRC = os.path.join(BASE, 'respaldo', 'index_sin_voces.html')

os.makedirs(os.path.dirname(SRC), exist_ok=True)
if not os.path.exists(SRC):
    shutil.copy2(os.path.join(MOD, 'index.html'), SRC)
html = open(SRC, encoding='utf-8').read()

# 1) audios -> objeto VOX { clave: {s: dataURI, t: [inicio de cada palabra]} }
vox = {}
for j in sorted(glob.glob(os.path.join(BASE, 'audios generados', '*.json'))):
    d = json.load(open(j, encoding='utf-8'))
    mp3 = open(j[:-5] + '.mp3', 'rb').read()
    vox[d['key']] = {'s': 'data:audio/mpeg;base64,' + base64.b64encode(mp3).decode(), 't': d['t']}
# paréntesis dentro de una línea: la voz guía los lee en ese punto (p = [{at: índice de palabra, k: clave guía}])
import re
hablado = lambda t: re.sub(r'\s+', ' ', re.sub(r'\([^)]*\)', ' ', t)).strip()
for k, v in vox.items():
    linea = k.split('|', 1)[1] if re.match(r'^(narradora|narrador)\|', k) else k
    if k.startswith('guia|') or '(' not in linea: continue
    p = []
    for m in re.finditer(r'\(([^)]*)\)', linea):
        at = len(hablado(linea[:m.start()]).split()) if hablado(linea[:m.start()]) else 0
        if 'guia|' + m.group(1) in vox and at < len(v['t']): p.append({'at': at, 'k': 'guia|' + m.group(1)})
    if p: v['p'] = p
musica = os.path.join(BASE, 'musica', 'musica_fondo.mp3')
vox_js = 'const VOX=' + json.dumps(vox, ensure_ascii=False, separators=(',', ':')) + ';\n'
vox_js += 'const MUSICA=' + json.dumps('data:audio/mpeg;base64,' + base64.b64encode(open(musica, 'rb').read()).decode() if os.path.exists(musica) else '') + ';\n'

def patch(old, new):
    global html
    if html.count(old) != 1:
        raise SystemExit(f'No se encontró exactamente una vez: {old[:60]}')
    html = html.replace(old, new)

# 2) declarar VOX justo después de <script>
patch('<script>\nconst AUDIO=', '<script>\n' + vox_js + 'const AUDIO=') if '<script>\nconst AUDIO=' in html else patch('const AUDIO=', vox_js + 'const AUDIO=')

# 3) usar la voz generada (según narrador/narradora) y resaltar palabra por palabra con sus tiempos reales
patch("const au=soundOn&&AUDIO_BY_TEXT.get(text);",
      "const vx=soundOn&&VOX[(roleId==='narradora'||roleId==='narrador')?roleId+'|'+text:text];"
      "const au=vx?vx.s:(soundOn&&AUDIO_BY_TEXT.get(text));const gd=new Set();")
patch("a.onplay=()=>{t=setInterval(()=>{if(tok!==spTok){a.pause();return fin(false)}if(a.duration)",
      "a.onplay=()=>{if(t)clearInterval(t);t=setInterval(()=>{if(tok!==spTok){a.pause();return fin(false)}"
      # paréntesis dentro de la línea: pausa al personaje, habla la voz guía y continúa
      "if(vx&&vx.p&&!a.paused){const q=vx.p.find(q=>!gd.has(q)&&a.currentTime>=vx.t[q.at]-.08);"
      "if(q){gd.add(q);a.pause();const g=new Audio(VOX[q.k].s);gAud=g;"
      "g.onended=g.onerror=()=>{if(gAud===g)gAud=null;if(tok===spTok)a.play().catch(()=>fin(true))};"
      "g.play().catch(()=>a.play());return}}"
      "if(vx&&vx.t){let j=0;while(j+1<vx.t.length&&vx.t[j+1]<=a.currentTime+.05)j++;onWord&&onWord(Math.min(words.length-1,j));return}"
      "if(a.duration)")
patch("onWord(Math.min(words.length-1,Math.floor(a.currentTime/a.duration*words.length)))},120)",
      "onWord(Math.min(words.length-1,Math.floor(a.currentTime/a.duration*words.length)))},50)")
patch('Suban el volumen: las voces son del navegador. Si no se escucha nada, pueden practicar leyendo en voz alta.',
      'Suban el volumen: cada personaje tiene su propia voz. Si no se escucha nada, pueden practicar leyendo en voz alta.')

# 3b) voz guía (voz en off femenina) para las acotaciones
patch("function stopSpeech(){spTok++;try{synth&&synth.cancel()}catch(e){}try{curAudio&&curAudio.pause()}catch(e){}curAudio=null}",
      "let gAud=null;"
      "function stopSpeech(){spTok++;try{synth&&synth.cancel()}catch(e){}try{curAudio&&curAudio.pause()}catch(e){}curAudio=null;"
      "try{gAud&&gAud.pause()}catch(e){}gAud=null}\n"
      "function guia(txt){const g=soundOn&&VOX['guia|'+txt];if(!g)return Promise.resolve(false);const tok=++spTok;"
      "try{synth&&synth.cancel()}catch(e){}try{curAudio&&curAudio.pause()}catch(e){}"
      "return new Promise(res=>{const a=new Audio(g.s);gAud=a;let done=false;"
      "const fin=ok=>{if(done)return;done=true;if(gAud===a)gAud=null;res(ok&&tok===spTok)};"
      "a.onended=()=>fin(true);a.onerror=()=>fin(false);a.onpause=()=>{if(!a.ended)fin(false)};a.play().catch(()=>fin(false))})}")
patch("    renderStage();\n    if(x.k==='H'){await wait(900)}\n    else if(x.k==='S'){await wait(2600+x.t.length*28)}",
      "    renderStage();\n"
      "    if(x.k==='L'&&x.d&&soundOn&&VOX['guia|'+x.d]){await guia(x.d);if(tok!==playTok||!playing)return;await wait(200)}\n"
      "    if(x.k==='H'){await wait(900)}\n"
      "    else if(x.k==='S'){if(soundOn&&VOX['guia|'+x.t]&&await guia(x.t))await wait(500);else await wait(2600+x.t.length*28)}")

# 3c) música de fondo tenue (ElevenLabs Music), con botón 🎵; baja sola cuando habla una voz
if os.path.exists(musica):
    patch('</style>', '#musBtn{position:fixed;right:14px;bottom:14px;z-index:9999;width:48px;height:48px;border-radius:50%;border:2px solid var(--gold);'
          'background:var(--night);color:var(--gold2);font-size:22px;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.35)}'
          '#musBtn.off{opacity:.5;filter:grayscale(1)}#musBtn.off::after{content:"";position:absolute;left:9px;right:9px;top:50%;height:3px;'
          'background:var(--gold2);transform:rotate(-45deg);border-radius:2px}\n</style>')
    patch('<body>', '<body>\n<button id="musBtn" onclick="toggleMusic()" aria-label="Música de fondo" title="Música de fondo (encender / apagar)">🎵</button>')
    patch("if(!(synth&&window.SpeechSynthesisUtterance)){soundOn=false;['tgSound','tgSound2'].forEach(id=>$(id).classList.remove('on'))}",
          "if(!(synth&&window.SpeechSynthesisUtterance)){soundOn=false;['tgSound','tgSound2'].forEach(id=>$(id).classList.remove('on'))}\n"
          "/* música de fondo */\n"
          "let musOn=true,musStarted=false;try{musOn=localStorage.getItem('le_musica')!=='0'}catch(e){}\n"
          "const bgm=new Audio(MUSICA);bgm.loop=true;bgm.volume=0;\n"
          "$('musBtn').classList.toggle('off',!musOn);\n"
          "function musTick(){const voz=(curAudio&&!curAudio.paused)||(gAud&&!gAud.paused)||(synth&&synth.speaking);"
          "const obj=musOn?(voz?.03:.12):0;bgm.volume=Math.max(0,Math.min(1,bgm.volume+(obj-bgm.volume)*.2));"
          "if(!musOn&&bgm.volume<.004&&!bgm.paused)bgm.pause()}\n"
          "setInterval(musTick,100);\n"
          "document.addEventListener('pointerdown',()=>{if(!musStarted){musStarted=true;if(musOn)bgm.play().catch(()=>{})}},true);\n"
          "function toggleMusic(){musOn=!musOn;musStarted=true;try{localStorage.setItem('le_musica',musOn?'1':'0')}catch(e){}"
          "$('musBtn').classList.toggle('off',!musOn);if(musOn)bgm.play().catch(()=>{})}")

# 3d) banner inicial: mantener la proporción de las imágenes (3:2) para que se vean completas
#     y tema claro con los colores de beitteshuva.com (fondo celeste claro, azul #1d71b8)
patch('</style>', '''
/* banner inicial: misma proporción que las imágenes (1200x800), sin recortes */
.hero{aspect-ratio:auto;width:min(100%,calc(60vh*1.5));max-height:none;margin:0 auto;background:linear-gradient(180deg,#1d71b8,#003f61)}
.hero::before{content:"";display:block;aspect-ratio:3/2}
.hero img{inset:auto;top:0;left:0;width:100%;height:auto;aspect-ratio:3/2;object-fit:cover}
.hero .veil{display:none}
.hero .ttl{position:static;padding:12px 14px 16px}
.hero h1{text-shadow:0 3px 0 #6b3d00,0 6px 18px rgba(0,0,0,.35)}
.hero p{color:#fff}
/* tema claro Beit Teshuvá */
:root{--bt-celeste:#36a9e1;--bt-azul:#1d71b8;--bt-claro:#5fc8fa;--bt-noche:#003f61;--bt-tinta:#0b2e4a;--bt-fondo:#f3f9fd;--bt-borde:#d3e9f7}
html,body{background-color:#e6f5fd;background:linear-gradient(180deg,#cdeafb 0%,#e6f5fd 40%,var(--bt-fondo) 100%) fixed;color:var(--bt-tinta)}
.stars{display:none}
.pick-title,.hub-head h2,.lvl-head h2,.parents h3,.group h3{color:var(--bt-azul)}
.screen [style*="color:var(--gold2)"]{color:var(--bt-azul)!important}
.parents,.ccard,.mcard,.chip,.toggle,.opt,.ev,.me-chip,.btn.ghost{background:#fff;color:var(--bt-tinta);box-shadow:0 4px 14px rgba(29,113,184,.14),inset 0 0 0 1px var(--bt-borde)}
.ccard:hover,.mcard:hover,.opt:hover{background:#eaf6fe}
.chip.on{background:var(--gold);color:#3b2500}
.mcard .num{background:#e3f3fc}
.mcard.done .num{background:linear-gradient(180deg,var(--gold2),var(--gold))}
.icon-btn{background:#fff;color:var(--bt-azul);box-shadow:0 3px 10px rgba(29,113,184,.18),inset 0 0 0 1px var(--bt-borde)}
.toggle .sw{background:#b8c9d6}
.dot{background:#c5e3f5}.dot.cur{background:var(--bt-azul)}
.ev.placed{background:#d4f3e2}.ev.wrong{background:#fde0e1}
.opt.right{background:var(--green);color:#fff}.opt.wrong{background:var(--red);color:#fff}
.act-tag{color:#fff}
.mbox{background:linear-gradient(180deg,var(--bt-celeste),var(--bt-azul));color:#fff}
.mbox h2{color:#fff}
.modal{background:rgba(0,63,97,.55)}
</style>''')

# 4) guardar: módulo SCORM, HTML suelto y zip
open(os.path.join(MOD, 'index.html'), 'w', encoding='utf-8', newline='').write(html)
shutil.copy2(os.path.join(MOD, 'index.html'), os.path.join(BASE, 'Lamparas_Encendidas_Ensayo.html'))
with zipfile.ZipFile(os.path.join(BASE, 'Lamparas_Encendidas_SCORM.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(MOD, 'imsmanifest.xml'), 'imsmanifest.xml')
    z.write(os.path.join(MOD, 'index.html'), 'index.html')
print(f'{len(vox)} voces insertadas · HTML {os.path.getsize(os.path.join(MOD, "index.html"))/1e6:.1f} MB')
