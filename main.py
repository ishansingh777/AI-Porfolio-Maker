import os
import sys
import json
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from google import genai
from google.genai import types

def print_header():
    print("╔══════════════════════════════════════════════════╗")
    print("║        AI RESUME → PORTFOLIO GENERATOR           ║")
    print("║        Gemini Powered Portfolio Builder          ║")
    print("╚══════════════════════════════════════════════════╝\n")

def load_environment():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("ERROR: GEMINI_API_KEY is not configured.\n")
        print("Please create a .env file and add your Gemini API key.")
        sys.exit(1)
    return api_key

def read_resume(filepath="resume.txt"):
    print("[1/5] Reading resume...")
    if not os.path.exists(filepath):
        print(f"\nERROR: {filepath} was not found.\n")
        print(f"Please create {filepath} and add your resume before running the program.")
        sys.exit(1)
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if not content.strip():
        print("\nERROR: resume.txt is empty.\n")
        print("Please add your resume content before running.")
        sys.exit(1)
        
    if len(content.strip()) < 50:
        print("\nERROR: Resume content is too short to generate a meaningful portfolio.\n")
        print("Please add more details to your resume.")
        sys.exit(1)
        
    print("✓ Resume loaded\n")
    return content

def clean_resume(content):
    print("[2/5] Validating and cleaning resume...")
    # Remove unnecessary spaces and blank lines
    lines = content.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    cleaned_resume = '\n'.join(cleaned_lines)
    print("✓ Resume validated\n")
    return cleaned_resume

def generate_ai_content(api_key, resume_text):
    print("[3/5] Sending resume to Gemini AI...")
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
You are an expert resume parser and portfolio generator. 
I will provide a resume below. Your task is to extract the information and return it strictly in the JSON structure requested.

CRITICAL INSTRUCTIONS:
* Use ONLY information contained in the resume.
* Do not invent information.
* Do not hallucinate.
* Do not create fake skills, projects, companies, dates, achievements, education, or links.
* Do not infer unsupported experience.
* Missing information must become empty values (empty string "" or empty array []).
* Keep the professional summary concise and factual.
* Return valid JSON ONLY. 

RESUME CONTENT:
{resume_text}
"""
        # Define the expected JSON schema using Gemini structured outputs
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING", "description": "Full name of the candidate"},
                "headline": {"type": "STRING", "description": "Professional headline, e.g., 'Software Engineer'"},
                "professional_summary": {"type": "STRING", "description": "Concise professional summary"},
                "skills": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "education": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "degree": {"type": "STRING"},
                            "institution": {"type": "STRING"},
                            "year": {"type": "STRING"}
                        }
                    }
                },
                "experience": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "title": {"type": "STRING"},
                            "company": {"type": "STRING"},
                            "duration": {"type": "STRING"},
                            "description": {"type": "STRING"}
                        }
                    }
                },
                "projects": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "title": {"type": "STRING"},
                            "description": {"type": "STRING"},
                            "technologies": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            }
                        }
                    }
                },
                "achievements": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "contact": {
                    "type": "OBJECT",
                    "properties": {
                        "email": {"type": "STRING"},
                        "phone": {"type": "STRING"},
                        "linkedin": {"type": "STRING"},
                        "github": {"type": "STRING"},
                        "portfolio": {"type": "STRING"}
                    }
                }
            },
            "required": ["name", "headline", "professional_summary", "skills", "education", "experience", "projects", "achievements", "contact"]
        }

        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1
            )
        )
        
        print("✓ AI response received\n")
        return response.text
        
    except Exception as e:
        print("\nERROR: Unable to communicate with Gemini.")
        print(f"Details: {e}")
        print("Please check your internet connection and API configuration.")
        sys.exit(1)

def parse_json(json_string):
    print("[4/5] Validating generated JSON...")
    try:
        if json_string.startswith("```json"):
            json_string = json_string.replace("```json\n", "")
            if json_string.endswith("```\n"):
                json_string = json_string[:-4]
            elif json_string.endswith("```"):
                json_string = json_string[:-3]
        
        data = json.loads(json_string)
        
        required_fields = ["name", "contact"]
        for field in required_fields:
            if field not in data:
                 print(f"WARNING: Missing field '{field}' in generated data.")
                 
        print("✓ JSON validated\n")
        return data
    except json.JSONDecodeError:
        print("\nERROR: Gemini returned an invalid JSON structure.")
        print("Please try again.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred while parsing JSON: {e}")
        sys.exit(1)

def generate_portfolio(data, template_name="template.html", output_name="portfolio.html"):
    print("[5/5] Generating portfolio...")
    try:
        if not os.path.exists(template_name):
            print(f"\nERROR: Template file {template_name} not found.")
            sys.exit(1)
            
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template(template_name)
        
        html_content = template.render(**data)
        
        with open(output_name, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"✓ {output_name} created\n")
        return True
    except Exception as e:
        print(f"\nERROR: Failed to generate portfolio: {e}")
        sys.exit(1)

def main():
    print_header()
    
    api_key = load_environment()
    
    raw_resume = read_resume("resume.txt")
    cleaned_resume = clean_resume(raw_resume)
    
    ai_response = generate_ai_content(api_key, cleaned_resume)
    
    portfolio_data = parse_json(ai_response)
    
    generate_portfolio(portfolio_data)
    
    print("────────────────────────────────────────────────────\n")
    print("SUCCESS!\n")
    print("Your portfolio has been generated successfully.\n")
    print("Output:")
    print("→ portfolio.html\n")
    print("Open portfolio.html in your browser to view it.")

if __name__ == "__main__":
    main()
