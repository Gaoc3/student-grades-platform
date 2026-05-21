const form = document.getElementById('signupForm');
const msg = document.getElementById('msg');
const langToggleBtn = document.getElementById('langToggleBtn');

const I18N = {
  ar: {
    signupTitle: 'إنشاء حساب دكتور جديد',
    signupSubtitle: 'سيتم إنشاء مساحة بيانات مستقلة ومؤمنة خاصة بمادتك العلمية.',
    fullNameLabel: 'الاسم الكامل',
    emailLabel: 'البريد الإلكتروني',
    subjectLabel: 'اسم المادة الدراسية',
    passwordLabel: 'كلمة المرور',
    signupAction: 'إنشاء الحساب',
    haveAccount: 'لديك حساب بالفعل؟',
    loginRedirect: 'تسجيل الدخول',
    creatingAccount: '...جارٍ إنشاء الحساب',
    signupFailed: 'فشل إنشاء الحساب',
    switchToEnglish: 'Switch to English',
    switchToArabic: 'التبديل إلى العربية',
  },
  en: {
    signupTitle: 'Create Account',
    signupSubtitle: 'A dedicated and secure data space will be created for your subject.',
    fullNameLabel: 'Full Name',
    emailLabel: 'Email Address',
    subjectLabel: 'Subject Name',
    passwordLabel: 'Password',
    signupAction: 'Create Account',
    haveAccount: 'Already have an account?',
    loginRedirect: 'Login Here',
    creatingAccount: 'Creating account...',
    signupFailed: 'Account creation failed',
    switchToEnglish: 'Switch to English',
    switchToArabic: 'التبديل إلى العربية',
  }
};

let currentLang = localStorage.getItem('dashboard_lang') || 'ar';

function applyLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('dashboard_lang', lang);
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';

  const pack = I18N[lang] || I18N.ar;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (pack[key]) el.textContent = pack[key];
  });

  if (langToggleBtn) {
    const nextLang = lang === 'ar' ? 'en' : 'ar';
    langToggleBtn.textContent = nextLang.toUpperCase();
    langToggleBtn.title = pack[nextLang === 'ar' ? 'switchToArabic' : 'switchToEnglish'];
  }
}

langToggleBtn?.addEventListener('click', () => {
  applyLanguage(currentLang === 'ar' ? 'en' : 'ar');
});

form?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const pack = I18N[currentLang] || I18N.ar;
  msg.textContent = pack.creatingAccount;
  msg.style.color = 'var(--text)';

  const formData = new FormData(form);
  const data = {};
  formData.forEach((value, key) => { data[key] = value; });

  try {
    const res = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      credentials: 'same-origin',
    });

    const payload = await res.json();
    if (!res.ok) {
      msg.textContent = payload.detail || pack.signupFailed;
      msg.style.color = 'var(--danger)';
      return;
    }

    window.location.replace('/dashboard');
  } catch (err) {
    msg.textContent = pack.signupFailed;
    msg.style.color = 'var(--danger)';
  }
});

// Init
applyLanguage(currentLang);
