"""세로(9:16) 쇼츠 부품. 세로콘티.py 가 `from 세로부품 import *` 로 불러 장면만 적고, 마지막에 마무리() 를 부른다.
모든 시각은 낱말 시각(화면/세로시각.json)에서 나온다 → 화면(세로데이터.js)·사람 움직임(세로합치기.py)·효과음(배치도.json)이 같은 숫자를 읽어 싱크가 맞는다.

시각 찾기
  L('줄 조각')            그 줄 첫 낱말 시작          E('줄 조각')  그 줄 끝
  W('줄 조각', '낱말')     그 줄(없으면 다음 줄)의 낱말 시작 · 같은 조각이 여러 줄이면 n=1,2…
화면 자리(1080×1920, 설정.json)
  자막_y(목 아래 고정) · 판_아래(종이 판이 덮는 높이) · 판_사람내림(판이 열릴 때 사람을 내리는 거리)
판(종이가 위에서 내려와 자막 위까지 덮고, 사람 화면은 아래로 내려가 얼굴이 자막 밑에 온다) 안에 층을 쌓는다
  판(열기, 닫기, 종이(t, 자료…), 벽사진(t, '이미지', 자료…), 첫=False)
  자료 = 사진 · 표(태그) · 메모(노란 포스트잇 손글씨) · 그림(동그라미·X·화살표·밑줄이 그려짐) · 도장 · 단계(원인→결과 사슬)
판 밖 = 훅(머리 위 큰 제목 2줄) · 위사진(얼굴 위에 뜨는 카드) · 포인트(예능 큰 자막) · 질문(Q 카드) · 이름표 · 코너 · 손글씨 · 행동(상담 버튼·↓·탭)
사람 화면 = 확대(t, 배율) — 다음 확대까지 유지, 0.35초 감속
효과음은 자료마다 역할(착·슉·휙·쿵·띵·펜·클릭·도장·틀림·코믹·반짝·뿅)로 적어 두면 마무리() 가 라이브러리에서 고른다.
  자료 등장 = 마우스 클릭 고정 · 종이 장 넘김 = 종이넘기는 소리 고정 · 판 전환 = 시작이 빠른 휙 계열만 돌려 씀 · 나머지 = 같은 파일 두 번 X"""
import collections, json, os, re, subprocess, sys
_p = os.path.abspath(__file__)
while not os.path.exists(os.path.join(_p, '_공용', '_귀.py')) and os.path.dirname(_p) != _p: _p = os.path.dirname(_p)
sys.path.insert(0, os.path.join(_p, '_공용'))
import 경로
설 = 경로.설정(__file__); os.chdir(설['프로젝트'])
D = json.load(open('화면/세로시각.json', encoding='utf-8'))
줄, 단어 = D['줄'], D['단어']; 길이 = D['길이']
라이브 = os.environ.get('SFX_DRYRUN_LIB') or 설['효과음라이브러리']
자막_y = 설.get('자막_y', 1060); 판_아래 = 설.get('판_아래', 자막_y - 120)


def K(조각, n=0):
    후보 = [k for k, l in enumerate(줄) if 조각 in l]
    if len(후보) <= n: raise SystemExit('줄 없음: ' + 조각)
    return 후보[n]
def Ws(k): return [d for d in 단어 if d['줄'] == k]
def L(조각, n=0): return Ws(K(조각, n))[0]['t0']
def E(조각, n=0): return Ws(K(조각, n))[-1]['t1']
def W(조각, 낱, n=0, m=0):
    k = K(조각, n); 후보 = [d for d in Ws(k) if 낱 in d['w']]
    if len(후보) <= m and k + 1 < len(줄): 후보 += [d for d in Ws(k + 1) if 낱 in d['w']]  # 뜻 단위로 나눈 다음 줄까지 본다
    if len(후보) <= m: raise SystemExit(f'낱말 없음: {조각} / {낱}')
    return 후보[m]['t0']


사건 = []  # (시각, 역할)
def 소리(t, 역할):
    if 역할: 사건.append((round(t, 3), 역할))
    return t

