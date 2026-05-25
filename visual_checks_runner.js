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
  console.log('Starting custom visual checks script...');

  const browser = await chromium.launch({
    headless: true
  });

  try {
    const context = await browser.newContext({
      viewport: { width: 1280, height: 800 },
      deviceScaleFactor: 2, // High resolution screenshots
      bypassCSP: true,
      ignoreHTTPSErrors: true
    });

    const page = await context.newPage();

    // 1. Determine which URL is responsive
    const urls = [
      'https://jackson-north-transit-descriptions.trycloudflare.com/login',
      'http://localhost:8000/login'
    ];

    let targetUrl = '';
    for (const url of urls) {
      try {
        console.log(`Trying to connect to ${url}...`);
        const response = await page.goto(url, { timeout: 10000, waitUntil: 'load' });
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

    // 2. Perform Login
    console.log('Logging in...');
    await page.fill('input[name="email"]', EMAIL);
    await page.fill('input[name="password"]', PASSWORD);
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await page.waitForURL('**/dashboard**');
    console.log('Successfully redirected to dashboard!');

    // 3. Force a hard reload of the dashboard to clear any browser cache
    console.log('Bypassing cache and forcing hard reload...');
    await page.reload({ waitUntil: 'networkidle' });
    console.log('Hard reload complete.');

    // 4. Handle Semester Gateway Select Overlay if present
    await selectSemesterIfVisible(page);

    // Wait for the main app layout and sidebar to be fully ready
    await page.waitForSelector('#dashboardSidebar', { state: 'visible' });
    await page.waitForTimeout(1000);

    // ==========================================
    // STEP 4: Switch the site language to Arabic (RTL)
    // ==========================================
    console.log('\n--- VERIFYING ARABIC RTL VIEW ---');
    let currentLang = await page.evaluate(() => document.documentElement.lang);
    if (currentLang !== 'ar') {
      console.log('Language is English. Swapping to Arabic...');
      await page.click('#langToggleBtn');
      await page.waitForSelector('html[lang="ar"]');
      await selectSemesterIfVisible(page);
      await page.waitForTimeout(1000);
    }
    console.log('Confirmed language is Arabic (RTL).');

    // Hover over "الطلبة" (Students) button in the sidebar and verify translation
    console.log('Hovering over "الطلبة" (Students) for verification...');
    const studentsBtn = page.locator('button.nav-btn[data-section="students"]');
    
    // Get style before hover
    const styleBefore = await studentsBtn.evaluate(el => {
      const computed = window.getComputedStyle(el);
      const textNode = el.querySelector('span:not(.nav-icon)');
      const textComputed = textNode ? window.getComputedStyle(textNode) : null;
      return {
        outerTransform: computed.transform,
        textTransform: textComputed ? textComputed.transform : 'none'
      };
    });
    console.log('Before Hover Styles (Arabic):', styleBefore);

    // Hover
    await studentsBtn.hover();
    await page.waitForTimeout(400); // let transition settle

    // Get style after hover
    const styleAfter = await studentsBtn.evaluate(el => {
      const computed = window.getComputedStyle(el);
      const textNode = el.querySelector('span:not(.nav-icon)');
      const textComputed = textNode ? window.getComputedStyle(textNode) : null;
      const iconNode = el.querySelector('.nav-icon');
      const iconComputed = iconNode ? window.getComputedStyle(iconNode) : null;
      return {
        outerTransform: computed.transform,
        outerBorderRadius: computed.borderRadius,
        textTransform: textComputed ? textComputed.transform : 'none',
        iconTransform: iconComputed ? iconComputed.transform : 'none',
        outerBoxShadow: computed.boxShadow
      };
    });
    console.log('After Hover Styles (Arabic):', styleAfter);

    // Let's do visual check for clipping of "سجل الدرجات" (Gradebook)
    console.log('Verifying "سجل الدرجات" (Gradebook) corners and clipping...');
    const gradebookBtn = page.locator('button.nav-btn[data-section="gradebook"]');
    const gradebookMetrics = await gradebookBtn.evaluate(el => {
      const computed = window.getComputedStyle(el);
      return {
        borderRadius: computed.borderRadius,
        overflow: computed.overflow,
        boxShadow: computed.boxShadow,
        border: computed.border
      };
    });
    console.log('Gradebook CSS Metrics:', gradebookMetrics);

    // Hover over "الطلبة" (Students) and take high-resolution screenshot clipping_fix_rtl_ar.png
    console.log('Taking screenshot clipping_fix_rtl_ar.png...');
    // We want a high-resolution screenshot of the sidebar itself, or the full screen focusing on the sidebar. Let's capture the full viewport
    const clippingArPath = path.join(WORKSPACE_DIR, 'clipping_fix_rtl_ar.png');
    await page.screenshot({ path: clippingArPath });
    console.log(`Saved screenshot: ${clippingArPath}`);

    // Set browser window viewport to tablet resolution (e.g. 900 x 768)
    console.log('Setting viewport to tablet size (900x768)...');
    await page.setViewportSize({ width: 900, height: 768 });
    await page.waitForTimeout(800);

    // Click the notification bell to open the dropdown
    console.log('Opening notification dropdown in Arabic (RTL)...');
    const notifToggle = page.locator('#notifToggle');
    await notifToggle.click();
    await page.waitForSelector('#notifDropdown.show', { state: 'visible' });
    await page.waitForTimeout(800);

    // Verify notifications window position and fit
    const notifDropdownGeom = await page.locator('#notifDropdown').boundingBox();
    const viewportSize = page.viewportSize();
    console.log('Notification Dropdown Bounding Box (Arabic):', notifDropdownGeom);
    console.log('Viewport Size:', viewportSize);

    // Let's check margin from the screen boundaries (16px margins on both sides)
    const leftMargin = notifDropdownGeom.x;
    const rightMargin = viewportSize.width - (notifDropdownGeom.x + notifDropdownGeom.width);
    console.log(`Arabic Tablet Margins -> Left: ${leftMargin}px, Right: ${rightMargin}px. Width: ${notifDropdownGeom.width}px.`);
    const fitsInViewport = (notifDropdownGeom.x >= 0) && (notifDropdownGeom.x + notifDropdownGeom.width <= viewportSize.width);
    console.log(`Dropdown fits in viewport: ${fitsInViewport}`);

    // Take screenshot of the open notification dropdown in tablet view in Arabic: tablet_notif_ar.png
    const tabletNotifArPath = path.join(WORKSPACE_DIR, 'tablet_notif_ar.png');
    await page.screenshot({ path: tabletNotifArPath });
    console.log(`Saved screenshot: ${tabletNotifArPath}`);

    // Close the notifications dropdown so it doesn't block other elements
    await notifToggle.click();
    await page.waitForSelector('#notifDropdown.show', { state: 'hidden' });

    // Restore desktop viewport before switching language and hovering
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.waitForTimeout(500);

    // ==========================================
    // STEP 5: Switch the site language to English (LTR)
    // ==========================================
    console.log('\n--- VERIFYING ENGLISH LTR VIEW ---');
    console.log('Swapping language to English...');
    await page.click('#langToggleBtn');
    await page.waitForSelector('html[lang="en"]');
    await selectSemesterIfVisible(page);
    await page.waitForTimeout(1000);
    console.log('Confirmed language is English (LTR).');

    // Hover over "Students" button in the sidebar and verify translation
    console.log('Hovering over "Students" (Students) for verification...');
    const studentsBtnEn = page.locator('button.nav-btn[data-section="students"]');
    
    // Get style before hover
    const styleBeforeEn = await studentsBtnEn.evaluate(el => {
      const computed = window.getComputedStyle(el);
      const textNode = el.querySelector('span:not(.nav-icon)');
      const textComputed = textNode ? window.getComputedStyle(textNode) : null;
      return {
        outerTransform: computed.transform,
        textTransform: textComputed ? textComputed.transform : 'none'
      };
    });
    console.log('Before Hover Styles (English):', styleBeforeEn);

    // Hover
    await studentsBtnEn.hover();
    await page.waitForTimeout(400); // let transition settle

    // Get style after hover
    const styleAfterEn = await studentsBtnEn.evaluate(el => {
      const computed = window.getComputedStyle(el);
      const textNode = el.querySelector('span:not(.nav-icon)');
      const textComputed = textNode ? window.getComputedStyle(textNode) : null;
      const iconNode = el.querySelector('.nav-icon');
      const iconComputed = iconNode ? window.getComputedStyle(iconNode) : null;
      return {
        outerTransform: computed.transform,
        outerBorderRadius: computed.borderRadius,
        textTransform: textComputed ? textComputed.transform : 'none',
        iconTransform: iconComputed ? iconComputed.transform : 'none',
        outerBoxShadow: computed.boxShadow
      };
    });
    console.log('After Hover Styles (English):', styleAfterEn);

    // Take English desktop screenshot clipping_fix_ltr_en.png
    console.log('Taking screenshot clipping_fix_ltr_en.png...');
    const clippingEnPath = path.join(WORKSPACE_DIR, 'clipping_fix_ltr_en.png');
    await page.screenshot({ path: clippingEnPath });
    console.log(`Saved screenshot: ${clippingEnPath}`);

    // Set viewport to tablet resolution (900 x 768)
    console.log('Setting viewport to tablet size (900x768) in English...');
    await page.setViewportSize({ width: 900, height: 768 });
    await page.waitForTimeout(800);

    // Click the notification bell to open the dropdown
    console.log('Opening notification dropdown in English (LTR)...');
    const notifToggleEn = page.locator('#notifToggle');
    await notifToggleEn.click();
    await page.waitForSelector('#notifDropdown.show', { state: 'visible' });
    await page.waitForTimeout(800);

    // Verify notifications window position and fit
    const notifDropdownGeomEn = await page.locator('#notifDropdown').boundingBox();
    console.log('Notification Dropdown Bounding Box (English):', notifDropdownGeomEn);

    // Let's check margin from the screen boundaries
    const leftMarginEn = notifDropdownGeomEn.x;
    const rightMarginEn = viewportSize.width - (notifDropdownGeomEn.x + notifDropdownGeomEn.width);
    console.log(`English Tablet Margins -> Left: ${leftMarginEn}px, Right: ${rightMarginEn}px. Width: ${notifDropdownGeomEn.width}px.`);
    const fitsInViewportEn = (notifDropdownGeomEn.x >= 0) && (notifDropdownGeomEn.x + notifDropdownGeomEn.width <= viewportSize.width);
    console.log(`Dropdown fits in viewport: ${fitsInViewportEn}`);

    // Take screenshot of the open dropdown in tablet view in English: tablet_notif_en.png
    const tabletNotifEnPath = path.join(WORKSPACE_DIR, 'tablet_notif_en.png');
    await page.screenshot({ path: tabletNotifEnPath });
    console.log(`Saved screenshot: ${tabletNotifEnPath}`);

    console.log('\nVisual checks execution finished successfully!');

  } catch (err) {
    console.error('An error occurred during verification:', err);
  } finally {
    await browser.close();
  }
}

run();
