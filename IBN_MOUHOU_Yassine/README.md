# TP DataOps - Pipeline ETL avec pandas + PostgreSQL

[![ETL DataOps CI](https://github.com/IBNMOUHOU/IBN_MOUHOU_Yassine/actions/workflows/ci.yml/badge.svg)](https://github.com/IBNMOUHOU/IBN_MOUHOU_Yassine/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![PostgreSQL 15](https://img.shields.io/badge/postgresql-15-blue.svg)](https://www.postgresql.org/)
[![Coverage](https://img.shields.io/badge/coverage->80%25-brightgreen.svg)](#tests)


**Cours :** DevOps & DataOps - Jour 2
**Auteur :** IBN MOUHOU Yassine
**Encadrant :** Dr. Abdelhak Touiti

---

## Principe : ETL (et non ELT)

```
  Extract            Transform           Load
 (pd.read_csv)  →    (pandas)        →   (PostgreSQL)
   CSV source        Nettoyage           Entrepot
                     Agregation          (warehouse)
```

**Les transformations se font intégralement en pandas, AVANT toute écriture en base.**
PostgreSQL joue uniquement le rôle d'entrepôt : il reçoit des données déjà propres.

Conséquence : les fonctions de transformation sont des **fonctions pures** testables
avec pytest **sans aucune base de données**.

---

## Structure du projet

```
IBN_MOUHOU_Yassine/
├── src/
│   ├── extract.py        # E : lit le CSV → DataFrame brut
│   ├── transform.py      # T : clean(), aggregate_by_month(), aggregate_by_category()
│   ├── load.py           # L : écrit les DataFrames dans PostgreSQL
│   └── run.py            # Orchestrateur E → T → L + logging
├── data/
│   └── ventes.csv        # Fichier source (10 lignes, 2 invalides)
├── tests/
│   ├── conftest.py       # Fixtures DataFrames + connexion DB
│   ├── test_transforms.py  # Tests unitaires pandas (SANS DB)
│   └── test_load.py      # Tests d'intégration PostgreSQL
├── .github/workflows/
│   └── ci.yml            # GitHub Actions CI
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## Installation et exécution

### 1. Prérequis

- Python 3.10+
- Docker Desktop
- Git

### 2. Cloner et installer les dépendances

```bash
git clone https://github.com/IBNMOUHOU/IBN_MOUHOU_Yassine.git
cd IBN_MOUHOU_Yassine
python -m venv .venv
source .venv/bin/activate     
pip install -r requirements.txt
```

### 3. Démarrer PostgreSQL (entrepôt)

```bash
docker-compose up -d
docker ps                                                 # vérifier que etl_warehouse tourne
docker exec -it etl_warehouse psql -U etl_user -d warehouse -c "\l"
```

### 4. Lancer le pipeline ETL

```bash
python src/run.py
```

Sortie attendue :

```
=== Pipeline ETL DataOps ===
[1/3] Extract ...
[Extract] 10 lignes lues depuis data/ventes.csv

[2/3] Transform (pandas) ...
  2 lignes invalides ecartees
  8 lignes valides
  3 mois agreges
  3 categories agregees

[3/3] Load (PostgreSQL) ...
  ventes_propres   : 8 lignes
  ca_par_mois      : 3 lignes
  ca_par_categorie : 3 lignes

[DONE] Pipeline ETL termine avec succes.
```

### 5. Vérifier les tables dans PostgreSQL

```bash
docker exec -it etl_warehouse psql -U etl_user -d warehouse
```

```sql
SELECT COUNT(*) FROM ventes_propres;      -- 8
SELECT * FROM ca_par_mois ORDER BY mois;  -- 3 lignes
SELECT * FROM ca_par_categorie;           -- 3 lignes triées par CA décroissant
SELECT * FROM run_log ORDER BY run_at;    -- historique des exécutions
```

---

## Tests

### Tests unitaires pandas (ultra-rapides, sans DB)

```bash
pytest -v tests/test_transforms.py
```

26 tests, exécution < 1 seconde. Ces tests fonctionnent sans PostgreSQL — c'est la
puissance de l'approche ETL : les transformations sont des fonctions pures.

### Tests d'intégration (avec PostgreSQL)

```bash
docker-compose up -d
pytest -v tests/test_load.py
```

### Tous les tests + couverture (bonus)

```bash
pytest --cov=src --cov-report=term-missing --cov-report=html tests/
open htmlcov/index.html    # macOS
xdg-open htmlcov/index.html # Linux
```

**Couverture cible : > 80%**

---

## Données de test

`data/ventes.csv` contient 10 lignes, dont **2 invalides intentionnelles** :

| Cas               | Ligne | Anomalie         | Action de `clean()` |
| ----------------- | ----- | ---------------- | ------------------- |
| Email vide        | 7     | `client_email=""` | Supprimée           |
| Montant négatif   | 10    | `montant=-10.00`  | Supprimée           |

**Valeurs attendues après transformation :**

- Lignes valides : **8**
- CA janvier : **485,50 EUR**
- CA février : **315,40 EUR**
- CA mars : **505,00 EUR**
- CA total : **1 305,90 EUR** *(somme cohérente des CA mensuels ; l'énoncé annonce 1 290,40 mais cette valeur n'est pas cohérente avec les CA mensuels annoncés — voir commentaire dans `tests/test_transforms.py`)*

---

## Bonus implémentés (+10 pts)

| Bonus | Pts | Implémentation |
| --- | --- | --- |
| Badge GitHub Actions vert dans README | +3 | En haut de ce fichier |
| Couverture de tests > 80% (pytest-cov) | +3 | Étape `Couverture de tests` dans `ci.yml` |
| `aggregate_by_category(df)` + tests | +4 | `src/transform.py` + classe `TestAggregateByCategory` + table `ca_par_categorie` |

---

## CI/CD - GitHub Actions

Le workflow `.github/workflows/ci.yml` :

1. Démarre un service PostgreSQL 15
2. Installe les dépendances
3. Lance les tests pandas (sans DB) — passent même si PostgreSQL n'est pas prêt
4. Lance les tests d'intégration (avec PostgreSQL)
5. Génère un rapport de couverture
6. Upload le rapport `coverage.xml` en artefact

---

## Nettoyage

```bash
docker-compose down          # arrêter PostgreSQL (volume préservé)
docker-compose down -v       # arrêter + supprimer les données
```
