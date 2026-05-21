const msg = document.getElementById('msg');
const gradeTable = document.getElementById('gradeTable');
let notificationsList = [];
let lastSeenNotifId = parseInt(localStorage.getItem('last_seen_notif_id') || '0', 10);
const publishComponents = document.getElementById('publishComponents');
const publishResult = document.getElementById('publishResult');

const langToggleBtn = document.getElementById('langToggleBtn');
const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
const sidebarBackdrop = document.getElementById('sidebarBackdrop');
const dashboardSidebar = document.getElementById('dashboardSidebar');

const importFileInput = document.getElementById('importFileInput');
const importFileName = document.getElementById('importFileName');
const studentsQuickList = document.getElementById('studentsQuickList');
const dashboardPanes = [...document.querySelectorAll('.dashboard-pane')];
const sectionNavButtons = [...document.querySelectorAll('[data-section]')];

const addComponentForm = document.getElementById('addComponentForm');
const cancelAddCompBtn = document.getElementById('cancelAddComp');

const semesterSelection = document.getElementById('semesterSelection');
const dashboardApp = document.getElementById('dashboardApp');
const switchSemesterBtn = document.getElementById('switchSemesterBtn');

const I18N = {
  ar: {
    toggleTheme: 'الوضع',
    logout: 'تسجيل خروج',
    language: 'تغيير اللغة',
    openMenu: 'فتح القائمة',
    closeMenu: 'إغلاق القائمة',
    switchToArabic: 'التبديل إلى العربية',
    switchToEnglish: 'Switch to English',
    studentsCount: 'عدد الطلبة',
    componentsCount: 'عدد عناصر التقييم',
    courseworkTotal: 'إجمالي الدرجة (من)',
    courseworkEditHint: 'حرّر الرقم مباشرة ثم اضغط Enter للحفظ.',
    saveTotal: 'حفظ',
    studentsManagement: 'إدارة الطلبة',
    addStudent: 'إضافة طالب',
    quickImport: 'استيراد سريع (name:email)',
    chooseFile: 'اختيار الملف',
    noFileSelected: 'لم يتم اختيار ملف بعد',
    uploadFile: 'رفع الملف',
    assessmentSetup: 'تهيئة عناصر التقييم',
    publishGrades: 'نشر الدرجات عبر QR',
    selectComponentsPublish: 'حدد عناصر التقييم المراد نشرها',
    sendQrByEmail: 'إرسال QR إلى البريد الإلكتروني للطلبة',
    forceNewQr: 'إنشاء QR جديد حتى لو لم يُفتح الرابط السابق',
    publishNow: 'نشر الآن',
    publishSettings: 'إعدادات وخيارات النشر',
    gradebook: 'سجل الدرجات',
    notifications: 'الإشعارات',
    clearOldNotifications: 'تنظيف الإشعارات القديمة',
    notifTitle: 'الإشعارات',
    notifClearAll: 'مسح الكل<i class="ri-delete-bin-6-line" style="vertical-align: middle; margin-inline-start: 6px;"></i>',
    notifStudentOpened: 'طالب فتح الرابط: {msg}',
    notifAllCleared: 'تم مسح جميع الإشعارات',
    notifDelete: 'حذف',
    notifDeleteLabel: 'حذف الإشعار',
    confirmLogout: 'تأكيد الخروج',
    confirmLogoutMsg: 'هل أنت متأكد من رغبتك في تسجيل الخروج؟ ستفقد أي تغييرات غير محفوظة.',
    confirmDelete: 'حذف الطالب',
    confirmDeleteMsg: 'هل أنت متأكد من حذف هذا الطالب نهائياً؟ لا يمكن التراجع عن هذا الإجراء.',
    actionConfirm: 'تأكيد',
    actionCancel: 'إلغاء',
    switchSemester: 'تبديل الكورس',

    dashboardSections: 'أقسام الداشبورد',
    dashboardSectionsHint: 'تنقّل سريع بين كل الأجزاء',
    navOverview: 'نظرة عامة',
    navStudents: 'الطلبة',
    navGrading: 'التقييم',
    navPublish: 'النشر',
    navGradebook: 'سجل الدرجات',
    navNotifications: 'الإشعارات',
    navOverviewTip: 'ملخص عام سريع',
    navStudentsTip: 'إدارة بيانات الطلبة',
    navGradingTip: 'إعداد عناصر الدرجات',
    navPublishTip: 'نشر النتائج والـQR',
    navGradebookTip: 'متابعة سجل الدرجات',
    navNotificationsTip: 'إشعارات فتح الروابط',
    quickStudentsList: 'قائمة الطلبة السريعة',

    badgeStudents: 'شؤون الطلبة',
    badgeGradingSetup: 'ضبط التقييم',
    badgePublishing: 'النشر',
    badgeGradebook: 'السجل الأكاديمي',

    studentNamePlaceholder: 'اسم الطالب',
    studentEmailPlaceholder: 'البريد الإلكتروني (اختياري)',
    searchStudentPlaceholder: 'بحث سريع باسم الطالب',

    heroTitle: 'لوحة متابعة المقرر: {subject}',
    heroSubtitle: 'مرحبًا دكتور {doctor} — إدارة الدرجات ونشر النتائج من واجهة موحدة',

    statusReady: 'النظام جاهز.',
    statusStudentAdded: 'تمت إضافة الطالب بنجاح.',
    statusImportDone: 'تم الاستيراد: جديد {created} | تحديث {updated} | متجاوز {skipped}',
    statusChooseFileFirst: 'يرجى اختيار ملف أولاً.',
    statusComponentUpdated: 'تم تحديث العنصر بنجاح.',
    statusComponentAdded: 'تمت إضافة العنصر بنجاح.',
    statusComponentDeleted: 'تم حذف العنصر بنجاح.',
    statusScoresSaved: 'تم حفظ درجات الطالب بنجاح.',
    statusStudentDeleted: 'تم حذف الطالب بنجاح.',
    statusPublished: 'تم نشر الدرجات بنجاح.',
    statusNotifCleaned: 'تم تنظيف الإشعارات القديمة.',

    notifEmpty: 'لا توجد إشعارات.',
    tableStudent: 'الطالب',
    tableEmail: 'البريد الإلكتروني',
    tableActions: 'الإجراءات',
    actionSave: 'حفظ',
    actionDelete: 'حذف',
    badgePublished: 'منشور',
    confirmDelete: 'هل أنت متأكد من حذف الطالب؟',
    confirmDeleteComp: 'هل أنت متأكد من حذف هذا العنصر؟ سيتم حذف درجات الطلبة المرتبطة به أيضاً!',

    course1: 'الكورس الأول',
    course2: 'الكورس الثاني',
    courseworkTitle: 'السعي',
    courseworkSectionTitle: 'السعي',
    finalTitle: 'الفاينل',
    finalSectionTitle: 'الفاينل',
    newComponent: 'عنصر جديد',
    compName: 'اسم العنصر',
    compMaxScore: 'الدرجة العظمى',
    save: 'حفظ',
    cancel: 'إلغاء',
    addComponent: '+ إضافة عنصر تقييم',
    selectCourseGateway: 'يرجى اختيار الكورس الدراسي',
    selectCourseGatewayDesc: 'كل كورس يعمل كبوابة مستقلة ببياناته ودرجاته الخاصة',
    course1Desc: 'الدخول إلى بوابة درجات الكورس الأول',
    course2Desc: 'الدخول إلى بوابة درجات الكورس الثاني',
    switchSemester: 'تبديل الكورس',
    publishTargetLabel: 'الجمهور المستهدف للنشر',
    publishModeAll: 'إذاعة لجميع الطلبة',
    publishModeManual: 'تحديد يدوي',
  },
  en: {
    toggleTheme: 'Theme',
    logout: 'Logout',
    language: 'Switch language',
    openMenu: 'Open menu',
    closeMenu: 'Close menu',
    switchToArabic: 'Switch to Arabic',
    switchToEnglish: 'Switch to English',
    studentsCount: 'Students',
    componentsCount: 'Components',
    courseworkTotal: 'Coursework Total (out of)',
    courseworkEditHint: 'Edit number directly and press Enter to save.',
    saveTotal: 'Save',
    studentsManagement: 'Student Management',
    addStudent: 'Add Student',
    quickImport: 'Quick Import (name:email)',
    chooseFile: 'Choose File',
    noFileSelected: 'No file selected',
    uploadFile: 'Upload File',
    assessmentSetup: 'Assessment Setup',
    publishGrades: 'Publish Grades via QR',
    selectComponentsPublish: 'Select components to publish',
    sendQrByEmail: 'Send QR to student emails',
    forceNewQr: 'Create a new QR even if previous link was not opened',
    publishNow: 'Publish Now',
    publishSettings: 'Publish Settings & Options',
    gradebook: 'Gradebook',
    notifications: 'Notifications',
    clearOldNotifications: 'Clear old notifications',
    notifTitle: 'Notifications',
    notifClearAll: 'Clear All<i class="ri-delete-bin-6-line" style="vertical-align: middle; margin-inline-start: 6px;"></i>',
    notifStudentOpened: 'Student opened link: {msg}',
    notifAllCleared: 'All notifications cleared.',
    notifDelete: 'Delete',
    notifDeleteLabel: 'Delete Notification',
    confirmLogout: 'Confirm Logout',
    confirmLogoutMsg: 'Are you sure you want to logout? Any unsaved changes will be lost.',
    confirmDelete: 'Delete Student',
    confirmDeleteMsg: 'Are you sure you want to delete this student permanently? This action cannot be undone.',
    actionConfirm: 'Confirm',
    actionCancel: 'Cancel',
    switchSemester: 'Switch Semester',

    dashboardSections: 'Dashboard Sections',
    dashboardSectionsHint: 'Quick navigation across all sections',
    navOverview: 'Overview',
    navStudents: 'Students',
    navGrading: 'Grading',
    navPublish: 'Publishing',
    navGradebook: 'Gradebook',
    navNotifications: 'Notifications',
    navOverviewTip: 'Quick course snapshot',
    navStudentsTip: 'Manage student records',
    navGradingTip: 'Configure grade components',
    navPublishTip: 'Publish results and QR links',
    navGradebookTip: 'Track all student grades',
    navNotificationsTip: 'View opening alerts',
    quickStudentsList: 'Quick Students List',

    badgeStudents: 'Students Affairs',
    badgeGradingSetup: 'Assessment Setup',
    badgePublishing: 'Publishing',
    badgeGradebook: 'Academic Gradebook',

    studentNamePlaceholder: 'Student name',
    studentEmailPlaceholder: 'Email (optional)',
    searchStudentPlaceholder: 'Search by student name',

    heroTitle: 'Course Monitoring Dashboard: {subject}',
    heroSubtitle: 'Welcome, Dr. {doctor} — Manage grading and results publishing through one unified interface',

    statusReady: 'System is ready.',
    statusStudentAdded: 'Student added successfully.',
    statusImportDone: 'Import complete: created {created} | updated {updated} | skipped {skipped}',
    statusChooseFileFirst: 'Please choose a file first.',
    statusComponentUpdated: 'Component updated successfully.',
    statusComponentAdded: 'Component added successfully.',
    statusComponentDeleted: 'Component deleted successfully.',
    statusScoresSaved: 'Student scores saved successfully.',
    statusStudentDeleted: 'Student deleted successfully.',
    statusPublished: 'Grades published successfully.',
    statusNotifCleaned: 'Old notifications were cleared.',

    notifEmpty: 'No notifications available.',
    tableStudent: 'Student',
    tableEmail: 'Email',
    tableActions: 'Actions',
    actionSave: 'Save',
    actionDelete: 'Delete',
    badgePublished: 'Published',
    confirmDelete: 'Are you sure you want to delete this student?',
    confirmDeleteComp: 'Are you sure you want to delete this component? All associated student scores will also be deleted!',

    course1: 'Semester 1',
    course2: 'Semester 2',
    courseworkTitle: 'Coursework',
    courseworkSectionTitle: 'Coursework',
    finalTitle: 'Final Exam',
    finalSectionTitle: 'Final Exam',
    newComponent: 'New Component',
    compName: 'Component Name',
    compMaxScore: 'Max Score',
    save: 'Save',
    cancel: 'Cancel',
    addComponent: '+ Add Component',
    selectCourseGateway: 'Please select a course',
    selectCourseGatewayDesc: 'Each course acts as an independent gate with its own data',
    course1Desc: 'Enter Semester 1 gate',
    course2Desc: 'Enter Semester 2 gate',
    switchSemester: 'Switch Course',
    publishTargetLabel: 'Target Audience',
    publishModeAll: 'Broadcast to all students',
    publishModeManual: 'Manual Selection',
  },
};

