import io
import os
import re
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

try:
    import pandas as pd
    import pdfplumber
    from flask import Flask, request, send_file
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except ImportError as e:
    print(f"IMPORT ERROR: {e}", flush=True)
    raise

app = Flask(__name__)

MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
ALLOWED_EXTENSIONS = {".pdf"}
GRADE_POINTS = {
    "O": 10,
    "A+": 9,
    "A": 8,
    "B+": 7,
    "B": 6,
    "C": 5,
    "P": 4,
    "F": 0,
}


def _sanitize_filename(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    return safe[:150] or "report.pdf"


def _extract_and_build_report(pdf_path: str, output_path: str) -> None:
    students = []
    course_records = []

    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            raise ValueError("PDF has no pages")

        first_page_text = pdf.pages[0].extract_text() or ""

        program_match = re.search(
            r"Result-cum-Grade Report Card\s+(.*?)\s+\(Semester", first_page_text, re.DOTALL
        )
        semester_match = re.search(r"\((Semester-[IVX]+)\)", first_page_text)
        session_match = re.search(r"Examination Session:\s*(.*?)\n", first_page_text)
        date_match = re.search(
            r"Result Declaration Date\s*:\s*(.*?)\s*Controller", first_page_text, re.DOTALL
        )

        program = (program_match.group(1).strip() if program_match else "Unknown Program")[:200]
        semester = (semester_match.group(1) if semester_match else "Semester-Unknown")[:100]
        exam_session = (session_match.group(1) if session_match else "Unknown")[:200]
        result_date = (
            date_match.group(1).strip() if date_match else datetime.now().strftime("%d-%m-%Y")
        )[:200]

        course_pattern = re.compile(
            r"(B23-[A-Z\-0-9]+)\s+"
            r"(.*?)\s+"
            r"(\d+\.\d)\s+"
            r"(O|A\+|A|B\+|B|C|P|F)\s+"
            r"([\d\.]+)\s+"
            r"(P|Re)"
        )

        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            name_match = re.search(r"Student's Name\s*:\s*(.*?)\s*DMC No", text, re.DOTALL)
            roll_match = re.search(r"Roll No\.\s*:\s*(\d+)", text)

            name = (name_match.group(1).strip() if name_match else "Unknown")[:200]
            roll_no = roll_match.group(1) if roll_match else ""

            if "Result Status : Pass" in text:
                status = "Pass"
                sgpa_match = re.search(r"SGPA\s*:\s*([\d\.]+)", text)
                sgpa = float(sgpa_match.group(1)) if sgpa_match else None
            else:
                status = "Re-appear"
                sgpa = None

            students.append({"Name": name, "RollNo": roll_no, "Status": status, "SGPA": sgpa})

            for code, cname, credits, grade, credit_pts, result in course_pattern.findall(text):
                try:
                    course_records.append(
                        {
                            "Student": name,
                            "RollNo": roll_no,
                            "CourseCode": code[:50],
                            "CourseName": cname.strip()[:200],
                            "Credits": float(credits),
                            "Grade": grade,
                            "GradePoint": GRADE_POINTS.get(grade, 0),
                            "CreditPoints": float(credit_pts),
                            "CourseResult": result,
                            "OverallStatus": status,
                        }
                    )
                except ValueError:
                    continue

    if not students:
        raise ValueError("No student data found in PDF")

    students_df = pd.DataFrame(students)
    courses_df = pd.DataFrame(course_records) if course_records else pd.DataFrame()

    total_students = len(students_df)
    pass_students = int(students_df["Status"].eq("Pass").sum())
    fail_students = total_students - pass_students
    pass_percentage = (pass_students / total_students * 100) if total_students else 0

    sgpa_series = students_df["SGPA"].dropna()
    avg_sgpa = round(float(sgpa_series.mean()), 2) if not sgpa_series.empty else 0
    max_sgpa = round(float(sgpa_series.max()), 2) if not sgpa_series.empty else 0
    min_sgpa = round(float(sgpa_series.min()), 2) if not sgpa_series.empty else 0

    student_summary = students_df.copy()
    if not courses_df.empty:
        student_course_summary = (
            courses_df.groupby("Student")
            .agg(
                CoursesPassed=("CourseResult", lambda x: (x == "P").sum()),
                CoursesFailed=("CourseResult", lambda x: (x == "Re").sum()),
            )
            .reset_index()
        )
        student_summary = student_summary.merge(
            student_course_summary, left_on="Name", right_on="Student", how="left"
        )
    else:
        student_summary["CoursesPassed"] = 0
        student_summary["CoursesFailed"] = 0

    student_summary = student_summary.sort_values("SGPA", ascending=False, na_position="last")

    styles = getSampleStyleSheet()
    elements = []
    doc = SimpleDocTemplate(output_path)

    elements.append(Paragraph("Result Analysis Report", styles["Title"]))
    elements.append(Spacer(1, 20))

    metadata_table = Table(
        [
            ["Program", program],
            ["Semester", semester],
            ["Examination Session", exam_session],
            ["Result Declaration Date", result_date],
            ["Generated On", datetime.now().strftime("%d-%m-%Y %H:%M")],
        ]
    )
    metadata_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ]
        )
    )
    elements.append(metadata_table)
    elements.append(Spacer(1, 20))

    summary_table = Table(
        [
            ["Metric", "Value"],
            ["Total Students", total_students],
            ["Passed", pass_students],
            ["Re-appear", fail_students],
            ["Pass Percentage", f"{pass_percentage:.2f}%"],
            ["Average SGPA", avg_sgpa],
            ["Highest SGPA", max_sgpa],
            ["Lowest SGPA", min_sgpa],
        ]
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(PageBreak())

    elements.append(Paragraph("Student Summary", styles["Heading1"]))
    student_table_data = [["Student", "Status", "SGPA", "Passed", "Failed"]]
    for _, row in student_summary.iterrows():
        sgpa_val = "-" if pd.isna(row.get("SGPA")) else round(float(row["SGPA"]), 2)
        passed = 0 if pd.isna(row.get("CoursesPassed")) else int(row.get("CoursesPassed", 0))
        failed = 0 if pd.isna(row.get("CoursesFailed")) else int(row.get("CoursesFailed", 0))
        student_table_data.append(
            [row.get("Name", ""), row.get("Status", ""), sgpa_val, passed, failed]
        )

    student_table = Table(student_table_data, repeatRows=1)
    student_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(student_table)

    doc.build(elements)


def _html_page(message: str = "") -> str:
    msg = (
        f"<p style='color:#b91c1c;font-weight:600'>{message}</p>" if message else ""
    )
    return f"""
<!doctype html>
<html>
  <head>
    <meta charset='utf-8' />
    <meta name='viewport' content='width=device-width, initial-scale=1' />
    <title>PDF Result Analyzer</title>
    <style>
      body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; background:#f3f4f6; margin:0; }}
      .wrap {{ max-width: 680px; margin: 48px auto; background:#fff; border-radius:16px; padding:28px; box-shadow:0 8px 30px rgba(0,0,0,.08); }}
      h1 {{ margin:0 0 12px; font-size: 28px; }}
      p {{ color:#374151; }}
      input[type=file] {{ margin: 12px 0 16px; }}
      button {{ background:#111827; color:#fff; border:0; padding:10px 16px; border-radius:10px; cursor:pointer; font-weight: 500; }}
      button:hover {{ background:#374151; }}
      .hint {{ font-size: 13px; color:#6b7280; margin-top:10px; }}
    </style>
  </head>
  <body>
    <div class='wrap'>
      <h1>📊 PDF Result Analyzer</h1>
      <p>Upload your university result PDF and download the generated analysis report.</p>
      {msg}
      <form method='POST' enctype='multipart/form-data'>
        <input type='file' name='pdf' accept='application/pdf' required />
        <br />
        <button type='submit'>🚀 Generate Report</button>
      </form>
      <p class='hint'>⚡ Max file size: 15 MB. Runs on Vercel serverless.</p>
    </div>
  </body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    try:
        return _html_page(), 200
    except Exception as e:
        print(f"GET / ERROR: {e}", flush=True)
        return _html_page(f"Error: {str(e)}"), 500


@app.route("/", methods=["POST"])
def process():
    try:
        uploaded = request.files.get("pdf")
        if uploaded is None or not uploaded.filename:
            return _html_page("Please choose a PDF file."), 400

        ext = Path(uploaded.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            return _html_page("Only .pdf files are allowed."), 400

        uploaded.stream.seek(0, io.SEEK_END)
        size = uploaded.stream.tell()
        uploaded.stream.seek(0)
        if size <= 0 or size > MAX_FILE_SIZE:
            return (
                _html_page(
                    f"File size must be between 1 byte and {MAX_FILE_SIZE // (1024 * 1024)} MB."
                ),
                400,
            )

        temp_dir = tempfile.mkdtemp(prefix="vercel_pdf_")
        in_path = os.path.join(temp_dir, "input.pdf")
        out_name = _sanitize_filename(Path(uploaded.filename).stem + "_Analysis.pdf")
        out_path = os.path.join(temp_dir, out_name)

        try:
            uploaded.save(in_path)
            _extract_and_build_report(in_path, out_path)

            return send_file(out_path, as_attachment=True, download_name=out_name)

        except Exception as exc:
            error_msg = f"Processing failed: {str(exc)}"
            print(f"ERROR: {error_msg}", flush=True)
            return _html_page(error_msg), 400

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    except Exception as e:
        print(f"POST / ERROR: {e}", flush=True)
        return _html_page(f"Error: {str(e)}"), 500

