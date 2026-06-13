import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Import database models
from models.models import db, Resume, Analysis, Setting

# Import services
from services.parser import extract_text_from_file
from services.ai_analysis import analyze_resume_with_ai, test_api_key, get_default_model
from services.report_generator import generate_pdf_report

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Flask Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-session-security-key-9876')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 Megabytes limit
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
db.init_app(app)

with app.app_context():
    db.create_all()

# Helper: Check if filename is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper: Retrieve setting from db or fallback to env
def get_system_setting(key, fallback_env_name=None):
    setting = Setting.query.filter_by(key=key).first()
    if setting and setting.value:
        return setting.value
    if fallback_env_name:
        return os.environ.get(fallback_env_name, '')
    return ''

# Helper: Save setting to db
def set_system_setting(key, value):
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        db.session.add(setting)
    db.session.commit()

@app.route('/')
def index():
    """
    Home page. Renders brief statistics and overview.
    """
    total_resumes = Resume.query.count()
    recent_analyses = Analysis.query.order_by(Analysis.created_at.desc()).limit(5).all()
    
    # Calculate average ATS score
    avg_score = 0
    if total_resumes > 0:
        scores = [a.ats_score for a in Analysis.query.all()]
        if scores:
            avg_score = int(sum(scores) / len(scores))
            
    return render_template('index.html', total_resumes=total_resumes, recent_analyses=recent_analyses, avg_score=avg_score)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """
    Handles PDF/DOCX resume upload and job description inputs.
    Extracts text and runs AI or heuristic analysis.
    """
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'resume' not in request.files:
            flash('No resume file provided.', 'danger')
            return redirect(request.url)
            
        file = request.files['resume']
        job_title = request.form.get('job_title', '').strip()
        job_description = request.form.get('job_description', '').strip()
        
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add unique name mapping to avoid overwriting files
            base, ext = os.path.splitext(filename)
            import time
            unique_filename = f"{base}_{int(time.time())}{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            try:
                # Save file
                file.save(filepath)
                
                # Extract text
                raw_text = extract_text_from_file(filepath)
                if not raw_text or len(raw_text.strip()) < 50:
                    raise Exception("Extracted text is too short or empty. Please check if the file is scanned or corrupted.")
                
                # Save Resume record
                resume = Resume(
                    filename=filename,
                    filepath=filepath,
                    extracted_text=raw_text,
                    job_title=job_title if job_title else None,
                    job_description=job_description if job_description else None
                )
                db.session.add(resume)
                db.session.commit()
                
                # Fetch AI API details from db settings or .env fallback
                active_provider = get_system_setting('ACTIVE_AI_PROVIDER', 'ACTIVE_AI_PROVIDER')
                api_key = ""
                if active_provider == 'gemini':
                    api_key = get_system_setting('GEMINI_API_KEY', 'GEMINI_API_KEY')
                elif active_provider == 'openrouter':
                    api_key = get_system_setting('OPENROUTER_API_KEY', 'OPENROUTER_API_KEY')
                elif active_provider == 'groq':
                    api_key = get_system_setting('GROQ_API_KEY', 'GROQ_API_KEY')
                    
                active_model = get_system_setting('ACTIVE_AI_MODEL', 'ACTIVE_AI_MODEL')
                if not active_model and active_provider:
                    active_model = get_default_model(active_provider)
                
                # Run Analysis (AI with fallback to Heuristics)
                print(f"[Upload] Parsing '{filename}' using provider: {active_provider}, model: {active_model}")
                analysis_result = analyze_resume_with_ai(
                    resume_text=raw_text,
                    job_description_text=job_description if job_description else None,
                    provider=active_provider,
                    api_key=api_key,
                    model=active_model
                )
                
                # Save Analysis record
                analysis = Analysis(
                    resume_id=resume.id,
                    ats_score=analysis_result["ats_score"],
                    score_breakdown=json.dumps(analysis_result["score_breakdown"]),
                    summary=analysis_result["summary"],
                    skills=json.dumps(analysis_result["skills"]),
                    missing_skills=json.dumps(analysis_result["missing_skills"]),
                    strengths=json.dumps(analysis_result["strengths"]),
                    weaknesses=json.dumps(analysis_result["weaknesses"]),
                    job_match_percentage=analysis_result["job_match_percentage"],
                    keywords=json.dumps(analysis_result["keywords"]),
                    suggestions=json.dumps(analysis_result["suggestions"])
                )
                db.session.add(analysis)
                db.session.commit()
                
                flash('Resume uploaded and analyzed successfully!', 'success')
                return redirect(url_for('dashboard', analysis_id=analysis.id))
                
            except Exception as e:
                flash(f"Error analyzing resume: {str(e)}", 'danger')
                # Clean up file if it was saved
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
                return redirect(request.url)
        else:
            flash('Invalid file format. Please upload a PDF or DOCX file.', 'danger')
            return redirect(request.url)
            
    return render_template('upload.html')

