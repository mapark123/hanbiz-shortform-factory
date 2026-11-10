---
name: hanbiz-shortform
description: 한비즈 쇼츠 공장 — 세로(9:16) 쇼츠·릴스·메타 광고 영상. 말하는 사람(원장님·대표) 세로 영상 한 편을 목 아래 고정 자막(가운데·샥샥·노란 알약) · 위에서 내려오는 종이 판(세로 반반, 사람은 아래로) · 인화 사진·포스트잇·도장·펜 표시 · 예능 큰 자막 · Q 카드 · 상담 버튼 · 한비즈 효과음 자동 배치 · −14 LUFS 로 완성본까지 만들고, 롱폼 → 채널 쇼츠(S6)도 한다. 저장소를 받고(처음) 업데이트(git pull)하는 법도 여기. 트리거 - 쇼츠 공장, 쇼츠 만들어, 쇼츠 광고, 원장님 쇼츠, 세로 영상, 릴스, 쇼츠 자막, 목 아래 자막, 쇼츠 공장 업데이트, 쇼츠 업데이트 땡겨와.
---

# 한비즈 쇼츠 공장

저장소: https://github.com/mapark123/hanbiz-shortform-factory (공개). **일은 저장소 폴더 안에서 한다** — 그 폴더의 `CLAUDE.md` 와 프로젝트 스킬(`.claude/skills/shortform/`)이 규칙 전부다. 이 파일은 «어디서 받고 어떻게 들어가나»만 안내한다.

## 1. 저장소 찾기 · 받기 · 업데이트

```
# 이 PC 에 있나?  (보통 C:\에이전트\hanbiz-shortform-factory)
git -C <저장소 폴더> pull                    # «쇼츠 공장 업데이트 땡겨와줘» = 이것
git clone https://github.com/mapark123/hanbiz-shortform-factory.git C:\에이전트\hanbiz-shortform-factory   # 없으면
```
- 업데이트 뒤: `git log --oneline -5` 의 새 줄을 사용자에게 짧게 알린다. 이 스킬 파일(`스킬/hanbiz-shortform/SKILL.md`)이 바뀌었으면 `~/.claude/skills/hanbiz-shortform/` 에 다시 복사한다.
- 고친 걸 올릴 때만 GitHub 로그인(mapark123)이 필요하다. 개인정보·병원명·영상·사진은 올리지 않는다(`.gitignore` 가 막는다).

## 2. 무엇을 열어 읽나

| 일 | 열 파일(저장소 기준) |
|---|---|
| 말하는 사람 세로 쇼츠 한 편(광고·정보) | `.claude/skills/shortform/references/s8-vertical-factory.md` → `세로공장/README.md` → 예시 `세로공장/예시_세로시험/` |
| 롱폼 → 채널 쇼츠 | `.claude/skills/shortform/references/s6-longform-shorts.md` |
| 전체 규칙·멈추는 곳 | `CLAUDE.md` → `.claude/skills/shortform/SKILL.md` |

## 3. 꼭 지킬 것 (짧게)
- 영상은 텔레그램에 올리지 않고 PC 에서 바로 띄운다. C 는 실행·임시만 — 완성본은 구글 드라이브.
- 효과음은 한비즈 라이브러리에서만(코드 합성음 X), 자료 등장 = 마우스 클릭 · 장 넘김 = 종이 소리 고정.
- 이미지는 Codex 실사 먼저(추가 과금 없음), 유료 생성은 사장님이 말씀하실 때만.
