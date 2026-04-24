import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
ADMIN_PASSWORD = "ton_mot_de_passe" 
MONTANT_PAR_MOTIF = 500 

st.set_page_config(page_title="Gestion Finance AS1A", layout="wide")

# Connexion Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # 1. Lecture des données
    df = conn.read(ttl=0)
    df.columns = [str(c).strip() for c in df.columns]

    # Sécurité colonnes
    if "Nom" not in df.columns:
        st.error("Case A1 doit être 'Nom'")
        st.stop()
    if "Surplus" not in df.columns:
        df["Surplus"] = 0.0

    # Liste des motifs
    motifs = [c for c in df.columns if c not in ["Nom", "Surplus", "Reste à Payer"]]

    st.title("📊 Suivi des Cotisations")

    # --- CALCULS ---
    def calculer_reste(row):
        nb_paye = sum(1 for m in motifs if str(row[m]).strip() == "✅")
        total_du = len(motifs) * MONTANT_PAR_MOTIF
        try:
            val_surplus = float(row["Surplus"]) if pd.notnull(row["Surplus"]) else 0
        except:
            val_surplus = 0
        return max(0, total_du - (nb_paye * MONTANT_PAR_MOTIF + val_surplus))

    df["Reste à Payer"] = df.apply(calculer_reste, axis=1)

    # --- ADMIN ---
    st.sidebar.title("🔐 Admin")
    pwd = st.sidebar.text_input("Mot de passe", type="password")
    
    if pwd == ADMIN_PASSWORD:
        st.header("🛠 Mise à jour")
        nom_sel = st.selectbox("Élève", df["Nom"].dropna().unique())
        idx = df.index[df["Nom"] == nom_sel][0]
        
        # LE FORMULAIRE CORRIGÉ
        with st.form("mon_formulaire"):
            st.write(f"Modification : **{nom_sel}**")
            
            # Affichage des cases à cocher
            cols = st.columns(min(len(motifs), 4) if motifs else 1)
            for i, m in enumerate(motifs):
                val = str(df.at[idx, m]).strip()
                with cols[i % 4]:
                    # On enregistre le résultat directement dans le DF local
                    if st.checkbox(m, value=(val == "✅")):
                        df.at[idx, m] = "✅"
                    else:
                        df.at[idx, m] = "❌"
            
            # Modification du surplus (en s'assurant que c'est un nombre)
            try:
                s_val = float(df.at[idx, "Surplus"])
            except:
                s_val = 0.0
            nuevo_surplus = st.number_input("Surplus", value=s_val)
            df.at[idx, "Surplus"] = nuevo_surplus
            
            # LE BOUTON OBLIGATOIRE
            submit = st.form_submit_button("💾 Enregistrer")
            
            if submit:
                # On enlève la colonne calculée avant d'envoyer à Google
                df_to_save = df.drop(columns=["Reste à Payer"])
                conn.update(data=df_to_save)
                st.success("C'est enregistré !")
                st.rerun()

    # --- AFFICHAGE ---
    st.divider()
    st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erreur : {e}")
   
