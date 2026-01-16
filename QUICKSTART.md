# ⚡ Quick Start - Deploy CortexAI ke GCP

## 1️⃣ Buka Google Cloud Console

👉 **https://console.cloud.google.com/**

---

## 2️⃣ Buat Project Baru

1. Klik dropdown project di atas → **NEW PROJECT**
2. Project name: `CortexAI`
3. Klik **CREATE**

---

## 3️⃣ Setup Billing (WAJIB)

1. Klik menu **Billing** di kiri
2. **Link a billing account**
3. Masukkan kartu kredit/debit
4. Pilih **Pay as you go** (gratis untuk pemakaian minimal)

---

## 4️⃣ Install gcloud CLI

### macOS:
```bash
brew install google-cloud-sdk
brew link --force google-cloud-sdk
source ~/.zshrc
```

### Windows:
Download dari: https://cloud.google.com/sdk/docs/install#windows

---

## 5️⃣ Login & Setup

```bash
# Login ke Google
gcloud auth login

# Set project (GANTI dengan project ID Anda)
export PROJECT_ID="gen-lang-client-0716506049"
gcloud config set project ${PROJECT_ID}
```

---

## 6️⃣ Enable APIs

```bash
gcloud services enable \
    bigquery.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com
```

---

## 7️⃣ Upload Secrets

```bash
# Upload Anthropic API Key
echo -n "sk-ant-api03-..." | \
  gcloud secrets versions add cortex-ai-anthropic-key --data-file=-

# Upload Service Account Key
gcloud secrets create cortex-ai-sa-key \
  --data-file=credentials/service-account.json
```

---

## 8️⃣ DEPLOY! 🚀

```bash
cd /Users/macbookpro/work/project/cortex-ai

# Automated deployment (semua otomatis)
./scripts/deploy-cloudrun.sh
```

**Tunggu 5-10 menit** sampai selesai.

---

## 9️⃣ Test Deployment

```bash
# Get service URL
gcloud run services describe cortex-ai \
  --region=asia-southeast1 \
  --format="value(status.url)"

# Test (GANTI URL dengan URL Anda)
curl https://cortex-ai-xxxxx.a.run.app/health
```

---

## ✅ Done!

Buka di browser:
```
https://cortex-ai-xxxxx.a.run.app/docs
```

---

## 💰 Biaya

**Cloud Run**:
- Gratis untuk testing (free tier)
- $10-50/bulan untuk production low-traffic
- Hanya bayar saat ada request

---

## 🛑 Stop Service (Jika tidak perlu)

```bash
gcloud run services delete cortex-ai --region=asia-southeast1
```

---

## 🆘 Error?

Lihat file `START_HERE.md` untuk troubleshooting lengkap.
