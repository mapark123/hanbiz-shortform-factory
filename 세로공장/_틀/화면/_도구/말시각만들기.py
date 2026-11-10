"""설정.json «기준영상»을 받아써서 화면/말시각.json 을 만든다(원고 정렬·검사가 이 시각을 쓴다).
형식: [{"t0", "t1", "글", "단어": [[낱말, 시작, 끝], ...]}, ...]
사용: python -X utf8 화면/_도구/말시각만들기.py"""
import json, os, subprocess, sys
_p = os.path.abspath(__file__)
while not os.path.exists(os.path.join(_p, '_공용', '_귀.py')) and os.path.dirname(_p) != _p: _p = os.path.dirname(_p)
sys.path.insert(0, os.path.join(_p, '_공용'))
import 경로
from _귀 import 귀열기

설 = 경로.설정(__file__)
여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace(chr(92), '/')
임시 = f'{여기}/_기준16k.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 설['기준영상'], '-vn', '-ac', '1', '-ar', '16000', 임시], check=True)
m = 귀열기('large-v3')
PROMPT = '어, 음, 그, 저, 그니까, 자, 이제, 어… 그 그러니까 이게 이게 말이죠.'
조각, _ = m.transcribe(임시, language='ko', word_timestamps=True, vad_filter=False, condition_on_previous_text=False, initial_prompt=PROMPT, beam_size=5)
결과 = []
for g in 조각:
    단어 = [[w.word.strip(), round(w.start, 3), round(w.end, 3)] for w in (g.words or []) if w.word.strip()]
    if 단어: 결과.append({'t0': 단어[0][1], 't1': 단어[-1][2], '글': ' '.join(w[0] for w in 단어), '단어': 단어})
json.dump(결과, open(f'{여기}/말시각.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
os.remove(임시)
print('말시각.json · 조각', len(결과), '· 낱말', sum(len(c['단어']) for c in 결과))
