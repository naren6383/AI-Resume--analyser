import re

# Comprehensive taxonomy of skills across multiple domains
SKILL_TAXONOMY = {
    # Languages
    "python": ["python", "py"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "java": ["java"],
    "c++": ["c\\+\\+"],
    "c#": ["c\\#", "csharp"],
    "c": ["\\bc\\b"],
    "ruby": ["ruby", "rails"],
    "php": ["php"],
    "go": ["go", "golang"],
    "rust": ["rust"],
    "swift": ["swift"],
    "kotlin": ["kotlin"],
    "sql": ["sql", "mysql", "postgresql", "sqlite", "pl/sql"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "r": ["\\br\\b"],
    "scala": ["scala"],
    "shell": ["bash", "shell", "powershell"],
    
    # Frameworks & Libraries
    "flask": ["flask"],
    "django": ["django"],
    "fastapi": ["fastapi"],
    "react": ["react", "reactjs", "react.js"],
    "angular": ["angular", "angularjs"],
    "vue": ["vue", "vuejs", "vue.js"],
    "node.js": ["node", "nodejs", "node.js"],
    "express": ["express", "expressjs"],
    "spring boot": ["spring", "springboot"],
    "asp.net": ["asp\\.net", "dotnet"],
    "laravel": ["laravel"],
    "jquery": ["jquery"],
    "bootstrap": ["bootstrap"],
    "tailwind css": ["tailwind", "tailwindcss"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "tensorflow": ["tensorflow", "tf"],
    "pytorch": ["pytorch"],
    "keras": ["keras"],
    "next.js": ["next\\.js", "nextjs"],
    
    # Cloud & DevOps
    "aws": ["aws", "amazon web services", "ec2", "s3", "rds", "lambda"],
    "azure": ["azure", "microsoft azure"],
    "google cloud": ["gcp", "google cloud", "google cloud platform"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "jenkins": ["jenkins"],
    "git": ["git", "github", "gitlab", "bitbucket"],
    "ci/cd": ["ci/cd", "continuous integration", "continuous deployment"],
    "terraform": ["terraform"],
    "ansible": ["ansible"],
    "linux": ["linux", "ubuntu", "debian", "redhat", "centos"],
    
    # Databases & Cache
    "postgresql": ["postgresql", "postgres"],
    "mysql": ["mysql"],
    "sqlite": ["sqlite"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "elasticsearch": ["elasticsearch"],
    "dynamodb": ["dynamodb"],
    "oracle": ["oracle"],
    "sql server": ["sql server", "mssql"],
    
    # Domains, Methodologies & Tools
    "agile": ["agile"],
    "scrum": ["scrum"],
    "project management": ["project management", "pmp"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "dl"],
    "artificial intelligence": ["artificial intelligence", "ai"],
    "data analysis": ["data analysis", "analytics"],
    "ui/ux": ["ui/ux", "user interface", "user experience", "figma"],
    "rest api": ["rest api", "restful", "apis"],
    "graphql": ["graphql"],
    "microservices": ["microservices"],
    "system design": ["system design"],
    "testing": ["testing", "qa", "unit testing", "selenium", "pytest", "mocha", "jest"],
    
    # Soft Skills & Business
    "leadership": ["leadership", "leading", "managed", "mentor", "mentoring"],
    "communication": ["communication", "writing", "presentation"],
    "problem solving": ["problem solving", "analytical"],
    "teamwork": ["teamwork", "collaboration", "collaborative"],
}

def detect_skills(text):
    """
    Detects skills from a text block using the SKILL_TAXONOMY database.
    Returns a list of standardized, lowercased skills.
    """
    if not text:
        return []
        
    detected = []
    text_lower = text.lower()
    
    for skill, patterns in SKILL_TAXONOMY.items():
        for pattern in patterns:
            # Match word boundaries or special chars
            if re.search(pattern, text_lower):
                detected.append(skill)
                break
                
    return list(set(detected))

def calculate_heuristic_ats(resume_text, job_description_text=None):
    """
    Computes an ATS score based on heuristic rules.
    If job_description_text is present, matches the resume content against the job description.
    """
    scores = {
        "contact_info": 0,
        "education": 0,
        "experience": 0,
        "skills": 0,
        "projects_certifications": 0,
        "formatting": 0
    }
    
    issues = []
    text_lower = resume_text.lower()
    
    # 1. Contact Information (Max 10 points)
    # Check for email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text_lower)
    if email_match:
        scores["contact_info"] += 3
    else:
        issues.append("Contact Info: Email address not detected.")
        
    # Check for phone
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text_lower)
    if phone_match:
        scores["contact_info"] += 3
    else:
        issues.append("Contact Info: Phone number not detected.")
        
    # Check for LinkedIn
    if "linkedin.com" in text_lower or "linkedin" in text_lower:
        scores["contact_info"] += 2
    else:
        issues.append("Contact Info: LinkedIn profile URL missing.")
        
    # Check for GitHub / Portfolio / Personal website
    if any(keyword in text_lower for keyword in ["github.com", "github", "portfolio", "website", "http", "www"]):
        scores["contact_info"] += 2
    else:
        issues.append("Contact Info: Portfolio website or GitHub link not detected.")
        
    # 2. Education (Max 15 points)
    education_keywords = ["bachelor", "master", "phd", "bsc", "msc", "mba", "btech", "mtech", "degree", "university", "college", "graduate", "diploma", "education", "academics"]
    edu_score = 0
    for kw in education_keywords:
        if kw in text_lower:
            edu_score += 3
            if edu_score >= 12:
                break
    # Check for date patterns (graduation years e.g., 2018, 2022, etc.)
    graduation_year = re.search(r'\b(19|20)\d{2}\b', text_lower)
    if graduation_year:
        edu_score += 3
        
    scores["education"] = min(edu_score, 15)
    if scores["education"] < 9:
        issues.append("Education: Minimal or no academic degree credentials detected.")
        
    # 3. Experience (Max 20 points)
    experience_keywords = ["experience", "work", "job", "employment", "history", "professional", "position", "role", "analyst", "engineer", "developer", "manager", "lead", "intern", "officer"]
    exp_score = 0
    for kw in experience_keywords:
        if kw in text_lower:
            exp_score += 2
            if exp_score >= 10:
                break
    # Action verbs which indicate results-oriented achievements
    action_verbs = ["managed", "designed", "developed", "led", "created", "implemented", "optimized", "increased", "solved", "analyzed", "reduced", "delivered", "built", "collaborated"]
    verb_count = sum(1 for verb in action_verbs if verb in text_lower)
    exp_score += min(verb_count * 2, 10)
    
    scores["experience"] = exp_score
    if scores["experience"] < 12:
        issues.append("Experience: Resume lacks impact verbs or standard professional experience headings.")
        
    # 4. Skills (Max 25 points)
    detected_resume_skills = detect_skills(resume_text)
    num_skills = len(detected_resume_skills)
    
    # Score skills based on count (up to 15 points)
    skills_score = min(num_skills * 1.5, 15)
    
    # Section header check (up to 10 points)
    if any(h in text_lower for h in ["skills", "technologies", "expertise", "technical proficiencies", "competencies"]):
        skills_score += 10
    else:
        issues.append("Skills: A dedicated 'Skills' or 'Technologies' section header was not detected.")
        
    scores["skills"] = int(skills_score)
    if num_skills < 5:
        issues.append("Skills: Very few recognizable professional skills detected.")

    # 5. Projects & Certifications (Max 15 points)
    proj_cert_score = 0
    if any(kw in text_lower for kw in ["project", "projects", "portfolio", "personal work"]):
        proj_cert_score += 8
    else:
        issues.append("Projects: No dedicated personal/academic projects section found.")
        
    if any(kw in text_lower for kw in ["certification", "certifications", "certified", "credentials", "coursework"]):
        proj_cert_score += 7
    else:
        issues.append("Certifications: No professional credentials or certifications detected.")
        
    scores["projects_certifications"] = proj_cert_score
    
    # 6. Formatting & Keyword Density (Max 15 points)
    formatting_score = 0
    # Length check (Word count)
    words = resume_text.split()
    word_count = len(words)
    
    if 300 <= word_count <= 1500:
        formatting_score += 6
    elif 150 < word_count < 300 or 1500 < word_count < 2500:
        formatting_score += 3
        issues.append(f"Formatting: Word count ({word_count}) is suboptimal (ideal is 300-1500 words).")
    else:
        issues.append(f"Formatting: Resume has an extreme word count ({word_count}), indicating bad formatting or content density.")
        
    # Bullet points indicators
    bullet_indicators = ["•", "▪", "●", " - ", " * "]
    if any(indicator in resume_text for indicator in bullet_indicators):
        formatting_score += 5
    else:
        issues.append("Formatting: Bullet points are missing, which makes readability harder for recruiters and scanners.")
        
    # Section diversity (checking if multiple section headers are present)
    headers = ["education", "experience", "skills", "projects", "summary", "objective", "certifications"]
    header_count = sum(1 for header in headers if header in text_lower)
    if header_count >= 4:
        formatting_score += 4
    else:
        formatting_score += 2
        issues.append("Formatting: Resume lacks standard section divisions (Summary, Experience, Education, Skills).")
        
    scores["formatting"] = formatting_score

    # Compute Total ATS Score (sum of all sections, max 100)
    total_ats_score = sum(scores.values())
    
    # Calculate Job Match Metrics if Job Description is provided
    job_match_pct = 0
    matched_skills = []
    missing_skills = []
    matched_keywords = []
    missing_keywords = []
    
    if job_description_text:
        job_skills = detect_skills(job_description_text)
        if job_skills:
            for skill in job_skills:
                if skill in detected_resume_skills:
                    matched_skills.append(skill)
                else:
                    missing_skills.append(skill)
            # Calculate match percentage
            job_match_pct = int((len(matched_skills) / len(job_skills)) * 100)
        else:
            # If no skills detected in job description, fall back to simple keyword overlap
            job_match_pct = 50
            
        # Basic keyword match (extract words longer than 4 characters from job description, check occurrences)
        jd_words = set(re.findall(r'\b[a-zA-Z]{4,15}\b', job_description_text.lower()))
        resume_words = set(re.findall(r'\b[a-zA-Z]{4,15}\b', text_lower))
        # Exclude common stop words
        stopwords = {"with", "about", "their", "would", "there", "these", "other", "which", "could", "should", "under", "while", "where", "after", "skills", "experience", "years"}
        jd_keywords = jd_words - stopwords
        
        matches = jd_keywords.intersection(resume_words)
        misses = jd_keywords - resume_words
        
        # Take top 15 matches/misses to show keyword density insights
        matched_keywords = list(matches)[:15]
        missing_keywords = list(misses)[:15]
    else:
        # Without job description, job match percentage is 0
        job_match_pct = 0
        
    return {
        "ats_score": min(total_ats_score, 100),
        "score_breakdown": scores,
        "detected_skills": detected_resume_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "job_match_percentage": job_match_pct,
        "formatting_issues": issues,
        "keywords": {
            "matched": matched_keywords,
            "missing": missing_keywords
        }
    }
