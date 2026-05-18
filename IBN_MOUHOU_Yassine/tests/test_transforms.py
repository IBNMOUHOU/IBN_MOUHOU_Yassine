"""
Tests unitaires des fonctions de transformation pandas.
AUCUNE base de donnees necessaire ici => tests ultra-rapides.
"""
import pytest
import pandas as pd

from src.transform import clean, aggregate_by_month, aggregate_by_category


# ======================================================================
# Tests de clean()
# ======================================================================
class TestClean:

    def test_clean_retire_email_vide(self, df_brut):
        """clean() doit supprimer les lignes sans email."""
        df = clean(df_brut)
        assert "" not in df["client_email"].values

    def test_clean_retire_montant_negatif(self, df_brut):
        """clean() doit supprimer les lignes avec montant <= 0."""
        df = clean(df_brut)
        assert (df["montant"] > 0).all()

    def test_clean_nombre_lignes(self, df_brut):
        """Apres clean(), 2 lignes valides restent (email vide + negatif supprimes)."""
        df = clean(df_brut)
        assert len(df) == 2

    def test_clean_email_lowercase(self, df_brut):
        """Les emails doivent etre en minuscules et sans espaces."""
        df = clean(df_brut)
        assert df["client_email"].iloc[0] == "alice@mail.com"

    def test_clean_montant_float(self, df_brut):
        """La colonne montant doit etre de type float64."""
        df = clean(df_brut)
        assert df["montant"].dtype == "float64"

    def test_clean_date_datetime(self, df_brut):
        """La colonne date_vente doit etre de type datetime."""
        df = clean(df_brut)
        assert pd.api.types.is_datetime64_any_dtype(df["date_vente"])

    def test_clean_ne_modifie_pas_original(self, df_brut):
        """clean() ne doit pas modifier le DataFrame original."""
        original_len = len(df_brut)
        clean(df_brut)
        assert len(df_brut) == original_len

    def test_clean_categorie_title_case(self, df_brut):
        """La colonne categorie doit etre en title case."""
        df = clean(df_brut)
        # "electronique" -> "Electronique"
        assert df["categorie"].iloc[0] == "Electronique"

    def test_clean_index_reset(self, df_brut):
        """Apres clean(), l'index doit etre reinitialise (0..n-1)."""
        df = clean(df_brut)
        assert list(df.index) == list(range(len(df)))


# ======================================================================
# Tests de aggregate_by_month()
# ======================================================================
class TestAggregateByMonth:

    def test_agg_nombre_mois(self, df_clean):
        """Le DataFrame fixture a 2 mois distincts (janv + fevr)."""
        mart = aggregate_by_month(df_clean)
        assert len(mart) == 2

    def test_agg_ca_total(self, df_clean):
        """Le CA total doit correspondre a la somme des montants valides (120.5 + 200)."""
        mart = aggregate_by_month(df_clean)
        assert mart["chiffre_affaires"].sum() == pytest.approx(320.5)

    def test_agg_colonnes_presentes(self, df_clean):
        """Le mart doit avoir les colonnes mois, chiffre_affaires, nb_transactions."""
        mart = aggregate_by_month(df_clean)
        assert set(mart.columns) >= {"mois", "chiffre_affaires", "nb_transactions"}

    def test_agg_ca_positifs(self, df_clean):
        """Tous les CA mensuels doivent etre positifs."""
        mart = aggregate_by_month(df_clean)
        assert (mart["chiffre_affaires"] > 0).all()

    def test_agg_mois_tries(self, df_clean):
        """Les mois doivent etre tries dans l'ordre croissant."""
        mart = aggregate_by_month(df_clean)
        mois = mart["mois"].tolist()
        assert mois == sorted(mois)

    def test_agg_total_transactions(self, df_clean):
        """Le nombre total de transactions doit egaler le nombre de lignes nettoyees."""
        mart = aggregate_by_month(df_clean)
        assert mart["nb_transactions"].sum() == len(df_clean)