let state = {
  components: [],
  rows: [],
  fullRows: [],
  lang: 'ar',
  activeSemester: null
};

function getTranslatedLabel(label) {
  if (state.lang !== 'ar') return label;
  const map = {
    'Midterm': 'ميدتيرم',
    'Midterm (Theory)': 'ميدتيرم (نظري)',
    'Midterm (Practical)': 'ميدتيرم (عملي)',
    'Quizzes': 'كويزات',
    'Quiz 1': 'كويز 1',
    'Attendance': 'الحضور',
    'Assignment': 'واجبات',
    'Report': 'التقرير',
    'Final (Theory)': 'الفاينل (نظري)',
    'Final (Practical)': 'الفاينل (عملي)'
  };
  return map[label] || label;
}

function t(key, vars = {}) {
  const pack = I18N[state.lang] || I18N.ar;
  let text = pack[key] || I18N.ar[key] || key;
  for (const [k, v] of Object.entries(vars)) {
    text = text.replaceAll(`{${k}}`, String(v));
  }
  return text;
}

function setStatus(text = '', type = 'info') {
  msg.textContent = text;
  msg.dataset.type = type;
}

async function api(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    credentials: 'same-origin',
  });

  if (res.status === 401) {
    window.location.href = '/login';
    return null;
  }

  const payload = await res.json();
  if (!res.ok) throw new Error(payload.detail || 'Request failed');
  return payload;
}

