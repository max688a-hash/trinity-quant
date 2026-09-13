import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';

const ARTIFACTS_DIR = '/Users/tianyou/.gemini/antigravity/brain/b9b559d7-559b-4b92-9494-42268873fd92/mobile_audit';
const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PORT = 9223;
const TARGET_URL = 'http://127.0.0.1:8088/';

fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

class CDPClient {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.ws = null;
    this.id = 1;
    this.callbacks = new Map();
    this.consoleErrors = [];
    this.consoleLogs = [];
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.wsUrl);
      this.ws.onopen = () => resolve();
      this.ws.onerror = (err) => reject(err);
      this.ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id && this.callbacks.has(msg.id)) {
          const { resolve, reject } = this.callbacks.get(msg.id);
          this.callbacks.delete(msg.id);
          if (msg.error) {
            reject(new Error(msg.error.message));
          } else {
            resolve(msg.result);
          }
        } else if (msg.method === 'Runtime.consoleAPICalled') {
          const type = msg.params.type;
          const text = msg.params.args.map(a => a.value || JSON.stringify(a)).join(' ');
          this.consoleLogs.push({ type, text });
          if (type === 'error') {
            this.consoleErrors.push(text);
          }
        } else if (msg.method === 'Runtime.exceptionThrown') {
          const desc = msg.params.exceptionDetails.exception?.description || msg.params.exceptionDetails.text;
          this.consoleErrors.push(desc);
        }
      };
    });
  }

  async send(method, params = {}) {
    const id = this.id++;
    const payload = { id, method, params };
    return new Promise((resolve, reject) => {
      this.callbacks.set(id, { resolve, reject });
      this.ws.send(JSON.stringify(payload));
    });
  }

  async eval(expression) {
    const res = await this.send('Runtime.evaluate', {
      expression,
      returnByValue: true,
      awaitPromise: true
    });
    if (res.exceptionDetails) {
      throw new Error(`Eval Error: ${res.exceptionDetails.text}`);
    }
    return res.result?.value;
  }

  async captureScreenshot(filename) {
    const res = await this.send('Page.captureScreenshot', { format: 'png' });
    const buffer = Buffer.from(res.data, 'base64');
    const outPath = path.join(ARTIFACTS_DIR, filename);
    fs.writeFileSync(outPath, buffer);
    console.log(`[SCREENSHOT] ${filename} (${buffer.length} bytes)`);
    return outPath;
  }

  close() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