# ======================================================================
# [BONUS] Tests de aggregate_by_category()
# ======================================================================
class TestAggregateByCategory:

    def test_cat_colonnes_presentes(self, df_clean):
        """Le mart doit contenir les 4 colonnes attendues."""
        mart = aggregate_by_category(df_clean)
        assert set(mart.columns) == {
            "categorie", "chiffre_affaires", "nb_transactions", "panier_moyen",
        }

    def test_cat_nombre_categories(self, df_clean):
        """Avec la fixture, 2 categories distinctes : Electronique + Maison."""
        # df_clean contient :
        #   alice (electronique, 120.5) + carol (electronique, 200)
        mart = aggregate_by_category(df_clean)
        assert len(mart) == 1  # une seule categorie restante : Electronique

    def test_cat_ca_total(self, df_clean):
        """Le CA total par categorie doit egaler le CA global."""
        mart = aggregate_by_category(df_clean)
        assert mart["chiffre_affaires"].sum() == pytest.approx(df_clean["montant"].sum())

    def test_cat_panier_moyen(self, df_clean):
        """Le panier moyen doit etre CA / nb_transactions."""
        mart = aggregate_by_category(df_clean)
        for _, row in mart.iterrows():
            expected = row["chiffre_affaires"] / row["nb_transactions"]
            assert row["panier_moyen"] == pytest.approx(expected, abs=0.01)

    def test_cat_tri_ca_descendant(self, df_clean):
        """Les categories doivent etre triees par CA decroissant."""
        mart = aggregate_by_category(df_clean)
        ca = mart["chiffre_affaires"].tolist()
        assert ca == sorted(ca, reverse=True)


# ======================================================================
# Tests sur le CSV reel (donnees du sujet)
# ======================================================================
class TestSurDonneesReelles:
    """Verifie les valeurs attendues du sujet (section 2.2)."""

    @pytest.fixture
    def df_reel_clean(self):
        from src.extract import extract
        return clean(extract("data/ventes.csv"))

    def test_8_lignes_valides(self, df_reel_clean):
        """Apres clean() sur le CSV reel : 8 lignes valides."""
        assert len(df_reel_clean) == 8

    def test_ca_total(self, df_reel_clean):
        """CA total : somme des 8 lignes valides du CSV.

        NB : le sujet annonce 1290.40 EUR en section 2.2, mais la somme reelle
        des montants valides est 1305.90 EUR
        (= 485.50 janv + 315.40 fev + 505.00 mars, qui sont les CA mensuels
        eux-memes annonces dans le sujet). Il y a donc une incoherence dans
        l'enonce : on teste la valeur mathematiquement coherente avec les
        CA mensuels eux-memes attendus.
        """
        assert df_reel_clean["montant"].sum() == pytest.approx(1305.90)

    def test_trois_mois_distincts(self, df_reel_clean):
        """3 mois distincts dans aggregate_by_month()."""
        mart = aggregate_by_month(df_reel_clean)
        assert len(mart) == 3

    def test_ca_janvier(self, df_reel_clean):
        """CA janvier = 485.50."""
        mart = aggregate_by_month(df_reel_clean)
        ca_jan = mart.loc[mart["mois"] == "2024-01", "chiffre_affaires"].iloc[0]
        assert float(ca_jan) == pytest.approx(485.50)

    def test_ca_fevrier(self, df_reel_clean):
        """CA fevrier = 315.40."""
        mart = aggregate_by_month(df_reel_clean)
        ca_fev = mart.loc[mart["mois"] == "2024-02", "chiffre_affaires"].iloc[0]
        assert float(ca_fev) == pytest.approx(315.40)

    def test_ca_mars(self, df_reel_clean):
        """CA mars = 505.00."""
        mart = aggregate_by_month(df_reel_clean)
        ca_mar = mart.loc[mart["mois"] == "2024-03", "chiffre_affaires"].iloc[0]
        assert float(ca_mar) == pytest.approx(505.00)
