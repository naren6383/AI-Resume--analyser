import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_report(analysis_obj, resume_obj):
    """
    Generates a professional, print-ready PDF resume analysis report using ReportLab.
    Returns a bytes object of the generated PDF.
    """
    buffer = io.BytesIO()
    
    # Setup document with 0.5 inch (36 pt) margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # UI Theme Palette (Matching our clean modern light mode)
    primary_color = colors.HexColor('#0d6efd')  # Blue Accent
    dark_neutral = colors.HexColor('#212529')   # Dark text
    light_neutral = colors.HexColor('#f8f9fa')  # Card BG
    border_color = colors.HexColor('#dee2e6')   # Borders
    
    # Custom styles
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=primary_color,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#6c757d'),
        spaceAfter=15
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['BodyText'],
        fontSize=9.5,
        leading=13,
        textColor=dark_neutral,
        spaceAfter=5
    )
    
    bullet_style = ParagraphStyle(
        'ReportBullet',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13,
        textColor=dark_neutral,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    score_title_style = ParagraphStyle(
        'ScoreTitle',
        parent=styles['Normal'],
        fontSize=11,
        leading=13,
        textColor=colors.white,
        alignment=1  # Center
    )
    
    score_val_style = ParagraphStyle(
        'ScoreVal',
        parent=styles['Normal'],
        fontSize=32,
        leading=38,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        alignment=1  # Center
    )
    
    story = []
    
    # Report Header
    story.append(Paragraph("Resume Analysis Report", title_style))
    created_time = analysis_obj.created_at.strftime('%B %d, %Y - %I:%M %p')
    story.append(Paragraph(f"Resume: {resume_obj.filename}  |  Generated: {created_time}", subtitle_style))
    
    # Score Summary Table
    score_data = []
    if resume_obj.job_title:
        score_data = [
            [
                Paragraph("<b>Overall ATS Score</b>", score_title_style),
                Paragraph("<b>Job Description Match</b>", score_title_style)
            ],
            [
                Paragraph(f"{analysis_obj.ats_score}/100", score_val_style),
                Paragraph(f"{analysis_obj.job_match_percentage}%", score_val_style)
            ]
        ]
        col_widths = [270, 270]  # 540 total width
    else:
        score_data = [
            [Paragraph("<b>Overall ATS Score</b>", score_title_style)],
            [Paragraph(f"{analysis_obj.ats_score}/100", score_val_style)]
        ]
        col_widths = [540]
        
    score_table = Table(score_data, colWidths=col_widths)
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('INNERGRID', (0,0), (-1,-1), 1, colors.white),
        ('BOX', (0,0), (-1,-1), 1.5, primary_color),
    ]))
    
    story.append(score_table)
    story.append(Spacer(1, 12))
    
    # Target Job Details
    if resume_obj.job_title:
        story.append(Paragraph(f"<b>Target Role:</b> {resume_obj.job_title}", body_style))
        story.append(Spacer(1, 8))
        
    # Executive Summary
    story.append(Paragraph("Executive Summary", section_heading))
    story.append(Paragraph(analysis_obj.summary or "No executive summary available.", body_style))
    story.append(Spacer(1, 10))
    
    # Score Breakdown Table
    story.append(Paragraph("ATS Scoring Breakdown", section_heading))
    breakdown_data = [["Section / Category", "Score Contribution"]]
    category_labels = {
        "contact_info": "Contact Info completeness (Max 10)",
        "education": "Education & Degrees (Max 15)",
        "experience": "Professional Experience & Action Verbs (Max 20)",
        "skills": "Core Skills coverage (Max 25)",
        "projects_certifications": "Academic/Personal Projects & Certifications (Max 15)",
        "formatting": "Formatting layout, word count, and bullet usage (Max 15)"
    }
    
    score_breakdown = analysis_obj.get_score_breakdown()
    for cat, label in category_labels.items():
        val = score_breakdown.get(cat, 0)
        breakdown_data.append([label, f"{val} pts"])
        
    breakdown_table = Table(breakdown_data, colWidths=[390, 150])
    breakdown_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), light_neutral),
        ('TEXTCOLOR', (0,0), (-1,0), primary_color),
        ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,1), (-1,-1), 4),
        ('BOTTOMPADDING', (0,1), (-1,-1), 4),
    ]))
    story.append(breakdown_table)
    story.append(Spacer(1, 12))
    
    # Skills Sections
    skills = analysis_obj.get_skills()
    missing_skills = analysis_obj.get_missing_skills()
    
    skills_flowables = []
    skills_flowables.append(Paragraph("Identified Core Skills", section_heading))
    if skills:
        skills_flowables.append(Paragraph(", ".join(skills), body_style))
    else:
        skills_flowables.append(Paragraph("No major technical or core skills extracted.", body_style))
        
    if resume_obj.job_description:
        skills_flowables.append(Spacer(1, 6))
        skills_flowables.append(Paragraph("Identified Skills Gaps (Missing from Job Description)", section_heading))
        if missing_skills:
            skills_flowables.append(Paragraph(", ".join(missing_skills), body_style))
        else:
            skills_flowables.append(Paragraph("Excellent! No major skills gaps identified.", body_style))
            
    story.append(KeepTogether(skills_flowables))
    story.append(Spacer(1, 10))
    
    # Strengths & Weaknesses
    sw_flowables = []
    sw_flowables.append(Paragraph("Key Strengths", section_heading))
    strengths = analysis_obj.get_strengths()
    if strengths:
        for strg in strengths:
            sw_flowables.append(Paragraph(f"&bull; {strg}", bullet_style))
    else:
        sw_flowables.append(Paragraph("No specific strengths documented.", body_style))
        
    sw_flowables.append(Spacer(1, 6))
    sw_flowables.append(Paragraph("Critical Areas for Improvement", section_heading))
    weaknesses = analysis_obj.get_weaknesses()
    if weaknesses:
        for weak in weaknesses:
            sw_flowables.append(Paragraph(f"&bull; {weak}", bullet_style))
    else:
        sw_flowables.append(Paragraph("No critical formatting or structural issues noted.", body_style))
        
    story.append(KeepTogether(sw_flowables))
    story.append(Spacer(1, 10))
    
    # Actionable Suggestions
    sug_flowables = []
    sug_flowables.append(Paragraph("Actionable Recommendations", section_heading))
    suggestions = analysis_obj.get_suggestions()
    if suggestions:
        for sug in suggestions:
            sug_flowables.append(Paragraph(f"&bull; {sug}", bullet_style))
    else:
        sug_flowables.append(Paragraph("Your resume is well optimized! No further action required.", body_style))
        
    story.append(KeepTogether(sug_flowables))
    
    # Build the doc
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