async function runMobileAudit() {
  console.log('▶ [1/5] 启动 Chrome CDP 针对移动端 (iPhone 14: 390x844)...');
  const chromeDataDir = '/Volumes/tianyou-168/顶级量化/.chrome_mobile_profile';
  fs.mkdirSync(chromeDataDir, { recursive: true });

  const chromeProc = spawn(CHROME_PATH, [
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${chromeDataDir}`,
    '--headless=new',
    '--disable-gpu',
    '--no-sandbox',
    '--disable-crash-reporter',
    '--window-size=390,844'
  ], { stdio: 'ignore' });

  let targets = null;
  for (let i = 0; i < 25; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      if (res.ok) {
        targets = await res.json();
        if (targets && targets.length > 0) break;
      }
    } catch (e) {
      await sleep(300);
    }
  }

  if (!targets || targets.length === 0) {
    const createRes = await fetch(`http://127.0.0.1:${PORT}/json/new?${TARGET_URL}`);
    targets = [await createRes.json()];
  }

  const pageTarget = targets.find(t => t.type === 'page') || targets[0];
  const client = new CDPClient(pageTarget.webSocketDebuggerUrl);
  await client.connect();

  await client.send('Page.enable');
  await client.send('Runtime.enable');
  await client.send('DOM.enable');

  // 模拟真实 iPhone 14: 390 x 844, 3x DPR, 移动端 touch 模式
  await client.send('Emulation.setDeviceMetricsOverride', {
    width: 390,
    height: 844,
    deviceScaleFactor: 3,
    mobile: true,
    hasTouch: true
  });
  await client.send('Emulation.setUserAgentOverride', {
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1'
  });

  console.log(`▶ [2/5] 导航至 ${TARGET_URL}...`);
  await client.send('Page.navigate', { url: TARGET_URL });
  await sleep(2000);

  // 覆盖 alert 避免阻断
  await client.eval(`
    window.__captured_alerts = [];
    window.alert = function(msg) {
      console.log("[MOBILE_ALERT] " + msg);
      window.__captured_alerts.push(msg);
    };
  `);

  console.log('▶ [3/5] 检测移动端横向溢出 (Horizontal Overflow / 宽屏撑破)...');
  const overflowCheck = await client.eval(`
    (function() {
      const docW = document.documentElement.clientWidth;
      const scrollW = document.documentElement.scrollWidth;
      const bodyScrollW = document.body.scrollWidth;
      const overflows = [];
      const allEls = document.querySelectorAll('*');
      for (let el of allEls) {
        const rect = el.getBoundingClientRect();
        if (rect.right > docW + 1) {
          overflows.push({
            tag: el.tagName,
            id: el.id,
            className: (el.className || '').toString().substring(0, 50),
            right: Math.round(rect.right),
            width: Math.round(rect.width),
            docWidth: docW
          });
        }
      }
      return {
        docW,
        scrollW,
        bodyScrollW,
        hasOverflow: scrollW > docW || bodyScrollW > docW,
        overflowElementsCount: overflows.length,
        sampleOverflows: overflows.slice(0, 15)
      };
    })()
  `);
  console.log('横向溢出检测结果:', JSON.stringify(overflowCheck, null, 2));

  console.log('▶ [4/5] 逐个 Tab 切换与移动端截图...');
  const tabs = [
    'tab-backtest',
    'tab-valuation',
    'tab-screener',
    'tab-autopsy',
    'tab-pit',
    'tab-calculator',
    'tab-multiasset',
    'tab-reflex',
    'tab-paper'
  ];

  const tabAuditResults = [];
  for (let tab of tabs) {
    console.log(`  • 切换并检验 Tab: ${tab}...`);
    const tabInfo = await client.eval(`
      (function(tid) {
        switchTab(tid);
        const el = document.getElementById(tid);
        if (!el) return { exists: false };
        const rect = el.getBoundingClientRect();
        const docW = document.documentElement.clientWidth;
        return {
          exists: true,
          width: Math.round(rect.width),
          scrollWidth: el.scrollWidth,
          hasOverflow: el.scrollWidth > docW + 2,
          display: window.getComputedStyle(el).display
        };
      })('${tab}')
    `);
    await sleep(400);
    await client.captureScreenshot(`mobile_${tab}.png`);
    tabAuditResults.push({ tab, tabInfo });
  }

  // 检查移动端底部导航条遮挡情况
  console.log('▶ [5/5] 检测移动端底部导航栏遮挡与触控...');
  const navCheck = await client.eval(`
    (function() {
      const nav = document.querySelector('nav.fixed.bottom-0');
      const body = document.body;
      const bodyPaddingBottom = window.getComputedStyle(body).paddingBottom;
      const navRect = nav ? nav.getBoundingClientRect() : null;
      return {
        hasBottomNav: !!nav,
        navHeight: navRect ? navRect.height : 0,
        bodyPaddingBottom,
        navButtonsCount: nav ? nav.querySelectorAll('button').length : 0,
        navButtonLabels: nav ? Array.from(nav.querySelectorAll('button span:last-child')).map(s => s.innerText) : []
      };
    })()
  `);
  console.log('底部导航栏检查:', JSON.stringify(navCheck, null, 2));

  // 收集控制台错误
  console.log('\n================ 控制台日志与错误 ================');
  console.log('错误数:', client.consoleErrors.length);
  if (client.consoleErrors.length > 0) {
    console.error('Errors:', client.consoleErrors);
  }
  console.log('日志概览 (最近10条):', client.consoleLogs.slice(-10));

  client.close();
  chromeProc.kill('SIGTERM');

  fs.writeFileSync(path.join(ARTIFACTS_DIR, 'audit_report.json'), JSON.stringify({
    overflowCheck,
    tabAuditResults,
    navCheck,
    consoleErrors: client.consoleErrors,
    consoleLogs: client.consoleLogs
  }, null, 2));

  console.log('移动端审计完成！');
}

runMobileAudit().catch(err => {
  console.error('Mobile audit error:', err);
  process.exit(1);
});
