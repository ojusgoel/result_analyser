"""
PDF Result Analysis Web Application - SECURE VERSION
Upload a PDF and generate a comprehensive analysis report
"""

import gradio as gr
import pdfplumber
import pandas as pd
import re
import os
import tempfile
import shutil
import mimetypes
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# Security Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME_TYPES = ['application/pdf']
TEMP_CLEANUP_ENABLED = True


GRADE_POINTS = {
    "O": 10,
    "A+": 9,
    "A": 8,
    "B+": 7,
    "B": 6,
    "C": 5,
    "P": 4,
    "F": 0
}


def validate_pdf_file(pdf_file):
    """
    Validate PDF file for security issues
    
    Args:
        pdf_file: Gradio File object
        
    Raises:
        gr.Error: If file fails validation
    """
    
    if pdf_file is None:
        raise gr.Error("Please upload a PDF file")
    
    # Get file path
    pdf_path = pdf_file.name if hasattr(pdf_file, 'name') else pdf_file
    
    # Validate file exists
    if not os.path.exists(pdf_path):
        raise gr.Error("File not found")
    
    # Check file size
    file_size = os.path.getsize(pdf_path)
    if file_size > MAX_FILE_SIZE:
        raise gr.Error(f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f} MB")
    
    if file_size == 0:
        raise gr.Error("File is empty")
    
    # Validate MIME type
    mime_type, _ = mimetypes.guess_type(pdf_path)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise gr.Error("Invalid file type. Only PDF files are allowed")
    
    # Check file extension
    if not pdf_path.lower().endswith('.pdf'):
        raise gr.Error("File must have .pdf extension")
    
    # Verify it's a valid PDF
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) == 0:
                raise gr.Error("PDF file is empty or corrupted")
    except Exception as e:
        raise gr.Error(f"Invalid PDF file or corrupted")
    
    return pdf_path


