import os
import json
import httpx
import PyPDF2
import docx
import io
from typing import Dict, Any, List, Optional
import dotenv

dotenv.load_dotenv()

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

async def extract_text_from_cv(file_path: str) -> str:
    """
    Extract text from a CV file (PDF or DOCX)
    
    Args:
        file_path: Path to the CV file
        
    Returns:
        Extracted text from the CV
    """
    try:
        # Check file extension
        file_extension = file_path.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            # Extract text from PDF
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ''
                for page in pdf_reader.pages:
                    text += page.extract_text() + '\n'
                return text
                
        elif file_extension == 'docx':
            # Extract text from DOCX
            doc = docx.Document(file_path)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            return text
            
        else:
            return f"Unsupported file format: {file_extension}"
            
    except Exception as e:
        print(f"Error extracting text from CV: {str(e)}")
        return f"Error extracting text: {str(e)}"


async def generate_candidate_summary(cv_text: str) -> str:
    """
    Generate a structured analysis report of the candidate from their CV text using OpenAI GPT-4o mini
   
    Args:
        cv_text: Extracted text from the candidate's CV
       
    Returns:
        A structured analysis report following the specified format
    """
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not configured")
   
    # Prepare the prompt for OpenAI
    prompt = f"""
    Analysez le CV fourni et générez un rapport structuré selon le format suivant :

    **RAPPORT D'ANALYSE DE CV**

    **Candidat :** [Nom du candidat]
    **Poste visé :** [Si mentionné dans le CV, sinon "Non spécifié"]
    **Date d'analyse :** [Date du jour]

    ## POINTS FORTS

    Identifiez et listez 5-7 points forts majeurs du candidat basés sur :
    • Expériences professionnelles pertinentes
    • Compétences techniques et soft skills
    • Formation et certifications
    • Réalisations et résultats quantifiables
    • Évolution de carrière
    • Éléments différenciants

    Format : Rédigez chaque point fort en 1-2 phrases explicatives avec des puces (•)

    ## POINTS À VÉRIFIER

    Générez exactement 3 questions stratégiques à poser au candidat lors d'un entretien pour :
    • Clarifier des zones d'ombre du CV
    • Vérifier la véracité de certaines affirmations
    • Approfondir des aspects critiques pour le poste
    • Évaluer des compétences non démontrées clairement

    Format des questions (sans mention d'objectif) :
    1. **[Question 1]**
    2. **[Question 2]**
    3. **[Question 3]**

    ## SYNTHÈSE

    Rédigez un paragraphe de synthèse (3-4 phrases) résumant le profil global du candidat et sa pertinence potentielle.

    Instructions :
    - Restez factuel et objectif
    - Basez-vous uniquement sur les informations présentes dans le CV
    - Évitez les suppositions non fondées
    - Utilisez un ton professionnel et bienveillant
    - Utilisez la date d'aujourd'hui pour "Date d'analyse"

    CV Content:
    {cv_text}
    """
   
    # Prepare the request to OpenAI
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
   
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Vous êtes un expert en ressources humaines chargé d'évaluer des CV de candidats. Votre mission est de fournir une analyse objective et constructive du profil présenté selon le format demandé."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,  # Lower temperature for more consistent outputs
        "max_tokens": 1500   # Increased for the detailed structured report
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
           
            return content.strip()
               
    except Exception as e:
        print(f"Error generating candidate analysis with OpenAI: {str(e)}")
        # Return a default response in case of error
        return "Unable to generate candidate analysis due to processing error."


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
    Vous êtes un consultant RH expérimenté chargé de rédiger un rapport d'évaluation professionnel basé sur une transcription d'entretien. Analysez la transcription fournie et produisez un rapport structuré suivant ce format exact :

    ## Structure du Rapport

    ### En-tête
     **Rapport d'évaluation**
    - **Candidat** : [Nom Prénom]
    - **Poste visé** : [Intitulé du poste]
    - **Expérience totale** : [Durée totale + détail stages/professionnel]
    - **Score global** : [Notation sur 5 étoiles avec note décimale]

    ### Section Présélection
    **Vérifications effectuées**
    - Listez les points du CV nécessitant des clarifications
    - Pour chaque point : problème identifié → confirmation/clarification obtenue
    - Utilisez des puces avec format : **[Entreprise/Élément]** : Description du problème → **Résolution**

    **Disponibilité**
    - Disponibilité immédiate ou date de prise de poste

    **Prétention salariale**
    - Fourchette mentionnée avec devise et conditions

    **Autres réponses sur les questions spécifiées par le recruteur**
    - Questions spécifiques posées et réponses obtenues

    ### Section Évaluation

    **Points forts**
    Organisez en catégories :
    - **Formation** : Diplômes, établissements, années
    - **Expériences professionnelles** : 
      - Liste des entreprises avec durées
      - Missions réalisées (sous-puces)
    - **Compétences techniques** : Outils, logiciels, certifications
    - **Langues** : Niveau de maîtrise
    - **Posture** : Qualités comportementales et motivation

    **Points faibles**
    - Identifiez 3-4 axes d'amélioration principaux
    - **[Titre du point faible]** : Explication détaillée
    - Soyez factuel et constructif

    **Recommandation**
    - **Synthèse du profil** en une phrase
    - Recommandation d'action (rencontrer, passer à l'étape suivante, etc.)
    - **Conditions recommandées** (niveau de poste, accompagnement nécessaire)
    - Justification de la recommandation

    ## Instructions d'Analyse

    1. **Extraction d'informations** :
       - Identifiez les informations factuelles (formations, expériences, compétences)
       - Repérez les clarifications apportées aux zones floues du CV
       - Notez les attentes salariales et disponibilité

    2. **Évaluation qualitative** :
       - Analysez la cohérence du parcours
       - Évaluez l'adéquation poste/profil
       - Identifiez les forces et axes d'amélioration
       - Estimez le potentiel d'évolution

    3. **Attribution du score** :
       - 5/5 : Profil excellent, parfaite adéquation
       - 4/5 : Très bon profil, quelques ajustements mineurs
       - 3/5 : Profil correct, potentiel avec accompagnement
       - 2/5 : Profil faible, écarts significatifs
       - 1/5 : Inadéquation majeure

    4. **Recommandation finale** :
       - Basez-vous sur l'analyse globale
       - Proposez des actions concrètes
       - Mentionnez les conditions de réussite

    ## Ton et Style

    - **Professionnel et objectif**
    - **Factuel et précis**
    - **Constructif dans les critiques**
    - **Format standardisé** pour faciliter la comparaison entre candidats
    - **Utilisez le gras** pour les éléments clés
    - **Puces et sous-puces** pour la lisibilité

    Transcription d'entretien à analyser :
    {summary}

    Générez maintenant le rapport d'évaluation correspondant en format JSON avec cette structure :
    {{
        "report_content": "Le rapport complet formaté en markdown selon la structure ci-dessus",
        "score": 4.2,
        "recommendation": "Synthèse de la recommandation finale"
    }}

    Le score doit être sur 5 avec une décimale (ex: 4.2/5).
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
            
            print(f"OpenAI raw response content: {content}")
            
            # Strip markdown code blocks if present
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
                print(f"Stripped markdown, cleaned content: {content}")
            
            # Parse the JSON response
            try:
                report_data = json.loads(content)
                
                # Validate the structure for new format
                if not all(k in report_data for k in ["report_content", "recommendation", "score"]):
                    raise ValueError("Missing required fields in the generated report")
                
                # Ensure score is within range (0-5 scale now)
                report_data["score"] = max(0, min(5, report_data["score"]))
                
                # Convert to the expected format for database storage
                # We'll store the full report content as a single field
                formatted_report = {
                    "report_content": report_data["report_content"],
                    "recommendation": report_data["recommendation"],
                    "score": int(report_data["score"] * 20),  # Convert 5-scale to 100-scale for compatibility
                    "strengths": ["Voir rapport complet"],  # Placeholder for backward compatibility
                    "weaknesses": ["Voir rapport complet"]   # Placeholder for backward compatibility
                }
                
                return formatted_report
                
            except json.JSONDecodeError as e:
                # If JSON parsing fails, log the error and content
                print(f"JSON parsing failed: {str(e)}")
                print(f"Failed to parse content: {content}")
                return {
                    "report_content": "# Rapport d'évaluation\n\nErreur lors de l'analyse automatique de la transcription. Veuillez analyser manuellement.",
                    "recommendation": "Analyse manuelle requise en raison d'une erreur de traitement",
                    "score": 65,
                    "strengths": ["Voir rapport complet"],
                    "weaknesses": ["Voir rapport complet"]
                }
    
    except Exception as e:
        print(f"Error generating report with OpenAI: {str(e)}")
        # Return a default response in case of error
        return {
            "report_content": "# Rapport d'évaluation\n\n**Erreur de traitement**\n\nImpossible de générer le rapport automatiquement. Une analyse manuelle est requise.",
            "recommendation": "Erreur de traitement - analyse manuelle requise",
            "score": 50,
            "strengths": ["Voir rapport complet"],
            "weaknesses": ["Voir rapport complet"]
        }
