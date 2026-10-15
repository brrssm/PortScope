# راهنمای فارسی PortScope (ویندوز + PowerShell)

> **هشدار قانونی:** فقط سیستم‌هایی را اسکن کنید که مال خودتان است یا اجازه‌ی کتبی صریح برای تست آن دارید. اسکن بدون مجوز ممکن است غیرقانونی باشد.

## ۱. این پروژه چه کاری می‌کند؟

PortScope یک برنامه‌ی ساده‌ی پایتون است که پورت‌های TCP یک سیستم را بررسی می‌کند و می‌گوید هر پورت:

- **open** (باز): اتصال موفق بود.
- **closed** (بسته): سیستم اتصال را صریحاً رد کرد.
- **filtered_or_unknown** (نامشخص): جواب قابل اعتمادی نیامد (مثلاً timeout). این به معنای اثبات وجود فایروال **نیست**.

همچنین زمان پاسخ را به میلی‌ثانیه اندازه می‌گیرد و خروجی JSON و CSV می‌دهد.

## ۲. فایل‌های مهم

| فایل | کاربرد |
|---|---|
| `portscope/scanner.py` | منطق اصلی اسکن، بررسی ورودی و محدودیت‌ها |
| `portscope/cli.py` | رابط خط فرمان (گزینه‌ها و نمایش نتیجه) |
| `portscope/exporter.py` | ذخیره‌ی نتیجه در JSON و CSV |
| `tests/` | تست‌های خودکار |
| `examples/sample_output.json` | نمونه‌ی خروجی واقعی |
| `README.md` | معرفی انگلیسی پروژه برای GitHub |
| `.gitignore` | فهرست فایل‌هایی که نباید به GitHub بروند |
| `LICENSE` | مجوز MIT |
| `pyproject.toml` | اطلاعات پروژه |

## ۳. نصب پایتون

1. به https://www.python.org/downloads/ بروید و نسخه‌ی ۳.۸ یا جدیدتر را دانلود کنید.
2. هنگام نصب حتماً گزینه‌ی **Add python.exe to PATH** را تیک بزنید.
3. یک PowerShell جدید باز کنید (منوی Start ← تایپ `PowerShell`) و بزنید:

```powershell
python --version
```

## ۴. باز کردن پوشه‌ی پروژه در ترمینال

پوشه را از حالت ZIP خارج کنید (مثلاً در `C:\Projects\PortScope`). سپس در PowerShell:

```powershell
cd C:\Projects\PortScope
```

(یا در File Explorer داخل پوشه بروید، روی نوار آدرس کلیک کنید، `powershell` بنویسید و Enter بزنید.)

## ۵. ساخت و فعال‌سازی محیط مجازی

همه‌ی دستورها داخل پوشه‌ی پروژه اجرا شوند:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

اگر خطای اجرای اسکریپت (ExecutionPolicy) دیدید، یک بار این را بزنید و دوباره فعال‌سازی کنید:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

اگر اول خط `(.venv)` ظاهر شد، فعال شده است. این پروژه پکیج خارجی ندارد.

## ۶. اجرای اسکنر

```powershell
python -m portscope 127.0.0.1
```

`127.0.0.1` یعنی همین کامپیوتر خودتان؛ امن‌ترین هدف برای تمرین است. راهنمای کامل:

```powershell
python -m portscope --help
```

به صورت پیش‌فرض فقط آدرس‌های محلی و خصوصی (مثل `127.0.0.1` و `192.168.x.x`) مجازند.

## ۷. انتخاب پورت‌ها و timeout

```powershell
python -m portscope 127.0.0.1 -p 80                    # یک پورت
python -m portscope 127.0.0.1 -p 20-100                # یک بازه
python -m portscope 127.0.0.1 -p 22,80,443,8080        # چند پورت
python -m portscope 127.0.0.1 -p 1-1024 -t 0.5         # timeout نیم‌ثانیه
python -m portscope 127.0.0.1 -p 1-200 --show-all      # نمایش همه‌ی وضعیت‌ها
```

