import random

from src.app_config import config
from src.db.models.postgres import postgres_factories
from src.util.local import load_local_env_vars
from tests.src.db.models.factories import SupportFactory, SupportListingFactory

names = [
    "Foundation Communities",
    "Salvation Army",
    "Any Baby Can",
    "Safe Alliance",
    "Manos de Cristo",
    "El Buen Samaritano",
    "Workforce Solutions (Capital & Rural Area)",
    "Lifeworks",
    "American YouthWorks",
    "Skillpoint Alliance",
    "Literacy Coalition",
    "Austin Area Urban League",
    "Austin Career Institute",
    "Capital IDEA",
    "Central Texas Food Bank",
    "St. Vincent De Paul",
    "Southside Community Center",
    "San Marcos Area Food Bank",
    "Community Action",
    "Catholic Charities",
    "Saint Louise House",
    "Jeremiah Program",
    "United Way",
    "Caritas",
    "Austin FreeNet",
    "AUTMHQ",
    "Austin Public Library",
    "ACC",
    "Latinitas",
    "TWC Voc Rehab",
    "Travis County Health & Human Services",
    "Mobile Loaves and Fishes",
    "Community First",
    "Other Ones Foundation",
    "Austin Integral Care",
    "Bluebonnet Trails",
    "Round Rock Area Serving Center",
    "Maximizing Hope",
    "Texas Baptist Children's Home",
    "Hope Alliance",
    "Austin Clubhouse",
    "NAMI",
    "Austin Tenants Council",
    "St. John Community Center",
    "Trinity Center",
    "Blackland Community Center",
    "Rosewood-Zaragoza Community Center",
    "Austin Public Health",
    "The Caring Place",
    "Samaritan Center",
    "Christi Center",
    "The NEST Empowerment Center",
    "Georgetown Project",
    "MAP - Central Texas",
    "Opportunities for Williamson & Burnet Counties",
]

descriptions = [
    "Provides clients with training for interviewing",
    "Trains prospective employees so that they have work experience relevant to their desired field",
    "Offers free or low-cost meals to individuals and families in need",
    "Assists clients in obtaining affordable housing options",
    "Provides access to healthcare screenings and referrals",
    "Supports families with childcare services while parents attend work or training",
    "Connects individuals to mental health counseling resources",
    "Guides clients through the process of applying for public benefits",
    "Offers English language and literacy classes",
    "Provides financial literacy workshops for budgeting and credit repair",
    "Helps individuals prepare resumes and job applications",
    "Supports youth with after-school programs and mentoring",
    "Provides transportation assistance to and from work or appointments",
    "Offers emergency utility and rental assistance",
    "Connects individuals with community volunteer and service opportunities",
]


def populate_support_listings() -> None:
    # Create a session
    load_local_env_vars()
    with config.db_session() as postgres_db_session:
        postgres_factories._postgres_db_session = postgres_db_session
        postgres_db_session.begin()

        support_listing = SupportListingFactory.build(name=random.choice(names))
        support = SupportFactory.build(
            support_listing=support_listing,
            name=random.choice(names),
            description=random.choice(descriptions),
        )

        postgres_db_session.add(support_listing)
        postgres_db_session.add(support)

        postgres_db_session.commit()
        postgres_db_session.close()
