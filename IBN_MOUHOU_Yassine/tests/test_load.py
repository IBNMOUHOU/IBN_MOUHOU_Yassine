"""
Tests d'integration : verifient le chargement dans PostgreSQL.
Necessite un PostgreSQL accessible via DATABASE_URL.
"""
import pytest

from src.load import (
    create_tables,
    load_ventes,
    load_mart,
    load_mart_categorie,
)
from src.transform import aggregate_by_month, aggregate_by_category


@pytest.fixture(scope="module", autouse=True)
def setup_db(db, engine, df_clean):
    """Prepare la base : cree les tables et charge les donnees de test."""
    create_tables(db)
    load_ventes(df_clean, engine)
    load_mart(aggregate_by_month(df_clean), engine)
    load_mart_categorie(aggregate_by_category(df_clean), engine)


def _scalar(db, sql):
    """Helper : execute une requete et retourne la premiere colonne du premier rang."""
    with db.cursor() as cur:
        cur.execute(sql)
        return cur.fetchone()[0]


# ======================================================================
# Tests sur ventes_propres
# ======================================================================
class TestLoadVentes:

    def test_ventes_propres_count(self, db, df_clean):
        """La table doit contenir le meme nombre de lignes que le DataFrame."""
        n = _scalar(db, "SELECT COUNT(*) FROM ventes_propres")
        assert n == len(df_clean)

    def test_ventes_pas_de_montant_negatif(self, db):
        """Aucun montant negatif dans la table."""
        n = _scalar(db, "SELECT COUNT(*) FROM ventes_propres WHERE montant <= 0")
        assert n == 0

    def test_ventes_pas_email_vide(self, db):
        """Aucun email vide dans la table."""
        n = _scalar(db, """
            SELECT COUNT(*) FROM ventes_propres
            WHERE client_email IS NULL OR client_email = ''
        """)
        assert n == 0

    def test_ventes_emails_lowercase(self, db):
        """Tous les emails charges doivent etre en minuscules."""
        n = _scalar(db, """
            SELECT COUNT(*) FROM ventes_propres
            WHERE client_email <> LOWER(client_email)
        """)
        assert n == 0


# ======================================================================
# Tests sur ca_par_mois
# ======================================================================
class TestLoadMart:

    def test_ca_par_mois_count(self, db):
        """La table ca_par_mois doit contenir 2 mois (fixture)."""
        n = _scalar(db, "SELECT COUNT(*) FROM ca_par_mois")
        assert n == 2

    def test_ca_par_mois_ca_positif(self, db):
        """Tous les CA mensuels doivent etre positifs."""
        mini = _scalar(db, "SELECT MIN(chiffre_affaires) FROM ca_par_mois")
        assert float(mini) > 0

    def test_ca_par_mois_colonnes(self, db):
        """La table doit avoir les colonnes mois, chiffre_affaires, nb_transactions."""
        with db.cursor() as cur:
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'ca_par_mois'
            """)
            cols = {row[0] for row in cur.fetchall()}
        assert {"mois", "chiffre_affaires", "nb_transactions"} <= cols


# ======================================================================
# [BONUS] Tests sur ca_par_categorie
# ======================================================================
class TestLoadMartCategorie:

    def test_ca_par_categorie_count(self, db):
        """La table doit contenir au moins une categorie."""
        n = _scalar(db, "SELECT COUNT(*) FROM ca_par_categorie")
        assert n >= 1

    def test_ca_par_categorie_panier_positif(self, db):
        """Tous les paniers moyens doivent etre strictement positifs."""
        mini = _scalar(db, "SELECT MIN(panier_moyen) FROM ca_par_categorie")
        assert float(mini) > 0


# ======================================================================
# Test end-to-end : execution complete de run.py
# ======================================================================
class TestPipelineEndToEnd:
    """Execute le pipeline complet via run.py et verifie le resultat dans la DB."""

    def test_run_py_execution(self, db):
        """run.py doit s'executer sans erreur et charger les 8 lignes attendues."""
        import subprocess, sys, os
        env = os.environ.copy()
        # Le CI definit deja DATABASE_URL ; en local on utilise la meme valeur que conftest
        result = subprocess.run(
            [sys.executable, "src/run.py"],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, f"run.py a echoue : {result.stderr}"

        # 8 lignes valides chargees apres execution du vrai pipeline
        n = _scalar(db, "SELECT COUNT(*) FROM ventes_propres")
        assert n == 8

        # 3 mois distincts (janv + fev + mars)
        n_mois = _scalar(db, "SELECT COUNT(*) FROM ca_par_mois")
        assert n_mois == 3

        # run_log contient au moins une entree de succes
        n_log = _scalar(db, "SELECT COUNT(*) FROM run_log WHERE statut = 'success'")
        assert n_log >= 1
