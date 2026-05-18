"""
Fixtures partagees pour les tests.

Deux categories :
  - Fixtures pandas (df_brut, df_clean) : utilisables SANS base de donnees.
  - Fixtures PostgreSQL (db, engine)    : pour les tests d'integration uniquement.
"""
import os
import pytest
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://etl_user:etl_secret@localhost:5432/warehouse",
)


# ----------------------------------------------------------------------
# Fixtures pandas (SANS base de donnees)
# ----------------------------------------------------------------------

@pytest.fixture
def df_brut():
    """DataFrame brut avec lignes invalides intentionnelles.

    4 lignes :
      - ligne 0 : valide (avec majuscules + espace dans l'email)
      - ligne 1 : invalide (email vide)
      - ligne 2 : invalide (montant negatif)
      - ligne 3 : valide
    => Apres clean(), il doit rester 2 lignes.
    """
    return pd.DataFrame({
        "id": ["1", "2", "3", "4"],
        "client_email": [
            "Alice@Mail.com ",
            "",
            "bob@mail.com",
            "carol@mail.com",
        ],
        "date_vente": [
            "2024-01-05",
            "2024-01-06",
            "2024-01-07",
            "2024-02-01",
        ],
        "montant": ["120.5", "50", "-10", "200"],
        "categorie": [
            "electronique",
            "vetements",
            "maison",
            "electronique",
        ],
    })


@pytest.fixture
def df_clean(df_brut):
    """DataFrame apres clean() - reutilisable dans tous les tests."""
    from src.transform import clean
    return clean(df_brut)


# ----------------------------------------------------------------------
# Fixtures PostgreSQL (tests d'integration uniquement)
# ----------------------------------------------------------------------

@pytest.fixture(scope="session")
def db():
    """Connexion psycopg2 partagee pour toute la session de tests."""
    conn = psycopg2.connect(DATABASE_URL)
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def engine():
    """Moteur SQLAlchemy partage pour toute la session de tests."""
    return create_engine(DATABASE_URL)
