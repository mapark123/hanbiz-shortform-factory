"""장면마다 자료가 다 나온 순간을 실제 사람 화면(판 내림·확대 적용) 위에 합성해 한 장으로 본다.
사용: python -X utf8 화면/_도구/세로미리모음.py [출력폴더=화면/_미리] [--시각 1.2,3.4] → 모음0.jpg …(한 장에 24칸) · 원본 크기 칸은 출력폴더/칸/"""
import glob, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
_p = os.path.abspath(__file__)
while not os.path.exists(os.path.join(_p, '_공용', '_귀.py')) and os.path.dirname(_p) != _p: _p = os.path.dirname(_p)
sys.path.insert(0, os.path.join(_p, '_공용')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 경로, 움직임
설 = 경로.설정(__file__); os.chdir(설['프로젝트'])
인자 = [a for a in sys.argv[1:]]
곳 = 인자[0] if 인자 and not 인자[0].startswith('--') else '화면/_미리'
for d in ('ov', '칸'): os.makedirs(f'{곳}/{d}', exist_ok=True)
for f in glob.glob(곳 + '/ov/*.png') + glob.glob(곳 + '/칸/*.jpg'): os.remove(f)
D = json.loads(open('화면/세로데이터.js', encoding='utf-8').read().replace('window.D=', '').rstrip(';\n'))
if '--시각' in 인자:
    ts = sorted(float(x) for x in 인자[인자.index('--시각') + 1].split(','))
else:
    ts = set()
    for p in D['판']:
        for c in p['층']:
            시각 = [it.get('t') for it in c['items'] if it.get('t')] + [s[1] for it in c['items'] if it['k'] == 'chain' for s in it['steps']]
            ts.add(round(max(시각 + [c['t'] + .7]) + .75, 2))
    for x in D['훅']: ts.add(round(x['t0'] + .9, 2))
    for x in D['포인트']: ts.add(round(x['t큰'] + .6, 2))
    for x in D['질문']: ts.add(round(x['t0'] + .6, 2))
    for x in D['위']: ts.add(round(x['t'] + .7, 2))
    for x in D['손글씨'] + D['이름표']: ts.add(round(x['t0'] + .6, 2))
    for x in D['행동']: ts.add(round((x.get('t탭') or x['t0']) + .3, 2))
    for k in range(0, len(D['줄']), max(1, len(D['줄']) // 6)):  # 자막만 나오는 곳도 몇 장
        ws = [d for d in D['단어'] if d['줄'] == k]; ts.add(round(ws[0]['t0'] + .4, 2))
    ts = sorted(t for t in ts if t < D['길이'])
print(len(ts), '장')
r = subprocess.run(['node', '화면/세로찍기.cjs', '미리', 곳 + '/ov', ','.join(map(str, ts))], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(r.stdout[-300:], r.stderr[-300:])
W, H = 1080, 1920; w, h, 열 = 270, 480, 6
칸들 = []
for t in ts:
    바 = 움직임.옮기기(움직임.한장(설, t, W, H), D, t)
    c = Image.alpha_composite(Image.fromarray(바).convert('RGBA'), Image.open(f'{곳}/ov/{t:.2f}.png').convert('RGBA').resize((W, H))).convert('RGB')
    c.save(f'{곳}/칸/{t:06.2f}.jpg', quality=88); 칸들.append((t, c))
장수 = 24
for 쪽 in range(0, len(칸들), 장수):
    묶 = 칸들[쪽:쪽 + 장수]; 판 = Image.new('RGB', (w * 열, h * ((len(묶) + 열 - 1) // 열)), (20, 20, 20))
    for i, (t, c) in enumerate(묶):
        c = c.resize((w, h)); ImageDraw.Draw(c).text((6, h - 16), f'{t:.2f}', fill=(255, 255, 0)); 판.paste(c, ((i % 열) * w, (i // 열) * h))
    판.save(f'{곳}/모음{쪽 // 장수}.jpg', quality=86)
print('끝', 곳)
