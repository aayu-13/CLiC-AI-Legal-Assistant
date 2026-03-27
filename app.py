from flask import Flask, request, jsonify, render_template
from search import search  
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os
import io
from datetime import datetime
from flask import send_file, request
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

app = Flask(__name__)

# 🔥 Home route (loads your HTML)
@app.route("/")
def home():
    return render_template("index.html")


# 🔥 API endpoint for AI suggestions
@app.route("/predict", methods=["POST"])
def predict():
    description = request.form.get("description")

    if not description:
        return jsonify([])

    results = search(description)

    # 🔥 Convert to UI format
    formatted = []
    for r in results:
        formatted.append({
            "section_no": r["section_no"],
            "offense": r["offense"],
            "description": r["description"],
            "score": r["score"]
        })

    return jsonify(formatted)

@app.route('/submit_fir', methods=['POST'])
def submit_fir():
    # Capture Form Data
    user_name = request.form.get('name', 'N/A')
    district = request.form.get('district', 'N/A')
    ps = request.form.get('police_station', 'N/A')
    location = request.form.get('location', 'N/A')
    inc_date = request.form.get('incident_date', 'N/A')
    inc_time = request.form.get('incident_time', 'N/A')
    incident_desc = request.form.get('description', 'N/A')
    selected_bns = request.form.getlist('bns_sections')
    
    uploaded_files = request.files.getlist('evidence_files')
    evidence_names = [f.filename for f in uploaded_files if f.filename]

    # 🔥 Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)

    elements = []
    styles = getSampleStyleSheet()
    body_style = styles['Normal']
    body_style.leading = 14

    # TITLE
    elements.append(Paragraph("<b>FIRST INFORMATION REPORT (F.I.R.)</b>", styles['Title']))
    elements.append(Paragraph("<center>(Under Bharatiya Nagarik Suraksha Sanhita - BNSS)</center>", styles['Normal']))
    elements.append(Spacer(1, 20))

    # META
    current_year = datetime.now().year

    meta_data = [
        [Paragraph(f"<b>1. District:</b> {district}", body_style), Paragraph(f"<b>P.S.:</b> {ps}", body_style)],
        [Paragraph(f"<b>2. FIR No:</b> {current_year}/BNS/001", body_style), Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}", body_style)]
    ]

    meta_table = Table(meta_data, colWidths=[250, 250])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10)
    ]))

    elements.append(meta_table)
    elements.append(Spacer(1, 15))

    # DETAILS
    elements.append(Paragraph(f"<b>3. Complainant Name:</b> {user_name}", body_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(f"<b>4. Date & Time:</b> {inc_date} at {inc_time}", body_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(f"<b>5. Location:</b> {location}", body_style))
    elements.append(Spacer(1, 8))

    bns_display = ", ".join(selected_bns) if selected_bns else "None Selected"
    elements.append(Paragraph(f"<b>6. BNS Sections:</b> {bns_display}", body_style))
    elements.append(Spacer(1, 15))

    # INCIDENT
    elements.append(Paragraph("<b>7. Brief Facts:</b>", body_style))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(incident_desc, body_style))
    elements.append(Spacer(1, 20))

    # EVIDENCE
    elements.append(Paragraph("<b>8. Evidence:</b>", body_style))
    elements.append(Spacer(1, 5))

    if evidence_names:
        table_data = [["S.No", "Filename", "Status"]]
        for i, name in enumerate(evidence_names, 1):
            table_data.append([str(i), name, "Uploaded"])

        ev_table = Table(table_data, colWidths=[50, 300, 150])
        ev_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), (0.9,0.9,0.9)),
            ('GRID', (0,0), (-1,-1), 0.5, (0,0,0)),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
        ]))

        elements.append(ev_table)
    else:
        elements.append(Paragraph("No evidence attached.", body_style))

    # SIGNATURE
    elements.append(Spacer(1, 60))

    sig_table = Table([
        ["Signature of Complainant", "Station House Officer (SHO)"]
    ], colWidths=[250, 250])

    elements.append(sig_table)

    # Build PDF
    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"BNS_FIR_{user_name}.pdf",
        mimetype='application/pdf'
    )

# 🔥 Run server
if __name__ == "__main__":
    app.run(debug=True)