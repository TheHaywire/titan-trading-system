import google.generativeai as genai
import config
import os

print("="*60)
print("🔍 GEMINI API DIAGNOSTIC TOOL")
print("="*60)

# 1. Check Credentials
if not hasattr(config, 'GOOGLE_API_KEY') or not config.GOOGLE_API_KEY:
    print("❌ ERROR: GOOGLE_API_KEY not found in config.py")
    exit()

print(f"✅ API Key found: {config.GOOGLE_API_KEY[:5]}...{config.GOOGLE_API_KEY[-3:]}")

genai.configure(api_key=config.GOOGLE_API_KEY)

# 2. Test Model Availability
print("\n📡 Testing Model Connection...")
models_to_try = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-1.5-flash', 'gemini-pro']

working_model = None

for model_name in models_to_try:
    print(f"   👉 Attempting {model_name}...", end=" ")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Test. Reply with 'OK'.")
        msg = f"✅ SUCCESS! Response: {response.text.strip()}"
        print(msg)
        with open("GEMINI_DEBUG_LOG.txt", "a") as f: f.write(f"\n{model_name}: {msg}")
        working_model = model_name
        break
    except Exception as e:
        msg = f"❌ FAILED. Error: {str(e)}"
        print(msg)
        with open("GEMINI_DEBUG_LOG.txt", "a") as f: f.write(f"\n{model_name}: {msg}")

if not working_model:
    print("\n⚠️  CRITICAL: All models failed. Check quota or API key permissions.")
else:
    print(f"\n✨ RECOMMENDED CONFIGURATION: Use '{working_model}'")

print("\n" + "="*60)
