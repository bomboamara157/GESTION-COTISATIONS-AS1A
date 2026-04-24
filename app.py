import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION SÉCURITÉ ---
ADMIN_PASSWORD = "ton_mot_de_passe"  # ⚠️ Pense à modifier ce mot de passe !

st.set_page_config(page_title="Finance Classe AS1A", layout="wide")

# --- CONNEXION GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def charger_donnees():
    # On lit le Google Sheet (on force ttl=0 pour avoir les données en direct)
    df = conn.read(ttl=0)
    # Nettoyage des colonnes (supprime les espaces invisibles)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def sauver_donnees(df_a_sauver):
    # On renvoie le tableau entier vers Google Sheets
    conn.update(data=df_a_sauver)
    st.cache_data.clear() # On vide le cache pour forcer la mise à jour

# Initialisation du DataFrame dans la session
if 'df' not in st.session_state:
    st.session_state.df = charger_donnees()

# --- DÉFINITION DES MOTIFS DYNAMIQUES ---
# Tout ce qui n'est pas "Nom", "Surplus" ou les colonnes calculées est un motif
colonnes_exclues = ["Nom", "Surplus", "TOTAL À PAYER", "Reste à Payer"]
motifs_actuels = [c for c in st.session_state.df.columns if c not in colonnes_exclues]

# --- INTERFACE ---
st.sidebar.title("🔐 Accès Administration")
pwd_input = st.sidebar.text_input("Mot de passe", type="password")
is_admin = (pwd_input == ADMIN_PASSWORD)

st.title("📊 État des Cotisations (Sync Google Sheets)")

# --- SECTION ADMINISTRATEUR ---
if is_admin:
    st.sidebar.success("Mode Administrateur Activé")
    st.header("🛠 Espace de Modification")
    
    tab1, tab2, tab3 = st.tabs([
        "✅ Gérer les Paiements", 
        "➕ Ajouter un Motif", 
        "🗑️ Supprimer un Motif"
    ])
    
    with tab1:
        with st.form("form_paiement"):
            nom_sel = st.selectbox("Sélectionner l'élève", st.session_state.df["Nom"].dropna().unique())
            idx = st.session_state.df.index[st.session_state.df["Nom"] == nom_sel][0]
            
            st.write(f"Modification pour : **{nom_sel}**")
            cols_p = st.columns(min(len(motifs_actuels), 4) if motifs_actuels else 1)
            
            for i, m in enumerate(motifs_actuels):
                val_brute = str(st.session_state.df.at[idx, m]).strip()
                is_paid = True if val_brute in ["✅", "True", "Payé"] else False
                
                with cols_p[i % 4]:
                    check = st.checkbox(m, value=is_paid)
                    st.session_state.df.at[idx, m] = "✅" if check else "❌"
            
            # Gestion du surplus
            try:
                s_val = float(st.session_state.df.at[idx, "Surplus"])
            except:
                s_val = 0.0
            st.session_state.df.at[idx, "Surplus"] = st.number_input("Surplus (FCFA)", value=s_val)
            
            # LE BOUTON SUBMIT OBLIGATOIRE
            if st.form_submit_button("💾 Enregistrer dans Google Sheets"):
                sauver_donnees(st.session_state.df)
                st.success("Synchronisation réussie !")
                st.rerun()

    with tab2:
        st.subheader("➕ Nouveau motif de cotisation")
        n_nom = st.text_input("Nom du motif (ex: Sortie, T-shirt)")
        if st.button("Créer la colonne"):
            if n_nom and n_nom not in st.session_state.df.columns:
                st.session_state.df[n_nom] = "❌"
                sauver_donnees(st.session_state.df)
                st.success(f"Motif {n_nom} ajouté !")
                st.rerun()

    with tab3:
        st.subheader("🗑️ Supprimer un motif")
        if motifs_actuels:
            motif_del = st.selectbox("Motif à supprimer", motifs_actuels)
            if st.button("Confirmer la suppression"):
                st.session_state.df.drop(columns=[motif_del], inplace=True)
                sauver_donnees(st.session_state.df)
                st.rerun()
        else:
            st.info("Aucun motif à supprimer.")

# --- SECTION PUBLIQUE ---
st.divider()
st.subheader("📋 Tableau de bord général")

# On crée une copie pour l'affichage avec le calcul du reste
df_public = st.session_state.df.copy()

# On définit un prix fixe par motif pour le calcul (ex: 1000 FCFA)
PRIX_UNITE = 1000 

def calc_reste(row):
    nb_impayes = sum(1 for m in motifs_actuels if "❌" in str(row[m]))
    total_du = nb_impayes * PRIX_UNITE
    try:
        surplus = float(row["Surplus"])
    except:
        surplus = 0
    reste = total_du - surplus
    return f"{int(max(0, reste))} FCFA"

df_public["Reste à Payer"] = df_public.apply(calc_reste, axis=1)

# Affichage du tableau final
st.dataframe(df_public, use_container_width=True, hide_index=True)

if not is_admin:
    st.info("Les modifications sont enregistrées en temps réel dans Google Sheets par l'administrateur.")
   
