"""
Module Transform du pipeline ETL.
Toutes les transformations se font ici, en pandas, AVANT toute ecriture en base.
Chaque fonction est pure : elle prend un DataFrame, retourne un DataFrame,
et ne modifie pas son entree.
"""
import pandas as pd


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie le DataFrame brut :
      - Cast des types (id, montant, date_vente)
      - Normalisation des emails (lower + strip) et categories (title + strip)
      - Suppression des lignes invalides :
          * email vide ou NaN
          * montant absent ou <= 0
          * date_vente non parsable
    Retourne une copie propre (n'altere pas l'original).
    """
    df = df.copy()

    # 1. Cast des types
    df["montant"] = pd.to_numeric(df["montant"], errors="coerce")
    df["date_vente"] = pd.to_datetime(df["date_vente"], errors="coerce")
    df["id"] = pd.to_numeric(df["id"], errors="coerce")

    # 2. Nettoyage email et categorie
    df["client_email"] = df["client_email"].str.strip().str.lower()
    df["categorie"] = df["categorie"].str.strip().str.title()

    # 3. Suppression des lignes invalides
    df = df[df["client_email"].notna() & (df["client_email"] != "")]
    df = df[df["montant"].notna() & (df["montant"] > 0)]
    df = df[df["date_vente"].notna()]

    return df.reset_index(drop=True)


def aggregate_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agregation mensuelle du chiffre d'affaires.
    Prend en entree le DataFrame nettoye (sortie de clean()).
    Retourne un DataFrame avec les colonnes : mois, chiffre_affaires, nb_transactions.
    """
    df = df.copy()
    df["mois"] = df["date_vente"].dt.to_period("M").astype(str)

    mart = (
        df.groupby("mois")
        .agg(
            chiffre_affaires=("montant", "sum"),
            nb_transactions=("montant", "count"),
        )
        .reset_index()
        .sort_values("mois")
        .reset_index(drop=True)
    )
    return mart


def aggregate_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    [BONUS] Agregation par categorie de produit.
    Prend en entree le DataFrame nettoye (sortie de clean()).
    Retourne un DataFrame avec les colonnes :
      - categorie
      - chiffre_affaires (somme des montants)
      - nb_transactions (nombre de ventes)
      - panier_moyen (CA / nb_transactions)
    """
    df = df.copy()

    mart = (
        df.groupby("categorie")
        .agg(
            chiffre_affaires=("montant", "sum"),
            nb_transactions=("montant", "count"),
        )
        .reset_index()
    )
    mart["panier_moyen"] = (mart["chiffre_affaires"] / mart["nb_transactions"]).round(2)
    mart = mart.sort_values("chiffre_affaires", ascending=False).reset_index(drop=True)
    return mart