/**
 * Custom Professional Confirmation Modal
 * @param {string} title - Modal heading
 * @param {string} message - Modal body text
 * @returns {Promise<boolean>}
 */
function showConfirm(title, message) {
  return new Promise((resolve) => {
    const modal = document.getElementById('customModal');
    const titleEl = document.getElementById('modalTitle');
    const msgEl = document.getElementById('modalMessage');
    const confirmBtn = document.getElementById('modalConfirmBtn');
    const cancelBtn = document.getElementById('modalCancelBtn');

    titleEl.textContent = title;
    msgEl.textContent = message;

    confirmBtn.textContent = t('actionConfirm') || 'تأكيد';
    cancelBtn.textContent = t('actionCancel') || 'إلغاء';

    modal.style.display = 'flex';

    const cleanup = (result) => {
      modal.style.display = 'none';
      confirmBtn.replaceWith(confirmBtn.cloneNode(true));
      cancelBtn.replaceWith(cancelBtn.cloneNode(true));
      resolve(result);
    };

    document.getElementById('modalConfirmBtn').addEventListener('click', () => cleanup(true));
    document.getElementById('modalCancelBtn').addEventListener('click', () => cleanup(false));

    // Also close on background click
    modal.onclick = (e) => {
      if (e.target === modal) cleanup(false);
    };
  });
}

function applyStaticTranslations() {
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    const key = el.dataset.i18n;
    const value = t(key);
    if (value && (value.includes('<') || value.includes('>'))) {
      el.innerHTML = value;
    } else {
      el.textContent = value;
    }
  });

  document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
    const key = el.dataset.i18nPlaceholder;
    el.placeholder = t(key);
  });

  document.querySelectorAll('[data-i18n-tooltip]').forEach((el) => {
    const key = el.dataset.i18nTooltip;
    const tip = t(key);
    el.title = tip;
    el.setAttribute('aria-label', tip);
  });
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.style.cssText = `
    position: fixed; top: 20px; left: 50%; transform: translateX(-50%) translateY(-20px);
    background: var(--card-strong); border: 1px solid var(--line); color: var(--text);
    padding: 12px 24px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    z-index: 9999; font-weight: 700; font-size: 14px; opacity: 0; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex; align-items: center; gap: 8px; backdrop-filter: blur(12px);
  `;

  let icon = '<i class="ri-information-line"></i>';
  if (type === 'success') icon = '<i class="ri-checkbox-circle-fill" style="color: var(--ok);"></i>';
  else if (type === 'error') icon = '<i class="ri-close-circle-fill" style="color: var(--danger);"></i>';

  toast.innerHTML = `${icon} <span style="flex:1">${message}</span>
    <button onclick="this.parentElement.style.opacity='0';this.parentElement.style.transform='translateX(-50%) translateY(-20px)';setTimeout(()=>this.parentElement.remove(),300)" 
      style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:18px;padding:0 0 0 8px;line-height:1;font-weight:700;transition:color 0.2s;"
      onmouseenter="this.style.color='var(--text)'" onmouseleave="this.style.color='var(--muted)'"
      aria-label="إغلاق">✕</button>`;

  document.body.appendChild(toast);

  requestAnimationFrame(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateX(-50%) translateY(0)';
  });

  const autoClose = setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(-50%) translateY(-20px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);

  // Pause auto-close on hover
  toast.addEventListener('mouseenter', () => clearTimeout(autoClose));
  toast.addEventListener('mouseleave', () => {
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(-50%) translateY(-20px)';
      setTimeout(() => toast.remove(), 300);
    }, 1500);
  });
}

function renderNotifications() {
  const badge = document.getElementById('notifBadge');
  const listEl = document.getElementById('notifList');

  if (!badge || !listEl) return;

  const unreadCount = notificationsList.filter(n => n.id > lastSeenNotifId).length;

  if (unreadCount > 0) {
    badge.style.display = 'flex';
    badge.textContent = unreadCount > 9 ? '9+' : unreadCount;
  } else {
    badge.style.display = 'none';
  }

  if (notificationsList.length === 0) {
    listEl.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--muted); font-size: 13px;">${t('notifEmpty')}</div>`;
    return;
  }

  listEl.innerHTML = notificationsList.map(n => {
    const isUnread = n.id > lastSeenNotifId;
    const dateObj = new Date(n.created_at + 'Z');
    const timeStr = dateObj.toLocaleTimeString(state.lang === 'ar' ? 'ar-IQ' : 'en-US', { hour: '2-digit', minute: '2-digit' });

    let icon = '<i class="ri-notification-3-line"></i>';
    if (n.event_type === 'grade_viewed') icon = '<i class="ri-eye-line" style="color: var(--primary);"></i>';
    else if (n.event_type === 'publish') icon = '<i class="ri-send-plane-fill" style="color: var(--ok);"></i>';

    return `
      <div class="notif-item" data-notif-id="${n.id}" style="padding: 12px 16px; border-bottom: 1px solid var(--line); background: ${isUnread ? 'color-mix(in oklab, var(--primary) 10%, transparent)' : 'transparent'}; display: flex; gap: 12px; align-items: flex-start; transition: transform 0.25s ease, opacity 0.25s ease, background 0.2s; position: relative; cursor: default; overflow: hidden;">
        <div style="font-size: 16px; margin-top: 2px;">${icon}</div>
        <div style="flex: 1; min-width: 0;">
          <div style="font-size: 13px; font-weight: ${isUnread ? '800' : '600'}; color: var(--text); margin-bottom: 4px;">${n.message}</div>
          <div style="font-size: 11px; color: var(--muted);">${timeStr}</div>
        </div>
        ${isUnread ? `<div style="width: 8px; height: 8px; border-radius: 50%; background: var(--primary); margin-top: 6px; flex-shrink: 0;"></div>` : ''}
        <button class="notif-delete-btn" data-delete-notif="${n.id}" title="${t('notifDelete')}"
          style="width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; background: none; border: none; color: var(--muted); cursor: pointer; font-size: 11px; border-radius: 50%; transition: all 0.2s; flex-shrink: 0; margin-top: 2px;"
          onmouseenter="this.style.color='var(--danger)';this.style.background='color-mix(in oklab, var(--danger) 12%, transparent)'"
          onmouseleave="this.style.color='var(--muted)';this.style.background='none'"
          aria-label="${t('notifDeleteLabel')}">✕</button>
      </div>
    `;
  }).join('');

  // Attach swipe-to-dismiss on each notification item
  listEl.querySelectorAll('.notif-item').forEach(item => initNotifSwipe(item));
}

