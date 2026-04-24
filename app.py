import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
ADMIN_PASSWORD = "ton_mot_de_passe" # ⚠️ À changer
MONTANT_PAR_MOTIF = 500 

st.set_page_config(page_title="Gestion Finance AS1A", layout="wide")

# Connexion Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Lecture des données
    df = conn.read(ttl=0)
    df.columns = [str(c).strip() for c in df.columns]

    # Sécurité : Si 'Nom' ou 'Surplus' manquent, on les crée pour éviter le crash
    if "Nom" not in df.columns:
        st.error("⚠️ La colonne 'Nom' est absente de ton Google Sheet (Case A1).")
        st.stop()
    if "Surplus" not in df.columns:
        df["Surplus"] = 0

    # Détection automatique des motifs (Tout sauf Nom, Surplus et Reste)
    motifs = [c for c in df.columns if c not in ["Nom", "Surplus", "Reste à Payer"]]

    st.title("📊 Suivi des Cotisations Dynamique")

    # --- CALCUL DU RESTE ---
    def calculer_reste(row):
        # On compte les ✅ dans les colonnes de motifs
        nb_paye = sum(1 for m in motifs if str(row[m]).strip() == "✅")
        total_du = len(motifs) * MONTANT_PAR_MOTIF
        # On convertit le surplus en nombre au cas où
        try:
            val_surplus = float(row["Surplus"]) if pd.notnull(row["Surplus"]) else 0
        except:
            val_surplus = 0
        
        deja_paye = (nb_paye * MONTANT_PAR_MOTIF) + val_surplus
        return max(0, total_du - deja_paye)

    df["Reste à Payer"] = df.apply(calculer_reste, axis=1)

    # --- ADMINISTRATION ---
    st.sidebar.title("🔐 Administration")
    pwd = st.sidebar.text_input("Mot de passe", type="password")
    
    if pwd == ADMIN_PASSWORD:
        st.header("🛠 Mise à jour")
        nom_sel = st.selectbox("Élève", df["Nom"].dropna().unique())
        idx = df.index[df["Nom"] == nom_sel][0]
        
        with st.form("form_ultra"):
            st.write(f"Gestion pour : **{nom_sel}**")
            cols = st.columns(min(len(motifs), 4) if motifs else 1)
            
            for i, m in enumerate(motifs):
                val = str(df.at[idx, m]).strip()
                with cols[i % 4]:
                    check = st.checkbox(m, value=(val == "✅"))
                    df.at[idx, m] = "✅" if check else "❌"
            
            # Modifier le surplus
            curr_surplus = float(df.at[idx, "Surplus"]) if pd.notnull(df.at[idx, "Surplus"]) else 0.0
            df.at[idx, "Surplus"] = st.number_input("Surplus (FCFA)", value=curr_surplus)
            
            if st.form_submit_button("💾 Sauvegarder"):
                df_save = df.drop(columns=["Reste à Payer"])
                conn.update(data=df_save)
                st.success("Synchronisation Google Sheets OK !")
                st.rerun()

    # --- AFFICHAGE ---
    st.divider()
    st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erreur technique : {e}")
