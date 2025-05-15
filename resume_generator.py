import pdfkit
import base64
from PIL import Image
import io
import qrcode
import os

def generate_resume(data, photo=None):
    photo_html = ""
    qr_html = ""

    # 1. Handle Profile Photo
    if photo is not None:
        image = Image.open(photo)
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        photo_html = f'<img src="data:image/png;base64,{img_str}" width="100" height="100" style="float:right;"/>'

    # 2. Handle QR Code
    if data.get("linkedin"):
        qr = qrcode.make(data["linkedin"])
        qr_buffer = io.BytesIO()
        qr.save(qr_buffer, format="PNG")
        qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()
        qr_html = f'<div style="margin-top:20px;"><strong>Portfolio / LinkedIn:</strong><br><img src="data:image/png;base64,{qr_base64}" width="100" height="100"/></div>'

    # 3. Preprocess education and experience to replace newlines
    education_html = data['education'].replace('\n', '<br>')
    experience_html = data['experience'].replace('\n', '<br>')

    # 4. Resume HTML
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 30px; }}
            .section {{ margin-bottom: 20px; }}
            h2 {{ border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
        </style>
    </head>
    <body>
        {photo_html}
        <h1>{data['name']}</h1>
        <p>Email: {data['email']}</p>
        <div class="section">
            <h2>Education</h2>
            <p>{education_html}</p>
        </div>
        <div class="section">
            <h2>Work Experience</h2>
            <p>{experience_html}</p>
        </div>
        <div class="section">
            <h2>Skills</h2>
            <p>{', '.join(data['extracted_skills'])}</p>
        </div>
        {qr_html}
    </body>
    </html>
    """

    # 5. Configure wkhtmltopdf path
    wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"  # Adjust this path if needed
    if not os.path.exists(wkhtmltopdf_path):
        wkhtmltopdf_path = "wkhtmltopdf"  # Fallback to PATH
        if not os.path.exists(wkhtmltopdf_path):
            raise OSError(
                "wkhtmltopdf executable not found. Please install wkhtmltopdf "
                "(https://wkhtmltopdf.org/downloads.html) or set the correct path in resume_generator.py."
            )
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

    # 6. Generate PDF
    path = "resume.pdf"
    try:
        pdfkit.from_string(html_content, path, configuration=config)
    except OSError as e:
        raise OSError(f"Failed to generate PDF: {str(e)}. Ensure wkhtmltopdf is installed and accessible.")
    
    return path