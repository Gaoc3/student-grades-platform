const { chromium } = require('playwright');
const path = require('path');

const EMAIL = 'ali123zxcvbnalizxcvbnm802@gmail.com';
const PASSWORD = 'farah1ST';

async function run() {
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({
      viewport: { width: 390, height: 844 },
      bypassCSP: true,
      ignoreHTTPSErrors: true
    });
    const page = await context.newPage();
    await page.goto('https://jackson-north-transit-descriptions.trycloudflare.com/login');
    await page.fill('input[name="email"]', EMAIL);
    await page.fill('input[name="password"]', PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard**');
    await page.waitForTimeout(1500);

    // Let's close sidebar if open
    await page.evaluate(() => {
      document.getElementById('sidebarCloseBtn')?.click() || document.getElementById('sidebarBackdrop')?.click();
    });
    await page.waitForTimeout(600);

    // Switch to Arabic
    let currentLang = await page.evaluate(() => document.documentElement.lang);
    if (currentLang !== 'ar') {
      await page.click('#langToggleBtn');
      await page.waitForSelector('html[lang="ar"]');
      await page.waitForTimeout(1000);
    }

    // Open notifications
    await page.click('#notifToggle');
    await page.waitForSelector('#notifDropdown.show', { state: 'visible' });
    await page.waitForTimeout(500);

    // Evaluate layout
    const info = await page.evaluate(() => {
      const topbar = document.querySelector('.topbar');
      const wrapper = document.querySelector('.notification-wrapper');
      const dropdown = document.querySelector('#notifDropdown');
      
      const topbarRect = topbar.getBoundingClientRect();
      const wrapperRect = wrapper.getBoundingClientRect();
      const dropdownRect = dropdown.getBoundingClientRect();
      
      const topbarStyle = window.getComputedStyle(topbar);
      const wrapperStyle = window.getComputedStyle(wrapper);
      const dropdownStyle = window.getComputedStyle(dropdown);
      
      return {
        viewportWidth: window.innerWidth,
        topbar: {
          x: topbarRect.x,
          width: topbarRect.width,
          position: topbarStyle.position,
          paddingLeft: topbarStyle.paddingLeft,
          paddingRight: topbarStyle.paddingRight,
          marginLeft: topbarStyle.marginLeft,
          marginRight: topbarStyle.marginRight
        },
        wrapper: {
          x: wrapperRect.x,
          width: wrapperRect.width,
          position: wrapperStyle.position
        },
        dropdown: {
          x: dropdownRect.x,
          width: dropdownRect.width,
          left: dropdownStyle.left,
          right: dropdownStyle.right,
          position: dropdownStyle.position
        }
      };
    });

    console.log('Mobile Layout Telemetry:', JSON.stringify(info, null, 2));

  } catch (err) {
    console.error(err);
  } finally {
    await browser.close();
  }
}
run();
