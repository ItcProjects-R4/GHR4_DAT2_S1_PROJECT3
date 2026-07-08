"""
app.py
====================================================================
الخادم (Backend) لواجهة "برج التحكم" - نظام التنبؤ بتأخير الرحلات.
بيقدّم واجهة ويب حقيقية (HTML/CSS/JS) بدل نافذة سطح مكتب، وبيوصلها
بمنطق التدريب والتنبؤ الموجود في flight_model.py من غير أي تكرار كود.

طريقة التشغيل:
  1) حط الملف ده ومجلدي templates/ و static/ بجانب flight_model.py
     وملفات الداتا (Aviation CSV و Weather CSV) في نفس المجلد.
  2) شغّل: python app.py
  3) هيفتحلك المتصفح تلقائياً على http://127.0.0.1:5000
  يل:
  1) حط الملف ده ومجلدي templates/ و static/ بجانب flight_model.py
     وملفات الداتا (Aviation CSV و Weather CSV) في نفس المجلد.
  2) شغّل: python app.py
  3) هيفتحلك المتصفح تلقائياً على http://127.0.0.1:5000
====================================================================
"""

import importlib
import subprocess
import sys
import os
import threading
import traceback
import time
import webbrowser


def _ensure_package(package_name, import_name=None):
    import_name = import_name or package_name
    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f"[Setup] '{package_name}' غير موجودة، جاري تثبيتها تلقائياً...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package_name])


for _pkg, _imp in [("flask", "flask")]:
    _ensure_package(_pkg, _imp)

import joblib
from flask import Flask, render_template, request, jsonify

import flight_model as fm


app = Flask(__name__)

MODEL_PATH = os.path.join(fm.BASE_DIR, "flight_delay_model.pkl")
ENCODER_PATH = os.path.join(fm.BASE_DIR, "categorical_encoder.pkl")
FEATURES_PATH = os.path.join(fm.BASE_DIR, "model_features.pkl")

# حالة السيرفر المشتركة (بديل بسيط عن قاعدة بيانات لتطبيق محلي شخصي)
_state = {
    "model": None, "encoder": None, "df_merged": None,
    "ready": False, "message": "جاري تجهيز البيانات...", "error": None,
}

_retrain_state = {"running": False, "done": True, "log": "", "error": None}


def _startup_worker():
    try:
        _state["message"] = "جاري تجهيز بيانات الطيران والطقس..."
        df_merged = fm._engineer_features(fm.load_and_merge_data())

        if os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_PATH):
            _state["message"] = "تم العثور على موديل محفوظ، جاري تحميله..."
            model = joblib.load(MODEL_PATH)
            encoder = joblib.load(ENCODER_PATH)
        else:
            _state["message"] = "لا يوجد موديل محفوظ، جاري تدريب موديل جديد (راقب الـ terminal)..."
            model, encoder, accuracy, report, df_merged = fm.train_model()
            joblib.dump(model, MODEL_PATH)
            joblib.dump(encoder, ENCODER_PATH)
            joblib.dump(fm.ALL_MODEL_FEATURES, FEATURES_PATH)

        _state.update(model=model, encoder=encoder, df_merged=df_merged, ready=True, message="جاهز")
    except Exception as e:
        traceback.print_exc()
        _state["error"] = str(e)


def _retrain_worker():
    try:
        _retrain_state["log"] = "جاري إعادة التدريب... تابع الـ terminal لمتابعة التفاصيل خطوة بخطوة."
        model, encoder, accuracy, report, df_merged = fm.train_model()
        joblib.dump(model, MODEL_PATH)
        joblib.dump(encoder, ENCODER_PATH)
        joblib.dump(fm.ALL_MODEL_FEATURES, FEATURES_PATH)
        _state.update(model=model, encoder=encoder, df_merged=df_merged)
        _retrain_state["log"] = f"✅ تم إعادة التدريب بنجاح.\n\nAccuracy: {accuracy:.4f}\n\n{report}"
    except Exception as e:
        traceback.print_exc()
        _retrain_state["error"] = str(e)
    finally:
        _retrain_state["running"] = False
        _retrain_state["done"] = True


# -----------------------------------------------------------------
# الصفحة الرئيسية
# -----------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -----------------------------------------------------------------
# حالة تجهيز الموديل (polling أثناء الإقلاع)
# -----------------------------------------------------------------
@app.route("/api/status")
def api_status():
    return jsonify(ready=_state["ready"], message=_state["message"], error=_state["error"])


# -----------------------------------------------------------------
# القيم المعروفة لملء القوائم المنسدلة
# -----------------------------------------------------------------
@app.route("/api/categories")
def api_categories():
    if not _state["ready"]:
        return jsonify(error="الموديل لسه بيتجهز، حاول تاني بعد شوية."), 503

    known = fm.get_known_categories(_state["encoder"])
    return jsonify(
        airlines=known["Airline IATA"],
        departures=known["Departure IATA"],
        arrivals=known["Arrival IATA"],
        days=known["Day of Week"],
    )


# -----------------------------------------------------------------
# تنبؤ تلقائي
# -----------------------------------------------------------------
@app.route("/api/predict/auto", methods=["POST"])
def api_predict_auto():
    data = request.get_json(force=True)
    try:
        pred, proba, estimated = fm.predict_delay_auto(
            _state["model"], _state["encoder"], _state["df_merged"],
            airline=data["airline"], dep_iata=data["dep"], arr_iata=data["arr"], day_of_week=data["day"],
        )
        return jsonify(pred=pred, proba=proba, estimated=estimated)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify(error="حصل خطأ غير متوقع أثناء التنبؤ."), 500


# -----------------------------------------------------------------
# تنبؤ يدوي
# -----------------------------------------------------------------
@app.route("/api/predict/manual", methods=["POST"])
def api_predict_manual():
    data = request.get_json(force=True)
    try:
        pred, proba = fm.predict_delay(
            _state["model"], _state["encoder"],
            airline=data["airline"], dep_iata=data["dep"], arr_iata=data["arr"], day_of_week=data["day"],
            dep_hour=float(data["dep_hour"]), dep_temp_max=float(data["dep_temp_max"]),
            dep_wind_speed=float(data["dep_wind_speed"]), arr_temp_max=float(data["arr_temp_max"]),
            arr_wind_speed=float(data["arr_wind_speed"]),
        )
        return jsonify(pred=pred, proba=proba)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify(error="حصل خطأ غير متوقع أثناء التنبؤ."), 500


# -----------------------------------------------------------------
# إعادة التدريب (غير متزامن + polling)
# -----------------------------------------------------------------
@app.route("/api/retrain", methods=["POST"])
def api_retrain():
    if _retrain_state["running"]:
        return jsonify(error="عملية إعادة تدريب شغالة بالفعل."), 409

    _retrain_state.update(running=True, done=False, log="بدأ التدريب...", error=None)
    threading.Thread(target=_retrain_worker, daemon=True).start()
    return jsonify(started=True)


@app.route("/api/retrain/status")
def api_retrain_status():
    return jsonify(done=_retrain_state["done"], log=_retrain_state["log"], error=_retrain_state["error"])


def _open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    threading.Thread(target=_startup_worker, daemon=True).start()
    threading.Thread(target=_open_browser, daemon=True).start()
    print("[Server] جاري التشغيل على http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)