/* ── Swipe-to-dismiss logic for individual notifications ── */
function initNotifSwipe(el) {
  let startX = 0, currentX = 0, isDragging = false;
  const THRESHOLD = 80; // px needed to trigger dismiss

  el.addEventListener('pointerdown', (e) => {
    if (e.target.closest('.notif-delete-btn')) return; // don't interfere with X button
    isDragging = true;
    startX = e.clientX;
    currentX = 0;
    el.style.transition = 'none';
    el.setPointerCapture(e.pointerId);
  });

  el.addEventListener('pointermove', (e) => {
    if (!isDragging) return;
    currentX = e.clientX - startX;
    // Allow swiping in both directions
    el.style.transform = `translateX(${currentX}px)`;
    el.style.opacity = Math.max(0, 1 - Math.abs(currentX) / 200).toString();
  });

  el.addEventListener('pointerup', () => {
    if (!isDragging) return;
    isDragging = false;
    el.style.transition = 'transform 0.25s ease, opacity 0.25s ease';

    if (Math.abs(currentX) > THRESHOLD) {
      // Dismiss!
      const direction = currentX > 0 ? 1 : -1;
      el.style.transform = `translateX(${direction * 400}px)`;
      el.style.opacity = '0';
      const notifId = el.dataset.notifId;
      setTimeout(() => deleteNotification(notifId), 250);
    } else {
      // Snap back
      el.style.transform = 'translateX(0)';
      el.style.opacity = '1';
    }
  });

  el.addEventListener('pointercancel', () => {
    isDragging = false;
    el.style.transition = 'transform 0.25s ease, opacity 0.25s ease';
    el.style.transform = 'translateX(0)';
    el.style.opacity = '1';
  });
}

/* ── Delete a single notification ── */
async function deleteNotification(notifId) {
  try {
    await api(`/api/notifications/${notifId}`, { method: 'DELETE' });
    notificationsList = notificationsList.filter(n => String(n.id) !== String(notifId));
    renderNotifications();
  } catch (err) {
    console.error('Failed to delete notification:', err);
  }
}

async function fetchNotifications() {
  try {
    const res = await fetch('/api/notifications');
    if (!res.ok) return;
    const data = await res.json();

    // Check for new notifications
    if (notificationsList.length > 0) {
      const newNotifs = data.filter(n => n.id > notificationsList[0].id && n.id > lastSeenNotifId);
      newNotifs.reverse().forEach(n => {
        if (n.event_type === 'grade_viewed') {
          showToast(t('notifStudentOpened', { msg: n.message }), 'info');
        }
      });
    }

    notificationsList = data;
    renderNotifications();
  } catch (err) {
    console.error('Failed to fetch notifications:', err);
  }
}

function applyLanguage(lang, animate = false) {
  const doSwitch = () => {
    state.lang = lang === 'en' ? 'en' : 'ar';
    localStorage.setItem('dashboard_lang', state.lang);

    document.documentElement.lang = state.lang;
    document.documentElement.dir = state.lang === 'ar' ? 'rtl' : 'ltr';

    const heroTitle = document.getElementById('heroTitle');
    const heroSubtitle = document.getElementById('heroSubtitle');
    if (heroTitle) heroTitle.textContent = t('heroTitle', { subject: heroTitle.dataset.subject || '' });
    if (heroSubtitle) heroSubtitle.textContent = t('heroSubtitle', { doctor: heroSubtitle.dataset.doctor || '' });

    if (langToggleBtn) {
      const nextLang = state.lang === 'ar' ? 'en' : 'ar';
      langToggleBtn.textContent = nextLang.toUpperCase();
      langToggleBtn.title = nextLang === 'ar' ? t('switchToArabic') : t('switchToEnglish');
    }

    applyStaticTranslations();

    if (state.activeSemester) {
      document.getElementById('semesterSelection').style.display = 'none';
      document.getElementById('dashboardApp').style.display = 'grid';
      renderStats();
      renderComponentsBuilder();
      renderPublishOptions();
      renderGradeTable();
      renderStudentsQuickList();
    } else {
      document.getElementById('semesterSelection').style.display = 'flex';
      document.getElementById('dashboardApp').style.display = 'none';
    }
  };

  if (!animate) { doSwitch(); return; }

  /* Animate: fade-blur out -> switch -> fade-blur in */
  const pageWrap = document.querySelector('.page-wrap');
  if (!pageWrap) { doSwitch(); return; }

  pageWrap.style.transition = 'opacity 0.2s ease, filter 0.2s ease, transform 0.2s ease';
  pageWrap.style.opacity = '0';
  pageWrap.style.filter = 'blur(6px)';
  pageWrap.style.transform = 'scale(0.98)';

  setTimeout(() => {
    doSwitch();

    /* Reset and animate back in */
    pageWrap.classList.add('lang-switch-animate');
    pageWrap.style.transition = '';
    pageWrap.style.opacity = '';
    pageWrap.style.filter = '';
    pageWrap.style.transform = '';

    const cleanup = () => {
      pageWrap.classList.remove('lang-switch-animate');
      pageWrap.removeEventListener('animationend', cleanup);
    };
    pageWrap.addEventListener('animationend', cleanup);
  }, 220);
}

function renderStats() {
  document.getElementById('statStudents').textContent = state.fullRows.length;
  document.getElementById('statComponents').textContent = state.components.length;

  const currentComponents = state.components.filter(c => c.semester === state.activeSemester);
  const cwSum = currentComponents.filter(c => c.category === 'coursework').reduce((sum, c) => sum + c.max_score, 0);
  const finalSum = currentComponents.filter(c => c.category === 'final').reduce((sum, c) => sum + c.max_score, 0);

  document.getElementById('statMaxTotal').textContent = cwSum + finalSum;
  document.getElementById('distributionHint').textContent = `السعي: ${cwSum} | النهائي: ${finalSum}`;
}

