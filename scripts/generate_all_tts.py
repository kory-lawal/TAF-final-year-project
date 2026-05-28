import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.tts import text_to_speech

OUT_DIR = Path('app/static')
OUT_DIR.mkdir(parents=True, exist_ok=True)

samples = {
    'yoruba': "Ólajide sọ pé ó yẹ kí ìjọba tètè dá sí àtúnṣe àwọn òòfísì náà kó tó pẹ́ ju kí ìjàmbá má baà wáyé sí àwọn tó ń ṣiṣẹ́ nínú rẹ̀.",
    'igbo': "Ndewo, a na m ekele gị. Anyị nwere olileanya na a ga-emezi ọrụ obodo nke ọma.",
    'hausa': "Assalamu alaikum, muna fatan gwamnati za ta yi gyara cikin gaggawa don amfanin al'umma."
}

results = {}
for lang, text in samples.items():
    data = text_to_speech(text, lang)
    if data:
        out = OUT_DIR / f"tts_{lang}.mp3"
        out.write_bytes(data)
        results[lang] = {'path': str(out), 'size': out.stat().st_size}
    else:
        results[lang] = {'error': 'no audio returned'}

for k, v in results.items():
    print(k, v)
