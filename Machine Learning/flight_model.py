import importlib
import subprocess
import sys

print("=" * 70)
print(f"[Diagnostics] Python Executable: {sys.executable}")
print(f"[Diagnostics] Python Version:    {sys.version.split()[0]}")
print("=" * 70)


def _ensure_package(package_name, import_name=None):
    """
    تتأكد إن المكتبة متثبتة، ولو مش متثبتة تثبتها تلقائياً عبر pip.
    بترجع True لو المكتبة بقت جاهزة للاستخدام، وبتوقف البرنامج برسالة
    واضحة لو التثبيت فشل بدل ما تسيبه ينهار بخطأ import غامض.
    """
    import_name = import_name or package_name
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        pass

    print(f"[Setup] '{package_name}' غير موجودة في هذه البيئة ({sys.executable})، "
          f"جاري تثبيتها تلقائياً...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "--upgrade", package_name]
        )
    except subprocess.CalledProcessError as e:
        print(f"[Setup][خطأ] فشل تثبيت '{package_name}' تلقائياً. "
              f"جرّب تثبتها يدوياً بالأمر التالي في نفس الـ terminal:\n"
              f'    "{sys.executable}" -m pip install {package_name}')
        raise RuntimeError(
            f"تعذر تثبيت المكتبة المطلوبة '{package_name}' تلقائياً."
        ) from e

    
    importlib.invalidate_caches()
    try:
        importlib.import_module(import_name)
        return True
    except ImportError as e:
        raise RuntimeError(
            f"تم تثبيت '{package_name}' لكن ما زال تعذر استيرادها في هذه البيئة "
            f"({sys.executable}).\n"
            "غالباً السبب إن VS Code بيشغل الكود بمفسّر بايثون (interpreter) مختلف "
            "عن اللي بيثبت فيه pip. تأكد من:\n"
            "  1) اضغط Ctrl+Shift+P في VS Code واختر 'Python: Select Interpreter'\n"
            "     وتأكد إنك مختار نفس النسخة الظاهرة فوق في [Diagnostics].\n"
            "  2) افتح terminal جديد داخل VS Code (عشان ياخد نفس الـ interpreter المختار)\n"
            f"     وشغّل: \"{sys.executable}\" -m pip install {package_name}\n"
            "  3) لو المشكلة استمرت (خصوصاً لو الرسالة فيها 'DLL load failed')، "
            "شغّل الأمرين دول في الـ terminal:\n"
            f'     "{sys.executable}" -m pip uninstall -y numpy scikit-learn scipy\n'
            f'     "{sys.executable}" -m pip install numpy scipy scikit-learn'
        ) from e



_REQUIRED_PACKAGES = [
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("scikit-learn", "sklearn"),
    ("xgboost", "xgboost"),
    ("lightgbm", "lightgbm"),
    ("imbalanced-learn", "imblearn"),
    ("joblib", "joblib")
]

for _pkg, _imp in _REQUIRED_PACKAGES:
    _ensure_package(_pkg, _imp)


# ---------------------------------------------------------------------
# استيراد المكتبات
# ---------------------------------------------------------------------
import glob
import os
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import (
    accuracy_score, classification_report, f1_score, make_scorer,
    roc_auc_score, confusion_matrix
)

# Algorithms
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from imblearn.ensemble import BalancedRandomForestClassifier

# نفس أسماء الحقول الأصلية للحفاظ على التوافق مع أي واجهة مستخدم (GUI)
CAT_FEATURES = ['Airline IATA', 'Departure IATA', 'Arrival IATA', 'Day of Week']
NUM_FEATURES = ['Departure Hour', 'dep_temp_max', 'dep_wind_speed', 'arr_temp_max', 'arr_wind_speed']

# الميزات الجديدة التي سيتم توليدها داخلياً (لن يطلب من المستخدم إدخالها)
ENGINEERED_NUM_FEATURES = ['dep_hour_sin', 'dep_hour_cos', 'is_weekend', 'weather_severity', 'temp_diff']
ALL_MODEL_FEATURES = CAT_FEATURES + NUM_FEATURES + ENGINEERED_NUM_FEATURES