function renderComponentsBuilder() {
  const c1cw = document.getElementById('courseworkComponentsList');
  const c1f = document.getElementById('finalComponentsList');
  if (!c1cw || !c1f) return;

  const currentComponents = state.components.filter(c => c.semester === state.activeSemester);
  const coursework = currentComponents.filter(c => c.category === 'coursework').sort((a, b) => a.order_index - b.order_index);
  const finals = currentComponents.filter(c => c.category === 'final').sort((a, b) => a.order_index - b.order_index);

  function makeCard(c) {
    return `
      <div class="component-editor-item">
        <div>
          <strong>${getTranslatedLabel(c.label)}</strong>
        </div>
        <div class="row-inline">
          <input type="number" step="0.5" min="1" value="${c.max_score}" data-update-id="${c.id}" class="tiny-input" />
          <button class="ghost-btn icon-btn" data-action="save-component" data-id="${c.id}" title="${t('actionSave')}">
            <i class="ri-check-line" style="font-size: 1.2rem; line-height: 1;"></i>
          </button>
          <button class="danger-btn icon-btn" data-action="delete-component" data-id="${c.id}" title="Delete">
            <i class="ri-delete-bin-line" style="font-size: 1.2rem; line-height: 1;"></i>
          </button>
        </div>
      </div>
    `;
  }

  c1cw.innerHTML = coursework.map(makeCard).join('');
  c1f.innerHTML = finals.map(makeCard).join('');
}

// Gateway card click handling is consolidated at the end of the file

document.getElementById('switchSemesterBtn')?.addEventListener('click', () => {
  state.activeSemester = null;
  localStorage.removeItem('active_semester');
  applyLanguage(state.lang, false);
  closeSidebar();
});

// Notifications Dropdown Logic
const notifToggle = document.getElementById('notifToggle');
const notifDropdown = document.getElementById('notifDropdown');
if (notifToggle && notifDropdown) {
  notifToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    const isVisible = notifDropdown.style.display === 'block';
    notifDropdown.style.display = isVisible ? 'none' : 'block';
    if (!isVisible) {
      // Mark as seen when opening
      if (notificationsList.length > 0) {
        lastSeenNotifId = notificationsList[0].id;
        localStorage.setItem('last_seen_notif_id', lastSeenNotifId);
        renderNotifications();
      }
    }
  });

  document.addEventListener('click', (e) => {
    if (!notifToggle.contains(e.target) && !notifDropdown.contains(e.target)) {
      notifDropdown.style.display = 'none';
    }
  });
}

document.getElementById('clearNotifsBtn')?.addEventListener('click', async (e) => {
  e.stopPropagation();
  try {
    await api('/api/notifications/cleanup', { method: 'POST' });
    notificationsList = [];
    lastSeenNotifId = 0;
    localStorage.setItem('last_seen_notif_id', '0');
    renderNotifications();
    setStatus(t('notifAllCleared'), 'ok');
  } catch (err) {
    setStatus(err.message, 'error');
  }
});

// Delegated click for individual notification X buttons
document.getElementById('notifDropdown')?.addEventListener('click', (e) => {
  const delBtn = e.target.closest('[data-delete-notif]');
  if (delBtn) {
    e.stopPropagation();
    deleteNotification(delBtn.dataset.deleteNotif);
  }
});

// Poll notifications every 10 seconds
setInterval(fetchNotifications, 10000);
fetchNotifications(); // Initial fetch

document.querySelectorAll('.add-comp-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const cat = btn.dataset.cat;
    document.getElementById('newCompSemester').value = state.activeSemester;
    document.getElementById('newCompCategory').value = cat;

    // Auto-generate name
    const existingCount = state.components.filter(c => c.semester === state.activeSemester && c.category === cat).length;
    const defaultName = cat === 'final'
      ? (existingCount === 0 ? 'الفاينل' : `الفاينل ${existingCount + 1}`)
      : (existingCount === 0 ? 'التقييم' : `التقييم ${existingCount + 1}`);
    document.getElementById('newCompLabel').value = defaultName;

    addComponentForm.style.display = 'grid';
    // Focus the name input so they can change it to "الفاينل العملي" if they want
    document.getElementById('newCompLabel').focus();
    document.getElementById('newCompLabel').select();
  });
});

cancelAddCompBtn?.addEventListener('click', () => {
  addComponentForm.style.display = 'none';
  addComponentForm.reset();
});

addComponentForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const label = document.getElementById('newCompLabel').value;
  const max_score = parseFloat(document.getElementById('newCompMax').value);
  const semester = parseInt(document.getElementById('newCompSemester').value);
  const category = document.getElementById('newCompCategory').value;

  try {
    await api('/api/components', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ label, semester, category, max_score, order_index: 0 }),
    });
    addComponentForm.style.display = 'none';
    addComponentForm.reset();
    await loadGradebook();
    setStatus(t('statusComponentAdded'), 'ok');
  } catch (err) {
    setStatus(err.message, 'error');
  }
});

