const fs = require('fs');
const path = require('path');

// المسارات النسبية للملفات داخل مجلد templates
const filesToUpdate = [
    "templates/base.html",
    "templates/dashboard.html",
    "templates/login.html",
    "templates/signup.html"
];

const newVersion = Math.floor(Date.now() / 1000).toString();
const pattern = /(\?v=)[a-zA-Z0-9\.]+/g;

// تحديد مسار مجلد app الذكي بغض النظر عن مكان وقوفك في الشاشة
let currentDir = process.cwd();
let appPath = currentDir.endsWith('app') ? currentDir : path.join(currentDir, 'app');

filesToUpdate.forEach(filePath => {
    const fullPath = path.join(appPath, filePath);
    if (fs.existsSync(fullPath)) {
        const content = fs.readFileSync(fullPath, 'utf8');
        const newContent = content.replace(pattern, `$1${newVersion}`);
        fs.writeFileSync(fullPath, newContent, 'utf8');
        console.log(`✅ Updated: app/${filePath} -> ?v=${newVersion}`);
    } else {
        console.log(`❌ Not Found: app/${filePath} (Checked: ${fullPath})`);
    }
});