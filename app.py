import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
ADMIN_PASSWORD = "ton_mot_de_passe" # ⚠️ À changer
MONTANT_PAR_MOTIF = 500 # Exemple : 500 FCFA par motif (à adapter)

st.set_page_config(page_title="Gestion Finance AS1A", layout="wide")

# Connexion Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Lecture des données (ttl=0 pour avoir le direct)
    df = conn.read(ttl=0)
    df.columns = [str(c).strip() for c in df.columns] # Nettoie les espaces

    # Détection automatique des colonnes de motifs
    # On considère que tout ce qui n'est pas "Nom" ou "Surplus" est un motif de paiement
    colonnes_fixes = ["Nom", "Surplus"]
    motifs = [c for c in df.columns if c not in colonnes_fixes]

    st.title("📊 Suivi des Cotisations Dynamique")

    # --- LOGIQUE DE CALCUL ---
    # On calcule le reste à payer pour chaque élève
    def calculer_reste(row):
        nb_paye = sum(1 for m in motifs if str(row[m]).strip() == "✅")
        nb_total = len(motifs)
        total_du = nb_total * MONTANT_PAR_MOTIF
        deja_paye = (nb_paye * MONTANT_PAR_MOTIF) + float(row["Surplus"] if pd.notnull(row["Surplus"]) else 0)
        reste = total_du - deja_paye
        return max(0, reste)

    df["Reste à Payer"] = df.apply(calculer_reste, axis=1)

    # --- ESPACE ADMIN ---
    st.sidebar.title("🔐 Administration")
    pwd = st.sidebar.text_input("Mot de passe", type="password")
    
    if pwd == ADMIN_PASSWORD:
        st.header("🛠 Mise à jour des paiements")
        nom_sel = st.selectbox("Sélectionner l'élève", df["Nom"].dropna().unique())
        idx = df.index[df["Nom"] == nom_sel][0]
        
        with st.form("modif_form"):
            st.write(f"Modifications pour **{nom_sel}**")
            
            # Création dynamique des cases à cocher selon les colonnes du Sheet
            cols = st.columns(min(len(motifs), 4)) # Affiche par rangées de 4
            for i, m in enumerate(motifs):
                val_actuelle = str(df.at[idx, m]).strip()
                with cols[i % 4]:
                    check = st.checkbox(m, value=(val_actuelle == "✅"))
                    df.at[idx, m] = "✅" if check else "❌"
            
            # Gestion du surplus
            current_surplus = float(df.at[idx, "Surplus"]) if pd.notnull(df.at[idx, "Surplus"]) else 0.0
            df.at[idx, "Surplus"] = st.number_input("Surplus / Avance (FCFA)", value=current_surplus)
            
            if st.form_submit_button("💾 Enregistrer sur Google Sheets"):
                # Avant de sauvegarder, on retire la colonne calculée "Reste à Payer" 
                # car elle ne doit pas être écrite dans le Sheet
                df_save = df.drop(columns=["Reste à Payer"])
                conn.update(data=df_save)
                st.success("Données synchronisées !")
                st.rerun()

    # --- AFFICHAGE PUBLIC ---
    st.divider()
    st.subheader("📋 État Global de la Classe")
    
    # On affiche le tableau avec le Reste à Payer bien en évidence
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_order=["Nom"] + motifs + ["Surplus", "Reste à Payer"]
    )

    st.info(f"Note : Le calcul est basé sur {MONTANT_PAR_MOTIF} FCFA par motif.")

except Exception as e:
    st.error(f"Erreur de structure : {e}")
    st.info("Vérifiez que votre Google Sheet a bien une colonne 'Nom' et une colonne 'Surplus'.")
    
