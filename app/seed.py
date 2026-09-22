"""
Starter roles, matching the example in the project brief:
Software Engineer, Backend Developer, Data Engineer, UI/UX Designer.

Skill names are shared across roles on purpose ("Databases & SQL" appears in
two roles), so one interview can be compared against every role.
Keywords are only used by the mock evaluator.
"""
from sqlalchemy.orm import Session

from app.models import Role

PROGRAMMING = {"name": "Programming fundamentals", "keywords": ["python", "java", "javascript", "code", "programming", "function", "class", "debugging"]}
ALGORITHMS = {"name": "Data structures & algorithms", "keywords": ["algorithm", "complexity", "array", "hash", "tree", "graph", "sorting", "recursion"]}
SYSTEM_DESIGN = {"name": "System design", "keywords": ["architecture", "scalable", "scaling", "cache", "microservice", "microservices", "load", "design"]}
TESTING = {"name": "Testing", "keywords": ["test", "tests", "testing", "unit", "pytest", "junit", "integration", "ci"]}
COLLABORATION = {"name": "Version control & collaboration", "keywords": ["git", "pull", "review", "branch", "agile", "scrum", "team"]}
APIS = {"name": "REST APIs", "keywords": ["api", "apis", "rest", "endpoint", "http", "json", "fastapi", "spring"]}
SQL = {"name": "Databases & SQL", "keywords": ["sql", "database", "postgres", "postgresql", "mysql", "query", "index", "join"]}
PIPELINES = {"name": "Data pipelines", "keywords": ["pipeline", "etl", "airflow", "spark", "batch", "streaming", "kafka", "warehouse"]}
CLOUD = {"name": "Cloud platforms", "keywords": ["aws", "azure", "gcp", "cloud", "docker", "kubernetes", "s3", "lambda"]}
RESEARCH = {"name": "User research", "keywords": ["research", "persona", "personas", "usability", "survey", "interviews", "users", "journey"]}
VISUAL = {"name": "Visual & interaction design", "keywords": ["figma", "prototype", "wireframe", "wireframes", "layout", "typography", "colour", "color"]}
ACCESSIBILITY = {"name": "Accessibility", "keywords": ["accessibility", "accessible", "wcag", "contrast", "screen", "keyboard", "inclusive"]}


def skill(base: dict, weight: float, required_level: int, critical: bool = False) -> dict:
    return {**base, "weight": weight, "required_level": required_level, "critical": critical}


STARTER_ROLES = [
    {
        "title": "Software Engineer",
        "description": "Builds and maintains production software across the stack as part of a product team.",
        "skills": [
            skill(PROGRAMMING, 3, 4, critical=True),
            skill(ALGORITHMS, 2, 3),
            skill(SYSTEM_DESIGN, 2, 3),
            skill(TESTING, 1, 3),
            skill(COLLABORATION, 1, 3),
        ],
    },
    {
        "title": "Backend Developer",
        "description": "Designs and runs the APIs and services behind the company's products.",
        "skills": [
            skill(APIS, 3, 4, critical=True),
            skill(PROGRAMMING, 2, 4, critical=True),
            skill(SQL, 2, 3),
            skill(SYSTEM_DESIGN, 2, 3),
            skill(TESTING, 1, 3),
        ],
    },
    {
        "title": "Data Engineer",
        "description": "Builds reliable data pipelines and models data for analytics.",
        "skills": [
            skill(SQL, 3, 4, critical=True),
            skill(PIPELINES, 3, 3, critical=True),
            skill(PROGRAMMING, 2, 3),
            skill(CLOUD, 1, 2),
        ],
    },
    {
        "title": "UI/UX Designer",
        "description": "Researches user needs and designs clear, accessible interfaces.",
        "skills": [
            skill(RESEARCH, 3, 4, critical=True),
            skill(VISUAL, 3, 4, critical=True),
            skill(ACCESSIBILITY, 1, 3),
            skill(COLLABORATION, 1, 3),
        ],
    },
]


def seed_roles(db: Session) -> None:
    """Insert the starter roles only if the table is empty."""
    if db.query(Role).first() is not None:
        return
    db.add_all(Role(**data) for data in STARTER_ROLES)
    db.commit()
