"""사람 화면 움직임 — 세로합치기·세로미리모음이 같이 쓴다(세로화면.html 의 판 움직임과 같은 곡선).
- 판이 열리면 사람 화면을 «판_사람내림» 만큼 아래로 내린다(얼굴이 자막 밑으로). 사람 위 끝은 판 아래 끝에 밀려 내려가므로(판보다 앞서지 않음) 틈이 안 보인다.
- 확대(t, 배율): 얼굴_y 를 기준으로 당긴다. 다음 확대까지 유지, 0.35초 감속."""
import subprocess
import numpy as np
from PIL import Image


def _cl(x): return min(1.0, max(0.0, x))
def outQ(x): return 1 - (1 - _cl(x)) ** 5
def outC(x): return 1 - (1 - _cl(x)) ** 3
def ioC(x):
    x = _cl(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def 판열림(D, t):
    """0~1 — 세로화면.html 의 boardwrap 과 같은 값"""
    for p in D['판']:
        if p['열기'] - .01 <= t < p['닫기'] + .7:
            return outQ((t - p['열기']) / .62) * (1 - ioC((t - p['닫기']) / .62))
    return 0.0


def 배율(D, t):
    z = 앞 = 1.0
    for t0, v in D.get('확대', []):
        if t < t0: break
        z = 앞 + (v - 앞) * outC((t - t0) / .35); 앞 = v
    return z


def 바탕필터(설, W, H):
    """기준영상 → W×H 세로 바탕(가로면 «가로자르기», 세로면 꽉 채워 가운데 자르기)"""
    c = 설.get('가로자르기')
    앞 = f'crop={c[2]}:{c[3]}:{c[0]}:{c[1]},' if c else ''
    return f'{앞}scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps=60,format=rgb24'


def 옮기기(fr, D, t, s=1):
    """fr: (H,W,3) uint8 바탕 한 장 → 확대·내림을 적용한 새 배열. s = 배율(1080 기준 대비)"""
    H, W = fr.shape[:2]
    z = 배율(D, t); k = 판열림(D, t); 판아래 = D['설정']['판_아래']
    끝 = 판아래 - 10 - (판아래 + 80) * (1 - k)        # 지금 판 아래 끝(찢은 가장자리 안쪽) — 세로화면.html boardwrap 과 같은 식
    내림 = int(round(max(0.0, min(D['설정'].get('판_사람내림') or 0, 끝)) * s))
    if abs(z - 1) > 1e-3:
        fy = (D['설정'].get('얼굴_y') or H / 2 / s) * s
        cw, ch = W / z, H / z
        x0 = (W - cw) / 2; y0 = min(max(fy - ch * fy / H, 0), H - ch)
        fr = np.asarray(Image.fromarray(fr).resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch)))
    if 내림 > 0:
        out = np.zeros_like(fr); out[내림:] = fr[:H - 내림]; fr = out
    return fr


def 한장(설, t, W, H):
    """기준영상의 t 초 한 장(바탕필터 적용)"""
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', 설['기준영상'], '-frames:v', '1', '-vf', 바탕필터(설, W, H), '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(r, np.uint8).reshape(H, W, 3).copy()