@app.route('/dashboard/<int:analysis_id>')
def dashboard(analysis_id):
    """
    Renders the metrics, charts, insights, and suggestions for an analysis.
    """
    analysis = Analysis.query.get_or_404(analysis_id)
    resume = Resume.query.get(analysis.resume_id)
    
    return render_template(
        'dashboard.html',
        analysis=analysis,
        resume=resume,
        score_breakdown=analysis.get_score_breakdown(),
        skills=analysis.get_skills(),
        missing_skills=analysis.get_missing_skills(),
        strengths=analysis.get_strengths(),
        weaknesses=analysis.get_weaknesses(),
        keywords=analysis.get_keywords(),
        suggestions=analysis.get_suggestions()
    )

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """
    Manages API keys and provider configuration.
    """
    if request.method == 'POST':
        # Retrieve form data
        gemini_key = request.form.get('gemini_api_key', '').strip()
        openrouter_key = request.form.get('openrouter_api_key', '').strip()
        groq_key = request.form.get('groq_api_key', '').strip()
        active_provider = request.form.get('active_ai_provider', 'none').strip()
        
        gemini_model = request.form.get('gemini_model', 'gemini-1.5-flash').strip()
        openrouter_model = request.form.get('openrouter_model', 'google/gemini-2.5-flash:free').strip()
        groq_model = request.form.get('groq_model', 'llama-3.3-70b-versatile').strip()
        
        # Save to database Settings
        set_system_setting('GEMINI_API_KEY', gemini_key)
        set_system_setting('OPENROUTER_API_KEY', openrouter_key)
        set_system_setting('GROQ_API_KEY', groq_key)
        set_system_setting('ACTIVE_AI_PROVIDER', active_provider)
        
        # Save models corresponding to selected provider
        if active_provider == 'gemini':
            set_system_setting('ACTIVE_AI_MODEL', gemini_model)
        elif active_provider == 'openrouter':
            set_system_setting('ACTIVE_AI_MODEL', openrouter_model)
        elif active_provider == 'groq':
            set_system_setting('ACTIVE_AI_MODEL', groq_model)
        else:
            set_system_setting('ACTIVE_AI_MODEL', '')
            
        set_system_setting('GEMINI_MODEL', gemini_model)
        set_system_setting('OPENROUTER_MODEL', openrouter_model)
        set_system_setting('GROQ_MODEL', groq_model)
        
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings'))
        
    # Get current values to display
    config = {
        'gemini_api_key': get_system_setting('GEMINI_API_KEY', 'GEMINI_API_KEY'),
        'openrouter_api_key': get_system_setting('OPENROUTER_API_KEY', 'OPENROUTER_API_KEY'),
        'groq_api_key': get_system_setting('GROQ_API_KEY', 'GROQ_API_KEY'),
        'active_ai_provider': get_system_setting('ACTIVE_AI_PROVIDER', 'ACTIVE_AI_PROVIDER'),
        
        'gemini_model': get_system_setting('GEMINI_MODEL') or 'gemini-1.5-flash',
        'openrouter_model': get_system_setting('OPENROUTER_MODEL') or 'google/gemini-2.5-flash:free',
        'groq_model': get_system_setting('GROQ_MODEL') or 'llama-3.3-70b-versatile'
    }
    
    return render_template('settings.html', config=config)

@app.route('/api/test-connection', methods=['POST'])
def api_test_connection():
    """
    Tests connection to the specified AI API provider with the given key.
    """
    data = request.json or {}
    provider = data.get('provider', '')
    api_key = data.get('api_key', '')
    model = data.get('model', '')
    
    if not provider or provider == 'none':
        return jsonify({'success': False, 'message': 'No provider selected for testing.'}), 400
        
    success, message = test_api_key(provider, api_key, model)
    return jsonify({'success': success, 'message': message})

@app.route('/history')
def history():
    """
    Lists past uploads, with searching and sorting logic.
    """
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'date_desc')
    
    query = Resume.query
    
    if search_query:
        query = query.filter(
            (Resume.filename.like(f"%{search_query}%")) | 
            (Resume.job_title.like(f"%{search_query}%"))
        )
        
    # Apply Sorting
    if sort_by == 'date_asc':
        query = query.order_by(Resume.upload_date.asc())
    elif sort_by == 'score_desc':
        # Join with Analysis and sort by score
        query = query.join(Analysis).order_by(Analysis.ats_score.desc())
    elif sort_by == 'score_asc':
        query = query.join(Analysis).order_by(Analysis.ats_score.asc())
    else: # Default date_desc
        query = query.order_by(Resume.upload_date.desc())
        
    resumes = query.all()
    return render_template('history.html', resumes=resumes, search=search_query, sort=sort_by)

@app.route('/history/delete/<int:resume_id>', methods=['POST'])
def delete_resume(resume_id):
    """
    Deletes a resume record, its associated analysis, and the physical uploaded file.
    """
    resume = Resume.query.get_or_404(resume_id)
    filepath = resume.filepath
    
    try:
        # Delete file from system
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            
        db.session.delete(resume)
        db.session.commit()
        flash('History record deleted successfully.', 'success')
    except Exception as e:
        flash(f"Error deleting history: {str(e)}", 'danger')
        
    return redirect(url_for('history'))

@app.route('/download-report/<int:analysis_id>')
def download_report(analysis_id):
    """
    Generates and downloads the PDF report of the analysis.
    """
    analysis = Analysis.query.get_or_404(analysis_id)
    resume = Resume.query.get(analysis.resume_id)
    
    try:
        pdf_bytes = generate_pdf_report(analysis, resume)
        
        # Return the PDF buffer directly as attachment
        import io
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"ATS_Report_{secure_filename(resume.filename.rsplit('.', 1)[0])}.pdf"
        )
    except Exception as e:
        flash(f"Error generating PDF report: {str(e)}", 'danger')
        return redirect(url_for('dashboard', analysis_id=analysis_id))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