- `-t` یا `--timeout`: زمان انتظار برای هر اتصال (ثانیه). پیش‌فرض ۱.
- `-w` یا `--workers`: تعداد اتصال همزمان (پیش‌فرض ۲۰، حداکثر ۱۰۰).
- `--max-ports`: سقف تعداد پورت در یک اجرا (پیش‌فرض ۱۰۲۴).

## ۸. خروجی JSON و CSV

```powershell
python -m portscope 127.0.0.1 -p 1-1024 --json reports\scan.json --csv reports\scan.csv
```

پوشه‌ی `reports` خودکار ساخته می‌شود. این پوشه در `.gitignore` است و به GitHub نمی‌رود.

## ۹. اجرای تست‌ها

```powershell
python -m unittest discover -v
```

در پایان باید `OK` ببینید. تست‌ها به اینترنت نیاز ندارند.

## ۱۰. آپلود پروژه روی GitHub (عمومی)

### الف) نصب Git

از https://git-scm.com/download/win نصب کنید (گزینه‌های پیش‌فرض کافی است). بعد PowerShell را ببندید و دوباره باز کنید:

```powershell
git --version
```

### ب) تنظیم هویت (فقط یک بار)

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

بهتر است ایمیل همان ایمیل حساب GitHub یا ایمیل `noreply` گیت‌هاب باشد.

### پ) ساخت مخزن در GitHub

1. وارد https://github.com شوید (در صورت نیاز ثبت‌نام کنید).
2. بالا سمت راست روی **+** ← **New repository** کلیک کنید.
3. نام: `PortScope`؛ توضیح کوتاه بنویسید؛ گزینه‌ی **Public** را انتخاب کنید.
4. تیک **Add a README**، **.gitignore** و **license** را **نزنید** (چون این فایل‌ها را دارید).
5. **Create repository** را بزنید و آدرس مخزن را کپی کنید، مثلاً `https://github.com/YOUR-USERNAME/PortScope.git`.

### ت) قبل از آپلود: چند فایل را شخصی‌سازی کنید

- در `LICENSE` و `pyproject.toml` عبارت `Your Name` را با نام خودتان عوض کنید.
- در `README.md` عبارت `<your-username>` را با نام کاربری GitHub خودتان عوض کنید.

### ث) دستورهای Git (داخل پوشه‌ی پروژه در PowerShell)

```powershell
cd C:\Projects\PortScope
git init
git branch -M main
git add .
git status
git commit -m "Initial commit: PortScope TCP port scanner"
git remote add origin https://github.com/YOUR-USERNAME/PortScope.git
git push -u origin main
```

`YOUR-USERNAME` را با نام کاربری خودتان جایگزین کنید. هنگام `push` یک پنجره برای ورود به GitHub باز می‌شود؛ وارد شوید و تأیید کنید.

### ج) جلوگیری از آپلود فایل‌های ناخواسته

قبل از `git commit` با `git status` فهرست را ببینید. این موارد **نباید** در فهرست باشند: `.venv/`، `__pycache__/`، `.env`، `reports/` و فایل‌های CSV. فایل `.gitignore` این‌ها را نادیده می‌گیرد. اگر چیزی ناخواسته اضافه شد:

```powershell
git rm -r --cached .venv
git commit -m "Remove unwanted files"
```

هرگز رمز عبور، توکن یا کلید API را در مخزن عمومی نگذارید.

## ۱۱. به‌روزرسانی مخزن بعد از تغییرات

```powershell
cd C:\Projects\PortScope
python -m unittest discover
git add .
git commit -m "توضیح کوتاه تغییر (ترجیحاً انگلیسی)"
git push
```

## ۱۲. نکات مصاحبه

- تفاوت `open`، `closed` و `filtered_or_unknown` را توضیح دهید و بگویید چرا timeout اثبات فایروال نیست.
- بگویید چرا اسکن پیش‌فرض فقط روی آدرس‌های محلی و خصوصی است و چرا سقف تعداد پورت دارد.
- توضیح دهید چرا از چند thread استفاده شده و چرا تعداد آن محدود است.
- نشان دهید تست‌ها بدون اینترنت و با socket شبیه‌سازی‌شده (mock) اجرا می‌شوند.
