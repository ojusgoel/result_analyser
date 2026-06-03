# PDF Result Analyzer - Web Application (Secure Edition)

A web-based application that analyzes PDF result files and generates comprehensive analysis reports with built-in security features.

**Now deployable on Vercel! 🚀**

## Quick Start - Local Development

```bash
pip install -r requirements.txt
python app.py
```
→ Open `http://localhost:7861`

## Deploy on Vercel

### Prerequisites
1. [Vercel account](https://vercel.com/signup) (free)
2. [Git](https://git-scm.com/downloads) installed
3. GitHub account (to push code)

### Step-by-Step Deployment

#### 1. **Push code to GitHub**

```bash
cd /home/ojusg/Desktop/Mom

# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit: PDF Result Analyzer"

# Create public GitHub repo at https://github.com/new
# Then push (replace YOUR_USERNAME and YOUR_REPO):
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

#### 2. **Deploy on Vercel**

**Option A: From CLI (Easiest)**
```bash
npm i -g vercel
vercel login
cd /home/ojusg/Desktop/Mom
vercel --prod
```

**Option B: From Web Dashboard**
1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repo
3. Select root directory: `/` (default is fine)
4. Click **Deploy**

#### 3. **Access your app**

Vercel will give you a URL like `https://your-app-xyz.vercel.app`

---

## Security First

This version includes enhanced security measures:
- ✅ File size limits (15 MB max for Vercel)
- ✅ PDF validation and integrity checks
- ✅ Input sanitization and string limits
- ✅ Safe temporary file handling
- ✅ Secure error handling (no data leakage)
- ✅ Automatic cleanup of sensitive files
- ✅ No data persistence

See [SECURITY.md](SECURITY.md) for detailed security information.

## Features

- **PDF Upload**: Simple and secure file upload interface
- **Automatic Parsing**: Extracts student data, course information, and grades from PDF
- **Comprehensive Analysis**: Generates detailed statistics including:
  - Student pass/fail statistics
  - SGPA calculations
  - Course-wise pass percentages
  - Grade distribution
  - Top performers
  - Individual student summaries
- **Professional PDF Report**: Creates formatted PDF with all analysis
- **Serverless**: Runs on Vercel serverless infrastructure

## File Structures

### Local Development
```
Mom/
├── app.py              # Gradio UI (localhost only)
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── SECURITY.md        # Security documentation
├── vercel.json        # Vercel config
├── runtime.txt        # Python version
└── api/
    └── index.py       # Vercel serverless function
```

## Configuration for Vercel

**File Size Limits:**
- Local: 50 MB
- Vercel: 15 MB (serverless memory constraints)

Edit `api/index.py` line ~13:
```python
MAX_FILE_SIZE = 15 * 1024 * 1024  # Change this value
```

## Troubleshooting

### Vercel Deployment Issues

**🔴 "Build failed"**
- Ensure `requirements.txt` exists
- Check Python version compatibility
- Verify `api/index.py` has no syntax errors

**🔴 "Timeout error"**
- Large PDFs may timeout
- Reduce `MAX_FILE_SIZE` in `api/index.py`
- Already set to 15 MB for serverless limits

**🔴 "502 Bad Gateway"**
- Check Vercel logs: `vercel logs`
- Ensure dependencies are installed
- Verify `api/index.py` has proper error handling

### Local Development Issues

**Port already in use**
- Change port in `app.py`: `server_port=7862`

**PDF parsing errors**
- Ensure PDF format matches requirements (see below)

**Installation errors**
- Run `pip install -r requirements.txt` with elevated privileges

## PDF Format Requirements

The application expects PDF files in the following format:
- **Title**: "Result-cum-Grade Report Card"
- **Contains**: Program name and Semester information
- **Metadata**: Examination Session and Result Declaration Date
- **Per Student**:
  - Student's Name
  - Roll No.
  - Result Status (Pass/Re-appear)
  - SGPA (for passing students)
  - Course details (Course Code, Name, Grade, etc.)

## Output

The generated PDF report includes:
- Title and metadata page
- Executive summary with statistics
- Course performance analysis
- Grade distribution by course
- Detailed student summary

## Development

To modify locally:
1. Edit `app.py` (Gradio UI) or `api/index.py` (Vercel backend)
2. Test with `python app.py`
3. Push to GitHub
4. Vercel automatically redeploys on `git push`

## Performance Notes

| Metric | Local | Vercel |
|--------|-------|--------|
| **Max File Size** | 50 MB | 15 MB |
| **Processing Time** | ~1-3 min | ~2-5 min |
| **Timeout** | N/A | 120 seconds |
| **Memory** | System | 1024 MB |

## Browser Compatibility

Works with:
- Chrome/Chromium
- Firefox
- Safari
- Edge

## System Requirements

### Local
- Python 3.8+
- 500 MB free disk space
- 2 GB RAM (minimum)

### Vercel
- No local requirements (runs in cloud)
- Any modern browser

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Show upload form |
| `/` | POST | Process PDF, return analysis |

## Support

For issues:
1. Check this README
2. Review [SECURITY.md](SECURITY.md)
3. Verify PDF format requirements
4. Check error messages in browser / terminal

## License

This application is for educational purposes.

---

**Created**: June 2026
**Version**: 1.0 (Secure Edition + Vercel Ready)
**Status**: Production Ready ✅

A web-based application that analyzes PDF result files and generates comprehensive analysis reports with built-in security features.

## Security First

This version includes enhanced security measures:
- ✅ File size limits (50 MB max)
- ✅ PDF validation and integrity checks
- ✅ Input sanitization and string limits
- ✅ Safe temporary file handling
- ✅ Secure error handling (no data leakage)
- ✅ Automatic cleanup of sensitive files
- ✅ No data persistence

See [SECURITY.md](SECURITY.md) for detailed security information.

## Features

- **PDF Upload**: Simple and secure file upload interface
- **Automatic Parsing**: Extracts student data, course information, and grades from PDF
- **Comprehensive Analysis**: Generates detailed statistics including:
  - Student pass/fail statistics
  - SGPA calculations
  - Course-wise pass percentages
  - Grade distribution
  - Top performers
  - Individual student summaries
- **Professional PDF Report**: Creates formatted PDF with all analysis
- **Security**: All inputs validated, no data logged or stored

## Installation

1. **Install Python 3.8 or higher** (if not already installed)

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Or install individually:
   ```bash
   pip install gradio pdfplumber pandas reportlab
   ```

## Usage

1. **Start the web application**:
   ```bash
   python app.py
   ```

2. **Open in browser**:
   - The app will start on `http://localhost:7861`
   - Open this URL in your web browser

3. **Use the interface**:
   - Click "📁 Upload PDF" and select your result PDF file
   - Click "🔄 Generate Report"
   - Download the generated analysis PDF

## PDF Format Requirements

The application expects PDF files in the following format:
- Title: "Result-cum-Grade Report Card"
- Contains: Program name and Semester information
- Metadata: Examination Session and Result Declaration Date
- Student pages with:
  - Student's Name
  - Roll No.
  - Result Status (Pass/Re-appear)
  - SGPA (for passing students)
  - Course details (Course Code, Name, Grade, etc.)

## Output

The generated PDF report includes:
- Title and metadata page
- Executive summary with statistics
- Course performance analysis
- Grade distribution by course
- Detailed student summary

## File Structure

```
Mom/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── SECURITY.md        # Security documentation
└── [sample PDFs]      # Your PDF files to analyze
```

## Troubleshooting

### Port already in use
Change the port in `app.py` (modify `server_port=7861`)

### PDF parsing errors
Ensure your PDF follows the expected format. Check the format requirements section.

### Installation errors
Run `pip install -r requirements.txt` again with elevated privileges if needed

### Gradio warnings
These are safe and do not affect functionality. The app works correctly despite warnings.

## Configuration

Edit `app.py` to modify:
- `MAX_FILE_SIZE`: Maximum upload size (default: 50 MB)
- `server_port`: Web server port (default: 7861)
- `TEMP_CLEANUP_ENABLED`: Auto-delete temp files (default: True)

## Security Features

- **File Validation**: Size, type, extension, and integrity checks
- **Input Sanitization**: All text limited to safe lengths
- **Error Handling**: Generic messages to users, detailed logs server-only
- **Temporary Files**: Securely created and deleted after processing
- **No Data Retention**: Nothing stored between sessions

For more details, see [SECURITY.md](SECURITY.md)

## Development

To modify the application:
- Edit `app.py` for logic or interface changes
- Update `requirements.txt` if adding new packages
- Restart the application for changes to take effect

## Performance Notes

- Processing speed depends on PDF size
- Large PDFs (30+ MB) may take 2-3 minutes
- Memory usage is optimized for large datasets

## Browser Compatibility

Works with:
- Chrome/Chromium
- Firefox
- Safari
- Edge

## System Requirements

- Python 3.8+
- 500 MB free disk space
- 2 GB RAM (minimum)

## Support

For issues or questions:
1. Check this README
2. Review [SECURITY.md](SECURITY.md)
3. Verify PDF format requirements
4. Check error messages in terminal

## License

This application is for educational purposes.

---

**Created**: June 2026
**Version**: 1.0 (Secure Edition)
**Status**: Production Ready

