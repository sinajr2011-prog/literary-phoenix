import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ===============================
# ✅ CORS Configuration
# ===============================
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000", 
                    "http://localhost:8000", "http://127.0.0.1:8000",
                    "http://localhost:5500", "http://127.0.0.1:5500",
                    "file://"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept"],
        "supports_credentials": True
    }
})

# ===============================
# 🔑 OpenRouter API Configuration
# ===============================
OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY", 
    "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"
)
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemma-3-27b-it:free"

print(f"✅ OpenRouter API متصل شد")
print(f"📊 مدل: {MODEL_NAME}")

# مسیر فایل‌های Static - والد فولڈر
STATIC_FOLDER = Path(__file__).parent.parent
print(f"📁 Static Folder: {STATIC_FOLDER}")

# ===============================
# 🏠 Home & Static Files
# ===============================
@app.route("/")
def home():
    """Serve site landing page"""
    return send_from_directory(STATIC_FOLDER, "index.html")

# Serve Static Files (HTML, CSS, JS, etc.)
@app.route("/<path:filename>")
def serve_file(filename):
    """Serve static files"""
    try:
        file_path = STATIC_FOLDER / filename
        
        print(f"\n📥 درخواست: {filename}")
        print(f"   📍 مسیر: {file_path}")
        
        # امنیت - مطمئن شو در STATIC_FOLDER است
        if not str(file_path.resolve()).startswith(str(STATIC_FOLDER.resolve())):
            print(f"   ❌ دسترسی رد شد!")
            return "Access Denied", 403
        
        # اگر فایل وجود ندارد
        if not file_path.exists():
            print(f"   ❌ فایل موجود نیست!")
            return f"فایل یافت نشد: {filename}", 404
        
        # اگر directory است
        if file_path.is_dir():
            index_file = file_path / "index.html"
            if index_file.exists():
                return send_from_directory(file_path, "index.html")
            return "دایرکتوری نمی‌تواند نمایش داده شود", 403
        
        print(f"   ✅ فایل سرو می‌شود ({file_path.stat().st_size} بایت)")
        return send_from_directory(STATIC_FOLDER, filename)
        
    except Exception as e:
        print(f"   ❌ خطا: {e}")
        return str(e), 500

# Test endpoint
@app.route("/test")
def test():
    return jsonify({"message": "✅ سرور کار می‌کند"})

# Test OpenRouter Connection
@app.route("/test-api")
def test_api():
    """تست اتصال به OpenRouter"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:8080",
            "X-Title": "Qoghnoos Adab Test",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "user", "content": "سلام"}
            ],
            "max_tokens": 100
        }
        
        print(f"🔍 تست اتصال OpenRouter...")
        print(f"📊 URL: {OPENROUTER_API_URL}")
        print(f"🔑 Key: {OPENROUTER_API_KEY[:30]}...")
        
        response = requests.post(
            OPENROUTER_API_URL,
            json=payload,
            headers=headers,
            timeout=15
        )
        
        print(f"📥 Status: {response.status_code}")
        
        if response.status_code == 200:
            return jsonify({
                "status": "✅ اتصال موفق",
                "model": MODEL_NAME,
                "response": response.json()
            }), 200
        else:
            return jsonify({
                "status": "❌ خطا",
                "code": response.status_code,
                "error": response.text
            }), response.status_code
            
    except Exception as e:
        print(f"❌ خطا: {str(e)}")
        return jsonify({
            "status": "❌ خطا",
            "error": str(e)
        }), 500

# ===============================
# 🤖 AI Teacher Endpoint
# ===============================
@app.route("/api/ai-teacher", methods=["POST", "OPTIONS"])
def ai_teacher():
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "درخواست خالی است"}), 400

        subject = data.get("subject", "").strip()
        grade = data.get("grade", "").strip()
        question = data.get("question", "").strip()
        student_id = data.get("studentId", "unknown")

        # ✅ Validation
        if not question:
            return jsonify({"error": "سوال خالی است"}), 400
        
        if len(question) < 5:
            return jsonify({"error": "سوال باید حداقل 5 کاراکتر داشته باشد"}), 400

        if not subject or subject not in ["math", "science", "persian"]:
            return jsonify({"error": "موضوع نامعتبر است"}), 400

        if not grade or grade not in ["7", "8", "9"]:
            return jsonify({"error": "پایه نامعتبر است"}), 400

        # 🤖 Generate prompt
        subject_names = {
            "math": "ریاضی",
            "science": "علوم",
            "persian": "فارسی"
        }
        
        grade_names = {
            "7": "هفتم",
            "8": "هشتم", 
            "9": "نهم"
        }

        system_prompt = f"""تو یک معلم حرفه‌ای {subject_names.get(subject)} برای پایه {grade_names.get(grade)} هستی.