# 종이 판 안의 자리 (x, y, 폭, 높이) — 판 높이 940 기준, 판_아래에 맞춰 세로로 늘고 준다.
# 맨 위 220px 은 비운다(쇼츠 위 버튼 0~150 · 코너 제목 120~200). 사진 1장 = 큰 · 2장 = 왼+오 (또는 왼위+오아래) · 3장 = 세1~3
# 표·메모·도장 같은 손 배치 자료도 y 220 아래에 둔다(코너를 안 쓰면 150 아래).
_f = 판_아래 / 940
슬롯 = {k: (x, 220 + round((y - 220) * _f), w, round(h * _f)) for k, (x, y, w, h) in {
    '큰': (110, 235, 860, 620), '왼': (40, 260, 490, 540), '오': (550, 310, 490, 540),
    '왼위': (40, 230, 520, 360), '오아래': (520, 520, 520, 360),
    '세1': (30, 230, 480, 330), '세2': (570, 290, 480, 330), '세3': (300, 560, 480, 300)}.items()}
회전 = {'큰': -1.4, '왼': -2.4, '오': 2.4, '왼위': -2.6, '오아래': 2.4, '세1': -2.6, '세2': 2.8, '세3': -1.4}
def 사진(img, 이름, t, 슬, r=None, 역할='착'):
    """인화 사진 + 테이프 + 아래 이름. img = 재료/이미지/{img}.png"""
    x, y, w, h = 슬롯[슬]; 소리(t, 역할)
    return {'k': 'print', 'img': img, 'label': 이름, 't': t, 'x': x, 'y': y, 'w': w, 'h': h, 'r': 회전[슬] if r is None else r}
def 표(html, t, x, y, r=-2, 역할='착', 크기=46):
    """종이 태그. <b>강조</b> 는 빨강"""
    소리(t, 역할); return {'k': 'tag', 'html': html, 't': t, 'x': x, 'y': y, 'r': r, 'fs': 크기}
def 메모(글, t, x, y, w=300, h=240, fs=104, r=4, 역할='펜'):
    """노란 포스트잇 손글씨. 줄바꿈 <br>"""
    소리(t, 역할); return {'k': 'note', 'text': 글, 't': t, 'x': x, 'y': y, 'w': w, 'h': h, 'fs': fs, 'r': r}
def 그림(종류, t, x, y, w, h, 색='#e0202e', 역할='클릭', 굵기=None, d=.36):
    """펜으로 그려지는 표시: circle · x · arrowR · arrowU · arrowD · under(밑줄)"""
    소리(t, 역할); return {'k': 'draw', 'd': 종류, 't': t, 'x': x, 'y': y, 'w': w, 'h': h, 'c': 색, 'sw': 굵기, 'dur': d}
def 도장(글, t, x, y, r=-7, 색='#d51c2d', fs=96, 역할='도장'):
    소리(t, 역할); return {'k': 'stamp', 'text': 글, 't': t, 'x': x, 'y': y, 'r': r, 'c': 색, 'fs': fs}
def 단계(목록, x, y, 역할='착', 폭=520):
    """원인→결과 단계: [(글, 시각)] — 말할 때마다 한 칸씩 붙는다"""
    for _, t in 목록: 소리(t, 역할)
    return {'k': 'chain', 'steps': 목록, 'x': x, 'y': y, 'w': 폭}
def 종이(t, *items, 역할='슉'): 소리(t, 역할); return {'t': t, 'kind': 'paper', 'items': list(items)}
def 벽사진(t, img, *items, 역할='슉'):
    """판 전체를 사진 한 장으로"""
    소리(t, 역할); return {'t': t, 'kind': 'photo', 'img': img, 'items': list(items)}

판들 = []
def 첫자료(c):
    시 = [it['t'] for it in c['items'] if it.get('t')] + [x[1] for it in c['items'] if it['k'] == 'chain' for x in it['steps']]
    return min(시) if 시 else c['t']