# ---------------------------------------------------------------------
# اكتشاف البيئة تلقائياً
# ---------------------------------------------------------------------
def detect_environment():
    try:
        import google.colab  # noqa: F401
        return "colab"
    except ImportError:
        pass

    try:
        shell = get_ipython().__class__.__name__  # noqa: F821
        if shell in ("ZMQInteractiveShell",):
            return "jupyter"
    except NameError:
        pass

    return "script"

ENVIRONMENT = detect_environment()


# ---------------------------------------------------------------------
# حل مسار الملفات بأمان
# ---------------------------------------------------------------------
def _get_base_dir():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.getcwd()

BASE_DIR = _get_base_dir()


def _colab_upload_if_missing(patterns, friendly_name):
    if ENVIRONMENT != "colab":
        return 

    print(f"[Colab] لم يتم العثور على ملف '{friendly_name}' في المجلد الحالي.")
    print(f"[Colab] الرجاء رفع الملف المطلوب الآن (أحد الأسماء المتوقعة: {patterns})")

    from google.colab import files
    uploaded = files.upload()
    if uploaded:
        print(f"[Colab] تم رفع الملفات التالية: {list(uploaded.keys())}")
    else:
        print("[Colab] لم يتم رفع أي ملف.")


def _find_file(patterns, friendly_name="ملف"):
    def _search():
        for pattern in patterns:
            matches = glob.glob(os.path.join(BASE_DIR, pattern))
            if matches:
                return matches[0]
        return None

    found = _search()
    if found:
        return found

    if ENVIRONMENT == "colab":
        _colab_upload_if_missing(patterns, friendly_name)
        found = _search()
        if found:
            return found

    env_hint = {
        "colab": "تأكد إنك رفعت الملف عبر نافذة الرفع، أو ارفعه يدوياً.",
        "jupyter": "تأكد إن الملف موجود في نفس مجلد الـ notebook.",
        "script": "تأكد إن الملف موجود في نفس مجلد السكريبت.",
    }[ENVIRONMENT]

    raise FileNotFoundError(
        f"لم يتم العثور على '{friendly_name}' (الأنماط المتوقعة: {patterns})\n"
        f"[{ENVIRONMENT}] {env_hint}"
    )


def _resolve_aviation_file():
    return _find_file([
        "Final Aviation Cleaning.csv",
        "Final_Aviation_Cleaning.csv",
        "final aviation cleaning.csv",
        "*viation*leaning*.csv",
    ], friendly_name="بيانات الطيران (Aviation CSV)")


def _resolve_weather_file():
    return _find_file([
        "Weather_Clean_2026_Ready.csv",
        "Weather Clean 2026 Ready.csv",
        "*eather*lean*eady*.csv",
    ], friendly_name="بيانات الطقس (Weather CSV)")


# ---------------------------------------------------------------------
# معالجة ودمج البيانات
# ---------------------------------------------------------------------
def load_and_merge_data():
    aviation = pd.read_csv(_resolve_aviation_file())
    weather = pd.read_csv(_resolve_weather_file())

    aviation['date_std'] = pd.to_datetime(aviation['Flight Date']).dt.strftime('%Y-%m-%d')
    weather['date_std'] = pd.to_datetime(weather['date']).dt.strftime('%Y-%m-%d')

    df_merged = aviation.merge(
        weather, left_on=['Departure IATA', 'date_std'],
        right_on=['iata_code', 'date_std'], how='inner'
    )
    df_merged.rename(columns={
        'temp_max': 'dep_temp_max', 'temp_min': 'dep_temp_min',
        'precipitation': 'dep_precipitation', 'wind_speed': 'dep_wind_speed'
    }, inplace=True)

    df_merged = df_merged.merge(
        weather, left_on=['Arrival IATA', 'date_std'],
        right_on=['iata_code', 'date_std'], how='inner'
    )
    df_merged.rename(columns={
        'temp_max': 'arr_temp_max', 'temp_min': 'arr_temp_min',
        'precipitation': 'arr_precipitation', 'wind_speed': 'arr_wind_speed'
    }, inplace=True)

    return df_merged


