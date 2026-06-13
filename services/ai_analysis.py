import json
import requests
from services.ats import calculate_heuristic_ats, detect_skills

def get_default_model(provider):
    """
    Returns the default recommended model for a provider if not specified.
    """
    defaults = {
        "gemini": "gemini-1.5-flash",
        "openrouter": "google/gemini-2.5-flash:free",
        "groq": "llama-3.3-70b-versatile"
    }
    return defaults.get(provider.lower(), "")

def build_analysis_prompt(resume_text, job_description_text=None):
    """
    Constructs the prompt detailing the resume and job description (if provided).
    Instructs the AI to evaluate and return a strict JSON structure.
    """
    prompt = (
        "You are an expert ATS (Applicant Tracking System) optimization specialist and senior technical recruiter. "
        "Analyze the candidate's resume and return a highly detailed, professional analysis.\n\n"
        "If a job description is provided, compare the resume against it to compute a job match percentage, "
        "identify missing skills/keywords, and give tailored feedback.\n"
        "If NO job description is provided, evaluate the resume generally, identify its core skills, strengths, "
        "weaknesses, and formatting, and set 'job_match_percentage' to 0.\n\n"
        "You MUST return a JSON object with the following exact keys and structure. Do not output markdown, "
        "do not output comments, and do not wrap the JSON in ```json...```. Output ONLY the raw JSON string.\n\n"
        "JSON SCHEMA:\n"
        "{\n"
        "  \"ats_score\": (integer between 0 and 100, representing the overall ATS score),\n"
        "  \"score_breakdown\": {\n"
        "    \"contact_info\": (integer between 0 and 10),\n"
        "    \"education\": (integer between 0 and 15),\n"
        "    \"experience\": (integer between 0 and 20),\n"
        "    \"skills\": (integer between 0 and 25),\n"
        "    \"projects_certifications\": (integer between 0 and 15),\n"
        "    \"formatting\": (integer between 0 and 15)\n"
        "  },\n"
        "  \"summary\": \"(A concise, executive summary of the candidate's background and suitability - 3-4 sentences)\",\n"
        "  \"skills\": [\"(skill 1)\", \"(skill 2)\", ...],\n"
        "  \"missing_skills\": [\"(missing skill 1 from job description)\", ...],\n"
        "  \"strengths\": [\"(strength 1 with specific reasons)\", \"(strength 2)\", \"(strength 3)\"],\n"
        "  \"weaknesses\": [\"(weakness/area of improvement 1)\", \"(weakness 2)\"],\n"
        "  \"job_match_percentage\": (integer between 0 and 100),\n"
        "  \"keywords\": {\n"
        "    \"matched\": [\"(matched industry keyword 1)\", ...],\n"
        "    \"missing\": [\"(missing industry keyword 1)\", ...]\n"
        "  },\n"
        "  \"suggestions\": [\"(actionable optimization suggestion 1)\", \"(suggestion 2)\", ...]\n"
        "}\n\n"
        "--- RESUME TEXT ---\n"
        f"{resume_text}\n\n"
    )
    
    if job_description_text:
        prompt += (
            "--- TARGET JOB DESCRIPTION ---\n"
            f"{job_description_text}\n\n"
        )
    else:
        prompt += "--- NO TARGET JOB DESCRIPTION PROVIDED ---\n\n"
        
    prompt += "Analyze now and return only the requested JSON content."
    return prompt

def test_api_key(provider, api_key, model=None):
    """
    Verifies that the API key and connection work for the selected provider.
    Returns (True, "Success Message") or (False, "Error Message").
    """
    if not api_key:
        return False, "API Key is empty."
        
    if not model:
        model = get_default_model(provider)
        
    provider = provider.lower()
    
    try:
        if provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": "Hello, respond with 'OK'"}]}]
            }
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                return True, "Successfully connected to Gemini API!"
            else:
                return False, f"Gemini Error ({response.status_code}): {response.text}"
                
        elif provider == "openrouter":
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "Resume Analyzer Test"
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Hello, respond with 'OK'"}]
            }
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                return True, "Successfully connected to OpenRouter API!"
            else:
                return False, f"OpenRouter Error ({response.status_code}): {response.text}"
                
        elif provider == "groq":
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Hello, respond with 'OK'"}]
            }
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                return True, "Successfully connected to Groq API!"
            else:
                return False, f"Groq Error ({response.status_code}): {response.text}"
                
        else:
            return False, f"Unsupported provider: {provider}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def clean_json_response(content):
    """
    Cleans raw response from LLMs to ensure it's a valid JSON string.
    Removes markdown block qualifiers like ```json or ``` if present.
    """
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()

