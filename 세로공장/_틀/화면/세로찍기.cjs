// 세로 겹침 층을 투명 PNG 로 찍어 prores 4444 로 묶는다.
// 사용: node 세로찍기.cjs 시작초 끝초 출력.mov [배율]   |   node 세로찍기.cjs 미리 폴더 시각목록(쉼표) [배율]
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');
let _u = __dirname; while (!fs.existsSync(_u + '/_공용/경로.cjs') && path.dirname(_u) !== _u) _u = path.dirname(_u);
const { chromium } = require(_u + '/_공용/경로.cjs').플레이라이트(__dirname);
const 여기 = __dirname.split(path.sep).join('/');
(async () => {
  const 인자 = process.argv.slice(2), 미리 = 인자[0] === '미리';
  const 배율 = +(인자[3] || 1);
  const br = await chromium.launch({ channel: 'chrome', args: ['--allow-file-access-from-files', '--use-angle=d3d11', '--enable-gpu-rasterization', '--ignore-gpu-blocklist', `--force-device-scale-factor=${배율}`] });
  const p = await br.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 배율 });
  const 오류 = []; p.on('pageerror', (e) => 오류.push(e.message));
  await p.goto('file:///' + 여기 + '/세로화면.html');
  await p.waitForFunction(() => window.__준비, null, { timeout: 180000 });
  const c = await p.context().newCDPSession(p);
  await c.send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });
  const 찍 = async () => Buffer.from((await c.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true })).data, 'base64');
  if (미리) {
    fs.mkdirSync(인자[1], { recursive: true });
    for (const s of 인자[2].split(',').map(Number)) { await p.evaluate((t) => window.__frame(t), s); fs.writeFileSync(`${인자[1]}/${s.toFixed(2)}.png`, await 찍()); }
    console.log('미리 끝 · 오류', JSON.stringify(오류)); await br.close(); return;
  }
  const [a, b, 출력] = 인자;
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '60', '-c:v', 'png', '-i', '-', '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', '-qscale:v', '13', '-threads', '2', 출력], { stdio: ['pipe', 'inherit', 'inherit'] });
  const 첫 = Math.round(+a * 60), 수 = Math.round(+b * 60) - 첫, t0 = Date.now();
  for (let i = 0; i < 수; i++) {
    await p.evaluate((t) => window.__frame(t), (첫 + i) / 60);
    if (!ff.stdin.write(await 찍())) await new Promise((o) => ff.stdin.once('drain', o));
  }
  ff.stdin.end();
  await new Promise((o, n) => ff.on('close', (k) => (k === 0 ? o() : n(new Error('ffmpeg ' + k)))));
  console.log(`끝 ${path.basename(출력)} ${수}장 ${Math.round((Date.now() - t0) / 1000)}초 오류 ${JSON.stringify(오류)}`);
  await br.close();
})().catch((e) => { console.error(e.message); process.exit(1); });
