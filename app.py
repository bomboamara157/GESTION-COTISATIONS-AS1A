import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
ADMIN_PASSWORD = "ton_mot_de_passe" # ⚠️ CHANGE-LE !

st.set_page_config(page_title="Finance Classe AS1A", layout="wide")

# Connexion au Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# Chargement des données
df = conn.read(ttl=0) # ttl=0 pour forcer la lecture des données fraîches

# On définit les motifs (les colonnes après 'Nom' et 'Surplus')
# On suppose que ton Sheet a : Nom, Surplus, GEH, MOMENT DE JOIE...
all_columns = df.columns.tolist()
motifs_cols = [c for c in all_columns if c not in ["Nom", "Surplus"]]

# --- INTERFACE ---
st.sidebar.title("🔐 Administration")
pwd_input = st.sidebar.text_input("Mot de passe", type="password")
is_admin = (pwd_input == ADMIN_PASSWORD)

st.title("📊 Suivi des Cotisations - Google Sheets Edition")

if is_admin:
    st.header("🛠 Espace Admin")
    nom_sel = st.selectbox("Élève à modifier", df["Nom"].unique())
    idx = df.index[df["Nom"] == nom_sel][0]
    
    cols_edit = st.columns(len(motifs_cols) + 1)
    
    # Modification des motifs (cases à cocher)
    for i, m in enumerate(motifs_cols):
        val_actuelle = df.at[idx, m]
        # On gère si la case est vide ou contient "Payé"
        is_checked = True if str(val_actuelle).strip().lower() in ["true", "payé", "✅ payé"] else False
        df.at[idx, m] = cols_edit[i].checkbox(m, value=is_checked, key=f"ch_{idx}_{m}")
    
    # Modification du Surplus
    df.at[idx, "Surplus"] = cols_edit[-1].number_input("Surplus", value=float(df.at[idx, "Surplus"]), key=f"sur_{idx}")

    if st.button("💾 Enregistrer dans Google Sheets"):
        # On transforme les booléens en texte propre avant l'envoi
        for m in motifs_cols:
            df[m] = df[m].apply(lambda x: "✅ Payé" if x == True or str(x) == "✅ Payé" else "❌ Impayé")
        
        conn.update(data=df)
        st.success("Données sauvegardées pour toujours !")
        st.rerun()

# --- AFFICHAGE PUBLIC ---
st.divider()
st.subheader("📋 État de la classe")

# On crée une copie pour l'affichage visuel
df_visuel = df.copy()

# Affichage du tableau
st.dataframe(df_visuel, use_container_width=True, hide_index=True)

if not is_admin:
    st.info("Connectez-vous dans la barre latérale pour modifier les statuts.")