document.addEventListener('click', async (e) => {
  const btn = e.target.closest('button');
  if (!btn) return;

  if (btn.dataset.action === 'save-component') {
    const id = btn.dataset.id;
    const input = document.querySelector(`input[data-update-id="${id}"]`);
    const max_score = parseFloat(input.value);
    const comp = state.components.find(c => c.id == id);
    if (!comp || isNaN(max_score)) return;

    try {
      await api(`/api/components/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label: comp.label, semester: comp.semester, category: comp.category, max_score, order_index: comp.order_index }),
      });
      await loadGradebook();
      setStatus(t('statusComponentUpdated'), 'ok');
    } catch (err) {
      setStatus(err.message, 'error');
    }
  }



  if (btn.dataset.action === 'delete-component') {
    if (!confirm(t('confirmDeleteComp'))) return;
    try {
      await api(`/api/components/${btn.dataset.id}`, { method: 'DELETE' });
      await loadGradebook();
      setStatus(t('statusComponentDeleted'), 'ok');
    } catch (err) {
      setStatus(err.message, 'error');
    }
  }
});

function renderPublishOptions() {
  if (!publishComponents) return;
  const currentComponents = state.components.filter(c => c.semester === state.activeSemester);
  publishComponents.innerHTML = currentComponents.map(c => `
    <label class="chip-check">
      <input type="checkbox" name="component_keys" value="${c.component_key}" checked />
      <span style="font-weight: 700;">${getTranslatedLabel(c.label)}</span>
      <span class="badge-soft" style="font-size: 11px;">${c.max_score}</span>
    </label>
  `).join('');

  const manualContainer = document.getElementById('manualStudentSelection');
  if (manualContainer) {
    manualContainer.innerHTML = state.fullRows.map(row => `
      <label class="check-card" style="margin-bottom: 8px;">
        <input type="checkbox" name="student_ids" value="${row.student.id}" />
        <span>${row.student.full_name} <small class="muted">(${row.student.email || '-'})</small></span>
      </label>
    `).join('');
  }
}

document.querySelectorAll('input[name="publish_mode"]').forEach(radio => {
  radio.addEventListener('change', (e) => {
    const manualDiv = document.getElementById('manualStudentSelection');
    if (manualDiv) {
      manualDiv.style.display = e.target.value === 'manual' ? 'flex' : 'none';
    }
  });
});

function renderGradeTable() {
  if (!gradeTable) return;

  const currentComponents = state.components.filter(c => c.semester === state.activeSemester);
  const coursework = currentComponents.filter(c => c.category === 'coursework').sort((a, b) => a.order_index - b.order_index);
  const finals = currentComponents.filter(c => c.category === 'final').sort((a, b) => a.order_index - b.order_index);

  const headers = [...coursework, ...finals].map((c) => `
    <th style="text-align: center; vertical-align: middle;">
      <div style="font-weight: 700; font-size: 13px; color: var(--text);">${getTranslatedLabel(c.label)}</div>
      <span style="font-size: 10px; font-weight: 700; color: var(--muted); background: color-mix(in oklab, var(--text) 8%, transparent); padding: 2px 6px; border-radius: 6px; display: inline-block; margin-top: 4px;">/ ${c.max_score}</span>
    </th>
  `).join('');

  const bodyRows = state.rows.map((row) => {
    const scoreInputs = [...coursework, ...finals].map((c) => {
      const existing = row.scores[c.component_key];
      const val = existing ? existing.score : '';
      const pubBadge = existing?.published ? `<div class="pub-badge" style="position: absolute; top: -6px; inset-inline-start: -6px; background: var(--ok); color: white; border-radius: 50%; width: 14px; height: 14px; display: flex; align-items: center; justify-content: center; font-size: 10px;" title="${t('badgePublished')}">✓</div>` : '';
      return `
        <td class="gradebook-cell">
          <span class="cell-label">${getTranslatedLabel(c.label)}</span>
          <div style="position: relative; display: inline-block;">
            <input type="number" step="0.5" min="0" max="${c.max_score}" data-score="${c.component_key}" value="${val}" class="tiny-input" />
            ${pubBadge}
          </div>
          <span class="max-score-badge">/ ${c.max_score}</span>
        </td>
      `;
    }).join('');

    const semKey = `c${state.activeSemester}`;
    const cwSum = row.sums[`${semKey}_coursework`];
    const finalSum = row.sums[`${semKey}_final`];
    const totalSum = row.sums[`${semKey}_total`];

    // Generate avatar initials
    const initials = row.student.full_name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase();

    return `
      <tr data-student-id="${row.student.id}" style="transition: all 0.2s ease;">
        <td class="student-info-cell" style="padding: 12px 16px;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <div class="student-avatar" style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, var(--primary), var(--primary-strong)); color: white; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 14px; flex-shrink: 0; box-shadow: 0 4px 10px color-mix(in oklab, var(--primary) 30%, transparent);">${initials}</div>
            <div>
              <div style="font-weight: 800; color: var(--text); font-size: 15px; margin-bottom: 2px;">${row.student.full_name}</div>
              <div class="editable-email" title="${row.student.email || ''} (انقر للتعديل)" onclick="startEditEmail(this, ${row.student.id}, '${row.student.full_name.replace(/'/g, "\\'")}')">${row.student.email || 'لا يوجد بريد'}</div>
            </div>
          </div>
        </td>
        ${scoreInputs}
        <td class="totals-cell" style="vertical-align: middle; text-align: center;">
          <div style="display: flex; flex-direction: column; gap: 4px; align-items: center;">
            <div style="font-weight: 800; color: var(--text); font-size: 14px; background: color-mix(in oklab, var(--primary) 8%, transparent); padding: 4px 10px; border-radius: 8px; border: 1px solid color-mix(in oklab, var(--primary) 15%, transparent); display: inline-flex; align-items: center; gap: 4px;">
              <span style="font-size: 11px; font-weight: 600; color: var(--muted); margin-inline-end: 2px;">${state.lang === 'ar' ? 'المجموع' : 'Total'}:</span>
              ${totalSum}
            </div>
            <div style="display: flex; gap: 4px; margin-top: 2px;">
              <span style="font-size: 10px; font-weight: 700; color: var(--muted); opacity: 0.85;" title="${t('courseworkTitle')}">
                ${state.lang === 'ar' ? 'سعي' : 'CW'}: ${cwSum}
              </span>
              <span style="color: var(--line); font-size: 10px; font-weight: 300;">|</span>
              <span style="font-size: 10px; font-weight: 700; color: var(--muted); opacity: 0.85;" title="${t('finalTitle')}">
                ${state.lang === 'ar' ? 'نهائي' : 'Final'}: ${finalSum}
              </span>
            </div>
          </div>
        </td>
        <td class="actions-cell" style="vertical-align: middle; text-align: center;">
          <div style="display: flex; gap: 8px; justify-content: center; align-items: center;">
            <button class="ghost-btn icon-btn" data-action="save-row" 
              style="width: 36px; height: 36px; min-width: 36px; min-height: 36px; display: inline-flex; align-items: center; justify-content: center; border-radius: 10px; padding: 0; font-size: 1.2rem; line-height: 1; border: 1px solid color-mix(in oklab, var(--primary) 18%, transparent); background: color-mix(in oklab, var(--primary) 8%, transparent); color: var(--primary); transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer;"
              title="${t('actionSave')}"
              onmouseover="this.style.background='color-mix(in oklab, var(--primary) 16%, transparent)'; this.style.borderColor='color-mix(in oklab, var(--primary) 30%, transparent)'; this.style.color='var(--primary-strong)'"
              onmouseout="this.style.background='color-mix(in oklab, var(--primary) 8%, transparent)'; this.style.borderColor='color-mix(in oklab, var(--primary) 18%, transparent)'; this.style.color='var(--primary)'">
              <i class="ri-check-line" style="font-size: 1.2rem; line-height: 1;"></i>
            </button>
            <button class="danger-btn icon-btn" data-action="delete-student" 
              style="width: 36px; height: 36px; min-width: 36px; min-height: 36px; display: inline-flex; align-items: center; justify-content: center; border-radius: 10px; padding: 0; font-size: 1.2rem; line-height: 1; border: 1px solid color-mix(in oklab, var(--danger) 18%, transparent); background: color-mix(in oklab, var(--danger) 8%, transparent); color: var(--danger); transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer; transform: none; box-shadow: none;"
              title="${t('actionDelete')}"
              onmouseover="this.style.background='color-mix(in oklab, var(--danger) 16%, transparent)'; this.style.borderColor='color-mix(in oklab, var(--danger) 30%, transparent)'"
              onmouseout="this.style.background='color-mix(in oklab, var(--danger) 8%, transparent)'; this.style.borderColor='color-mix(in oklab, var(--danger) 18%, transparent)'">
              <i class="ri-delete-bin-line" style="font-size: 1.2rem; line-height: 1;"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  gradeTable.innerHTML = `
    <thead>
      <tr>
        <th style="padding: 16px; vertical-align: middle;">${t('tableStudent')}</th>
        ${headers}
        <th style="text-align: center; vertical-align: middle;">${state.lang === 'ar' ? 'المجاميع' : 'Totals'}</th>
        <th style="text-align: center; vertical-align: middle;">${t('tableActions')}</th>
      </tr>
    </thead>
    <tbody>
      ${bodyRows.length ? bodyRows : `<tr><td colspan="10" style="text-align: center; padding: 40px; color: var(--muted); font-weight: 600;">لا توجد بيانات، قم بإضافة طلبة.</td></tr>`}
    </tbody>
  `;
}

function renderStudentsQuickList() {
  if (!studentsQuickList) return;
  studentsQuickList.innerHTML = state.fullRows.map((row) => {
    const studentId = row.student.id;
    const name = row.student.full_name || '-';
    const total = row.sums[`c${state.activeSemester}_total`] || 0;
    return `<li><a href="#gradebookSection" class="student-mini" data-student-target="${studentId}"><span class="student-mini-name">${name}</span><span class="student-mini-score">${total}</span></a></li>`;
  }).join('') || `<li class="muted small-text">-</li>`;
}

async function loadGradebook() {
  const data = await api('/api/gradebook');
  if (!data) return;
  state.components = data.components;
  state.fullRows = data.rows;
  state.rows = [...data.rows];

  applyLanguage(state.lang, false);
}

// Sidebar, Auth, Search, Publish Logic remains standard
function closeSidebar() {
  if (window.innerWidth > 768) document.body.classList.add('sidebar-collapsed');
  else document.body.classList.remove('sidebar-open');
}
function toggleSidebar() {
  if (window.innerWidth > 768) document.body.classList.toggle('sidebar-collapsed');
  else document.body.classList.toggle('sidebar-open');
}

sidebarToggleBtn?.addEventListener('click', toggleSidebar);
sidebarCloseBtn?.addEventListener('click', closeSidebar);
sidebarBackdrop?.addEventListener('click', closeSidebar);
window.addEventListener('resize', () => {
  if (window.innerWidth > 768) {
    document.body.classList.remove('sidebar-open');
  }
});

function setActiveSection(section) {
  const next = section || 'overview';
  localStorage.setItem('dashboard_active_section', next);
  dashboardPanes.forEach(p => p.classList.toggle('is-active', p.dataset.pane === next));
  sectionNavButtons.forEach(btn => {
    const active = btn.dataset.section === next;
    btn.classList.toggle('is-active', active);
    btn.setAttribute('aria-current', active ? 'page' : 'false');
  });
}

sectionNavButtons.forEach(btn => btn.addEventListener('click', () => {
  setActiveSection(btn.dataset.section || 'overview');
  if (window.innerWidth <= 768) closeSidebar();
}));

langToggleBtn?.addEventListener('click', () => applyLanguage(state.lang === 'ar' ? 'en' : 'ar', true));

document.addEventListener('click', async (e) => {
  const btn = e.target.closest('button');
  if (!btn) return;

  if (btn.id === 'logoutBtn') {
    e.preventDefault();
    const confirmed = await showConfirm(t('confirmLogout') || 'تأكيد الخروج', t('confirmLogoutMsg') || 'هل أنت متأكد من رغبتك في تسجيل الخروج؟');
    if (!confirmed) return;

    try {
      await api('/api/auth/logout', { method: 'POST' });
      window.location.replace('/login');
    } catch (err) {
      console.error('Logout failed:', err);
      setStatus(err.message, 'error');
    }
    return;
  }

  if (btn.dataset.action === 'save-row') {
    const tr = btn.closest('tr');
    const studentId = tr.dataset.studentId;
    const scores = {};
    tr.querySelectorAll('input[data-score]').forEach(inp => {
      if (inp.value !== '') scores[inp.dataset.score] = Number(inp.value);
    });
    try {
      await api(`/api/students/${studentId}/scores`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scores }),
      });
      await loadGradebook();
      setStatus(t('statusScoresSaved'), 'ok');
    } catch (err) {
      setStatus(err.message, 'error');
    }
  }

  if (btn.dataset.action === 'delete-student') {
    const confirmed = await showConfirm(t('confirmDelete') || 'حذف الطالب', t('confirmDeleteMsg') || 'هل أنت متأكد من حذف هذا الطالب نهائياً؟');
    if (!confirmed) return;
    try {
      await api(`/api/students/${btn.closest('tr').dataset.studentId}`, { method: 'DELETE' });
      await loadGradebook();
      setStatus(t('statusStudentDeleted'), 'ok');
    } catch (err) {
      setStatus(err.message, 'error');
    }
  }
});

