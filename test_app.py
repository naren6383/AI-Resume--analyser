import os
import unittest
import json
from datetime import datetime

# Import application components
from app import app
from models.models import db, Resume, Analysis, Setting
from services.ats import calculate_heuristic_ats, detect_skills
from services.parser import clean_text

class ResumeAnalyzerTestCase(unittest.TestCase):

    def setUp(self):
        """
        Set up testing environment.
        Configures Flask app to use an in-memory SQLite database.
        """
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        """
        Cleans database and pops app context.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_text_cleaning(self):
        """
        Tests formatting sanitization logic.
        """
        dirty = "Hello \t \n\n world! \xa0 Test"
        cleaned = clean_text(dirty)
        self.assertEqual(cleaned, "Hello \n world! Test")

    def test_skill_detection(self):
        """
        Tests matching skill keywords against taxonomy.
        """
        text = "I am a skilled developer expert in Python, Flask, React, and AWS cloud deployment."
        skills = detect_skills(text)
        
        self.assertIn("python", skills)
        self.assertIn("flask", skills)
        self.assertIn("react", skills)
        self.assertIn("aws", skills)
        self.assertNotIn("java", skills)

    def test_heuristic_ats_scoring_without_jd(self):
        """
        Tests heuristic scoring calculations without job descriptions.
        """
        resume = (
            "JOHN DOE\n"
            "Email: john.doe@email.com | Phone: 123-456-7890 | Website: github.com/johndoe | LinkedIn: linkedin.com/in/johndoe\n\n"
            "SUMMARY\n"
            "Professional and result-driven Software Engineer with over 5 years of experience building secure web architectures and designing robust REST APIs. Proven record of optimization, team leadership, and clean code principles.\n\n"
            "EXPERIENCE\n"
            "Senior Backend Engineer - Tech Solutions Inc. (2021 - Present)\n"
            "• Managed, designed, and developed complex database models and microservices using Python and Flask frameworks.\n"
            "• Optimized API query response times by 35% through query caching, indexing, and database connection pooling.\n"
            "• Led a collaborative group of 4 junior developers to design and deploy CI/CD pipelines to AWS cloud systems.\n"
            "• Solved critical latency bottlenecks in legacy data loaders, reducing daily report processing times significantly.\n"
            "• Collaborated with product owners to convert business specifications into clean, testable system code architectures.\n"
            "• Analyzed database query logs to isolate sluggish joins, introducing optimized composite indexing patterns.\n\n"
            "Software Developer - WebApps Corp (2019 - 2021)\n"
            "• Developed responsive web frontends using React and integrated them with Node.js backend systems and SQL databases.\n"
            "• Implemented unit testing and integration testing suites using Pytest and Jest, achieving 90% code coverage.\n"
            "• Created secure payment interfaces using Stripe integrations and standard OAuth authentication rules.\n"
            "• Maintained and updated legacy codebases to improve security guidelines, styling layouts, and formatting rules.\n"
            "• Reduced client onboarding delays by automating environment generation with Docker containers and Docker Compose.\n"
            "• Participated in weekly sprint reviews, estimating task difficulties and maintaining active scrum boards.\n\n"
            "EDUCATION\n"
            "Bachelor of Science in Computer Science - University of Technology, 2018\n\n"
            "PROJECTS\n"
            "• Portfolio App: Designed a serverless PDF scanning utility using AWS Lambda, Python, and SQLite databases.\n"
            "• Open Source: Active contributor to Django-based developer frameworks, managing pull request reviews and documentation updates.\n\n"
            "CERTIFICATIONS\n"
            "• AWS Certified Solutions Architect Associate (2022)\n"
            "• Certified Scrum Master (CSM) (2020)\n\n"
            "SKILLS\n"
            "Python, Flask, JavaScript, SQL, AWS, Docker, Git, REST APIs, Agile, Scrum, Testing"
        )
        
        result = calculate_heuristic_ats(resume)
        
        self.assertGreater(result["ats_score"], 0)
        self.assertEqual(result["job_match_percentage"], 0)
        self.assertIn("python", result["detected_skills"])
        self.assertIn("flask", result["detected_skills"])
        self.assertEqual(len(result["formatting_issues"]), 0) # Should be clean formatting

    def test_heuristic_ats_scoring_with_jd(self):
        """
        Tests heuristic scoring calculations with a matching job description.
        """
        resume = (
            "John Doe\njohn.doe@email.com\n"
            "Skills: Python, Flask, Docker, Kubernetes"
        )
        jd = "Looking for a backend engineer with Python, Flask, Docker, Kubernetes, and AWS."
        
        result = calculate_heuristic_ats(resume, jd)
        
        self.assertGreater(result["job_match_percentage"], 0)
        self.assertIn("python", result["matched_skills"])
        self.assertIn("aws", result["missing_skills"])
        self.assertIn("python", result["keywords"]["matched"])

    def test_database_models_and_relationships(self):
        """
        Tests insertion and queries of database models.
        """
        # Create resume
        resume = Resume(
            filename="test_resume.pdf",
            filepath="/static/uploads/test_resume.pdf",
            extracted_text="John Doe content here...",
            job_title="Software Architect"
        )
        db.session.add(resume)
        db.session.commit()
        
        # Verify saved
        saved_resume = Resume.query.first()
        self.assertEqual(saved_resume.filename, "test_resume.pdf")
        self.assertEqual(saved_resume.job_title, "Software Architect")
        
        # Create analysis relation
        analysis = Analysis(
            resume_id=saved_resume.id,
            ats_score=85,
            summary="Strong candidate",
            skills=json.dumps(["Python", "SQL"]),
            score_breakdown=json.dumps({"education": 12, "experience": 15})
        )
        db.session.add(analysis)
        db.session.commit()
        
        # Verify relationship cascade
        saved_analysis = Analysis.query.first()
        self.assertEqual(saved_analysis.ats_score, 85)
        self.assertEqual(saved_analysis.resume.filename, "test_resume.pdf")
        self.assertEqual(saved_analysis.get_skills(), ["Python", "SQL"])
        self.assertEqual(saved_analysis.get_score_breakdown()["education"], 12)

    def test_settings_storage(self):
        """
        Tests dynamic settings management.
        """
        setting = Setting(key="ACTIVE_AI_PROVIDER", value="gemini")
        db.session.add(setting)
        db.session.commit()
        
        saved_setting = Setting.query.filter_by(key="ACTIVE_AI_PROVIDER").first()
        self.assertEqual(saved_setting.value, "gemini")

    def test_endpoints_accessibility(self):
        """
        Verifies GET endpoints return status 200.
        """
        response_home = self.client.get('/')
        self.assertEqual(response_home.status_code, 200)
        
        response_upload = self.client.get('/upload')
        self.assertEqual(response_upload.status_code, 200)
        
        response_settings = self.client.get('/settings')
        self.assertEqual(response_settings.status_code, 200)
        
        response_history = self.client.get('/history')
        self.assertEqual(response_history.status_code, 200)

if __name__ == '__main__':
    unittest.main()
