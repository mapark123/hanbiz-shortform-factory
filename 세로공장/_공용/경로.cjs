// 프로젝트 설정 읽기 (node 도구 공통). 경로.py 와 같은 규칙.
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const 위로찾기 = (시작, 조건) => { let p = path.resolve(시작); if (fs.existsSync(p) && fs.statSync(p).isFile()) p = path.dirname(p); for (;;) { if (조건(p)) return p.split(path.sep).join('/'); const 위 = path.dirname(p); if (위 === p) return null; p = 위; } };
const 프로젝트 = (시작) => { const p = 위로찾기(시작, (d) => fs.existsSync(path.join(d, '설정.json'))); if (!p) throw new Error('설정.json 을 못 찾음 — 프로젝트 폴더 맨 위에 _틀/설정.json 을 복사해 채우세요'); return p; };
const 공용 = (시작) => { const p = 위로찾기(시작, (d) => fs.existsSync(path.join(d, '_공용', '_귀.py'))); return p ? p + '/_공용' : null; };
const 설정 = (시작) => {
  const 뿌리 = 프로젝트(시작); const s = JSON.parse(fs.readFileSync(path.join(뿌리, '설정.json'), 'utf8')); s.프로젝트 = 뿌리;
  for (const k of ['기준영상', '원본녹화']) if (s[k] && !path.isAbsolute(s[k])) s[k] = `${뿌리}/${s[k]}`;
  if (!s.길이 && s.기준영상 && fs.existsSync(s.기준영상)) s.길이 = Math.round(+execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', s.기준영상]).toString().trim() * 1000) / 1000;
  return s;
};
// 플레이라이트: 설정.json «playwright» 경로 → 환경변수 PLAYWRIGHT_PATH → 설치된 playwright-core
const 플레이라이트 = (시작) => { let s = {}; try { s = 설정(시작); } catch {} const 후보 = [s.playwright, process.env.PLAYWRIGHT_PATH, 'playwright-core', 'playwright'].filter(Boolean); for (const c of 후보) { try { return require(c); } catch {} } throw new Error('playwright-core 가 없음 — npm i -g playwright-core 또는 설정.json 의 playwright 경로'); };
module.exports = { 프로젝트, 공용, 설정, 플레이라이트 };
