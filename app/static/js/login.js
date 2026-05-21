const form = document.getElementById('loginForm');
const msg = document.getElementById('msg');
const langToggleBtn = document.getElementById('langToggleBtn');

const I18N = {
  ar: {
    loginTitle: 'تسجيل دخول الدكاترة',
    loginSubtitle: 'الدخول مخصص لأعضاء الهيئة التدريسية فقط لإدارة درجات الطلبة ونشر النتائج.',
    emailLabel: 'البريد الإلكتروني',
    passwordLabel: 'كلمة المرور',
    rememberMe: 'حفظ تسجيل الدخول',
    loginAction: 'دخول',
    noAccount: 'ليس لديك حساب؟',
    createAccount: 'إنشاء حساب جديد',
    loggingIn: '...جارٍ تسجيل الدخول',
    loginFailed: 'فشل تسجيل الدخول',
    switchToEnglish: 'Switch to English',
    switchToArabic: 'التبديل إلى العربية',
  },
  en: {
    loginTitle: 'Faculty Login',
    loginSubtitle: 'Access is restricted to faculty members only for student grade management.',
    emailLabel: 'Email Address',
    passwordLabel: 'Password',
    rememberMe: 'Save login',
    loginAction: 'Sign In',
    noAccount: "Don't have an account?",
    createAccount: 'Create New Account',
    loggingIn: 'Signing in...',
    loginFailed: 'Login failed',
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

async function checkExistingSession() {
  try {
    const res = await fetch('/api/auth/me', { credentials: 'same-origin' });
    if (res.ok) {
      window.location.replace('/dashboard');
    }
  } catch {
    // ignore
  }
}

form?.addEventListener('submit', async (e) => {
  e.preventDefault();
  console.log('Login form submitted');
  
  const pack = I18N[currentLang] || I18N.ar;
  msg.textContent = pack.loggingIn;
  msg.style.color = 'var(--text)';

  const formData = new FormData(form);
  const data = {};
  formData.forEach((value, key) => {
    data[key] = value;
  });
  data.remember_me = !!data.remember_me;

  console.log('Sending login request for:', data.email);

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      credentials: 'same-origin',
    });

    console.log('Login response status:', res.status);
    const payload = await res.json();
    
    if (!res.ok) {
      console.warn('Login failed:', payload.detail);
      msg.textContent = payload.detail || pack.loginFailed;
      msg.style.color = 'var(--danger)';
      return;
    }

    console.log('Login successful, redirecting...');
    localStorage.removeItem('active_semester');
    localStorage.setItem('force_gateway', 'true');
    window.location.replace('/dashboard');
  } catch (err) {
    console.error('Network or server error during login:', err);
    msg.textContent = pack.loginFailed + ' (Network Error)';
    msg.style.color = 'var(--danger)';
  }
});

console.log('Login script initialized');
// Init
applyLanguage(currentLang);
checkExistingSession();
document.body.style.opacity = '1';
