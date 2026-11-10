"""원고(원고.txt — 한 줄 = 자막 한 줄, 2~3어절)를 소리에 강제 정렬한다. 문단(말시각 기준 큰 쉼)마다 나눠 정렬해 오류가 번지지 않게 한다.
검사: 줄 시작이 whisper 줄 시각에서 크게 벗어나면 알린다. 사용: python -X utf8 화면/_도구/세로시각.py → 화면/세로시각.json"""
import difflib, json, os, re, subprocess, sys
import numpy as np
_p = os.path.abspath(__file__)
while not os.path.exists(os.path.join(_p, '_공용', '_귀.py')) and os.path.dirname(_p) != _p: _p = os.path.dirname(_p)
sys.path.insert(0, os.path.join(_p, '_공용'))
import 경로
설 = 경로.설정(__file__); os.chdir(설['프로젝트'])  # 모든 경로는 프로젝트 폴더 기준
from ko_align import Aligner  # _공용/ko_align.py (torch·torchaudio 필요)

영상 = 설['기준영상']
줄 = [l.strip() for l in open('원고.txt', encoding='utf-8') if l.strip()]
r = subprocess.run(['ffmpeg', '-v', 'error', '-i', 영상, '-vn', '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True, check=True)
소리 = np.frombuffer(r.stdout, np.float32).copy()
SR = 16000; 길이 = len(소리) / SR
n = lambda s: re.sub(r'[^가-힣0-9A-Za-z]', '', s)
# whisper 글자별 시각
말 = json.load(open('화면/말시각.json', encoding='utf-8'))
W글, WT = [], []
for c in 말:
    for w, a, b in c['단어']:
        g = n(w)
        for i, ch in enumerate(g): W글.append(ch); WT.append(a + (b - a) * i / max(1, len(g)))
원글, 소속 = [], []
for k, l in enumerate(줄):
    for ch in n(l): 원글.append(ch); 소속.append(k)
sm = difflib.SequenceMatcher(None, 원글, W글, autojunk=False); 짝 = {}
for a, b, m in sm.get_matching_blocks():
    for i in range(m): 짝[a + i] = b + i
대략 = []
for k in range(len(줄)):
    idx = [i for i, s in enumerate(소속) if s == k and i in 짝]
    대략.append(WT[짝[idx[0]]] if idx else None)
for k in range(len(줄)):
    if 대략[k] is None: 대략[k] = 대략[k - 1] + 1
# 약 40초마다, 줄 경계에서 묶어 정렬
묶음 = []; 시작 = 0
for k in range(1, len(줄)):
    if 대략[k] - 대략[시작] > 40: 묶음.append((시작, k)); 시작 = k
묶음.append((시작, len(줄)))
al = Aligner(); 단어 = []; 경고 = []
for a, b in 묶음:
    # 다음 묶음은 앞 묶음이 끝난 자리에서 시작한다(경계에서 순서가 뒤집히지 않게)
    t0 = max(0, 단어[-1]['t1'] - .05) if 단어 else 0.0
    t1 = min(길이, 대략[b] + 1.6) if b < len(줄) else 길이
    낱 = [(k, w) for k in range(a, b) for w in 줄[k].split()]
    # 다음 묶음 머리까지 넣으면 정렬이 끝에서 늘어나므로 그 말도 함께 넣고 버린다
    덧 = 줄[b].split()[:3] if b < len(줄) else []
    결과 = al.align(소리[int(t0 * SR):int(t1 * SR)], [w for _, w in 낱] + 덧)
    for (k, w), s in zip(낱, 결과):
        if s is None: s = ((단어[-1]['t1'] if 단어 else t0) - t0, (단어[-1]['t1'] if 단어 else t0) - t0 + .05, 0.0)  # 글자 없는 낱말(기호만)
        단어.append({'줄': k, 'w': w, 't0': round(t0 + s[0], 3), 't1': round(t0 + s[1], 3), '점수': round(s[2], 2)})
for k in range(len(줄)):
    d = [x for x in 단어 if x['줄'] == k]
    if abs(d[0]['t0'] - 대략[k]) > .7: 경고.append(f"{k} 정렬 {d[0]['t0']:.2f} vs 받아쓰기 {대략[k]:.2f} {줄[k]}")
# 순서 검사
앞 = 0
for d in 단어:
    if d['t0'] < 앞 - .02: 경고.append(f"순서 뒤집힘 {d['w']} {d['t0']}")
    앞 = d['t0']
print('줄', len(줄), '낱말', len(단어), '묶음', len(묶음), '· 평균 점수', round(float(np.mean([d['점수'] for d in 단어])), 2), '· 길이', round(길이, 2))
print('낮은 점수', [(d['w'], d['점수']) for d in 단어 if d['점수'] < .3][:30])
print('경고', len(경고)); print('\n'.join(경고[:30]))
json.dump({'길이': 길이, '줄': 줄, '단어': 단어}, open('화면/세로시각.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
