# Flight Dashboard Setup Guide

اتبع الخطوات التالية بالترتيب حتى يعمل المشروع بدون أي مشاكل.

## Step 1: Create the Main Project Folder

قم بإنشاء فولدر جديد باسم:


flight_dashboard


ثم قم بتحميل **جميع الملفات الموجودة داخل الريبو (باستثناء فولدري `templates` و `static`)** وضعها مباشرة داخل فولدر:


flight_dashboard


---

## Step 2: Create the Templates Folder

داخل فولدر **flight_dashboard** قم بإنشاء فولدر جديد باسم:


templates


بعد ذلك قم بتحميل جميع الملفات الموجودة داخل فولدر **templates** في الريبو وضعها داخل:


flight_dashboard/templates


---

## Step 3: Create the Static Folder

داخل فولدر **flight_dashboard** قم بإنشاء فولدر جديد باسم:


static


ثم قم بتحميل جميع الملفات الموجودة داخل فولدر **static** في الريبو وضعها داخل:


flight_dashboard/static


---

## Step 4: Final Project Structure

يجب أن يكون ترتيب الملفات بالشكل التالي:

```text
flight_dashboard/
│
├── app.py
├── flight_model.py
├── requirements.txt
├── *.csv
├── *.pkl
├── ...
│
├── templates/
│   ├── index.html
│   ├── result.html
│   └── ...
│
└── static/
    ├── css/
    ├── js/
    ├── images/
    └── ...
```

---

## Step 5: Run the Project

1. افتح فولدر **flight_dashboard** باستخدام **Visual Studio Code**.

2. شغل الملف:


flight_model.py


سيقوم هذا الملف بتثبيت المكتبات المطلوبة وإعداد بيئة التشغيل (Environment).

3. بعد انتهاء تشغيله، قم بتشغيل الملف:


app.py


سيعمل المشروع مباشرة.



## Important Notes

* **يجب أن تكون أسماء الملفات والفولدرات مطابقة تمامًا للأسماء الموجودة في الريبو.**
* **يجب الحفاظ على نفس ترتيب وهيكل الملفات كما هو موضح أعلاه.**
* **لا تقم بنقل أو إعادة تسمية أي ملف أو فولدر، لأن الكود يعتمد على هذا الهيكل، وأي تغيير قد يؤدي إلى عدم عمل المشروع بشكل صحيح.**

