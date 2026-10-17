"""
Skill Inference Engine
Extracts likely skills from free text using TF-IDF cosine similarity
against a curated skills taxonomy. Inferred skills are marked unverified.
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple

# ─── Skills Taxonomy ─────────────────────────────────────────────────────────
# Each entry: (canonical_skill_name, description + keywords)
SKILLS_TAXONOMY = [
    ("Python",          "python programming scripting data science automation flask django fastapi"),
    ("Java",            "java programming spring boot enterprise jvm backend"),
    ("JavaScript",      "javascript typescript node js react angular frontend web"),
    ("REST API Design", "rest api restful http json endpoint openapi swagger design"),
    ("GraphQL",         "graphql api query mutations subscriptions"),
    ("Microservices",   "microservices distributed systems service mesh architecture"),
    ("Cloud Deployment","cloud deployment aws azure gcp cloud native infrastructure saas"),
    ("Kubernetes",      "kubernetes k8s container orchestration pods deployments helm"),
    ("Docker",          "docker container containerization dockerfile compose"),
    ("Terraform",       "terraform infrastructure as code iac provisioning cloud"),
    ("CI/CD Pipelines", "ci cd pipeline github actions jenkins gitlab devops automation"),
    ("Linux",           "linux unix bash shell scripting sysadmin ubuntu centos"),
    ("PostgreSQL",      "postgresql postgres sql relational database rdbms"),
    ("MySQL",           "mysql mariadb relational database sql"),
    ("MongoDB",         "mongodb nosql document database json bson"),
    ("SQL",             "sql structured query language database queries joins aggregate"),
    ("Data Pipelines",  "data pipelines etl elt airflow spark databricks batch streaming"),
    ("Machine Learning","machine learning ml scikit learn model training classification regression"),
    ("Deep Learning",   "deep learning neural networks pytorch tensorflow keras"),
    ("Data Engineering","data engineering warehouse lakehouse dbt snowflake redshift"),
    ("Test Automation", "test automation selenium pytest junit testing qa automated"),
    ("Selenium",        "selenium webdriver browser automation end to end testing"),
    ("Performance Testing","performance load testing jmeter gatling k6"),
    ("Security",        "security penetration testing owasp vulnerability assessment"),
    ("Kafka",           "kafka event streaming messaging pub sub distributed"),
    ("Redis",           "redis cache in memory key value store"),
    ("Elasticsearch",   "elasticsearch search engine kibana logstash elk"),
    ("Flask",           "flask python web framework microframework rest"),
    ("Django",          "django python web framework orm admin cms"),
    ("Spring Boot",     "spring boot java framework rest microservices enterprise"),
    ("React",           "react reactjs frontend javascript ui components hooks"),
    ("Git",             "git version control github gitlab branching merge"),
    ("Agile",           "agile scrum kanban sprint retrospective story points"),
    ("Technical Writing","technical writing documentation markdown api docs"),
    ("Project Management","project management planning risk stakeholders"),
    ("Leadership",      "leadership team lead mentoring coaching management"),
    ("z/OS",            "zos ibm mainframe mvs jcl batch processing"),
    ("COBOL",           "cobol mainframe legacy programming ibm z"),
    ("JCL",             "jcl job control language mainframe batch ibm"),
    ("Db2",             "db2 ibm relational database mainframe linux"),
    ("LinuxONE",        "linuxone ibm z s390x linux enterprise server"),
]

_skill_names = [s[0] for s in SKILLS_TAXONOMY]
_skill_docs  = [s[1] for s in SKILLS_TAXONOMY]

_vectorizer = TfidfVectorizer(ngram_range=(1, 2))
_taxonomy_matrix = _vectorizer.fit_transform(_skill_docs)


def infer_skills(text: str, top_k: int = 8, threshold: float = 0.10) -> List[Tuple[str, float]]:
    """
    Given free text (resume snippet, project note), return the most likely
    skills with confidence scores. All results are marked unverified.

    Returns: [(skill_name, confidence_score), ...] sorted descending by score
    """
    if not text or not text.strip():
        return []

    query_vec = _vectorizer.transform([text.lower()])
    similarities = cosine_similarity(query_vec, _taxonomy_matrix).flatten()

    results = [
        (_skill_names[i], float(similarities[i]))
        for i in range(len(_skill_names))
        if similarities[i] >= threshold
    ]
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def get_all_skill_names() -> List[str]:
    """Return the full canonical skills taxonomy list."""
    return _skill_names.copy()
