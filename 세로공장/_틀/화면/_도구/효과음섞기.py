"""배치도.json 의 효과음을 목소리 위에 얹는다(«목소리 크기 올려 놨으니 낮추지 말고 배치» — 목소리는 한 샘플도 안 줄임, 크기 마감은 세로합치기가 한다).
- 목소리: 설정.json «기준영상» 소리 그대로(이득 1.0 · 한 샘플도 안 줄임)
- 효과음: 분류별 목표 최대치(dBFS)로 맞춤 · 소리 시작점(앞 무음 뒤)을 닻 시각에 맞춤 · 2.6초 넘으면 꼬리 페이드
- 등급표 소재상태: «고역 셈» → 7kHz 위 -4dB · «순간음» → 6ms 페이드인
- 겹쳐서 0dB 넘을 순간엔 효과음만 줄임(목소리는 그대로)
사용: python -X utf8 화면/_도구/효과음섞기.py → 화면/_소리_최종.wav · 화면/_효과음만.wav · 효과음기록.txt"""
import json, os, subprocess, io
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
import os, sys
_p = os.path.abspath(__file__)
while not os.path.exists(os.path.join(_p, '_공용', '_귀.py')) and os.path.dirname(_p) != _p: _p = os.path.dirname(_p)
sys.path.insert(0, os.path.join(_p, '_공용'))
import 경로
설 = 경로.설정(__file__)


여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace(chr(92), '/')
뿌리 = os.path.dirname(여기)
SR = 48000
배치 = json.load(open(f'{여기}/배치도.json', encoding='utf-8'))
등급표 = {}
for r in json.load(open(설['효과음라이브러리'] + '/예능효과음-등급.json', encoding='utf-8')):
    등급표.setdefault(r['파일'].replace(chr(92), '/').split('/')[-1], r)

def 읽기(p):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()

목, _ = None, None
r = subprocess.run(['ffmpeg', '-v', 'error', '-i', 설['기준영상'], '-vn', '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True)
목 = np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()
효 = np.zeros_like(목)

def 목표(경로):
    p = 경로
    if '01_쿵쾅' in p: return -7.0
    if '09_긴장' in p or '18_라이저' in p or '17_흡입' in p: return -9.0
    if '13_삑' in p: return -11.0
    if '06_실패' in p or '07_띠용' in p or '15_코믹' in p: return -12.0
    if '04_반짝' in p or '05_띵동' in p or '11_징글' in p or '19_음정' in p: return -12.5
    if '03_띵' in p or '12_종' in p: return -13.0
    if '10_휙' in p: return -12.0
    if '02_뿅' in p: return -14.0
    if '16_UI' in p: return -15.0
    if '5_장면음' in p or '20_종이' in p: return -12.5
    return -13.0

한계 = 10 ** (-1.0 / 20)
창 = int(.01 * SR)
def 포락(v):
    a = np.abs(v).max(1)
    n = len(a) // 창 * 창
    k = a[:n].reshape(-1, 창).max(1)
    return np.repeat(np.append(k, a[n:].max() if n < len(a) else 0), 창)[:len(a)]
mv = 포락(목)
여유 = np.clip(한계 - mv, 0, None)
옮김 = []
hs = butter(2, 7000, 'highpass', fs=SR, output='sos')
기록 = []
for s in 배치:
    for e in s['효과음']:
        x = 읽기(e['파일'])
        if len(x) == 0: 기록.append(f'빈 파일 {e["이름"]}'); continue
        m = np.abs(x).max(1)
        첫 = int(np.argmax(m > 10 ** (-40 / 20) * max(m.max(), 1e-9)))  # 소리 시작점(최대치 대비 -40dB)
        x = x[max(0, 첫 - int(.004 * SR)):]
        상태 = 등급표.get(e['이름'], {}).get('소재상태', '') or ''
        if '고역 셈' in 상태: x = x - (1 - 10 ** (-4 / 20)) * sosfilt(hs, x, axis=0)
        if len(x) > 2.6 * SR:
            x = x[:int(2.6 * SR)]; f = int(.5 * SR); x[-f:] *= np.linspace(1, 0, f)[:, None]
        fi = int(.006 * SR); x[:fi] *= np.linspace(0, 1, fi)[:, None]
        fo = int(.02 * SR); x[-fo:] *= np.linspace(1, 0, fo)[:, None]
        pk = np.abs(x).max()
        g = 10 ** (목표(e['파일']) / 20) / max(pk, 1e-9)
        x = x * g
        a0 = int(round(e['t'] * SR)); 길 = min(len(x), int(.35 * SR))
        xe = np.abs(x[:길]).max(1)
        def 점수(a):
            if a < 0 or a + 길 > len(여유): return -1
            h = 여유[a:a + 길]; m = xe > 1e-4
            return float(np.min(np.clip(h[m] / xe[m], 0, 1))) if m.any() else 1.0
        best, bs = a0, 점수(a0)
        if bs < .7:
            옮김폭 = int(설.get('효과음옮김_최대', .15) * 100)  # 뒷 장면(A) 0.15초 · 풀화면(B)은 자료가 낱말에 딱 붙어 0.04초
            for d in range(-옮김폭, 옮김폭 + 1):
                aa = a0 + int(d * .01 * SR); sc = 점수(aa) - abs(d) * .004
                if sc > bs + .05: best, bs = aa, sc
        if best != a0: 옮김.append(f'{e["t"]:7.2f} {e["이름"]} → {(best - a0) / SR:+.2f}초')
        a = best; b = min(len(효), a + len(x))
        if a < 0 or a >= len(효): 기록.append(f'자리 밖 {e["이름"]} {e["t"]}'); continue
        효[a:b] += x[:b - a]
        기록.append(f'{e["t"]:7.2f} 장면{s["번호"]:02d} {e["등급"]:3s} {목표(e["파일"]):6.1f}dBFS {"셸빙 " if "고역 셈" in 상태 else ""}{e["이름"]}')

# 겹쳐서 넘칠 때 효과음만 줄이기 (부드러운 이득 곡선)
ms = 포락(효)
g = np.ones(len(목))
넘 = (mv + ms) > 한계
g[넘] = np.clip((한계 - mv[넘]) / np.maximum(ms[넘], 1e-9), 0, 1)
# 이득 곡선을 30ms 로 부드럽게(최솟값 유지)
from scipy.ndimage import minimum_filter1d, uniform_filter1d
g = uniform_filter1d(minimum_filter1d(g, int(.03 * SR)), int(.03 * SR))
효 *= g[:, None]
합 = 목 + 효
print('효과음 줄인 구간(초)', round(float((g < .999).sum() / SR), 2), '· 합친 최대', round(float(20 * np.log10(np.abs(합).max())), 2), 'dBFS · 목소리 최대', round(float(20 * np.log10(np.abs(목).max())), 2), 'dBFS')
sf.write(f'{여기}/_효과음만.wav', 효, SR, subtype='FLOAT')
sf.write(f'{여기}/_소리_최종.wav', 합, SR, subtype='FLOAT')
open(f'{여기}/효과음기록.txt', 'w', encoding='utf-8').write('\n'.join(기록 + ['', '[목소리 피해 옮긴 것]'] + 옮김))
print('옮긴 효과음', len(옮김), '·', ' / '.join(옮김))
print('효과음', len([l for l in 기록 if '장면' in l]), '개 얹음 ·', len([l for l in 기록 if '장면' not in l]), '문제')
