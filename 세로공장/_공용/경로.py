"""프로젝트 설정 읽기 (모든 파이썬 도구가 공통으로 씀).
- 프로젝트 = 위로 올라가며 `설정.json` 이 있는 첫 폴더 (예: 쇼츠_이름/)
- 공용 = 위로 올라가며 `_공용/_귀.py` 가 있는 폴더의 _공용
- 설정.json 의 상대 경로는 프로젝트 기준으로 풀고, «길이»가 0 이면 기준영상을 ffprobe 로 잰다."""
import json, os, subprocess


def 위로찾기(시작, 조건):
    p = os.path.abspath(시작)
    if os.path.isfile(p): p = os.path.dirname(p)
    while True:
        if 조건(p): return p.replace(chr(92), '/')
        위 = os.path.dirname(p)
        if 위 == p: return None
        p = 위


def 프로젝트(시작):
    p = 위로찾기(시작, lambda d: os.path.exists(os.path.join(d, '설정.json')))
    if not p: raise SystemExit('설정.json 을 못 찾음 — 프로젝트 폴더(쇼츠_이름/) 맨 위에 _틀/설정.json 을 복사해 채우세요')
    return p


def 공용(시작):
    p = 위로찾기(시작, lambda d: os.path.exists(os.path.join(d, '_공용', '_귀.py')))
    return (p + '/_공용') if p else None


def 설정(시작):
    뿌리 = 프로젝트(시작)
    s = json.load(open(os.path.join(뿌리, '설정.json'), encoding='utf-8'))
    s['프로젝트'] = 뿌리
    for k in ('기준영상', '원본녹화'):
        if s.get(k) and not os.path.isabs(s[k]): s[k] = f'{뿌리}/{s[k]}'
    s['효과음라이브러리'] = os.environ.get('HANBIZ_SFX_LIB') or s.get('효과음라이브러리', '')
    if not s.get('길이') and s.get('기준영상') and os.path.exists(s['기준영상']):
        r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', s['기준영상']], capture_output=True, text=True)
        s['길이'] = round(float(r.stdout.strip()), 3)
    return s
