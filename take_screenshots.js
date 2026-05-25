const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const EMAIL = 'ali123zxcvbnalizxcvbnm802@gmail.com';
const PASSWORD = 'farah1ST';

const WORKSPACE_DIR = __dirname;

async function selectSemesterIfVisible(page) {
  await page.waitForTimeout(800); // let page load and settle
  const isVisible = await page.locator('#semesterSelection').isVisible();
  if (isVisible) {
    console.log('Semester Selection Gateway detected. Selecting Semester 1...');
    await page.click('.gateway-card[data-select-semester="1"]');
    await page.waitForSelector('#dashboardApp', { state: 'visible' });
    await page.waitForTimeout(500);
  }
}

async function run() {
  console.log('Starting visual validation automation...');

  const browser = await chromium.launch({
    headless: true
  });

  try {
    const context = await browser.newContext({
      viewport: { width: 1280, height: 800 },
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

    // 3. Bypass browser cache and force a hard reload
    console.log('Bypassing cache and forcing hard reload...');
    await page.reload({ waitUntil: 'networkidle' });
    console.log('Hard reload complete.');

    // 4. Handle Semester Gateway Select Overlay if present
    await selectSemesterIfVisible(page);

    // Wait for the main app layout and sidebar to be fully ready
    await page.waitForSelector('#dashboardSidebar', { state: 'visible' });
    await page.waitForTimeout(1000); // Wait for transition animations to settle

    // ==========================================
    // VERIFICATION 1: Arabic RTL View (Desktop)
    // ==========================================
    console.log('\n--- VERIFYING ARABIC RTL VIEW (DESKTOP) ---');

    // Switch language to Arabic if it is in English
    let currentLang = await page.evaluate(() => document.documentElement.lang);
    if (currentLang !== 'ar') {
      console.log('Language is English. Swapping to Arabic...');
      await page.click('#langToggleBtn');
      await page.waitForSelector('html[lang="ar"]');
      await selectSemesterIfVisible(page);
      await page.waitForTimeout(1000);
    }
    console.log('Confirmed language is Arabic (RTL).');

    // A. Check that the layout is clean, compact, and Snaps to the RIGHT side
    const bodyWidth = await page.evaluate(() => document.body.clientWidth);
    let sidebarBox = await page.locator('#dashboardSidebar').boundingBox();
    console.log(`Body Width: ${bodyWidth}px. Sidebar Position: x=${sidebarBox.x}px, width=${sidebarBox.width}px.`);
    let isRightSnapped = (sidebarBox.x + sidebarBox.width / 2) > (bodyWidth / 2);
    console.log(`Is Sidebar Snapped to Right? ${isRightSnapped} (Expected: true)`);

    // B. Verify layout lines/dividers symmetry (exactly 16px gap on both sides of each line)
    const lineMetrics = await page.evaluate(() => {
      const line = document.querySelector('.sidebar-nav .line');
      if (!line) return null;
      const computed = window.getComputedStyle(line);
      return {
        marginTop: computed.marginTop,
        marginBottom: computed.marginBottom,
        marginLeft: computed.marginLeft,
        marginRight: computed.marginRight,
        height: computed.height
      };
    });
    console.log('Sidebar Navigation Divider (.line) Spacing:', lineMetrics);

    // C. Hover over "الطلبة" (Students) and check translate-x and color glow
    console.log('Hovering over "الطلبة" (Students)...');
    const studentsBtn = page.locator('button.nav-btn[data-section="students"]');
    await studentsBtn.hover();
    await page.waitForTimeout(300); // Wait for transition
    const studentsHoverStyle = await page.evaluate(() => {
      const el = document.querySelector('button.nav-btn[data-section="students"]');
      const style = window.getComputedStyle(el);
      const icon = el.querySelector('.nav-icon');
      const iconStyle = icon ? window.getComputedStyle(icon) : {};
      return {
        transform: style.transform,
        color: style.color,
        boxShadow: style.boxShadow,
        iconBg: iconStyle.backgroundColor,
        iconColor: iconStyle.color
      };
    });
    console.log('Students Hover CSS details:', studentsHoverStyle);

    // D. Hover over Logout button and check hover effects
    console.log('Hovering over Logout button...');
    const logoutBtn = page.locator('#sidebarLogoutBtn');
    await logoutBtn.hover();
    await page.waitForTimeout(300); // Wait for transition
    const logoutHoverStyle = await page.evaluate(() => {
      const el = document.getElementById('sidebarLogoutBtn');
      const style = window.getComputedStyle(el);
      return {
        transform: style.transform,
        color: style.color,
        boxShadow: style.boxShadow,
        border: style.border
      };
    });
    console.log('Logout Hover CSS details:', logoutHoverStyle);

    // Take Arabic desktop screenshot showing the open sidebar while hovering over Logout
    const arDesktopScreenshotPath = path.join(WORKSPACE_DIR, 'sidebar_polish_rtl_ar.png');
    await page.screenshot({ path: arDesktopScreenshotPath });
    console.log(`Arabic Desktop Sidebar Screenshot saved to: ${arDesktopScreenshotPath}`);

    // ==========================================
    // VERIFICATION 2: English LTR View (Desktop)
    // ==========================================
    console.log('\n--- VERIFYING ENGLISH LTR VIEW (DESKTOP) ---');

    // Switch language to English
    console.log('Swapping language to English (LTR)...');
    await page.click('#langToggleBtn');
    await page.waitForSelector('html[lang="en"]');
    await selectSemesterIfVisible(page);
    await page.waitForTimeout(1000);
    console.log('Confirmed language is English (LTR).');

    // A. Check that the sidebar snaps close to the LEFT edge of the viewport
    const sidebarBoxEn = await page.locator('#dashboardSidebar').boundingBox();
    console.log(`Sidebar Position: x=${sidebarBoxEn.x}px, width=${sidebarBoxEn.width}px.`);
    const isLeftSnapped = (sidebarBoxEn.x + sidebarBoxEn.width / 2) < (bodyWidth / 2);
    console.log(`Is Sidebar Snapped to Left? ${isLeftSnapped} (Expected: true)`);

    // B. Hover over "Students" or "Grading" and verify slide right and glow
    console.log('Hovering over "Grading"...');
    const gradingBtn = page.locator('button.nav-btn[data-section="grading"]');
    await gradingBtn.hover();
    await page.waitForTimeout(300); // Wait for transition
    const gradingHoverStyle = await page.evaluate(() => {
      const el = document.querySelector('button.nav-btn[data-section="grading"]');
      const style = window.getComputedStyle(el);
      return {
        transform: style.transform,
        color: style.color,
        boxShadow: style.boxShadow
      };
    });
    console.log('Grading Hover CSS details:', gradingHoverStyle);

    // Take English desktop screenshot showing the open sidebar while hovering over Grading
    const enDesktopScreenshotPath = path.join(WORKSPACE_DIR, 'sidebar_polish_ltr_en.png');
    await page.screenshot({ path: enDesktopScreenshotPath });
    console.log(`English Desktop Sidebar Screenshot saved to: ${enDesktopScreenshotPath}`);

    // ==========================================
    // VERIFICATION 3: Mobile Viewports (iPhone 12/13 Width)
    // ==========================================
    console.log('\n--- VERIFYING MOBILE VIEWPORTS ---');

    // A. Mobile English View
    console.log('Setting viewport to mobile width (390px)...');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(500);

    // Ensure we are in English
    let mobLang = await page.evaluate(() => document.documentElement.lang);
    if (mobLang !== 'en') {
      console.log('Swapping to English for mobile view...');
      await page.click('#langToggleBtn');
      await page.waitForSelector('html[lang="en"]');
      await selectSemesterIfVisible(page);
      await page.waitForTimeout(500);
    }

    // Mobile sidebar is collapsed by default. Open it.
    console.log('Opening mobile English sidebar...');
    await page.click('#sidebarToggleBtn');
    await page.waitForSelector('#dashboardSidebar', { state: 'visible' });
    await page.waitForTimeout(500);

    const enMobileScreenshotPath = path.join(WORKSPACE_DIR, 'sidebar_polish_mobile_en.png');
    await page.screenshot({ path: enMobileScreenshotPath });
    console.log(`English Mobile Sidebar Screenshot saved to: ${enMobileScreenshotPath}`);

    // B. Mobile Arabic View
    console.log('Swapping language to Arabic for mobile view...');
    
    // Close sidebar on mobile securely using evaluate click
    await page.evaluate(() => {
      document.getElementById('sidebarCloseBtn')?.click() || document.getElementById('sidebarBackdrop')?.click();
    });
    await page.waitForTimeout(600);
    
    // Toggle language
    await page.click('#langToggleBtn');
    await page.waitForSelector('html[lang="ar"]');
    await selectSemesterIfVisible(page);
    await page.waitForTimeout(800);

    // Open mobile Arabic sidebar
    console.log('Opening mobile Arabic sidebar...');
    await page.click('#sidebarToggleBtn');
    await page.waitForSelector('#dashboardSidebar', { state: 'visible' });
    await page.waitForTimeout(500);

    const arMobileScreenshotPath = path.join(WORKSPACE_DIR, 'sidebar_polish_mobile_ar.png');
    await page.screenshot({ path: arMobileScreenshotPath });
    console.log(`Arabic Mobile Sidebar Screenshot saved to: ${arMobileScreenshotPath}`);

    console.log('\nAll visual validation operations completed successfully!');

  } catch (err) {
    console.error('An error occurred during automation:', err);
  } finally {
    await browser.close();
  }
}

run();