# ---------------------------------------------------------------------
# هندسة الميزات (Feature Engineering)
# ---------------------------------------------------------------------
def _engineer_features(df):
    """
    تستخرج ميزات إضافية من البيانات الأساسية لزيادة قوة الموديل في اكتشاف التأخيرات.
    تعمل هذه الدالة داخلياً قبل التدريب وقبل التنبؤ للمحافظة على واجهة الإدخال.
    """
    df_eng = df.copy()

    # 1. Cyclic departure hour (تساعد الموديل على فهم أن الساعة 23 قريبة من الساعة 0)
    if 'Departure Hour' in df_eng.columns:
        df_eng['dep_hour_sin'] = np.sin(2 * np.pi * df_eng['Departure Hour'] / 24.0)
        df_eng['dep_hour_cos'] = np.cos(2 * np.pi * df_eng['Departure Hour'] / 24.0)
    
    # 2. Weekend indicator (أيام العطلات غالباً ما تشهد زحاماً وتأخيراً)
    if 'Day of Week' in df_eng.columns:
        # تحديد الإجازة بناءً على الاسم (السبت والأحد كمعيار عالمي في الطيران)
        df_eng['is_weekend'] = df_eng['Day of Week'].astype(str).str.lower().isin(['saturday', 'sunday']).astype(int)

    # 3. Weather Severity & Temp Differences (مؤشرات خطورة الطقس)
    if 'dep_wind_speed' in df_eng.columns and 'arr_wind_speed' in df_eng.columns:
        df_eng['weather_severity'] = df_eng['dep_wind_speed'] + df_eng['arr_wind_speed']
        
    if 'dep_temp_max' in df_eng.columns and 'arr_temp_max' in df_eng.columns:
        df_eng['temp_diff'] = abs(df_eng['dep_temp_max'] - df_eng['arr_temp_max'])

    # تعبئة القيم المفقودة (في حالة عدم وجودها) بـ 0 للحماية
    for col in ENGINEERED_NUM_FEATURES:
        if col not in df_eng.columns:
            df_eng[col] = 0.0

    return df_eng


# ---------------------------------------------------------------------
# التدريب (Training Pipeline) المطور
# ---------------------------------------------------------------------
def train_model():
    """
    يحمل الداتا، يبني ميزات جديدة، يختار أفضل موديل للتعامل مع الـ Imbalance
    بناءً على F1-Score، ويرجع النتائج.
    """
    df_merged = load_and_merge_data()

    # هندسة الميزات الجديدة
    df_merged = _engineer_features(df_merged)

    X = df_merged[ALL_MODEL_FEATURES].copy()
    y = df_merged['Is Delayed'].astype(int)

    # التكويد (Ordinal Encoding)
    encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    X[CAT_FEATURES] = encoder.fit_transform(X[CAT_FEATURES].astype(str))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # حساب معدل التوازن لـ XGBoost
    pos_count = sum(y_train == 1)
    neg_count = sum(y_train == 0)
    spw = neg_count / pos_count if pos_count > 0 else 1.0

    # تعريف الموديلات المدعومة بالتعامل مع البيانات غير المتوازنة
    models_to_try = {
        'LightGBM': (
            LGBMClassifier(class_weight='balanced', random_state=42, verbose=-1),
            {'n_estimators': [100, 200], 'max_depth': [5, 10, -1], 'learning_rate': [0.05, 0.1]}
        ),
        'XGBoost': (
            XGBClassifier(scale_pos_weight=spw, random_state=42, eval_metric='logloss'),
            {'n_estimators': [100, 200], 'max_depth': [5, 8], 'learning_rate': [0.05, 0.1]}
        ),
        'BalancedRandomForest': (
            BalancedRandomForestClassifier(random_state=42, replacement=True),
            {'n_estimators': [100, 200], 'max_depth': [10, 15, None]}
        ),
        'HistGradientBoosting': (
            HistGradientBoostingClassifier(class_weight='balanced', random_state=42),
            {'max_iter': [100, 200], 'max_depth': [5, 10, None], 'learning_rate': [0.05, 0.1]}
        )
    }

    # التقييم موجه نحو رفع كفاءة التنبؤ بالتأخير (Class 1)
    scorer = make_scorer(f1_score, pos_label=1)
    
    best_model = None
    best_f1 = -1
    best_name = ""

    print("[Model Selection] جاري تقييم الخوارزميات لاختيار الأفضل في اكتشاف التأخيرات...")
    
    for name, (clf, param_grid) in models_to_try.items():
        # بحث عشوائي سريع وفعال
        search = RandomizedSearchCV(
            clf, param_grid, n_iter=3, scoring=scorer, cv=3, random_state=42, n_jobs=-1
        )
        search.fit(X_train, y_train)
        mean_f1 = search.best_score_
        print(f" -> {name}: متوسط F1-Score (تأخير) = {mean_f1:.4f}")
        
        if mean_f1 > best_f1:
            best_f1 = mean_f1
            best_model = search.best_estimator_
            best_name = name

    print(f"\n[Model Selection] أفضل خوارزمية تم اختيارها: {best_name}\n")

    # التقييم الشامل على بيانات الاختبار
    y_pred = best_model.predict(X_test)
    y_proba = best_model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)

    print("--- التقييم المفصل للموديل (Evaluation) ---")
    print(f"Overall Accuracy: {accuracy:.4f}")
    print(f"ROC AUC Score:    {roc_auc_score(y_test, y_proba):.4f}")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(report)

    # عرض أهمية الميزات (Feature Importances) لو كانت مدعومة
    if hasattr(best_model, 'feature_importances_'):
        importances = best_model.feature_importances_
        indices = np.argsort(importances)[::-1]
        print("\nأهم الميزات المؤثرة في القرار (Top Features):")
        for i in range(min(10, len(ALL_MODEL_FEATURES))):
            feature_name = ALL_MODEL_FEATURES[indices[i]]
            print(f"  {feature_name}: {importances[indices[i]]:.4f}")
    else:
        print("\n(الموديل المختار لا يدعم خاصية feature_importances_ المباشرة)")

    return best_model, encoder, accuracy, report, df_merged