const addStudentForm = document.getElementById('addStudentForm');
addStudentForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(addStudentForm).entries());
  try {
    await api('/api/students', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
    addStudentForm.reset();
    await loadGradebook();
    setStatus(t('statusStudentAdded'), 'ok');
  } catch (err) { setStatus(err.message, 'error'); }
});

const searchInput = document.getElementById('searchInput');
searchInput?.addEventListener('input', (e) => {
  const value = e.target.value.trim().toLowerCase();
  state.rows = !value ? [...state.fullRows] : state.fullRows.filter(r => r.student.full_name.toLowerCase().includes(value));
  renderGradeTable();
});

const publishForm = document.getElementById('publishForm');
publishForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(publishForm);
  const mode = fd.get('publish_mode');

  const data = {
    component_keys: fd.getAll('component_keys'),
    send_email: fd.get('send_email') === 'on',
    force_new_token: fd.get('force_new_token') === 'on',
    semester: state.activeSemester,
    student_ids: mode === 'manual' ? fd.getAll('student_ids').map(Number) : null
  };

  if (mode === 'manual' && data.student_ids.length === 0) {
    setStatus('Please select at least one student.', 'error');
    return;
  }

  try {
    const payload = await api('/api/publish', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
    publishResult.innerHTML = `
      <div style="background: color-mix(in oklab, var(--card) 60%, transparent); border: 1px solid var(--line); border-radius: 16px; padding: 20px; margin-top: 16px;">
        <h3 style="margin-top:0; margin-bottom: 16px; font-size: 16px; color: var(--text); display: flex; align-items: center; gap: 8px;">
          <i class="ri-history-line" style="color: var(--primary);"></i> تفاصيل عملية النشر
        </h3>
        ${payload.emailed && payload.emailed.length ? `
        <ul style="padding: 0; list-style: none; display: flex; flex-direction: column; gap: 8px; margin-bottom: ${payload.skipped && payload.skipped.length ? '20px' : '0'};">
          ${payload.emailed.map(l => `
            <li style="padding: 12px 16px; background: color-mix(in oklab, var(--card-strong) 40%, transparent); border: 1px solid var(--line); border-radius: 12px; display: flex; justify-content: space-between; align-items: center; gap: 12px; direction: rtl;">
              <div style="display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 26px; line-height: 1; display: flex; align-items: center; justify-content: center;">
                  ${l.status === 'sent' ? '<i class="ri-mail-send-fill" style="color: var(--primary);"></i>' : '<i class="ri-error-warning-fill" style="color: var(--danger);"></i>'}
                </div>
                <div style="display: flex; flex-direction: column; gap: 4px; align-items: flex-start; text-align: right;">
                  <strong style="font-size: 14px; color: var(--text); font-weight: 800; margin: 0; line-height: 1;">${l.student}</strong>
                  <span style="font-size: 12px; font-weight: 700; color: ${l.status === 'sent' ? 'var(--ok)' : 'var(--danger)'}; margin: 0; line-height: 1;">
                    ${l.status === 'sent' ? '<i class="ri-check-line"></i> تم إرسال الإيميل بنجاح' : `<i class="ri-close-line"></i> فشل الإرسال (${l.detail})`}
                  </span>
                </div>
              </div>
              ${l.grade_url ? `<a href="${l.grade_url}" target="_blank" class="primary-btn" style="padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 700; text-decoration: none; display: flex; align-items: center; gap: 4px; white-space: nowrap; flex-shrink: 0; box-shadow: 0 2px 6px color-mix(in oklab, var(--primary) 30%, transparent);">فتح النتيجة <i class="ri-external-link-line"></i></a>` : ''}
            </li>
          `).join('')}
        </ul>` : ''}
      
      ${payload.skipped && payload.skipped.length ? `
        <h4 style="margin: 0 0 12px; font-size: 14px; color: var(--muted); display: flex; align-items: center; gap: 6px;">
          <i class="ri-skip-forward-line"></i> تم التخطي (لم يتم النشر لـ):
        </h4>
        <ul style="padding: 0; list-style: none; display: grid; gap: 8px;">
          ${payload.skipped.map(s => `
            <li style="padding: 10px 14px; background: color-mix(in oklab, var(--danger) 10%, transparent); border: 1px solid color-mix(in oklab, var(--danger) 20%, transparent); border-radius: 8px; font-size: 13px; display: flex; align-items: center; gap: 8px; color: var(--text);">
              <i class="ri-information-line" style="color: var(--danger);"></i>
              <div><strong style="font-weight: 800;">${s.student}:</strong> ${s.reason}</div>
            </li>
          `).join('')}
        </ul>
      ` : ''}
      </div>
    `;
    publishResult.style.display = 'block';
    publishResult.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    await loadGradebook();
    setStatus(t('statusPublished'), 'ok');
  } catch (err) { setStatus(err.message, 'error'); }
});

