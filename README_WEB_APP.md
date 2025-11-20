# 🌐 Geocoding Web App

**Simple, free web-based geocoding tool using OpenStreetMap Nominatim**

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Live Demo

**🔗 [Open App](https://your-app-name.streamlit.app)** (Replace with actual URL after deployment)

No login required! Just open and use! 🎉

---

## ✨ Features

- 📤 **Upload Excel** - Drag & drop .xlsx files
- 📥 **Download Template** - Pre-configured Excel template
- 🗺️ **Free Geocoding** - Using OpenStreetMap (no API key!)
- ⚡ **Parallel Processing** - 3-5x faster with multi-threading
- 📊 **Real-time Progress** - See live processing status
- 🎯 **Quality Control** - Confidence scoring & validation
- 📈 **Statistics** - Visual analytics of results
- 💾 **Download Results** - Get geocoded data as Excel

---

## 🚀 Quick Start for Users

### 1. Open the App

Visit: **https://your-app-name.streamlit.app**

### 2. Download Template

Click "Download Template.xlsx" button → Open in Excel

### 3. Fill Your Data

Required columns:
- `latitude` (required)
- `longitude` (required)
- `kelurahan` (optional - for validation)
- `kecamatan` (optional - for validation)

### 4. Upload & Process

1. Click "Choose Excel file"
2. Select your .xlsx file
3. Click "Start Geocoding"
4. Wait for completion
5. Download results!

**That's it!** ✅

---

## 💻 Local Development

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/python-gis-toolkit.git
cd python-gis-toolkit

# Install dependencies
pip install -r requirements_web.txt

# Run locally
streamlit run streamlit_app.py
```

App will open at: http://localhost:8501

---

## 🌐 Deployment

### Option 1: Streamlit Cloud (Recommended - FREE)

**Easiest deployment! 5 minutes setup!**

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select repository & branch
   - Main file: `streamlit_app.py`
   - Requirements file: `requirements_web.txt`
   - Click "Deploy"!

3. **Your app is live!**
   - URL: `https://[your-app-name].streamlit.app`
   - Auto-deploy on git push
   - HTTPS included
   - 100% FREE!

**Detailed guide:** See [DEPLOYMENT_GUIDE_WEB.txt](DEPLOYMENT_GUIDE_WEB.txt)

### Option 2: Railway.app

1. Sign up at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Select repository
4. Railway auto-configures
5. Get your URL!

### Option 3: Heroku

```bash
# Install Heroku CLI
# Login
heroku login

# Create app
heroku create your-app-name

# Deploy
git push heroku main

# Open
heroku open
```

---

## 📁 Project Structure

```
python-gis-toolkit/
├── streamlit_app.py          # Main web application
├── requirements_web.txt      # Python dependencies
├── Procfile                  # For Railway/Heroku
├── setup.sh                  # Heroku setup script
├── runtime.txt               # Python version
├── .streamlit/
│   └── config.toml          # Streamlit configuration
├── DEPLOYMENT_GUIDE_WEB.txt # Deployment instructions
└── WEB_APP_USER_GUIDE.txt   # User guide
```

---

## ⚙️ Configuration

### Workers (Performance)

Adjust in sidebar:
- **1 worker**: Slowest, safest
- **3 workers**: Recommended (default)
- **5 workers**: Fastest, max recommended

### Validation

Enable kelurahan/kecamatan validation:
- Calculates confidence scores
- Identifies mismatches
- Better quality control

---

## 📊 Understanding Results

### Output Columns

**Geocoded Data:**
- `Nama_Jalan`: Street name
- `Kelurahan`: Village/kelurahan
- `Kecamatan`: District/kecamatan
- `Kota`: City
- `Provinsi`: Province
- `Alamat_Lengkap`: Full address

**Quality Metrics:**
- `Confidence_Score`: 0.0-1.0
  - 0.9-1.0: Excellent ⭐⭐⭐
  - 0.7-0.9: Good ⭐⭐
  - <0.7: Review manually ⚠️
- `Status`: OK or NOT_FOUND
- `Source`: nominatim or photon

---

## ⏱️ Performance

### Processing Time (3 workers)

| Rows | Time |
|------|------|
| 10 | ~10 seconds |
| 50 | ~30 seconds |
| 100 | ~1 minute |
| 500 | ~5 minutes |
| 1,000 | ~10 minutes |

### Success Rate

- Overall: 85-90%
- Urban areas: 90%+
- Rural areas: 80-85%

---

## ⚠️ Limitations

### Rate Limits
- Nominatim: 1 request/second
- Photon: 2 requests/second
- Please respect fair use!

### Data Size
- Recommended: <1000 rows
- Maximum: ~5000 rows
- For larger data: Use desktop scripts

### Accuracy
- Success rate: 85-90%
- Urban > Rural coverage
- Some areas may have gaps

---

## 🐛 Troubleshooting

### "Column not found" error
- Check column names: `latitude`, `longitude`
- Case insensitive
- Alternative names supported: `lat`, `lon`, `lng`

### Many NOT_FOUND results
- Verify coordinates are valid
- Check coordinates not swapped
- Try reducing workers to 1
- Coordinates may be in remote areas

### Slow processing
- Increase workers (up to 5)
- Check internet connection
- Process in smaller batches
- Try at different time

### Upload failed
- Ensure file is .xlsx format
- File size <200MB
- Re-save file in Excel if corrupted

---

## 📚 Documentation

- **User Guide**: [WEB_APP_USER_GUIDE.txt](WEB_APP_USER_GUIDE.txt)
- **Deployment Guide**: [DEPLOYMENT_GUIDE_WEB.txt](DEPLOYMENT_GUIDE_WEB.txt)
- **Desktop Version**: See main [README.md](README.md)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork repository
2. Create feature branch
3. Make changes
4. Test locally
5. Submit PR

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 💬 Support

### In-App Help
Click "Help" tab in the app for:
- How to use
- Settings explained
- Understanding results
- Troubleshooting

### Team Support
- 📧 Email: support@company.com
- 💬 Slack: #gis-team
- 📚 [Full Documentation](https://github.com)

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- [OpenStreetMap](https://www.openstreetmap.org/) - Map data
- [Nominatim](https://nominatim.org/) - Geocoding service
- [Photon](https://photon.komoot.io/) - Backup geocoding
- [Streamlit](https://streamlit.io/) - Web framework

---

## 🎯 Related Projects

- **Desktop Scripts**: Full Python toolkit for large data processing
- **Google Maps Version**: High-accuracy geocoding (paid)
- **API Integration**: RESTful API wrapper (coming soon)

---

**Made with ❤️ by Team GIS**

**Last Updated:** November 2024
