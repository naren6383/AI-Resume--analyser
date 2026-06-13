from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Resume(db.Model):
    """
    Model representing an uploaded resume document and its extracted text.
    """
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    extracted_text = db.Column(db.Text, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    job_title = db.Column(db.String(255), nullable=True)
    job_description = db.Column(db.Text, nullable=True)

    # Relationship to analyses
    analyses = db.relationship('Analysis', backref='resume', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Resume {self.filename}>"


class Analysis(db.Model):
    """
    Model representing the analysis output of a resume.
    Stores numerical metrics and JSON-serialized text outputs.
    """
    __tablename__ = 'analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=False)
    
    # Core Scores
    ats_score = db.Column(db.Integer, nullable=False, default=0)
    job_match_percentage = db.Column(db.Integer, default=0)
    
    # Analysis breakdowns stored as JSON strings
    score_breakdown = db.Column(db.Text, nullable=True)  # {"contact_info": X, "education": X, ...}
    summary = db.Column(db.Text, nullable=True)
    skills = db.Column(db.Text, nullable=True)           # List: ["Python", "Flask"]
    missing_skills = db.Column(db.Text, nullable=True)   # List: ["Docker", "K8s"]
    strengths = db.Column(db.Text, nullable=True)        # List: ["Strong background...", ...]
    weaknesses = db.Column(db.Text, nullable=True)       # List: ["Lacks projects in...", ...]
    keywords = db.Column(db.Text, nullable=True)         # Object: {"matched": [...], "missing": [...]}
    suggestions = db.Column(db.Text, nullable=True)      # List: ["Add metrics...", ...]
    
    report_path = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Help methods to easily serialize/deserialize JSON properties
    def get_score_breakdown(self):
        try:
            return json.loads(self.score_breakdown) if self.score_breakdown else {}
        except Exception:
            return {}
            
    def get_skills(self):
        try:
            return json.loads(self.skills) if self.skills else []
        except Exception:
            return []
            
    def get_missing_skills(self):
        try:
            return json.loads(self.missing_skills) if self.missing_skills else []
        except Exception:
            return []
            
    def get_strengths(self):
        try:
            return json.loads(self.strengths) if self.strengths else []
        except Exception:
            return []
            
    def get_weaknesses(self):
        try:
            return json.loads(self.weaknesses) if self.weaknesses else []
        except Exception:
            return []
            
    def get_keywords(self):
        try:
            return json.loads(self.keywords) if self.keywords else {"matched": [], "missing": []}
        except Exception:
            return {"matched": [], "missing": []}
            
    def get_suggestions(self):
        try:
            return json.loads(self.suggestions) if self.suggestions else []
        except Exception:
            return []

    def __repr__(self):
        return f"<Analysis id={self.id} resume_id={self.resume_id} score={self.ats_score}>"


class Setting(db.Model):
    """
    Model for storing system-wide dynamic settings (like API configurations).
    """
    __tablename__ = 'settings'
    
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Setting {self.key}={self.value}>"
