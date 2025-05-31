import os
import argparse
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, Table, Column, Integer, String, Text, Date, MetaData, text
from sqlalchemy.orm import sessionmaker
from datetime import date

def seed_jobs(force=False):
    # Get database connection parameters from environment variables
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")  # Use environment variable or default to 'db' for Docker
    port = os.getenv("POSTGRES_PORT")
    db = os.getenv("POSTGRES_DB")
    
    # Create a direct database URL for local connection
    database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    print(f"Connecting to: {database_url}")
    
    # Create a new session
    engine = create_engine(database_url)
    
    # Create metadata object
    metadata = MetaData()
    
    # Define tables directly using SQLAlchemy Core to avoid model dependencies
    jobs = Table(
        'jobs', 
        metadata,
        Column('id', Integer, primary_key=True),
        Column('title', String),
        Column('company', String),
        Column('location', String),
        Column('description', Text),
        Column('posted_date', Date)
    )
    
    job_requirements = Table(
        'job_requirements',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('requirement', String, nullable=False),
        Column('job_id', Integer)
    )
    
    # Sample job data
    jobs_data = [
        {
            "title": "Full Stack Developer",
            "company": "BM Tech",
            "location": "Remote",
            "description": "We are looking for a Full Stack Developer to join our team. The ideal candidate should have experience with both frontend and backend technologies.",
            "posted_date": date.today(),
            "requirements": [
                "3+ years of experience with JavaScript/TypeScript",
                "Experience with React or Angular",
                "Experience with Node.js or Python",
                "Knowledge of SQL and NoSQL databases",
                "Good communication skills"
            ]
        },
        {
            "title": "Data Scientist",
            "company": "BM Tech",
            "location": "Algeirs, Algeria",
            "description": "Join our data science team to work on cutting-edge machine learning projects and help drive business decisions through data analysis.",
            "posted_date": date.today(),
            "requirements": [
                "MS or PhD in Computer Science, Statistics, or related field",
                "Experience with Python, R, or Julia",
                "Knowledge of machine learning frameworks like TensorFlow or PyTorch",
                "Experience with data visualization tools",
                "Strong analytical and problem-solving skills"
            ]
        },
        {
            "title": "DevOps Engineer",
            "company": "BM Tech",
            "location": "Algeirs, Algeria",
            "description": "Looking for a DevOps Engineer to help us build and maintain our cloud infrastructure and CI/CD pipelines.",
            "posted_date": date.today(),
            "requirements": [
                "Experience with AWS, Azure, or GCP",
                "Knowledge of Docker and Kubernetes",
                "Experience with CI/CD tools like Jenkins or GitHub Actions",
                "Scripting skills in Python, Bash, or PowerShell",
                "Understanding of infrastructure as code principles"
            ]
        },
        {
            "title": "UX/UI Designer",
            "company": "BM Tech",
            "location": "Remote",
            "description": "We're seeking a talented UX/UI Designer to create beautiful and intuitive user interfaces for our web and mobile applications.",
            "posted_date": date.today(),
            "requirements": [
                "Portfolio demonstrating UI/UX projects",
                "Proficiency in design tools like Figma, Sketch, or Adobe XD",
                "Understanding of user-centered design principles",
                "Experience with responsive design",
                "Ability to collaborate with developers and stakeholders"
            ]
        },
        {
            "title": "Backend Engineer",
            "company": "BM Tech",
            "location": "Algeirs, Algeria",
            "description": "Join our backend team to build scalable and secure APIs for our financial services platform.",
            "posted_date": date.today(),
            "requirements": [
                "Strong experience with Java, Python, or Go",
                "Knowledge of RESTful API design",
                "Experience with relational databases",
                "Understanding of microservices architecture",
                "Knowledge of security best practices"
            ]
        }
    ]
    
    try:
        # Check if jobs already exist
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) FROM jobs"))
            existing_jobs_count = result.scalar()
        
        if existing_jobs_count > 0 and not force:
            print(f"There are already {existing_jobs_count} jobs in the database. Use --force to add more jobs.")
            return
        
        # Add jobs and their requirements
        with engine.begin() as connection:  # This automatically handles transactions
            for job_data in jobs_data:
                requirements = job_data.pop("requirements")
                
                # Insert job
                result = connection.execute(jobs.insert().values(**job_data))
                job_id = result.inserted_primary_key[0]
                
                # Insert requirements for the job
                for req_text in requirements:
                    connection.execute(job_requirements.insert().values(
                        requirement=req_text,
                        job_id=job_id
                    ))
            
            print(f"Successfully seeded {len(jobs_data)} jobs with their requirements.")
    except Exception as e:
        print(f"Error seeding jobs: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Seed jobs into the database')
    parser.add_argument('--force', action='store_true', help='Force adding jobs even if some already exist')
    args = parser.parse_args()
    
    seed_jobs(force=args.force)
