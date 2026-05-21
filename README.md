# Student Grades Platform (FastAPI)

مشروع ويب حديث لإدارة درجات الطلاب بلغة Python.

## Features

- تسجيل دخول وإنشاء حساب للدكاترة (Cookie Session + JWT)
- عزل بيانات كل دكتور في **قاعدة بيانات مستقلة** داخل `data/tenants/doctor_<id>.db`
- إدارة الطلاب: إضافة، تعديل، بحث، حذف
- إدارة الدرجات: Midterm, Attendance, Quizzes (عدد متغير), Assignment, Report
- كل مكون درجة قابل للتخصيص (من كم)
- نشر درجات جزئية/كلية للطلاب عبر QR
- إرسال QR لكل طالب عبر البريد الإلكتروني
- صلاحية QR لمدة 3 أيام + تنظيف تلقائي
- إشعار للدكتور عند فتح الطالب للرابط
- مسح سجل الإشعارات الأقدم من 30 يوم (تنظيف يومي تلقائي)
- واجهة حديثة مع Light/Dark mode في كل الصفحات
- إعداد الجامعة والشعار من `config/university.json`

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

ثم افتح:
- `http://127.0.0.1:8000/login`

## Security Notes

- ORM parameterized queries (ضد SQL Injection)
- Security headers middleware
- HttpOnly cookie + SameSite
- Rate limiting عبر `slowapi`
- يفضّل وضعه خلف Nginx/Cloudflare للإنتاج (WAF + DDoS edge protection)

## University Branding Config

عدّل الملف:

`config/university.json`

```json
{
  "university_name": "University Name Here",
  "university_logo_path": "/static/images/university-logo.png",
  "college_name": "College Name Here",
  "support_email": "support@university.edu"
}
```
