const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const EMAIL = 'ali123zxcvbnalizxcvbnm802@gmail.com';
const PASSWORD = 'farah1ST';
const WORKSPACE_DIR = __dirname;

async function selectSemesterIfVisible(page) {
  await page.waitForTimeout(1000); // let page load and settle
  const isVisible = await page.locator('#semesterSelection').isVisible();
  if (isVisible) {
    console.log('Semester Selection Gateway detected. Selecting Semester 1...');
    await page.click('.gateway-card[data-select-semester="1"]');
    await page.waitForSelector('#dashboardApp', { state: 'visible' });
    await page.waitForTimeout(800);
  }
}

async function run() {
  console.log('Starting mobile notifications verification script...');

  const browser = await chromium.launch({
    headless: true
  });

  try {
    const context = await browser.newContext({
      viewport: { width: 390, height: 844 },
      deviceScaleFactor: 2, // High resolution screenshots
      bypassCSP: true,
      ignoreHTTPSErrors: true
    });

    const page = await context.newPage();

    // Determine which URL is responsive
    const urls = [
      'https://jackson-north-transit-descriptions.trycloudflare.com/login',
      'http://localhost:8000/login'
    ];

    let targetUrl = '';
    for (const url of urls) {
      try {
        console.log(`Trying to connect to ${url}...`);
        const response = await page.goto(url, { timeout: 15000, waitUntil: 'load' });
        if (response && response.status() < 500) {
          targetUrl = url;
          console.log(`Successfully connected to ${url}`);
          break;
        }
      } catch (err) {
        console.log(`Failed to connect to ${url}: ${err.message}`);
      }
    }

    if (!targetUrl) {
      throw new Error('All target login URLs are unresponsive!');
    }

    // 1. Perform Login
    console.log('Logging in...');
    await page.fill('input[name="email"]', EMAIL);
    await page.fill('input[name="password"]', PASSWORD);
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await page.waitForURL('**/dashboard**');
    console.log('Successfully redirected to dashboard!');

    // 2. Bypass browser cache and force a hard reload of the page
    console.log('Bypassing cache and forcing hard reload...');
    await page.reload({ waitUntil: 'networkidle' });
    console.log('Hard reload complete.');

    // Handle Semester Gateway Select Overlay if present
    await selectSemesterIfVisible(page);

    // Wait for the main app layout or elements to settle
    await page.waitForTimeout(1000);

    // Close mobile sidebar if it starts open
    const isSidebarVisible = await page.locator('#dashboardSidebar').isVisible();
    if (isSidebarVisible) {
      console.log('Sidebar is visible, closing it to avoid overlaps...');
      await page.evaluate(() => {
        document.getElementById('sidebarCloseBtn')?.click() || document.getElementById('sidebarBackdrop')?.click();
      });
      await page.waitForTimeout(600);
    }

    // ==========================================
    // STEP 4: Switch the site language to Arabic (RTL)
    // ==========================================
    console.log('\n--- VERIFYING ARABIC RTL VIEW (MOBILE) ---');
    let currentLang = await page.evaluate(() => document.documentElement.lang);
    if (currentLang !== 'ar') {
      console.log('Language is English. Swapping to Arabic...');
      await page.click('#langToggleBtn');
      await page.waitForSelector('html[lang="ar"]');
      await selectSemesterIfVisible(page);
      await page.waitForTimeout(1000);
    }
    console.log('Confirmed language is Arabic (RTL).');

    // Make sure sidebar is closed
    await page.evaluate(() => {
      document.getElementById('sidebarCloseBtn')?.click() || document.getElementById('sidebarBackdrop')?.click();
    });
    await page.waitForTimeout(600);

    // Open notifications
    console.log('Opening notification dropdown in Arabic (RTL)...');
    const notifToggle = page.locator('#notifToggle');
    await notifToggle.click();
    await page.waitForSelector('#notifDropdown.show', { state: 'visible' });
    await page.waitForTimeout(800);

    // Check geometries
    let dropdownGeom = await page.locator('#notifDropdown').boundingBox();
    let viewportSize = page.viewportSize();
    console.log('Notification Dropdown Bounding Box (Arabic Mobile):', dropdownGeom);
    console.log('Viewport Size:', viewportSize);

    if (dropdownGeom) {
      const leftMargin = dropdownGeom.x;
      const rightMargin = viewportSize.width - (dropdownGeom.x + dropdownGeom.width);
      console.log(`Arabic Mobile Margins -> Left: ${leftMargin.toFixed(2)}px, Right: ${rightMargin.toFixed(2)}px. Width: ${dropdownGeom.width.toFixed(2)}px.`);
      
      const fitsInViewport = (dropdownGeom.x >= 0) && (dropdownGeom.x + dropdownGeom.width <= viewportSize.width);
      console.log(`Dropdown fits in viewport: ${fitsInViewport}`);
    } else {
      console.log('Could not retrieve bounding box for #notifDropdown in Arabic!');
    }

    // Capture high-resolution mobile screenshot of the open dropdown in Arabic
    const arMobileNotifPath = path.join(WORKSPACE_DIR, 'mobile_notif_ar_fixed.png');
    await page.screenshot({ path: arMobileNotifPath });
    console.log(`Saved Arabic mobile screenshot to: ${arMobileNotifPath}`);

    // Close notification dropdown
    await notifToggle.click();
    await page.waitForSelector('#notifDropdown.show', { state: 'hidden' });
    await page.waitForTimeout(500);

    // ==========================================
    // STEP 8: Switch the site language to English (LTR)
    // ==========================================
    console.log('\n--- VERIFYING ENGLISH LTR VIEW (MOBILE) ---');
    console.log('Swapping language to English...');
    await page.click('#langToggleBtn');
    await page.waitForSelector('html[lang="en"]');
    await selectSemesterIfVisible(page);
    await page.waitForTimeout(1000);
    console.log('Confirmed language is English (LTR).');

    // Make sure sidebar is closed
    await page.evaluate(() => {
      document.getElementById('sidebarCloseBtn')?.click() || document.getElementById('sidebarBackdrop')?.click();
    });
    await page.waitForTimeout(600);

    // Open notifications
    console.log('Opening notification dropdown in English (LTR)...');
    const notifToggleEn = page.locator('#notifToggle');
    await notifToggleEn.click();
    await page.waitForSelector('#notifDropdown.show', { state: 'visible' });
    await page.waitForTimeout(800);

    // Check geometries
    dropdownGeom = await page.locator('#notifDropdown').boundingBox();
    console.log('Notification Dropdown Bounding Box (English Mobile):', dropdownGeom);

    if (dropdownGeom) {
      const leftMargin = dropdownGeom.x;
      const rightMargin = viewportSize.width - (dropdownGeom.x + dropdownGeom.width);
      console.log(`English Mobile Margins -> Left: ${leftMargin.toFixed(2)}px, Right: ${rightMargin.toFixed(2)}px. Width: ${dropdownGeom.width.toFixed(2)}px.`);
      
      const fitsInViewport = (dropdownGeom.x >= 0) && (dropdownGeom.x + dropdownGeom.width <= viewportSize.width);
      console.log(`Dropdown fits in viewport: ${fitsInViewport}`);
    } else {
      console.log('Could not retrieve bounding box for #notifDropdown in English!');
    }

    // Capture mobile screenshot of the open dropdown in English
    const enMobileNotifPath = path.join(WORKSPACE_DIR, 'mobile_notif_en_fixed.png');
    await page.screenshot({ path: enMobileNotifPath });
    console.log(`Saved English mobile screenshot to: ${enMobileNotifPath}`);

    console.log('\nMobile verification script completed successfully!');

  } catch (err) {
    console.error('An error occurred during mobile verification:', err);
  } finally {
    await browser.close();
  }
}

run();
