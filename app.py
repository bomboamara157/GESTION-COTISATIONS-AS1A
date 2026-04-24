import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
ADMIN_PASSWORD = "ton_mot_de_passe" 
MONTANT_PAR_MOTIF = 500 

st.set_page_config(page_title="Gestion Finance AS1A", layout="wide")

# Connexion
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # 1. Chargement des données
    df = conn.read(ttl=0)
    df.columns = [str(c).strip() for c in df.columns]

    # Sécurité colonnes de base
    if "Nom" not in df.columns:
        st.error("La colonne A1 de ton Google Sheet doit s'appeler 'Nom'")
        st.stop()
    if "Surplus" not in df.columns:
        df["Surplus"] = 0.0

    # Liste des motifs de paiement (tout sauf Nom, Surplus et Reste)
    motifs = [c for c in df.columns if c not in ["Nom", "Surplus", "Reste à Payer"]]

    # --- CALCULS ---
    def calculer_reste(row):
        nb_paye = sum(1 for m in motifs if str(row[m]).strip() == "✅")
        total_du = len(motifs) * MONTANT_PAR_MOTIF
        try:
            val_s = float(row["Surplus"]) if pd.notnull(row["Surplus"]) else 0
        except:
            val_s = 0
        return max(0, total_du - (nb_paye * MONTANT_PAR_MOTIF + val_s))

    df["Reste à Payer"] = df.apply(calculer_reste, axis=1)

    st.title("📊 Suivi des Cotisations")

    # --- ESPACE ADMIN ---
    st.sidebar.title("🔐 Connexion")
    pwd = st.sidebar.text_input("Mot de passe", type="password")

    if pwd == ADMIN_PASSWORD:
        st.header("🛠 Mode Modification")
        nom_sel = st.selectbox("Choisir l'élève", df["Nom"].dropna().unique())
        idx = df.index[df["Nom"] == nom_sel][0]

        # --- LE FORMULAIRE AVEC LE BOUTON SUBMIT ---
        with st.form("formulaire_paiement"):
            st.write(f"Mise à jour pour : **{nom_sel}**")
            
            # Affichage des motifs sur plusieurs colonnes
            cols = st.columns(min(len(motifs), 4) if motifs else 1)
            for i, m in enumerate(motifs):
                val_actuelle = str(df.at[idx, m]).strip()
                with cols[i % 4]:
                    # On crée la case à cocher et on met à jour le tableau directement
                    if st.checkbox(m, value=(val_actuelle == "✅")):
                        df.at[idx, m] = "✅"
                    else:
                        df.at[idx, m] = "❌"

            # Champ pour le Surplus (en s'assurant que c'est bien un nombre)
            try:
                s_actuel = float(df.at[idx, "Surplus"])
            except:
                s_actuel = 0.0
            
            nouveau_surplus = st.number_input("Surplus (Nombre uniquement)", value=s_actuel)
            df.at[idx, "Surplus"] = nouveau_surplus

            # --- LE BOUTON SUBMIT (OBLIGATOIRE) ---
            bouton_valider = st.form_submit_button("💾 ENREGISTRER LES MODIFICATIONS")

            if bouton_valider:
                # On retire la colonne calculée avant d'envoyer chez Google
                df_final = df.drop(columns=["Reste à Payer"])
                conn.update(data=df_final)
                st.success(f"Modifications enregistrées pour {nom_sel} !")
                st.rerun()

    # --- AFFICHAGE PUBLIC ---
    st.divider()
    st.subheader("📋 Tableau récapitulatif")
    st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Une erreur est survenue : {e}")
   
