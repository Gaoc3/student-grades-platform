/* ========================================
   ArabSeed Home7 — JavaScript
   ======================================== */

/**
 * Update the hamburger button visual state
 */
function AS_UpdateHome7ButtonState(isOpen) {
  var btn = document.getElementById('AS_Home7_Menu_Button');
  if (!btn) return;
  btn.classList.toggle('is-open', !!isOpen);
  btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
}

/**
 * Smart toggle — opens/closes the Mirror Drawer (mobile menu)
 * Falls back to original drawer if present
 */
function AS_SmartToggle(open) {
  var mirrorDrawer  = document.getElementById('AS_Mirror_Drawer');
  var mirrorOverlay = document.getElementById('AS_Mirror_Drawer_Overlay');

  if (mirrorDrawer && mirrorOverlay) {
    var mirrorIsOpen    = mirrorDrawer.classList.contains('active');
    var shouldOpenMirror = (typeof open === 'boolean') ? open : !mirrorIsOpen;

    if (shouldOpenMirror) {
      mirrorDrawer.classList.add('active');
      mirrorOverlay.classList.add('active');
      mirrorDrawer.setAttribute('aria-hidden', 'false');
      mirrorOverlay.setAttribute('aria-hidden', 'false');
      document.documentElement.classList.add('as-mirror-open');
      document.body.classList.add('as-mirror-open');
    } else {
      mirrorDrawer.classList.remove('active');
      mirrorOverlay.classList.remove('active');
      mirrorDrawer.setAttribute('aria-hidden', 'true');
      mirrorOverlay.setAttribute('aria-hidden', 'true');
      document.documentElement.classList.remove('as-mirror-open');
      document.body.classList.remove('as-mirror-open');
    }

    AS_UpdateHome7ButtonState(shouldOpenMirror);
    return false;
  }

  // Fallback for original drawer
  var originalDrawer =
    document.getElementById('AS_Main_Drawer') ||
    document.querySelector('.as-main-drawer') ||
    document.querySelector('.as-main-domain-drawer') ||
    document.querySelector('.mobile__big__menu');

  var originalIsOpen = false;
  if (originalDrawer) {
    originalIsOpen =
      originalDrawer.classList.contains('active') ||
      originalDrawer.classList.contains('open') ||
      originalDrawer.classList.contains('is-open') ||
      document.documentElement.classList.contains('as-drawer-open') ||
      document.body.classList.contains('as-drawer-open');
  }

  var shouldOpenOriginal = (typeof open === 'boolean') ? open : !originalIsOpen;

  if (typeof AS_ToggleMainDrawer === 'function') {
    AS_ToggleMainDrawer(shouldOpenOriginal);
    AS_UpdateHome7ButtonState(shouldOpenOriginal);
    return false;
  }

  if (originalDrawer) {
    originalDrawer.classList.toggle('active', shouldOpenOriginal);
    originalDrawer.classList.toggle('open', shouldOpenOriginal);
    originalDrawer.classList.toggle('is-open', shouldOpenOriginal);
    originalDrawer.setAttribute('aria-hidden', shouldOpenOriginal ? 'false' : 'true');
    document.documentElement.classList.toggle('as-drawer-open', shouldOpenOriginal);
    document.body.classList.toggle('as-drawer-open', shouldOpenOriginal);
    AS_UpdateHome7ButtonState(shouldOpenOriginal);
    return false;
  }

  return false;
}

// Close drawer on Escape key
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    AS_SmartToggle(false);
  }
});
