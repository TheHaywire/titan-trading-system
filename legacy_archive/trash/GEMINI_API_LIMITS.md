# Gemini API Configuration Guide

## Your Current Limits (As of Dec 2025)

Based on your Google AI Studio dashboard:

### 🎯 BEST MODELS FOR YOUR USE CASE

#### Option 1: `gemini-2.5-flash` (RECOMMENDED)
- **RPM (Requests Per Minute):** 5
- **TPM (Tokens Per Minute):** 250,000
- **RPD (Requests Per Day):** 20
- **Best For:** Production use with moderate daily volume

#### Option 2: `gemini-2.5-flash-lite` (BACKUP)
- **RPM:** 10 (better than regular flash!)
- **TPM:** 250,000
- **RPD:** 20
- **Best For:** Higher RPM needs, same daily limit

### ⚠️ IMPORTANT LIMITS

**Daily Limit:** Only **20 requests per day** for both models
- This means you can run the Daily Analyst **20 times** before hitting the limit
- Resets at midnight Pacific Time

**Per-Minute Limit:** 
- `gemini-2.5-flash`: 5 requests/min
- `gemini-2.5-flash-lite`: 10 requests/min

### 🚀 OPTIMIZATION STRATEGY

To stay within limits:

1. **Daily Email:** Run ONCE per day (uses 1 request)
2. **Multi-Category Scan:** Run ONCE per day (uses 1 request)
3. **Leaves 18 requests** for manual testing/retraining

### 🔧 CURRENT CONFIGURATION

The system is now configured to:
1. **Primary:** Use `gemini-2.5-flash`
2. **Fallback:** Switch to `gemini-2.5-flash-lite` if error

### 📊 TRACKING USAGE

Monitor your usage at: https://aistudio.google.com/apikey

Current usage: **0/20 requests used today** ✅

---

## Models NOT Recommended

- `gemini-2.5-flash-tts` - For text-to-speech only (3 RPM)
- `gemini-2.5-flash-live` - For streaming conversations (different API)
- `gemma-*` models - Research/experimental only

---

**Last Updated:** December 7, 2025
