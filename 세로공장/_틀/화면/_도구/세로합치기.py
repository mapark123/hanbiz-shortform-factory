"""완성본: 효과음 섞기 → 마감(배경음악 덕킹 · -14 LUFS) → 겹침 층 나눠 찍기 → 사람 화면 움직임(판 내림·확대) 위에 겹침 → mp4.
이미 찍은 조각은 건너뛴다(끊겨도 이어서 · 콘티를 고쳤으면 --새로). 사용: python -X utf8 화면/_도구/세로합치기.py [--화면만] [--새로] [--구간 시작 끝]
결과 = 완성/{제목}_쇼츠.mp4 (1080×1920·60fps, 배율 2면 2160×3840)"""
import glob, json, os, subprocess, sys, time
import numpy as np
_p = os.path.abspath(__file__)
while not os.path.exists(os.path.join(_p, '_공용', '_귀.py')) and os.path.dirname(_p) != _p: _p = os.path.dirname(_p)
sys.path.insert(0, os.path.join(_p, '_공용')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 경로, 인코더, 움직임
설 = 경로.설정(__file__); os.chdir(설['프로젝트'])
D = json.loads(open('화면/세로데이터.js', encoding='utf-8').read().replace('window.D=', '').rstrip(';\n'))
길이 = D['길이']; s = int(설.get('배율') or 1); W, H = 1080 * s, 1920 * s
인자 = sys.argv[1:]; 화면만 = '--화면만' in 인자
구간 = (float(인자[인자.index('--구간') + 1]), float(인자[인자.index('--구간') + 2])) if '--구간' in 인자 else (0.0, 길이)
t0 = time.time()
곳 = '화면/찍은것'; os.makedirs(곳, exist_ok=True)
if '--새로' in 인자:
    for f in glob.glob(f'{곳}/*'): os.remove(f)

# ── 소리
소리 = None
if not 화면만:
    env = {**os.environ, 'HANBIZ_SFX_LIB': 설['효과음라이브러리']}
    r = subprocess.run([sys.executable, '-X', 'utf8', '화면/_도구/효과음섞기.py'], capture_output=True, text=True, encoding='utf-8', env=env)
    if r.returncode != 0: raise SystemExit('효과음 섞기 실패 — 렌더 중단\n' + r.stderr[-800:])  # 옛 소리로 몰래 넘어가지 않는다
    print(r.stdout[-300:], flush=True)
    소리 = '화면/_소리_최종.wav'
    음악 = 설.get('배경음악'); 크기 = 설.get('마감_LUFS')
    if 음악 or 크기 is not None:
        입력 = ['-i', 소리]; 끝손 = f',loudnorm=I={크기}:TP=-1.5:LRA=11' if 크기 is not None else ''
        if 음악:  # 음악은 목소리가 나오면 줄어든다(덕킹)
            p = 음악 if os.path.isabs(음악) else f"{설['프로젝트']}/{음악}"
            입력 += ['-stream_loop', '-1', '-i', p]
            사슬 = (f"[0:a]aresample=48000[v];[1:a]aresample=48000,atrim=0:{길이 + .5},afade=t=in:d=.6,afade=t=out:st={max(0, 길이 - 1.6)}:d=1.6,volume={설.get('배경음악_dB', -21)}dB[b];"
                  f"[v]asplit=2[v1][vk];[b][vk]sidechaincompress=threshold=0.02:ratio=6:attack=80:release=450[bd];[v1][bd]amix=inputs=2:normalize=0:duration=first{끝손}[o]")
        else:
            사슬 = f'[0:a]aresample=48000{끝손}[o]'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', *입력, '-filter_complex', 사슬, '-map', '[o]', '-ar', '48000', '-t', str(길이), '화면/_소리_마감.wav'], check=True)
        소리 = '화면/_소리_마감.wav'
    print('소리 끝', round(time.time() - t0), '초', flush=True)

# ── 겹침 층(10초 조각, 동시에 4개)
조각 = 10.0; 첫k = int(구간[0] // 조각); 끝k = int(np.ceil(구간[1] / 조각))
할일 = [k for k in range(첫k, 끝k) if not os.path.exists(f'{곳}/{k:03d}.done')]; 도는 = {}
while 할일 or 도는:
    while 할일 and len(도는) < 4:
        k = 할일.pop(0); a, b = k * 조각, min(길이, (k + 1) * 조각)
        도는[k] = subprocess.Popen(['node', '화면/세로찍기.cjs', str(a), str(b), f'{곳}/{k:03d}.mov', str(s)], stdout=subprocess.DEVNULL)
    time.sleep(2)
    for k, p in list(도는.items()):
        if p.poll() is None: continue
        if p.returncode: raise SystemExit(f'찍기 실패 {k}')
        open(f'{곳}/{k:03d}.done', 'w').close(); 도는.pop(k)
print('찍기 끝', round(time.time() - t0), '초', flush=True)
open(f'{곳}/목록.txt', 'w', encoding='utf-8').write('\n'.join(f"file '{설['프로젝트']}/{곳}/{k:03d}.mov'" for k in range(첫k, 끝k)))

# ── 합치기: 바탕(사람) 한 장씩 움직이고 그 위에 겹침
a0, a1 = 구간; 앞자름 = a0 - 첫k * 조각; 수 = int(round((a1 - a0) * 60))
바 = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{a0:.3f}', '-i', 설['기준영상'], '-t', f'{a1 - a0:.3f}', '-vf', 움직임.바탕필터(설, W, H), '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
겹 = subprocess.Popen(['ffmpeg', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', f'{곳}/목록.txt', '-ss', f'{앞자름:.3f}', '-t', f'{a1 - a0:.3f}', '-vf', f'scale={W}:{H},format=rgba', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
os.makedirs('완성', exist_ok=True)
결과 = f"완성/{설['제목']}_쇼츠{'_화면' if 화면만 else ''}{'_구간' if '--구간' in 인자 else ''}.mp4"
입력소리 = [] if 화면만 else ['-ss', f'{a0:.3f}', '-t', f'{a1 - a0:.3f}', '-i', 소리]
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '60', '-i', '-', *입력소리,
                        '-map', '0:v', *([] if 화면만 else ['-map', '1:a', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000']),
                        *인코더.컷옵션(), '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', '-shortest', 결과], stdin=subprocess.PIPE)
n = 0
while n < 수:
    b = 바.stdout.read(W * H * 3); o = 겹.stdout.read(W * H * 4)
    if len(b) < W * H * 3: break
    fr = 움직임.옮기기(np.frombuffer(b, np.uint8).reshape(H, W, 3), D, a0 + n / 60, s)
    if len(o) == W * H * 4:
        ov = np.frombuffer(o, np.uint8).reshape(H, W, 4)
        줄 = np.flatnonzero(ov[::4, ::8, 3].max(axis=1)) * 4  # 겹침이 있는 줄만 섞는다(자막·고지만 있는 장면이 대부분)
        if len(줄):
            y0, y1 = max(0, 줄[0] - 4), min(H, 줄[-1] + 8)
            al = ov[y0:y1, :, 3:4].astype(np.uint16); fr = fr.copy()
            fr[y0:y1] = ((fr[y0:y1].astype(np.uint16) * (255 - al) + ov[y0:y1, :, :3].astype(np.uint16) * al + 127) // 255).astype(np.uint8)
    enc.stdin.write(fr.tobytes()); n += 1
    if n % 600 == 0: print(f'합치기 {n}/{수} · {round(time.time() - t0)}초', flush=True)
enc.stdin.close(); enc.wait(); 바.kill(); 겹.kill()
print('끝', 결과, n, '장 ·', round(time.time() - t0), '초', flush=True)
print(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,width,height,r_frame_rate:format=duration', '-of', 'compact', 결과], capture_output=True, text=True).stdout[:400])
