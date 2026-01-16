# 🚀 Panduan Deploy CortexAI dari NOL

Panduan langkah demi langkah untuk deploy CortexAI ke Google Cloud Platform (GCP) untuk pemula.

---

## 📋 Prasyarat

Sebelum mulai, pastikan Anda sudah memiliki:
- [ ] Google Account (Gmail)
- [ ] Komputer/Laptop
- [ ] Koneksi internet
- [ ] Project code CortexAI dari GitHub

---

## 🔑 STEP 1: Buat Google Cloud Account

### 1.1 Buka Google Cloud Console

1. Buka browser (Chrome/Edge/Firefox)
2. Kunjungi: **https://console.cloud.google.com/**
3. Login dengan akun Google Anda

### 1.2 Buat Project Baru (Jika belum punya)

1. Di bagian atas, klik dropdown project
2. Klik **"NEW PROJECT"**
3. Isi form:
   - **Project name**: `CortexAI` (atau nama lain)
   - **Organization**: Pilih organisasi jika ada, jika tidak ada biarkan saja
4. Klik **"CREATE"**

> **Note**: Project ID akan dibuat otomatis (contoh: `cortexai-123456`)

### 1.3 Setup Billing (Wajib untuk Cloud Run)

1. Di menu kiri, klik **"Billing"**
2. Klik **"Link a billing account"**
3. Pilih atau buat billing account baru
4. Masukkan data pembayaran (kartu kredit/debit)
5. Pilih plan: **"Pay as you go"** (tidak ada biaya tetap)

> **PENTING**: Anda tidak akan langsung dikenakan biaya. GCP punya **free tier** dan Anda hanya bayar jika resource digunakan.

---

## 🛠️ STEP 2: Install Google Cloud SDK

### 2.1 Install gcloud CLI

#### **macOS** (dengan Homebrew)

```bash
# Buka Terminal, jalankan:
brew install google-cloud-sdk

# Tambahkan ke PATH
brew install --cask google-cloud-sdk

# Atau manually:
echo "$(brew --prefix)/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/path.bash.inc" >> ~/.zshrc
echo "$(brew --prefix)/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/completion.zsh.inc" >> ~/.zshrc

# Reload shell
source ~/.zshrc
```

#### **Linux**

```bash
# Download dan install
curl https://sdk.cloud.google.com | bash

# Reload shell
exec -l $SHELL
```

#### **Windows**

1. Download installer: https://cloud.google.com/sdk/docs/install#windows
2. Jalankan installer `google-cloud-sdk-installer.exe`
3. Buka **PowerShell** atau **Command Prompt**

### 2.2 Authenticate ke Google Cloud

```bash
# Login ke Google Cloud
gcloud auth login

# Akan membuka browser → Login → Allow access → Kembali ke terminal
```

### 2.3 Set Default Project

```bash
# Lihat list project
gcloud projects list

# Set default project (GANTI dengan project ID Anda)
export PROJECT_ID="gen-lang-client-0716506049"
gcloud config set project ${PROJECT_ID}

# Verifikasi
gcloud config list project
```

---

## 🔓 STEP 3: Enable APIs

```bash
# Enable semua API yang dibutuhkan
gcloud services enable \
    bigquery.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com
```

> **Tunggu** beberapa detik hingga muncul pesan "Waiting for... [done]" atau selesai.

---

## 🔐 STEP 4: Upload Secrets ke GCP

### 4.1 Upload Anthropic API Key

```bash
# Jika punya API key di file
echo -n "sk-ant-api03-..." | \
  gcloud secrets versions add cortex-ai-anthropic-key --data-file=-

# Atau ketik langsung
gcloud secrets create cortex-ai-anthropic-key --data-file=-
# (paste API key Anda, tekan Ctrl+D untuk save)
```

### 4.2 Upload Service Account Key

```bash
# Upload file service-account.json
gcloud secrets create cortex-ai-sa-key \
  --data-file=credentials/service-account.json

# Verifikasi secrets sudah terupload
gcloud secrets list
```

---

## 🚀 STEP 5: Deploy ke Cloud Run

### 5.1 Automated Deployment (Recommended)

```bash
# Masuk ke directory project
cd /Users/macbookpro/work/project/cortex-ai

# Jalankan deployment script
chmod +x scripts/deploy-cloudrun.sh
./scripts/deploy-cloudrun.sh
```

**Script akan otomatis:**
1. Create Artifact Registry
2. Build Docker image
3. Push ke Artifact Registry
4. Deploy ke Cloud Run
5. Test deployment

### 5.2 Manual Deployment (Jika automated gagal)

#### A. Create Artifact Registry

```bash
export REGION="asia-southeast1"
export REPO_NAME="cortex-ai"

gcloud artifacts repositories create ${REPO_NAME} \
  --repository-format=docker \
  --location=${REGION} \
  --description="CortexAI Docker images"
```

#### B. Build Docker Image

```bash
# Build dan push dengan Cloud Build
gcloud builds submit \
  --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/cortex-ai:latest
```

> **Note**: Proses ini memakan waktu 3-5 menit