def 판(열기, 닫기, *층, 첫=False):
    """종이 판. 열기~닫기 동안 위를 덮고 사람은 내려간다(설정 «판_사람내림»)."""
    if 층 and (round(층[0]['t'], 3), '슉') in 사건: 사건.remove((round(층[0]['t'], 3), '슉'))  # 첫 장 소리는 판 여는 소리와 겹친다
    이어짐 = 판들 and abs(판들[-1]['닫기'] - 열기) < .05
    # 빈 종이 금지: 첫 자료 0.75초 전에 연다 · 다음 장은 첫 자료 0.5초 전에 넘긴다
    if 층 and not 첫 and not 이어짐:
        처음 = 첫자료(층[0]) if 층[0]['kind'] == 'paper' else 층[0]['t']   # 벽사진은 사진이 곧 첫 자료
        if 처음 - 열기 > .85: 열기 = 처음 - .75
        층[0]['t'] = 열기 + .05
    for c in 층[1:]:
        if c['kind'] == 'paper' and 첫자료(c) - c['t'] > .6:
            옛 = (round(c['t'], 3), '슉')
            if 옛 in 사건: 사건.remove(옛)
            c['t'] = 첫자료(c) - .5; 소리(c['t'], '슉')
    if not 이어짐: 소리(열기, '휙')
    소리(닫기, '휙')
    판들.append({'열기': round(열기, 3), '닫기': round(닫기, 3), '층': list(층), '첫': 첫})
훅들, 위들, 포인트들, 질문들, 손글씨들, 이름표들, 코너들, 행동들, 확대들 = [], [], [], [], [], [], [], [], []
숨김 = set()
def 훅(줄1, 줄2, t0, t1, 강조=None, y=170, 역할='쿵'):
    """첫 화면 머리 위 큰 제목 2줄(얼굴은 안 가림). 둘째 줄이 0.3초 뒤 쾅 박힌다. 강조 글자는 노랑"""
    소리(t0 + .3, 역할); 훅들.append({'줄1': 줄1, '줄2': 줄2, 't0': round(t0, 3), 't1': round(t1, 3), '강조': 강조, 'y': y})
