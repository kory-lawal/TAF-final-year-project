import os
import sys
from pathlib import Path

# Ensure project root is on sys.path when running this script from scripts/
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.tts import text_to_speech

print('YARNGPT_API_KEY present:', bool(os.environ.get('YARNGPT_API_KEY')))

data = text_to_speech('This is a test of the TTS system.', 'yoruba')
print('Returned bytes length:', len(data))
# write output if non-empty
if data:
    out = 'scripts/tts_test_output.mp3'
    with open(out, 'wb') as f:
        f.write(data)
    print('Wrote:', out)
else:
    print('No audio returned')