# ---------------------------------------------------------------------
# التنبؤ والتعامل مع المدخلات (بدون أي تغيير في الـ Signature)
# ---------------------------------------------------------------------
def estimate_numeric_features(df_merged, dep_iata, arr_iata, day_of_week=None, airline=None):
    df = df_merged

    def _avg(subset):
        if len(subset) == 0:
            return None
        return {
            'dep_hour': subset['Departure Hour'].mean(),
            'dep_temp_max': subset['dep_temp_max'].mean(),
            'dep_wind_speed': subset['dep_wind_speed'].mean(),
            'arr_temp_max': subset['arr_temp_max'].mean(),
            'arr_wind_speed': subset['arr_wind_speed'].mean(),
            'n_matches': len(subset),
        }

    route = df[(df['Departure IATA'] == dep_iata) & (df['Arrival IATA'] == arr_iata)]

    if airline and day_of_week:
        subset = route[(route['Airline IATA'] == airline) & (route['Day of Week'] == day_of_week)]
        result = _avg(subset)
        if result:
            result['match_level'] = 'route+airline+day'
            return result

    if day_of_week:
        subset = route[route['Day of Week'] == day_of_week]
        result = _avg(subset)
        if result:
            result['match_level'] = 'route+day'
            return result

    result = _avg(route)
    if result:
        result['match_level'] = 'route'
        return result

    dep_weather = df[df['Departure IATA'] == dep_iata]
    arr_weather = df[df['Arrival IATA'] == arr_iata]

    if len(dep_weather) > 0 and len(arr_weather) > 0:
        return {
            'dep_hour': df['Departure Hour'].mean(),
            'dep_temp_max': dep_weather['dep_temp_max'].mean(),
            'dep_wind_speed': dep_weather['dep_wind_speed'].mean(),
            'arr_temp_max': arr_weather['arr_temp_max'].mean(),
            'arr_wind_speed': arr_weather['arr_wind_speed'].mean(),
            'n_matches': 0,
            'match_level': 'airport_average',
        }

    return None


def get_known_categories(encoder):
    return {col: sorted(encoder.categories_[i]) for i, col in enumerate(CAT_FEATURES)}