def analyze_resume_with_ai(resume_text, job_description_text=None, provider=None, api_key=None, model=None):
    """
    Orchestrates the AI resume analysis.
    If credentials are missing or the API call fails, falls back to the local heuristic calculations.
    """
    # 1. Fallback if provider is not configured
    if not provider or provider.lower() == "none" or not api_key:
        print("[AI Service] AI not configured. Running heuristic fallback.")
        return get_fallback_data(resume_text, job_description_text, "AI API is not configured. Please add an API Key in Settings.")
        
    provider = provider.lower()
    if not model:
        model = get_default_model(provider)
        
    prompt = build_analysis_prompt(resume_text, job_description_text)
    
    try:
        response_text = ""
        
        # 2. Call Gemini
        if provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            if response.status_code == 200:
                res_data = response.json()
                response_text = res_data['candidates'][0]['content']['parts'][0]['text']
            else:
                raise Exception(f"Gemini API returned status {response.status_code}: {response.text}")
                
        # 3. Call OpenRouter
        elif provider == "openrouter":
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "Resume Analyzer"
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            if response.status_code == 200:
                res_data = response.json()
                response_text = res_data['choices'][0]['message']['content']
            else:
                raise Exception(f"OpenRouter API returned status {response.status_code}: {response.text}")
                
        # 4. Call Groq
        elif provider == "groq":
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            if response.status_code == 200:
                res_data = response.json()
                response_text = res_data['choices'][0]['message']['content']
            else:
                raise Exception(f"Groq API returned status {response.status_code}: {response.text}")
                
        else:
            raise ValueError(f"Unknown AI Provider: {provider}")
            
        # Parse Response
        cleaned_json = clean_json_response(response_text)
        result = json.loads(cleaned_json)
        
        # Verify result contains the keys we need or populate default structure
        required_keys = ["ats_score", "score_breakdown", "summary", "skills", "missing_skills", "strengths", "weaknesses", "job_match_percentage", "keywords", "suggestions"]
        for key in required_keys:
            if key not in result:
                if key == "score_breakdown":
                    result["score_breakdown"] = {"contact_info": 8, "education": 12, "experience": 15, "skills": 18, "projects_certifications": 12, "formatting": 12}
                elif key == "keywords":
                    result["keywords"] = {"matched": [], "missing": []}
                elif isinstance(result.get(key), list):
                    result[key] = []
                elif isinstance(result.get(key), int):
                    result[key] = 0
                else:
                    result[key] = ""
                    
        return result
        
    except Exception as e:
        print(f"[AI Service] Error calling AI service: {str(e)}. Falling back to local heuristic analysis.")
        return get_fallback_data(resume_text, job_description_text, f"AI analysis failed: {str(e)}. Showing local heuristic results.")

def get_fallback_data(resume_text, job_description_text, fallback_message):
    """
    Computes analysis parameters using standard heuristics.
    Appends the fallback warning to suggestions.
    """
    heuristics = calculate_heuristic_ats(resume_text, job_description_text)
    
    # Map raw heuristic data to our standard AI return format
    skills = heuristics["detected_skills"]
    missing_skills = heuristics["missing_skills"]
    
    # Synthesize standard strings for strengths/weaknesses if not using AI
    strengths = []
    if len(skills) > 3:
        strengths.append(f"Detected a strong skill set containing: {', '.join(skills[:5])}.")
    if heuristics["score_breakdown"]["experience"] > 10:
        strengths.append("Demonstrates solid job experience history and results-oriented metrics.")
    if heuristics["score_breakdown"]["contact_info"] >= 8:
        strengths.append("Excellent and complete contact information (Email, Phone, LinkedIn).")
    else:
        strengths.append("Contains basic resume contact structures.")
        
    weaknesses = []
    for issue in heuristics["formatting_issues"][:3]:
        weaknesses.append(issue)
    if not weaknesses:
        weaknesses.append("No critical resume structural weaknesses found by heuristics.")
        
    suggestions = [
        "Customize your summary header to target specific job opportunities.",
        "Ensure all project listings show measurable business impact metrics."
    ]
    suggestions.append(f"NOTE: {fallback_message}")
    
    summary = (
        f"This is a local heuristic review of the resume '{'for the targeted role' if job_description_text else 'general review'}'. "
        f"A total of {len(skills)} skills were identified. Core structural elements like Contact info, Experience, "
        "and Formatting layout were scanned to compute the base score."
    )
    
    return {
        "ats_score": heuristics["ats_score"],
        "score_breakdown": heuristics["score_breakdown"],
        "summary": summary,
        "skills": skills,
        "missing_skills": missing_skills,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "job_match_percentage": heuristics["job_match_percentage"],
        "keywords": heuristics["keywords"],
        "suggestions": suggestions
    }