#### C. Deploy ke Cloud Run

```bash
gcloud run deploy cortex-ai \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/cortex-ai:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --max-instances=100 \
  --timeout=300s \
  --concurrency=10 \
  --set-env-vars=FASTAPI_ENV=production,GCP_PROJECT_ID=${PROJECT_ID},BIGQUERY_LOCATION=US \
  --set-secrets=ANTHROPIC_API_KEY=cortex-ai-anthropic-key:latest,GOOGLE_APPLICATION_CREDENTIALS=cortex-ai-sa-key:latest
```

---

## ✅ STEP 6: Verifikasi Deployment

### 6.1 Get Service URL

```bash
# Get URL dari Cloud Run
SERVICE_URL=$(gcloud run services describe cortex-ai \
  --region=${REGION} \
  --format="value(status.url)")

echo "Service URL: ${SERVICE_URL}"
```

### 6.2 Test Endpoints

```bash
# Test health endpoint
curl ${SERVICE_URL}/health

# Test root endpoint
curl ${SERVICE_URL}/

# Test list datasets
curl ${SERVICE_URL}/api/v1/datasets
```

### 6.3 Buka di Browser

Buka URL yang muncul di browser:
```
https://cortex-ai-xxxxx.a.run.app
```

Anda akan melihat:
```json
{
  "service": "BigQuery AI Service",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

---

## 📊 STEP 7: Akses API Documentation

Buka di browser:
```
https://cortex-ai-xxxxx.a.run.app/docs
```

Anda akan melihat **Swagger UI** untuk mencoba semua API endpoints.

---

## 🔍 STEP 8: Monitoring

### View Logs

```bash
# Real-time logs
gcloud run logs tail cortex-ai --region=${REGION}

# View recent logs
gcloud run logs read cortex-ai --region=${REGION} --limit=50
```

### Check Service Status

```bash
# Service details
gcloud run services describe cortex-ai --region=${REGION}

# List revisions
gcloud run revisions list --service=cortex-ai --region=${REGION}
```

---

## 💰 STEP 9: Cek Biaya

```bash
# View estimated costs
gcloud billing projects describe ${PROJECT_ID}

# Atau buka di browser:
# https://console.cloud.google.com/billing
```

**Estimasi Biaya Cloud Run:**
- CPU: $0.0000125 per vCPU-second
- Memory: $0.00000025 per GB-second
- Requests: $0.40 per million requests
- **Total estimasi**: $10-50/bulan untuk low-medium traffic

---

## 🛑 STEP 10: Stop/Hapus Service (Jika tidak digunakan)

### Stop Cloud Run Service

```bash
# Hapus service (tidak ada biaya ketika stopped)
gcloud run services delete cortex-ai --region=${REGION}
```

### Hapus Project

1. Buka: https://console.cloud.google.com/
2. Pilih project
3. Klik menu "IAM & Admin" → "Settings"
4. Scroll ke bawah → Klik "SHUTDOWN"

---

## 📝 Checklist Sebelum Deploy

- [ ] Google account sudah dibuat
- [ ] GCP project sudah dibuat
- [ ] Billing sudah disetup (perlu kartu kredit)
- [ ] gcloud CLI sudah terinstall
- [ ] Sudah login: `gcloud auth login`
- [ ] Project sudah diset: `gcloud config set project PROJECT_ID`
- [ ] APIs sudah di-enable
- [ ] Secrets sudah di-upload (API key, service account)
- [ ] Deployment script sudah siap

---

## 🆘 Troubleshooting

### Error: "Permission denied"

**Solusi**:
```bash
# Pastikan sudah login
gcloud auth login

# Cek project
gcloud config list project

# Enable APIs
gcloud services enable run.googleapis.com
```

### Error: "Billing not enabled"

**Solusi**:
1. Buka: https://console.cloud.google.com/billing
2. Link billing account ke project

### Error: "Secret not found"

**Solusi**:
```bash
# Cek secrets
gcloud secrets list

# Upload ulang secrets
gcloud secrets create cortex-ai-anthropic-key --data-file=-
```

### Error: "Build failed"

**Solusi**:
```bash
# Cek logs
gcloud builds list --limit=5

# View build logs
gcloud builds log BUILD_ID
```

---

## 🎯 Summary

**Urutan yang harus dilakukan:**

1. ✅ Buka https://console.cloud.google.com/
2. ✅ Buat project baru
3. ✅ Setup billing (wajib)
4. ✅ Install gcloud CLI di komputer
5. ✅ Login: `gcloud auth login`
6. ✅ Set project: `gcloud config set project PROJECT_ID`
7. ✅ Enable APIs
8. ✅ Upload secrets (API key, service account)
9. ✅ Deploy: `./scripts/deploy-cloudrun.sh`
10. ✅ Test deployment
11. ✅ Done! 🎉

---

## 📞 Help & Resources

- **GCP Documentation**: https://cloud.google.com/docs
- **Cloud Run Docs**: https://cloud.google.com/run/docs
- **GCP Support**: https://cloud.google.com/support

---

**Last Updated**: 2025-01-16
**Version**: 1.0.0