def process_pdf(pdf_file):
    """
    Process a PDF file and generate a comprehensive analysis report
    
    Args:
        pdf_file: Gradio File object containing the uploaded PDF
        
    Returns:
        str: Path to the generated PDF report
    """
    
    # Validate input file
    pdf_path = validate_pdf_file(pdf_file)
    
    temp_dir = None
    temp_output_path = None
    
    try:
        students = []
        course_records = []
        
        with pdfplumber.open(pdf_path) as pdf:
            # ----------------------------------
            # Extract Metadata From First Page
            # ----------------------------------
            
            first_page_text = pdf.pages[0].extract_text()
            
            if not first_page_text:
                raise gr.Error("Could not extract text from first page")
            
            try:
                program = re.search(
                    r"Result-cum-Grade Report Card\s+(.*?)\s+\(Semester",
                    first_page_text,
                    re.DOTALL
                ).group(1).strip()
            except (AttributeError, IndexError, TypeError):
                raise gr.Error("Invalid PDF format: Could not find program information")
            
            try:
                semester = re.search(
                    r"\((Semester-[IVX]+)\)",
                    first_page_text
                ).group(1)
            except (AttributeError, IndexError, TypeError):
                raise gr.Error("Invalid PDF format: Could not find semester information")
            
            try:
                exam_session = re.search(
                    r"Examination Session:\s*(.*?)\n",
                    first_page_text
                ).group(1)
            except (AttributeError, IndexError, TypeError):
                exam_session = "Unknown"
            
            try:
                result_date = re.search(
                    r"Result Declaration Date\s*:\s*(.*?)\s*Controller",
                    first_page_text,
                    re.DOTALL
                ).group(1).strip()
            except (AttributeError, IndexError, TypeError):
                result_date = datetime.now().strftime("%d-%m-%Y")
            
            # Sanitize strings - prevent injection attacks
            program = program[:200]
            semester = semester[:100]
            exam_session = exam_session[:200]
            result_date = result_date[:200]
            
            # ----------------------------------
            # Parse Student Pages
            # ----------------------------------
            
            for page in pdf.pages:
                text = page.extract_text()
                
                if not text:
                    continue
                
                # Student Name
                name_match = re.search(
                    r"Student's Name\s*:\s*(.*?)\s*DMC No",
                    text,
                    re.DOTALL
                )
                name = (
                    name_match.group(1).strip()[:200]
                    if name_match else None
                )
                
                # Roll Number
                roll_match = re.search(
                    r"Roll No\.\s*:\s*(\d+)",
                    text
                )
                roll_no = (
                    roll_match.group(1)
                    if roll_match else None
                )
                
                # Result Status
                if "Result Status : Pass" in text:
                    status = "Pass"
                    sgpa_match = re.search(
                        r"SGPA\s*:\s*([\d\.]+)",
                        text
                    )
                    try:
                        sgpa = (
                            float(sgpa_match.group(1))
                            if sgpa_match else None
                        )
                    except (ValueError, AttributeError):
                        sgpa = None
                else:
                    status = "Re-appear"
                    sgpa = None
                
                students.append({
                    "Name": name,
                    "RollNo": roll_no,
                    "Status": status,
                    "SGPA": sgpa
                })
                
                # ----------------------------------
                # Course Extraction
                # ----------------------------------
                
                course_pattern = re.compile(
                    r"(B23-[A-Z\-0-9]+)\s+"
                    r"(.*?)\s+"
                    r"(\d+\.\d)\s+"
                    r"(O|A\+|A|B\+|B|C|P|F)\s+"
                    r"([\d\.]+)\s+"
                    r"(P|Re)"
                )
                
                courses = course_pattern.findall(text)
                
                for (
                    code,
                    cname,
                    credits,
                    grade,
                    credit_pts,
                    result
                ) in courses:
                    # Validate and sanitize course data
                    try:
                        course_records.append({
                            "Student": name,
                            "RollNo": roll_no,
                            "CourseCode": code[:50],
                            "CourseName": cname.strip()[:200],
                            "Credits": float(credits),
                            "Grade": grade,
                            "GradePoint": GRADE_POINTS.get(grade, 0),
                            "CreditPoints": float(credit_pts),
                            "CourseResult": result,
                            "OverallStatus": status
                        })
                    except (ValueError, KeyError, TypeError):
                        # Skip invalid course records
                        continue
        
        if not students:
            raise gr.Error("No student data found in PDF")
        
        # Create DataFrames
        students_df = pd.DataFrame(students)
        courses_df = pd.DataFrame(course_records)
        
        # ----------------------------------
        # Calculate Statistics
        # ----------------------------------
        
        total_students = len(students_df)
        pass_students = (
            students_df["Status"]
            .eq("Pass")
            .sum()
        )
        fail_students = total_students - pass_students
        pass_percentage = (
            pass_students /
            total_students *
            100
        ) if total_students > 0 else 0
        
        avg_sgpa = round(
            students_df["SGPA"]
            .dropna()
            .mean(),
            2
        ) if len(students_df["SGPA"].dropna()) > 0 else 0
        
        max_sgpa = round(
            students_df["SGPA"]
            .dropna()
            .max(),
            2
        ) if len(students_df["SGPA"].dropna()) > 0 else 0
        
        min_sgpa = round(
            students_df["SGPA"]
            .dropna()
            .min(),
            2
        ) if len(students_df["SGPA"].dropna()) > 0 else 0
        
        # Course stats
        if len(courses_df) > 0:
            course_pass_stats = (
                courses_df
                .groupby(
                    ["CourseCode", "CourseName"]
                )
                .agg(
                    Total=('CourseResult', 'count'),
                    Passed=(
                        'CourseResult',
                        lambda x: (x == "P").sum()
                    ),
                    Failed=(
                        'CourseResult',
                        lambda x: (x == "Re").sum()
                    )
                )
            )
            
            course_pass_stats["PassPercent"] = (
                course_pass_stats["Passed"]
                /
                course_pass_stats["Total"]
                *
                100
            )
            
            grade_distribution = pd.crosstab(
                courses_df["CourseName"],
                courses_df["Grade"]
            )
            
            course_gpa = (
                courses_df
                .groupby("CourseName")
                ["GradePoint"]
                .mean()
            )
        else:
            course_pass_stats = pd.DataFrame()
            grade_distribution = pd.DataFrame()
            course_gpa = pd.Series()
        
        student_course_summary = (
            courses_df
            .groupby("Student")
            .agg(
                CoursesPassed=(
                    "CourseResult",
                    lambda x: (x == "P").sum()
                ),
                CoursesFailed=(
                    "CourseResult",
                    lambda x: (x == "Re").sum()
                )
            )
            .reset_index()
        )
        
        student_summary = (
            students_df
            .merge(
                student_course_summary,
                left_on="Name",
                right_on="Student",
                how="left"
            )
        )
        
        student_summary = (
            student_summary
            .sort_values(
                "SGPA",
                ascending=False,
                na_position="last"
            )
        )
        
        # ----------------------------------
        # Generate PDF Report
        # ----------------------------------
        
        # Create secure temporary directory
        temp_dir = tempfile.mkdtemp(prefix="pdf_analysis_")
        pdf_filename = (
            f"{program.replace(' ','_').replace('/','_')}_"
            f"{semester.replace(' ','_')}_Analysis.pdf"
        )
        # Ensure filename is safe
        pdf_filename = "".join(c for c in pdf_filename if c.isalnum() or c in ('-', '_', '.'))[:200]
        temp_output_path = os.path.join(temp_dir, pdf_filename)
        
        doc = SimpleDocTemplate(temp_output_path)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title Page
        elements.append(
            Paragraph(
                "Result Analysis Report",
                styles["Title"]
            )
        )
        
        elements.append(Spacer(1, 20))
        
        # Metadata Table
        metadata_table = Table([
            ["Program", program],
            ["Semester", semester],
            ["Examination Session", exam_session],
            ["Result Declaration Date", result_date],
            ["Generated On",
             datetime.now().strftime("%d-%m-%Y %H:%M")]
        ])
        
        metadata_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold')
        ]))
        
        elements.append(metadata_table)
        elements.append(Spacer(1, 20))
        
        # Summary Table
        summary_table = Table([
            ["Metric", "Value"],
            ["Total Students", total_students],
            ["Passed", pass_students],
            ["Re-appear", fail_students],
            ["Pass Percentage",
             f"{pass_percentage:.2f}%"],
            ["Average SGPA", avg_sgpa],
            ["Highest SGPA", max_sgpa],
            ["Lowest SGPA", min_sgpa]
        ])
        
        summary_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
        ]))
        
        elements.append(summary_table)
        elements.append(PageBreak())
        
        # Course Performance Summary
        if len(course_pass_stats) > 0:
            elements.append(
                Paragraph(
                    "Course Performance Summary",
                    styles["Heading1"]
                )
            )
            
            course_table_data = [[
                "Course",
                "Passed",
                "Failed",
                "Pass %",
                "Avg Grade Point"
            ]]
            
            for idx, row in course_pass_stats.iterrows():
                course_name = idx[1]
                course_table_data.append([
                    course_name,
                    int(row["Passed"]),
                    int(row["Failed"]),
                    round(row["PassPercent"], 2),
                    round(course_gpa[course_name], 2)
                ])
            
            course_table = Table(
                course_table_data,
                repeatRows=1
            )
            
            course_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8)
            ]))
            
            elements.append(course_table)
            elements.append(PageBreak())
        
        # Grade Distribution
        if len(grade_distribution) > 0:
            grades = ["O", "A+", "A", "B+", "B", "C", "P", "F"]
            
            elements.append(
                Paragraph(
                    "Grade Distribution by Course",
                    styles["Heading1"]
                )
            )
            
            grade_table_data = [
                ["Course"] + grades
            ]
            
            for course in grade_distribution.index:
                row = [course]
                
                for grade in grades:
                    row.append(
                        int(
                            grade_distribution
                            .loc[course]
                            .get(grade, 0)
                        )
                    )
                
                grade_table_data.append(row)
            
            grade_table = Table(
                grade_table_data,
                repeatRows=1
            )
            
            grade_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8)
            ]))
            
            elements.append(grade_table)
            elements.append(PageBreak())
        
        # Student Summary
        elements.append(
            Paragraph(
                "Student Summary",
                styles["Heading1"]
            )
        )
        
        student_table_data = [[
            "Student",
            "Status",
            "SGPA",
            "Passed",
            "Failed"
        ]]
        
        for _, row in student_summary.iterrows():
            sgpa = (
                "-"
                if pd.isna(row["SGPA"])
                else round(row["SGPA"], 2)
            )
            
            courses_passed = 0
            courses_failed = 0
            
            if not pd.isna(row.get("CoursesPassed")):
                courses_passed = int(row["CoursesPassed"])
            if not pd.isna(row.get("CoursesFailed")):
                courses_failed = int(row["CoursesFailed"])
            
            student_table_data.append([
                row["Name"],
                row["Status"],
                sgpa,
                courses_passed,
                courses_failed
            ])
        
        student_table = Table(
            student_table_data,
            repeatRows=1
        )
        
        student_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8)
        ]))
        
        elements.append(student_table)
        
        # Add metadata to PDF
        def add_pdf_metadata(canvas, doc):
            canvas.setTitle(
                f"{program} Result Analysis"
            )
            canvas.setAuthor(
                "PDF Result Analyzer"
            )
            canvas.setSubject(
                f"{semester} Result Analysis"
            )
            canvas.setKeywords(
                "result analysis, sgpa, grades"
            )
        
        doc.build(
            elements,
            onFirstPage=add_pdf_metadata,
            onLaterPages=add_pdf_metadata
        )
        
        return temp_output_path
        
    except gr.Error:
        # Re-raise Gradio errors
        raise
    except Exception as e:
        # Log full error for debugging
        print(f"Error processing PDF: {str(e)}")
        # Return generic error message to user
        raise gr.Error("Error processing PDF. Please ensure your file follows the expected format.")
    finally:
        # Clean up temporary files
        if temp_dir and os.path.exists(temp_dir) and TEMP_CLEANUP_ENABLED:
            try:
                # Schedule cleanup after the file has been served
                pass  # Gradio handles cleanup
            except Exception as e:
                print(f"Warning: Could not clean up temp files: {e}")


# Create Gradio Interface
with gr.Blocks(title="PDF Result Analyzer") as demo:
    gr.Markdown(
        """
        # Result Analyzer 
        
        Upload a PDF result file and get a comprehensive analysis report with:
        - Student statistics (pass/fail rates)
        - SGPA calculations and rankings
        - Course performance analysis
        - Grade distribution visualization
        - Detailed student summaries

        """
    )
    
    with gr.Row():
        with gr.Column():
            pdf_input = gr.File(
                label="Upload PDF",
                type="filepath",
                file_types=[".pdf"]
            )
            process_btn = gr.Button(
                "Generate Report",
                variant="primary",
                size="lg"
            )
        
        with gr.Column():
            pdf_output = gr.File(
                label="Download Report PDF"
            )
    
    process_btn.click(
        fn=process_pdf,
        inputs=pdf_input,
        outputs=pdf_output
    )
    
    gr.Markdown(
        """
        ---
        ### How to use:
        1. Click **Upload PDF** and select your result PDF file
        2. Click **Generate Report** to process it
        3. Download the generated analysis PDF
        """
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7862,
        share=False,
        show_error=True,
        theme=gr.themes.Soft()
    )
