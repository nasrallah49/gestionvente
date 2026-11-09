
import pandas as pd

# 1. Charger les données
df = pd.read_csv(
    "ventes.csv",
    dtype={"phone": "string", "email": "string"}
)

# Garder une copie pour la traçabilité
df["order_date"] = df["order_date"].replace(r"^\s*$", pd.NA, regex=True)

# 2. Nettoyer les espaces dans les textes
for col in ["first_name", "last_name", "email", "nom_product"]:
    df[col] = df[col].astype("string").str.strip()
    df[col] = df[col].replace("", pd.NA)

df["email"] = df["email"].str.lower()

# 3. Convertir les types
df["order_date"] = pd.to_datetime(
    df["order_date"], errors="coerce"
)

df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
df["prix_product"] = pd.to_numeric(
    df["prix_product"], errors="coerce"
)

# 4. Identifier les lignes à supprimer
motifs = pd.DataFrame(index=df.index)

motifs["vente_erronée"] = df["sale_id"].isin([9002, 9003])
motifs["date_invalide"] = df["order_date"].isna()
motifs["quantité_invalide"] = (
    df["quantity"].isna() | (df["quantity"] <= 0)
)
motifs["prix_invalide"] = (
    df["prix_product"].isna() | (df["prix_product"] <= 0)
)

# Champs obligatoires : toute valeur manquante entraîne
# la suppression de la ligne, y compris un e-mail absent.
colonnes_obligatoires = [
    "sale_id", "customer_id", "product_id", "quantity",
    "order_date", "first_name", "last_name",
    "email", "phone", "nom_product", "prix_product"
]

motifs["champ_manquant"] = df[
    colonnes_obligatoires
].isna().any(axis=1)

# Doublons exacts
motifs["doublon_exact"] = df.duplicated(keep="first")

# Identifiants de vente dupliqués
motifs["sale_id_duplique"] = df.duplicated(
    subset=["sale_id"], keep="first"
)

# Une ligne est supprimée si au moins une règle est violée
a_supprimer = motifs.any(axis=1)

# 5. Créer le fichier des lignes supprimées
lignes_supprimees = df.loc[a_supprimer].copy()

lignes_supprimees["motif_suppression"] = motifs.loc[
    a_supprimer
].apply(
    lambda ligne: ", ".join(ligne.index[ligne.values]),
    axis=1
)

# 6. Créer le fichier propre
df_clean = df.loc[~a_supprimer].copy()

# Supprimer les colonnes redondantes si elles sont identiques
for col1, col2 in [
    ("customer_id", "idcustomers"),
    ("product_id", "idproduct")
]:
    if col1 in df_clean.columns and col2 in df_clean.columns:
        if df_clean[col1].equals(df_clean[col2]):
            df_clean.drop(columns=[col2], inplace=True)

# 7. Exporter les résultats
df_clean.to_csv("ventes_propres.csv", index=False)
lignes_supprimees.to_csv("ventes_supprimees.csv", index=False)

# 8. Bilan
print("Lignes initiales :", len(df))
print("Lignes supprimées :", len(lignes_supprimees))
print("Lignes conservées :", len(df_clean))
print("\nValeurs manquantes restantes :")
print(df_clean.isna().sum())
print("\nFichiers créés :")
print("- ventes_propres.csv")
print("- ventes_supprimees.csv")
