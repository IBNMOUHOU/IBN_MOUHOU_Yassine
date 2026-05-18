"""
Module Load du pipeline ETL.
Ecrit les DataFrames deja propres dans PostgreSQL (role d'entrepot).
Aucune transformation ici.
"""
import pandas as pd
from sqlalchemy import create_engine


def get_engine(database_url: str):
    """Retourne un moteur SQLAlchemy pour df.to_sql()."""
    return create_engine(database_url)


def create_tables(conn):
    """
    Cree les tables de l'entrepot si elles n'existent pas.
    Les donnees arriveront deja propres depuis pandas.
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ventes_propres (
                id            INTEGER,
                client_email  TEXT,
                date_vente    DATE,
                montant       NUMERIC,
                categorie     TEXT
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ca_par_mois (
                mois             TEXT,
                chiffre_affaires NUMERIC,
                nb_transactions  INTEGER
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ca_par_categorie (
                categorie        TEXT,
                chiffre_affaires NUMERIC,
                nb_transactions  INTEGER,
                panier_moyen     NUMERIC
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS run_log (
                id        SERIAL PRIMARY KEY,
                run_at    TIMESTAMP DEFAULT NOW(),
                etape     TEXT,
                statut    TEXT,
                nb_lignes INTEGER,
                message   TEXT
            );
        """)
    conn.commit()


def load_ventes(df: pd.DataFrame, engine) -> int:
    """Charge le DataFrame nettoye dans ventes_propres."""
    df.to_sql(
        "ventes_propres",
        engine,
        if_exists="replace",
        index=False,
        method="multi",
    )
    return len(df)


def load_mart(df: pd.DataFrame, engine) -> int:
    """Charge le DataFrame agrege par mois dans ca_par_mois."""
    df.to_sql(
        "ca_par_mois",
        engine,
        if_exists="replace",
        index=False,
        method="multi",
    )
    return len(df)


def load_mart_categorie(df: pd.DataFrame, engine) -> int:
    """[BONUS] Charge le DataFrame agrege par categorie dans ca_par_categorie."""
    df.to_sql(
        "ca_par_categorie",
        engine,
        if_exists="replace",
        index=False,
        method="multi",
    )
    return len(df)


def log_etape(conn, etape: str, statut: str,
              nb_lignes: int = None, message: str = None):
    """Enregistre une etape du pipeline dans run_log (table d'audit)."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO run_log (etape, statut, nb_lignes, message)
            VALUES (%s, %s, %s, %s)
        """, (etape, statut, nb_lignes, message))
    conn.commit()
