# Quick Start Guide

**Get the Sales Insight Automator running in 5 minutes!**

---

## 🎯 Prerequisites

- Docker & Docker Compose installed
- Google Gemini API key (free): https://aistudio.google.com/app/apikeys
- Gmail account (or SMTP server)

---

## ⚡ 5-Minute Setup

### Step 1: Clone & Configure (1 min)
```bash
git clone https://github.com/rabbitai/sales-insight-automator.git
cd sales-insight-automator
cp .env.example .env
```

### Step 2: Edit `.env` (2 min)
Open `.env` and add:
```env
GOOGLE_API_KEY=your_key_from_aistudio.google.com
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your_app_password
```

**How to get Gmail App Password:**
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Copy the 16-character password to `SENDER_PASSWORD`

### Step 3: Start Containers (1 min)
```bash
docker-compose up -d
```

### Step 4: Verify & Test (1 min)
```bash
# Check services are running
docker-compose ps

# Access application
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health: curl http://localhost:8000/health
```

**Done! ✅**

---

## 📤 First Upload

1. Go to http://localhost:3000
2. Upload `sales_q1_2026.csv` (provided)
3. Enter your test email
4. Click "Generate & Send Summary"
5. Check your email inbox within 30 seconds

---

## 🐛 Troubleshooting

### Services won't start?
```bash
docker-compose logs backend
docker-compose logs frontend
```

### API key error?
```bash
# Verify key is set
grep GOOGLE_API_KEY .env | wc -c  # Should be > 20 chars
```

### Email not sending?
- Verify Gmail app password (not account password)
- Check "Less secure app access" if using Gmail
- Look at logs: `docker-compose logs backend | grep -i email`

---

## 📚 Learn More

- **Full README**: See [README.md](README.md) for complete documentation
- **Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details

---

## 🚀 Next Steps

After successful local testing:

1. **Create GitHub Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Sales Insight Automator"
   git remote add origin https://github.com/YOUR-USERNAME/sales-insight-automator.git
   git push -u origin main
   ```

2. **Deploy Frontend to Vercel**
   - Visit https://vercel.com/new
   - Import your GitHub repository
   - Set `NEXT_PUBLIC_API_URL` environment variable

3. **Deploy Backend to Render**
   - Visit https://render.com
   - Create new Web Service
   - Connect GitHub repository
   - Set environment variables (same as your .env)

4. **Point Frontend to Live Backend**
   - Update Vercel `NEXT_PUBLIC_API_URL` to your Render backend URL
   - Redeploy on Vercel

---

**Time to production: ~15 minutes from here! 🚀**
