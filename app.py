import streamlit as st
import pandas as pd
import os

# --- CONFIGURATION SÉCURITÉ ---
ADMIN_PASSWORD = "ton_mot_de_passe"  # ⚠️ Pense à modifier ce mot de passe !

# --- FICHIERS DE STOCKAGE ---
DATA_FILE = "base_paiements.csv"
CONFIG_FILE = "config_prix.csv"


# --- CHARGEMENT DES DONNÉES ---
def initialiser_donnees():
    if os.path.exists(CONFIG_FILE):
        motifs = pd.read_csv(CONFIG_FILE).set_index('motif')['prix'].to_dict()
    else:
        motifs = {"GEH": 3000, "MOMENT DE JOIE": 1000}

    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame({"Nom": [f"Élève {i + 1}" for i in range(35)], "Surplus": [0] * 35})
        for m in motifs.keys():
            df[m] = False
    return df, motifs


def sauver(df, motifs):
    df.to_csv(DATA_FILE, index=False)
    # On sauvegarde les motifs sous forme de liste de dictionnaires pour le CSV
    pd.DataFrame(list(motifs.items()), columns=['motif', 'prix']).to_csv(CONFIG_FILE, index=False)


if 'df' not in st.session_state:
    st.session_state.df, st.session_state.motifs = initialiser_donnees()

# --- INTERFACE ---
st.set_page_config(page_title="Finance Classe", layout="wide")

# --- SYSTÈME DE CONNEXION ---
st.sidebar.title("🔐 Accès Administration")
pwd_input = st.sidebar.text_input("Mot de passe pour modifier", type="password")
is_admin = (pwd_input == ADMIN_PASSWORD)

if is_admin:
    st.sidebar.success("Mode Administrateur Activé")
else:
    if pwd_input != "":
        st.sidebar.error("Mot de passe incorrect")
    st.sidebar.info("Mode Consultation : Seul l'administrateur peut modifier les données.")

st.title("📊 État des Cotisations de la Classe")

# --- SECTION ADMINISTRATEUR ---
if is_admin:
    st.header("🛠 Espace de Modification")

    tab1, tab2, tab3, tab4 = st.tabs([
        "✅ Valider un Paiement",
        "👤 Noms des Élèves",
        "➕ Ajouter un Motif",
        "🗑️ Supprimer un Motif"
    ])

    with tab1:
        nom_sel = st.selectbox("Sélectionner l'élève", st.session_state.df["Nom"])
        idx = st.session_state.df.index[st.session_state.df["Nom"] == nom_sel][0]

        cols_p = st.columns(len(st.session_state.motifs) + 1)
        for i, (m, p) in enumerate(st.session_state.motifs.items()):
            st.session_state.df.at[idx, m] = cols_p[i].checkbox(f"{m}", value=bool(st.session_state.df.at[idx, m]),
                                                                key=f"chk_{idx}_{m}")
        st.session_state.df.at[idx, "Surplus"] = cols_p[-1].number_input("Surplus", value=int(
            st.session_state.df.at[idx, "Surplus"]), key=f"sur_{idx}")

        if st.button("💾 Enregistrer le paiement"):
            sauver(st.session_state.df, st.session_state.motifs)
            st.success("Enregistré !")
            st.rerun()

    with tab2:
        st.write("Modifiez les noms de la liste (35 élèves) :")
        for i in range(35):
            st.session_state.df.at[i, "Nom"] = st.text_input(f"Place {i + 1}", value=st.session_state.df.at[i, "Nom"],
                                                             key=f"edit_nom_{i}")
        if st.button("Enregistrer tous les noms"):
            sauver(st.session_state.df, st.session_state.motifs)
            st.success("Liste des noms mise à jour !")

    with tab3:
        n_nom = st.text_input("Nom du nouveau motif (ex: T-shirt)")
        n_prix = st.number_input("Montant fixé (FCFA)", min_value=0, step=500)
        if st.button("Créer le motif"):
            if n_nom and n_nom not in st.session_state.df.columns:
                st.session_state.df[n_nom] = False
                st.session_state.motifs[n_nom] = int(n_prix)
                sauver(st.session_state.df, st.session_state.motifs)
                st.rerun()

    with tab4:
        st.warning("Attention : La suppression d'un motif effacera tous les paiements liés à celui-ci.")
        motif_a_supprimer = st.selectbox("Choisir le motif à supprimer", list(st.session_state.motifs.keys()))

        if st.button("🗑️ Supprimer définitivement"):
            # Suppression de la colonne dans le DataFrame
            st.session_state.df.drop(columns=[motif_a_supprimer], inplace=True)
            # Suppression dans le dictionnaire des prix
            del st.session_state.motifs[motif_a_supprimer]
            # Sauvegarde
            sauver(st.session_state.df, st.session_state.motifs)
            st.success(f"Le motif '{motif_a_supprimer}' a été supprimé.")
            st.rerun()

# --- SECTION PUBLIQUE ---
st.divider()
st.subheader("📋 Tableau de bord général")

df_public = st.session_state.df.copy()

# Transformation pour l'affichage
for m in st.session_state.motifs.keys():
    df_public[m] = df_public[m].apply(lambda x: "✅ Payé" if x else "❌ Impayé")


def calc_reste(row):
    total = 0
    for m, p in st.session_state.motifs.items():
        if "Impayé" in str(row[m]): total += p
    return f"{total} FCFA"


df_public["TOTAL À PAYER"] = df_public.apply(calc_reste, axis=1)

# Affichage tableau
st.dataframe(df_public, use_container_width=True, hide_index=True)

if not is_admin:
    st.caption("Dernière mise à jour effectuée par l'administrateur.")