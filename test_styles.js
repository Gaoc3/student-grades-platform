const { chromium } = require('playwright');
const EMAIL = 'ali123zxcvbnalizxcvbnm802@gmail.com';
const PASSWORD = 'farah1ST';

async function run() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ bypassCSP: true, ignoreHTTPSErrors: true });
  const page = await context.newPage();

  const urls = [
    'https://jackson-north-transit-descriptions.trycloudflare.com/login',
    'http://localhost:8000/login'
  ];

  let targetUrl = '';
  for (const url of urls) {
    try {
      const response = await page.goto(url, { timeout: 10000 });
      if (response && response.status() < 500) {
        targetUrl = url;
        break;
      }
    } catch {}
  }

  await page.fill('input[name="email"]', EMAIL);
  await page.fill('input[name="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL('**/dashboard**');

  const isVisible = await page.locator('#semesterSelection').isVisible();
  if (isVisible) {
    await page.click('.gateway-card[data-select-semester="1"]');
    await page.waitForSelector('#dashboardApp', { state: 'visible' });
  }

  // Switch to Arabic
  let currentLang = await page.evaluate(() => document.documentElement.lang);
  if (currentLang !== 'ar') {
    await page.click('#langToggleBtn');
    await page.waitForSelector('html[lang="ar"]');
    const isVisible2 = await page.locator('#semesterSelection').isVisible();
    if (isVisible2) {
      await page.click('.gateway-card[data-select-semester="1"]');
    }
  }

  await page.setViewportSize({ width: 900, height: 768 });
  await page.waitForTimeout(1000);
  await page.click('#notifToggle');
  await page.waitForSelector('#notifDropdown.show', { state: 'visible' });

  const ancestorTracer = await page.evaluate(() => {
    let el = document.getElementById('notifDropdown');
    const path = [];
    while (el && el !== document.body) {
      const computed = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      path.push({
        tagName: el.tagName,
        id: el.id,
        className: el.className,
        position: computed.position,
        left: computed.left,
        right: computed.right,
        width: computed.width,
        rect: {
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height
        }
      });
      el = el.parentElement;
    }
    return path;
  });

  console.log('ANCESTOR TRACE:');
  console.log(JSON.stringify(ancestorTracer, null, 2));

  await browser.close();
}

run();