def 위사진(img, t, t1, 스타일='카드', 이름='', y=None, w=860, h=640, r=0, 역할='착'):
    """판 없이 얼굴 위에 뜨는 사진. 스타일 카드(흰 테두리 둥근 판) | 인화(테이프 + 아래 이름). y = 위 끝(없으면 자막 위 가운데)"""
    if y is None: y = max(150, (자막_y - 110 - h) // 2)
    소리(t, 역할)
    위들.append({'k': 'card' if 스타일 == '카드' else 'print', 'img': img, 'label': 이름, 't': round(t, 3), 't1': round(t1, 3), 'x': (1080 - w) // 2, 'y': y, 'w': w, 'h': h, 'r': r})
def 위자료(item, t1):
    """판 안 자료(표·메모·도장·그림·단계)를 판 없이 화면 좌표로 띄운다"""
    위들.append({**item, 't1': round(t1, 3)})
def 포인트(큰글, t큰, 끝, 색='y', y=None, fs=132, 역할='쿵', 숨길=()):
    """예능 큰 자막. 색 y = 노랑 글자 검정 테두리 · r = 빨강 글자 흰 테두리(위험·하지 마세요). 줄바꿈 <br>.
    뜨는 동안 아래 자막은 숨는다(서브 문구 없이 큰 자막만 — 대표 피드백). y = 글 가운데(없으면 자막 자리)"""
    소리(t큰, 역할); 포인트들.append({'big': 큰글, 't큰': round(t큰, 3), '끝': round(끝, 3), 'c': 색, 'y': 자막_y if y is None else y, 'fs': fs})
    for 조각 in 숨길: 숨김.add(K(조각))
def 질문(글, t0, t1, 숨길=()):
    """파란 Q 카드(시청자 질문, 위쪽). 뜨는 동안 그 줄 자막은 숨긴다. 줄바꿈 <br>"""
    소리(t0, '띵'); 질문들.append({'text': 글, 't0': round(t0, 3), 't1': round(t1, 3)})
    for 조각 in 숨길: 숨김.add(K(조각))
def 이름표(위, 아래, t0, t1, y=None, 역할='반짝'):
    """왼쪽 이름표(자막 위): 위(노랑 작은 글) · 아래(검정 큰 글)"""
    소리(t0, 역할); 이름표들.append({'t0': round(t0, 3), 't1': round(t1, 3), '위': 위, '아래': 아래, 'y': 자막_y - 300 if y is None else y})
def 코너(번호, 글, t, 역할='뿅'):
    """왼쪽 위 코너 제목(① 원인). 마무리(코너끝=…) 에서 사라진다"""
    소리(t, 역할); 코너들.append({'t': round(t, 3), 'n': str(번호), 'text': 글})
def 손글씨(글, t0, t1, x, y, r=-4, 역할='코믹'):
    """예능 손글씨 자막(속마음·드립)"""
    소리(t0, 역할); 손글씨들.append({'text': 글, 't0': round(t0, 3), 't1': round(t1, 3), 'x': x, 'y': y, 'r': r})
def 행동(글, t0, 끝, t화살=None, t탭=None, t눌림=None, y=None):
    """행동 유도: 버튼 올라옴(t0) → ↓ 화살표(t화살) → 손가락 탭(t탭) → 눌림·노랑(t눌림). y = 버튼 위 끝(없으면 자막 아래)"""
    소리(t0, '뿅')
    if t화살: 소리(t화살, '뿅')
    if t탭: 소리(t탭, '클릭')
    if t눌림: 소리(t눌림, '띵')
    행동들.append({'글': 글, 't0': round(t0, 3), '끝': round(끝, 3), 't화살': t화살, 't탭': t탭, 't눌림': t눌림, 'y': 자막_y + 110 if y is None else y})
def 확대(t, 배율=1.08):
    """사람 화면 당기기(얼굴_y 기준). 다음 확대까지 유지 · 1.0 이면 풀림"""
    확대들.append([round(t, 3), 배율])


def _등급(p):
    return next((v for k, v in [('/1_A', 'A★'), ('/2_A/', 'A'), ('/3_B/', 'B'), ('/4_C/', 'C'), ('/5_', '장면음'), ('/6_', '미등급')] if k in p), '?')


def 마무리(핵심=(), 코너끝=None):
    """핵심: [(줄 조각, 칠할 글자)] — 그 줄이 뜨고 0.06초 뒤 노란 알약이 왼→오로 쓸며 칠해진다. 한 줄에 하나, 모든 줄에 넣지 않는다"""
    핵심표 = {}
    for 조각, 칠 in 핵심:
        k = K(조각)
        if 칠 not in 줄[k]: raise SystemExit(f'핵심 글자가 줄에 없음: {조각} / {칠}')
        핵심표[k] = 칠
    # 큰 자막 시작과 거의 같이 시작해 그 안에서 끝나는 줄은 아예 숨긴다(한순간 깜빡임 방지)
    for 포 in 포인트들:
        for k in range(len(줄)):
            ws = Ws(k)
            if ws and ws[0]['t0'] >= 포['t큰'] - .3 and ws[-1]['t1'] <= 포['끝'] + .3: 숨김.add(k)
    코끝 = 코너끝 if 코너끝 is not None else (길이 if 코너들 else 0)
    화면설정 = {k: 설.get(k) for k in ('자막_y', '판_아래', '판_사람내림', '얼굴_y', '로고', '고지')}
    화면설정['자막_y'] = 자막_y; 화면설정['판_아래'] = 판_아래
    데이터 = {'길이': 길이, '설정': 화면설정, '줄': 줄, '단어': 단어, '판': 판들, '위': 위들, '훅': 훅들, '포인트': 포인트들, '질문': 질문들, '손글씨': 손글씨들,
            '이름표': 이름표들, '코너': 코너들, '코너끝': 코끝, '행동': 행동들, '확대': sorted(확대들), '숨김': sorted(숨김), '핵심': 핵심표}
    open('화면/세로데이터.js', 'w', encoding='utf-8', newline='\n').write('window.D=' + json.dumps(데이터, ensure_ascii=False) + ';\n')
    쓴 = set()
    def 찾기(o):
        if isinstance(o, dict):
            if 'img' in o: 쓴.add(o['img'])
            for v in o.values(): 찾기(v)
        elif isinstance(o, list):
            for v in o: 찾기(v)
    찾기(판들); 찾기(위들)
    없음 = [i for i in sorted(쓴) if not os.path.exists(f'재료/이미지/{i}.png')]
    목록, 부족 = 효과음고르기()
    print('판', len(판들), '· 위사진', len(위들), '· 포인트', len(포인트들), '· 질문', len(질문들), '· 이미지', len(쓴), '· 효과음', len(목록), dict(collections.Counter(e['등급'] for e in 목록)))
    print('없는 이미지', 없음); print('효과음 부족', 부족)
    print('판 겹침', [(판들[i]['닫기'], 판들[i + 1]['열기']) for i in range(len(판들) - 1) if 판들[i]['닫기'] > 판들[i + 1]['열기'] + .01])
    겹침 = [(a['t'], b['t']) for a, b in zip(sorted(위들, key=lambda x: x['t']), sorted(위들, key=lambda x: x['t'])[1:]) if a['k'] in ('card', 'print') and b['k'] in ('card', 'print') and a['t1'] > b['t'] + .05]
    if 겹침: print('위사진 겹침(앞 사진이 안 나갔는데 다음이 뜸)', 겹침)
    판위 = [(w['t'], p['열기']) for w in 위들 for p in 판들 if w['t'] < p['닫기'] + .6 and w['t1'] > p['열기'] - .1]
    if 판위: print('위사진이 판과 겹침', 판위)


def 효과음고르기():
    import numpy as np
    if not 라이브 or not os.path.exists(라이브 + '/예능효과음-등급.json'): print('효과음 라이브러리 없음(예능효과음-등급.json) — 설정.json «효과음라이브러리» 또는 환경변수 HANBIZ_SFX_LIB:', 라이브); return [], sorted(사건)
    등급표 = {}
    for r in json.load(open(라이브 + '/예능효과음-등급.json', encoding='utf-8')): 등급표[r['파일'].replace(chr(92), '/').split('/')[-1]] = r
    모든 = []
    for root, _, fs in os.walk(라이브):
        for f in fs:
            if f.lower().endswith(('.wav', '.mp3')): 모든.append(os.path.join(root, f).replace(chr(92), '/'))
    # 광고·정보 쇼츠에 안 맞는 소리(때리기·비명·탈것·안내 방송 등)
    제외 = re.compile(r'뺨|패는|허얽|허어|에엥|글리치|전기|카캇|웃음|박수|呪|不安|사장님라이브러리|PA - |announcement|Bus|Truck|Train|train|car|Car|drone|engine|Engine|tram|Helicopter|Propeller|Motorcycle|월세|카운터|도미노|Elevator|ちゃんちゃん|トランペット|마림바|실로폰|marimba|xylophone', re.I)
    등급순 = lambda p: (0 if '/1_A' in p else 1 if '/2_A/' in p else 2 if '/5_' in p else 3 if '/3_B/' in p else 4 if '/4_C/' in p else 5)
    def 후보(*폴더, 이름들=()):
        앞 = [p for 이름 in 이름들 for p in 모든 if os.path.basename(p).startswith(이름)]
        뒤 = [p for p in 모든 if any(f'/{x}' in p for x in 폴더) and not 제외.search(os.path.basename(p)) and (등급표.get(os.path.basename(p), {}).get('핵심길이') or 0) <= 1.4]
        뒤.sort(key=lambda p: (등급순(p), -(등급표.get(os.path.basename(p), {}).get('점수') or 0), os.path.basename(p)))
        return 앞 + 뒤
    창고 = {
        '착': 후보('16_UI', 이름들=['사진_착착', '후기_착착', '매거진_착착', '카드_촤르륵', '사진_넘김']),
        '뿅': 후보('02_뿅'), '슉': 후보('10_휙', 이름들=['그리드_슉_빠름', '그리드_슉_느림']), '휙': 후보('10_휙', 이름들=['두꺼운 바람', '휙1', '휙２']),
        '쿵': 후보('01_쿵쾅', 이름들=['쿠궁', '도돈', 'SEL_文字表示の衝撃音1']), '띵': 후보('03_띵'), '펜': 후보('16_UI', 이름들=['SEL_シャーペン', '24. 연필']), '클릭': 후보('16_UI', 이름들=['마우스 클릭', '15. 마우스클릭']),
        '도장': 후보('06_실패', 이름들=['도장']), '틀림': 후보('06_실패'), '코믹': 후보('15_코믹'), '반짝': 후보('04_반짝'),
    }
    def 빠른소리(p):
        """판 여는 순간과 맞아야 하므로 소리 시작 0.25초 안에 최대가 되는 전환음만"""
        r = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-t', '3', '-ac', '1', '-ar', '8000', '-f', 'f32le', '-'], capture_output=True).stdout
        x = np.abs(np.frombuffer(r, np.float32))
        if not len(x) or x.max() < 1e-4: return False
        return (int(np.argmax(x)) - int(np.argmax(x > x.max() * .01))) / 8000 <= .25
    시험 = bool(os.environ.get('SFX_DRYRUN_LIB'))
    if not 시험:
        휙이름 = re.compile(r'휙|훅|바람|whoosh|woosh|swoosh|sweep|transition|高速|切り替え|マント', re.I)
        창고['휙'] = [p for p in 창고['휙'] if 휙이름.search(os.path.basename(p)) and 빠른소리(p)]
    고정 = {'착': '마우스 클릭.mp3', '슉': '종이넘기는 소리.mp3'}
    # 0.22초 안에 겹친 사건은 하나만 — 판 전환·큰 강조가 이기고, 자료 착은 진다(겹치면 «듣기싫어»)
    순위 = {'휙': 6, '쿵': 6, '슉': 5, '도장': 5, '띵': 4, '틀림': 4, '반짝': 3, '뿅': 3, '코믹': 3, '펜': 2, '클릭': 2, '착': 1}
    남김 = []
    for t, 역할 in sorted(사건):
        if 남김 and t - 남김[-1][0] < .22:
            if 순위.get(역할, 2) > 순위.get(남김[-1][1], 2): 남김[-1] = (남김[-1][0], 역할)  # 시각은 먼저 뜬 것, 소리는 센 것
            continue
        남김.append((t, 역할))
    쓴소리 = set(고정.values()); 목록 = []; 부족 = []; 앞고정 = {}; 휙번호 = 0
    for t, 역할 in 남김:
        if 역할 == '휙' and 창고['휙'] and not 시험:  # 판 전환은 고른 전환음 안에서 돌려 쓴다
            p = 창고['휙'][휙번호 % len(창고['휙'])]; 휙번호 += 1; n = os.path.basename(p); 쓴소리.add(n)
            목록.append({'t': t, '닻': 역할, '파일': p, '이름': n, '등급': _등급(p), '왜': '판 전환'}); continue
        if 역할 in 고정:
            if t - 앞고정.get(역할, -9) < .08: continue  # 같은 순간 두 번 울리지 않게
            앞고정[역할] = t; p = next((x for x in 모든 if os.path.basename(x) == 고정[역할]), None)
            if p is None: 부족.append((t, 역할)); continue
            목록.append({'t': t, '닻': 역할, '파일': p, '이름': 고정[역할], '등급': _등급(p), '왜': '자료 고정' if 역할 == '착' else '장 넘김 고정'}); continue
        p = next((x for 역 in {'슉': ['슉', '휙', '착'], '휙': ['휙', '슉', '착']}.get(역할, [역할]) for x in 창고[역] if os.path.basename(x) not in 쓴소리), None)
        if p is None: 부족.append((t, 역할)); continue
        n = os.path.basename(p); 쓴소리.add(n)
        목록.append({'t': t, '닻': 역할, '파일': p, '이름': n, '등급': _등급(p), '왜': 역할})
    # 라이브러리가 비거나 모자라면 배치도.json 을 덮어쓰지 않는다(전에 잘 만든 배치를 날리지 않게)
    if 부족 or 시험: print('효과음 부족', len(부족), '— 배치도.json 그대로 둠')
    else: json.dump([{'번호': 1, 't0': 0, 't1': 길이, '제목': '전체', '효과음': 목록}], open('화면/배치도.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    return 목록, 부족