def _normalize_categorical_value(value, known_categories):
    value = str(value).strip()

    if value in known_categories:
        return value

    upper_value = value.upper()
    for cat in known_categories:
        if str(cat).upper() == upper_value:
            return cat

    try:
        as_float = float(value)
        candidates = [str(as_float), str(int(as_float)), f"{as_float:.1f}"]
        for candidate in candidates:
            if candidate in known_categories:
                return candidate
    except ValueError:
        pass

    return value


def predict_delay_auto(model, encoder, df_merged, airline, dep_iata, arr_iata, day_of_week):
    estimated = estimate_numeric_features(df_merged, dep_iata, arr_iata, day_of_week, airline)

    if estimated is None:
        raise ValueError(
            f"لا توجد بيانات تاريخية كافية لخط الرحلة {dep_iata} → {arr_iata}. "
            "تأكد من اختيار مطارات موجودة فعلاً في بيانات التدريب."
        )

    pred, proba = predict_delay(
        model, encoder,
        airline=airline, dep_iata=dep_iata, arr_iata=arr_iata, day_of_week=day_of_week,
        dep_hour=estimated['dep_hour'],
        dep_temp_max=estimated['dep_temp_max'],
        dep_wind_speed=estimated['dep_wind_speed'],
        arr_temp_max=estimated['arr_temp_max'],
        arr_wind_speed=estimated['arr_wind_speed'],
    )

    return pred, proba, estimated


def predict_delay(model, encoder, airline, dep_iata, arr_iata, day_of_week,
                  dep_hour, dep_temp_max, dep_wind_speed, arr_temp_max, arr_wind_speed):
    
    raw_values = {
        'Airline IATA': airline,
        'Departure IATA': dep_iata,
        'Arrival IATA': arr_iata,
        'Day of Week': day_of_week,
    }

    normalized_values = {}
    for i, col in enumerate(CAT_FEATURES):
        known_categories = set(encoder.categories_[i])
        normalized_values[col] = _normalize_categorical_value(raw_values[col], known_categories)

    row = pd.DataFrame([{
        **normalized_values,
        'Departure Hour': dep_hour,
        'dep_temp_max': dep_temp_max,
        'dep_wind_speed': dep_wind_speed,
        'arr_temp_max': arr_temp_max,
        'arr_wind_speed': arr_wind_speed,
    }])

    # استخراج الميزات الجديدة داخلياً (مخفية عن الواجهة)
    row = _engineer_features(row)

    encoded = encoder.transform(row[CAT_FEATURES].astype(str))

    unknown_cols = [
        CAT_FEATURES[i] for i in range(len(CAT_FEATURES))
        if encoded[0][i] == -1
    ]
    if unknown_cols:
        details = []
        for col in unknown_cols:
            idx = CAT_FEATURES.index(col)
            sample = sorted(encoder.categories_[idx])[:8]
            details.append(f"{col} (مثال على قيم صحيحة: {sample})")
        raise ValueError(
            "Unknown value(s) for: " + "; ".join(details)
        )

    row[CAT_FEATURES] = encoded
    
    # التأكد من الترتيب الصحيح للأعمدة كما تدرب عليها الموديل
    row = row[ALL_MODEL_FEATURES]

    pred = model.predict(row)[0]
    proba = model.predict_proba(row)[0][pred]

    return int(pred), float(proba)


# ---------------------------------------------------------------------
# نقطة التشغيل الرئيسية
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print(f"[Info] البيئة المكتشفة: {ENVIRONMENT}")
    print(f"[Info] مجلد العمل (BASE_DIR): {BASE_DIR}\n")

    model, encoder, accuracy, report, df = train_model()

    print("\nKnown categorical values:")
    for col, values in get_known_categories(encoder).items():
        print(f"  {col}: {values[:10]}{' ...' if len(values) > 10 else ''}")

    # حفظ الملفات المطلوبة للإنتاج (Production)
    joblib.dump(model, 'flight_delay_model.pkl')
    joblib.dump(encoder, 'categorical_encoder.pkl')
    joblib.dump(ALL_MODEL_FEATURES, 'model_features.pkl')
    
    print("\n[Save] تم حفظ الموديل (Model)، والمحول (Encoder)، وقائمة الميزات بنجاح باستخدام Joblib.")