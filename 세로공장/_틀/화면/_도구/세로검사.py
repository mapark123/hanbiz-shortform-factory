"""완성본 검사 — 오류가 있으면 끝에 «ERROR» 줄을 찍고 1 로 끝난다(보여 드리기 전에 0 이어야 한다).
① 자막 줄: 2~3어절 · 0.4초 미만 · 다음 줄과 겹침  ② 줄마다 그 구간 소리만 받아써 자막 글자와 대조(싱크)
③ 목소리 그대로(효과음 섞기 전후)  ④ 효과음: 같은 파일 반복(고정음 빼고)·너무 작은 소리·0.25초 안에 두 개
⑤ 최종 소리 크기(LUFS·트루피크)  ⑥ 2초 넘는 화면 멈춤
사용: python -X utf8 화면/_도구/세로검사.py [--싱크만] [--빠르게(받아쓰기 건너뜀)]"""
import collections, difflib, json, os, re, subprocess, sys
import numpy as np, soundfile as sf
_p = os.path.abspath(__file__)
while not os.path.exists(os.path.join(_p, '_공용', '_귀.py')) and os.path.dirname(_p) != _p: _p = os.path.dirname(_p)
sys.path.insert(0, os.path.join(_p, '_공용'))
import 경로
설 = 경로.설정(__file__); os.chdir(설['프로젝트'])
영상 = 설['기준영상']; 결과 = f"완성/{설['제목']}_쇼츠.mp4"
D = json.loads(open('화면/세로데이터.js', encoding='utf-8').read().replace('window.D=', '').rstrip(';\n'))
n = lambda s: re.sub(r'[^가-힣0-9A-Za-z]', '', s)
오류, 경고 = [], []
말 = []
for k, l in enumerate(D['줄']):
    ws = [d for d in D['단어'] if d['줄'] == k]; 말.append({'k': k, 'l': l, 't0': ws[0]['t0'], 't1': ws[-1]['t1'], '어절': len(l.split())})
긴줄 = [(m['k'], m['l']) for m in 말 if m['어절'] > 4]
if 긴줄: 경고.append(f'자막 줄 4어절 넘음(2~3어절씩 끊기) {긴줄[:8]}')
짧 = [(m['k'], m['l'][:14], round(m['t1'] - m['t0'], 2)) for m in 말 if m['t1'] - m['t0'] < .4 and m['k'] not in D['숨김']]
if 짧: 경고.append(f'0.4초 미만 줄(읽기 전에 바뀜 — 앞줄과 합치기) {짧[:8]}')
겹 = [(m['k'], m['l'][:14]) for m, x in zip(말, 말[1:]) if m['t1'] > x['t0'] + .05]
if 겹: 오류.append(f'말 끝이 다음 줄 시작을 넘음(정렬 확인) {겹[:8]}')
SR = 16000
if '--빠르게' not in sys.argv:
    x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', 영상, '-vn', '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
    from _귀 import 귀열기
    m = 귀열기('large-v3'); 점 = []; 나쁨 = []
    for c in 말:
        a, b = c['t0'] - .06, c['t1'] + .1
        seg, _ = m.transcribe(x[int(max(0, a) * SR):int(b * SR)], language='ko', condition_on_previous_text=False, beam_size=5, temperature=0)
        들 = ' '.join(g.text.strip() for g in seg); q = difflib.SequenceMatcher(None, n(c['l']), n(들), autojunk=False).ratio(); 점.append(q)
        if q < .6: 나쁨.append(f"{q:.2f} {a:.2f}-{b:.2f} [{c['l']}] 들림: {들}")
    점 = np.array(점)
    print('싱크: 줄', len(말), '· 글자 일치 평균', round(float(점.mean()), 3), '· 0.6 미만', int((점 < .6).sum()))
    if 나쁨: 경고.append('싱크 의심 줄(받아쓰기 오류일 수도 — 귀로 확인)\n  ' + '\n  '.join(나쁨))
if '--싱크만' not in sys.argv:
    SR2 = 48000
    목 = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', 영상, '-vn', '-f', 'f32le', '-ac', '2', '-ar', str(SR2), '-'], capture_output=True).stdout, np.float32).reshape(-1, 2)
    합, _ = sf.read('화면/_소리_최종.wav', dtype='float32'); 효, _ = sf.read('화면/_효과음만.wav', dtype='float32'); k = min(len(목), len(합))
    차 = float(np.abs(합[:k] - 효[:k] - 목[:k]).max())
    print('목소리 차이 최대(섞기 전후)', 차)
    if 차 > 1e-4: 오류.append(f'목소리가 바뀜 {차}')
    배 = json.load(open('화면/배치도.json', encoding='utf-8'))[0]['효과음']
    고정 = {'마우스 클릭.mp3', '종이넘기는 소리.mp3'}
    반복 = [(이름, c) for 이름, c in collections.Counter(e['이름'] for e in 배 if e['왜'] != '판 전환').items() if c > 1 and 이름 not in 고정]
    if 반복: 오류.append(f'같은 효과음 반복 {반복}')
    붙음 = [(round(a['t'], 2), round(b['t'], 2)) for a, b in zip(배, 배[1:]) if b['t'] - a['t'] < .25]
    if 붙음: 경고.append(f'0.25초 안에 효과음 두 개(겹쳐 시끄러움) {붙음[:10]}')
    약 = []
    for e in 배:
        a = int(e['t'] * SR2); pk = 20 * np.log10(np.abs(효[a:a + int(.4 * SR2)]).max() + 1e-9)
        if pk < -26: 약.append((round(e['t'], 2), e['이름'][:24], round(float(pk), 1)))
    if 약: 경고.append(f'-26dB 아래 작은 효과음 {약}')
    print('효과음', len(배), '· 서로 다른 파일', len({e['이름'] for e in 배}))
    if os.path.exists(결과):
        r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', 결과, '-af', 'ebur128=peak=true', '-vn', '-f', 'null', '-'], capture_output=True, text=True, encoding='utf-8', errors='replace').stderr
        I = re.findall(r'I:\s+(-?[\d.]+) LUFS', r); TP = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)
        if I: print('최종 소리', I[-1], 'LUFS · 트루피크', TP[-1] if TP else '?', 'dBFS')
        목표 = 설.get('마감_LUFS')
        if I and 목표 is not None and abs(float(I[-1]) - 목표) > 1: 경고.append(f'소리 크기 {I[-1]} LUFS (목표 {목표})')
        if TP and float(TP[-1]) > -1.0: 오류.append(f'트루피크 {TP[-1]} dBFS (-1.5 이하)')
        r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', 결과, '-vf', 'scale=270:480,fps=15,freezedetect=n=0.0008:d=2', '-an', '-f', 'null', '-'], capture_output=True, text=True, encoding='utf-8', errors='replace').stderr
        멈 = re.findall(r'freeze_start: ([\d.]+)', r)
        if 멈: 경고.append(f'2초 넘는 멈춤 {멈[:10]}')
    else: 경고.append(f'완성본 없음 {결과} — 소리 크기·멈춤 검사 건너뜀')
print('\n'.join('WARN ' + w for w in 경고))
print('\n'.join('ERROR ' + e for e in 오류))
print('검사 끝 · ERROR', len(오류), '· WARN', len(경고))
sys.exit(1 if 오류 else 0)
