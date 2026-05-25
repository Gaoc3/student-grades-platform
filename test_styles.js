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

  const traceDetails = await page.evaluate(() => {
    const wrapper = document.querySelector('.notification-wrapper');
    const actions = document.querySelector('.topbar-actions');
    const dropdown = document.getElementById('notifDropdown');
    return {
      wrapper: {
        tagName: wrapper.tagName,
        position: window.getComputedStyle(wrapper).position,
        transform: window.getComputedStyle(wrapper).transform,
        filter: window.getComputedStyle(wrapper).filter,
        backdropFilter: window.getComputedStyle(wrapper).backdropFilter,
        webkitBackdropFilter: window.getComputedStyle(wrapper).webkitBackdropFilter,
        willChange: window.getComputedStyle(wrapper).willChange
      },
      actions: {
        tagName: actions.tagName,
        position: window.getComputedStyle(actions).position,
        transform: window.getComputedStyle(actions).transform,
        filter: window.getComputedStyle(actions).filter,
        backdropFilter: window.getComputedStyle(actions).backdropFilter,
        webkitBackdropFilter: window.getComputedStyle(actions).webkitBackdropFilter,
        willChange: window.getComputedStyle(actions).willChange
      },
      dropdown: {
        tagName: dropdown.tagName,
        position: window.getComputedStyle(dropdown).position,
        left: window.getComputedStyle(dropdown).left,
        right: window.getComputedStyle(dropdown).right,
        width: window.getComputedStyle(dropdown).width
      }
    };
  });

  console.log('TRACE DETAILS:');
  console.log(JSON.stringify(traceDetails, null, 2));

  await browser.close();
}

run();