دانش‌آموز سطح متوسط تا پیشرفته دارد.

قوانین پاسخ:
1. پاسخ را فارسی و شفاف بدهید
2. مرحله‌به‌مرحله توضیح دهید
3. مثال‌های ملموس بزنید
4. طول پاسخ: 150-300 کلمه
5. اگر فرمول دارد، توضیح دهید"""

        print(f"📨 درخواست از {student_id}: {subject} - پایه {grade}")
        print(f"❓ سوال: {question[:100]}...")

        # 🚀 Call OpenRouter API
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:8080",
            "X-Title": "Qoghnoos Adab AI Teacher",
            "Content-Type": "application/json"
        }

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 0.95
        }

        # 🚀 Call OpenRouter API
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:8080",
            "X-Title": "Qoghnoos Adab AI Teacher",
            "Content-Type": "application/json"
        }

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 0.95
        }

        print(f"📤 درخواست به OpenRouter...")
        print(f"🔑 API Key: {OPENROUTER_API_KEY[:30]}...")
        print(f"🧠 مدل: {MODEL_NAME}")
        print(f"📊 Headers: {headers}")
        print(f"📋 Payload: {json.dumps(payload, ensure_ascii=False)[:200]}...")
        
        response = requests.post(
            OPENROUTER_API_URL,
            json=payload,
            headers=headers,
            timeout=60
        )

        print(f"📥 پاسخ دریافت شد - Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            try:
                error_detail = response.json()
            except:
                error_detail = response.text
            
            print(f"❌ OpenRouter Error ({response.status_code}):")
            print(f"   {error_detail}")
            
            return jsonify({
                "error": f"خطا از OpenRouter: {response.status_code}",
                "details": str(error_detail),
                "statusCode": response.status_code
            }), response.status_code

        result = response.json()
        print(f"✅ JSON پارس شد")
        
        # بررسی اینکه آیا choices وجود دارد
        if not result.get("choices"):
            print(f"❌ choices نیست در جواب: {result}")
            return jsonify({"error": "پاسخ نامعتبر: choices وجود ندارد"}), 500
        
        choice = result["choices"][0]
        print(f"✅ choice[0] پیدا شد")
        
        if not choice.get("message"):
            print(f"❌ message نیست در choice: {choice}")
            return jsonify({"error": "پاسخ نامعتبر: message وجود ندارد"}), 500
        
        answer = choice["message"].get("content", "")
        print(f"✅ content استخراج شد: {answer[:100]}...")
        
        if not answer:
            print(f"❌ content خالی است")
            return jsonify({"error": "پاسخ خالی است"}), 500

        print(f"✅ پاسخ موفق ({len(answer)} کاراکتر)")

        return jsonify({
            "answer": answer,
            "source": "openrouter",
            "model": MODEL_NAME,
            "subject": subject,
            "grade": grade
        }), 200

    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout - سرور پاسخ نداد")
        return jsonify({
            "error": "سرور پاسخ نداد. لطفاً دوباره تلاش کنید.",
            "timeout": True
        }), 504

    except requests.exceptions.ConnectionError as e:
        print(f"❌ خطای اتصال: {str(e)}")
        return jsonify({
            "error": "ارتباط برقرار نشد. لطفاً اینترنت را بررسی کنید.",
            "connection_error": True
        }), 503

    except Exception as e:
        print(f"❌ خطا: {str(e)}")
        return jsonify({
            "error": "خطا در پردازش درخواست",
            "details": str(e)
        }), 500

# ===============================
# 🛡️ Error Handlers
# ===============================
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "endpoint پیدا نشد"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "خطای سرور"}), 500

# ===============================
# 🚀 Main
# ===============================
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 AI TEACHER SERVER")
    print("=" * 50)
    print(f"🌐 URL: http://127.0.0.1:8081")
    print(f"📍 Home: http://127.0.0.1:8081/")
    print(f"🎯 API: http://127.0.0.1:8081/api/ai-teacher")
    print(f"🧠 مدل: {MODEL_NAME}")
    print(f"📡 Provider: OpenRouter")
    print("=" * 50)
    
    app.run(
        host="127.0.0.1",
        port=8081,
        debug=True,
        use_reloader=True
    )
