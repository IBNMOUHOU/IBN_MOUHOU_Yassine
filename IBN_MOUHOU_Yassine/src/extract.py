"""
Module Extract du pipeline ETL.
Responsabilite unique : lire la source de donnees et retourner un DataFrame BRUT.
Aucune transformation, aucun cast de type.
"""
import pandas as pd


def extract(csv_path: str) -> pd.DataFrame:
    """
    Lit le fichier CSV source et retourne un DataFrame brut.
    Aucune transformation ici : on garde tout tel quel.

    Le parametre dtype=str garantit que pandas ne fait aucune inference
    de type. Les types seront castes explicitement dans clean().
    """
    df = pd.read_csv(csv_path, dtype=str)
    print(f"[Extract] {len(df)} lignes lues depuis {csv_path}")
    return df
