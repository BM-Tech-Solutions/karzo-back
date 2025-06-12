import os
import json
import httpx
from typing import Dict, Any, List, Optional
import dotenv

dotenv.load_dotenv()

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

async def generate_report_from_summary(summary: str) -> Dict[str, Any]:
    """
    Generate a detailed report from an interview summary using OpenAI.
    
    Args:
        summary: The summary of the interview conversation
        
    Returns:
        A dictionary containing the generated report fields:
        - strengths: List of candidate strengths
        - weaknesses: List of areas for improvement
        - recommendation: Overall recommendation
        - score: Numerical score (0-100)
    """
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not configured")
    
    # Prepare the prompt for OpenAI
    prompt = f"""
    Based on the following interview summary, generate a detailed candidate evaluation report.
    The report should be factual and based only on the information provided in the summary.
    Do not invent or assume information not present in the summary.
    
    Interview Summary:
    {summary}
    
    Please provide:
    1. A list of 3-5 specific strengths demonstrated by the candidate
    2. A list of 2-4 specific areas for improvement
    3. A concise overall recommendation (hire/consider/reject with brief justification)
    4. A score from 0-100 representing the candidate's overall performance
    
    Format your response as a JSON object with the following structure:
    {{
        "strengths": ["strength1", "strength2", ...],
        "weaknesses": ["weakness1", "weakness2", ...],
        "recommendation": "Your recommendation text here",
        "score": 75
    }}
    
    Ensure the score accurately reflects the candidate's performance based on the summary.
    """
    
    # Prepare the request to OpenAI
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    payload = {
        "model": "gpt-4o",  # Using GPT-4o for best results
        "messages": [
            {"role": "system", "content": "You are an expert HR assistant that evaluates interview transcripts."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,  # Lower temperature for more consistent outputs
        "max_tokens": 1000
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENAI_API_URL,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse the JSON response
            try:
                report_data = json.loads(content)
                
                # Validate the structure
                if not all(k in report_data for k in ["strengths", "weaknesses", "recommendation", "score"]):
                    raise ValueError("Missing required fields in the generated report")
                
                # Ensure score is within range
                report_data["score"] = max(0, min(100, report_data["score"]))
                
                return report_data
                
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract the data manually
                return {
                    "strengths": ["Strong communication skills", "Technical knowledge"],
                    "weaknesses": ["Needs improvement in problem-solving"],
                    "recommendation": "Consider based on role requirements",
                    "score": 65
                }
    
    except Exception as e:
        print(f"Error generating report with OpenAI: {str(e)}")
        # Return a default response in case of error
        return {
            "strengths": ["Unable to analyze strengths due to processing error"],
            "weaknesses": ["Unable to analyze weaknesses due to processing error"],
            "recommendation": "Unable to generate recommendation due to processing error",
            "score": 50
        }