async function bootstrap() {
  try {
    const savedLang = localStorage.getItem('dashboard_lang') || 'ar';
    applyLanguage(savedLang, false);

    await api('/api/auth/me');
    setActiveSection(localStorage.getItem('dashboard_active_section') || 'overview');

    const savedSem = localStorage.getItem('active_semester');
    if (savedSem) {
      state.activeSemester = parseInt(savedSem, 10);
      semesterSelection.style.display = 'none';
      dashboardApp.style.display = '';
      if (window.innerWidth > 768) document.body.classList.remove('sidebar-collapsed');
      await loadGradebook();
    }

    setStatus(t('statusReady'), 'ok');
  } catch (err) {
    setStatus(err.message, 'error');
  } finally {
    document.documentElement.classList.remove('dashboard-preload');
  }
}

document.querySelectorAll('.gateway-card').forEach(card => {
  card.addEventListener('click', async () => {
    state.activeSemester = parseInt(card.dataset.selectSemester, 10);
    localStorage.setItem('active_semester', state.activeSemester);
    semesterSelection.style.display = 'none';
    dashboardApp.style.display = ''; // Removes inline display:none, falls back to CSS grid
    setActiveSection('overview'); // Force the user back to the overview when entering a course
    if (window.innerWidth > 768) document.body.classList.remove('sidebar-collapsed');
    await loadGradebook();
  });
});



document.addEventListener('DOMContentLoaded', bootstrap);

window.startEditEmail = function (el, studentId, fullName) {
  if (el.querySelector('input')) return; // Already editing
  el.classList.add('editing');
  const currentEmail = el.textContent === 'لا يوجد بريد' ? '' : el.textContent;

  // Rely on app.css for premium styling and animation
  el.innerHTML = `<input type="email" value="${currentEmail}" placeholder="example@gmail.com" />`;

  const input = el.querySelector('input');
  
  // Dynamically auto-grow input width to match content length
  const updateWidth = () => {
    const len = input.value ? input.value.length : (input.placeholder ? input.placeholder.length : 15);
    input.style.width = `${len + 1}ch`;
  };
  input.addEventListener('input', updateWidth);
  updateWidth();

  input.focus();
  input.select();

  const saveEmail = async () => {
    const newEmail = input.value.trim() || null;
    try {
      await api(`/api/students/${studentId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: newEmail, full_name: fullName })
      });
      const row = state.fullRows.find(r => r.student.id == studentId);
      if (row) row.student.email = newEmail;
      el.textContent = newEmail || 'لا يوجد بريد';
      el.classList.remove('editing');
      renderPublishOptions();
      setStatus('تم التحديث بنجاح', 'ok');
    } catch (err) {
      setStatus(err.message, 'error');
      el.textContent = currentEmail || 'لا يوجد بريد';
      el.classList.remove('editing');
    }
  };

  input.addEventListener('blur', saveEmail);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      input.blur();
    } else if (e.key === 'Escape') {
      el.textContent = currentEmail || 'لا يوجد بريد';
      el.classList.remove('editing');
    }
  });
};
