# 📍 Documentation - Smart GeoCoding

# geocoder_bot

# 🗺️ Robot de Géocodage Multi-API

---

## 📋 Table des Matières

1. [Vue d'ensemble du projet](#1-vue-densemble-du-projet)
2. [Architecture du projet](#2-architecture-du-projet)
3. [Configuration et installation](#3-configuration-et-installation)
4. [Modules principaux](#4-modules-principaux)
5. [Pages de l'application](#5-pages-de-lapplication)
6. [APIs de géocodage](#6-apis-de-géocodage)
7. [Flux de données](#7-flux-de-données)
8. [Guide utilisateur](#8-guide-utilisateur)
9. [Développement et maintenance](#9-développement-et-maintenance)

---

## 1. Vue d'ensemble du projet

### 🎯 Objectif

Application Streamlit permettant de **géocoder des adresses en masse** en utilisant plusieurs APIs de géocodage (HERE, Google Maps, OpenStreetMap) avec système de **fallback intelligent** et **relance optimisée** des échecs.

### ✨ Fonctionnalités principales

- **Géocodage par batch** : Traitement de milliers d'adresses en lots configurables
- **Multi-API avec fallback** : Tentative automatique avec plusieurs APIs en cas d'échec
- **Relance intelligente** : Ré-essai des échecs avec variantes d'adresses
- **Analytics avancées** : Visualisations et statistiques détaillées
- **Persistance des données** : Conservation de l'état entre les pages
- **Export flexible** : CSV, JSON, TXT, PDF

### 📊 Statistiques clés

- **3 pages principales** : Géocodage, Relance, Analytics
- **3 APIs intégrées** : HERE, Google, OSM
- **4 niveaux de précision** : ROOFTOP, RANGE_INTERPOLATED, GEOMETRIC_CENTER, APPROXIMATE
- **Support batch** : Jusqu'à 10 000 lignes par batch

---

## 2. Architecture du projet

### 📁 Structure des dossiers

```
GEOCODER_BOT/
│
├── app/                          # Application Streamlit
│   ├── __pycache__/              # Cache Python
│   ├── __init__.py               # Init du package
│   ├── page_analytics.py         # Page d'analyse
│   ├── page_geocoding.py         # Page de géocodage
│   └── page_retry.py             # Page de relance
│
├── data/                         # Données et exports
│   ├── input/                    # Fichiers d'entrée
│   └── output/                   # Fichiers de sortie
│
├── logs/                         # Logs de l'application
│
├── src/                          # Code source principal
│   ├── __pycache__/              # Cache Python
│   ├── apis/                     # Modules des APIs
│   │   ├── __init__.py
│   │   ├── google.py             # API Google Maps
│   │   ├── here.py               # API HERE Maps
│   │   └── osm.py                # API OpenStreetMap
│   │
│   ├── __init__.py
│   ├── config.py                 # Configuration (clés API)
│   ├── geocoding.py              # Logique de géocodage principale
│   ├── geocoding_retry.py        # Logique de relance intelligente
│   ├── ingestion.py              # Lecture de fichiers
│   ├── logger.py                 # Système de logging
│   └── utils.py                  # Utilitaires (export, PDF)
│
├── tests/                        # Tests unitaires
│
├── venv/                         # Environnement virtuel Python
│
├── .env                          # Variables d'environnement (clés API)
├── .env.example                  # Template pour .env
├── .gitignore                    # Fichiers à ignorer par Git
├── main.py                       # Point d'entrée de l'application
├── README.md                     # Documentation projet
└── requirements.txt              # Dépendances Python
```

### 🔗 Relations entre modules

```
main.py
    ↓
┌───────────────────────────────────────┐
│  Streamlit Navigation                 │
├───────────────────────────────────────┤
│  page_geocoding.py                    │
│  page_retry.py                        │
│  page_analytics.py                    │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│  Logique Métier                       │
├───────────────────────────────────────┤
│  geocoding.py ──→ apis/here.py        │
│                 ├→ apis/google.py     │
│                 └→ apis/osm.py        │
│  geocoding_retry.py                   │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│  Utilitaires                          │
├───────────────────────────────────────┤
│  ingestion.py                         │
│  utils.py                             │
│  config.py                            │
│  logger.py                            │
└───────────────────────────────────────┘
```

---

## 3. Configuration et installation

### 📦 Installation

```bash
# 1. Cloner le projet
git clone https://server-rtit-consulting.com/rabah.taalbi/geocoder_bot.git
cd geocoder_bot

# 2. Créer l'environnement virtuel
python -m venv venv

# 3. Activer l'environnement
source venv/bin/activate  # Sur Linux/Mac
venv\Scripts\activate     # Sur Windows

# 4. Installer les dépendances
pip install -r requirements.txt
```

### 🔑 Configuration des clés API

**Copier le fichier `.env.example` en `.env` :**

```bash
cp .env.example .env
```

**Remplir les clés API dans `.env` :**

```env
# API HERE Maps
HERE_API_KEY=your_here_api_key

# API Google Maps
GOOGLE_API_KEY=your_google_api_key

# API OpenStreetMap (Nominatim)
OSM_EMAIL=your_email@example.com
```

**Obtention des clés :**

- **HERE** : https://developer.here.com/
- **Google** : https://console.cloud.google.com/
- **OSM** : Email de contact (gratuit, pas de clé)

### 🚀 Lancement

```bash
streamlit run main.py
```

L'application s'ouvre automatiquement dans le navigateur à l'adresse : `http://localhost:8501`

---

## 4. Modules principaux

### 📄 `config.py` - Configuration

**Rôle** : Charge les variables d'environnement et les clés API

```python
from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OSM_EMAIL = os.getenv("OSM_EMAIL")
HERE_API_KEY = os.getenv("HERE_API_KEY")
```

**Variables** :
- `GOOGLE_API_KEY` : Clé pour Google Maps Geocoding API
- `HERE_API_KEY` : Clé pour HERE Geocoding API
- `OSM_EMAIL` : Email pour respecter la policy de Nominatim

---

### 📄 `ingestion.py` - Lecture de fichiers

**Rôle** : Détecte automatiquement le séparateur et lit les fichiers CSV/TXT

#### Fonctions principales

##### `detect_separator(file, max_lines=5)`

Détecte automatiquement le séparateur d'un fichier CSV.

**Paramètres** :
- `file` : Fichier uploadé
- `max_lines` : Nombre de lignes à analyser (défaut: 5)

**Retour** : Séparateur détecté (`,`, `;`, `\t`, etc.)

**Algorithme** :
1. Lit les 2048 premiers octets
2. Utilise `csv.Sniffer()` pour détecter le délimiteur
3. Fallback sur `,` en cas d'échec

##### `read_file(uploaded_file, sep=None)`

Lit un fichier CSV avec gestion automatique de l'encodage.

**Paramètres** :
- `uploaded_file` : Fichier Streamlit
- `sep` : Séparateur (auto-détecté si None)

**Retour** : DataFrame pandas

**Gestion d'erreurs** :
- Essai UTF-8 d'abord
- Fallback sur ISO-8859-1 en cas d'échec

---

### 📄 `utils.py` - Utilitaires

**Rôle** : Export de données et génération de rapports PDF

#### Fonctions principales

##### `export_enriched_results(df, export_format, sep, line_delimited_json)`

Exporte les résultats de géocodage.

**Paramètres** :
- `df` : DataFrame à exporter
- `export_format` : "csv", "json", ou "txt"
- `sep` : Séparateur pour CSV/TXT
- `line_delimited_json` : JSON ligne par ligne (bool)

**Sortie** : `data/output/geocodage_result_YYYY-MM-DD_HH-MM.{format}`

##### `export_job_history_to_pdf(jobs, output_path)`

Génère un PDF récapitulatif de l'historique des jobs.

**Paramètres** :
- `jobs` : Liste des jobs (dict)
- `output_path` : Chemin de sortie

**Contenu du PDF** :
- Tableau avec ID, dates, stats
- Niveaux de précision
- Statuts

**Classe PDF personnalisée** :
- Header avec titre
- Footer avec numéro de page
- Tableau multi-lignes avec gestion dynamique

##### `get_precision_stats(enriched_df)`

Extrait les statistiques de précision triées.

**Ordre de tri** :
1. ROOFTOP
2. RANGE_INTERPOLATED
3. GEOMETRIC_CENTER
4. APPROXIMATE
5. Autres

---

### 📄 `geocoding.py` - Géocodage principal

**Rôle** : Orchestration du géocodage multi-API avec fallback

#### Architecture

```
parallel_geocode_row()
    ↓
┌─────────────────┐
│  Mode sélection │
├─────────────────┤
│  • here         │ → geocode_with_here()
│  • google       │ → geocode_with_google()
│  • osm          │ → geocode_with_osm()
│  • multi        │ → Fallback cascade
└─────────────────┘
```

#### Fonctions principales

##### `parallel_geocode_row(df, address_column, max_workers, progress_callback, api_mode)`

Géocode en parallèle avec ThreadPoolExecutor.

**Paramètres** :
- `df` : DataFrame avec adresses
- `address_column` : Nom de la colonne d'adresse
- `max_workers` : Threads simultanés (défaut: 10)
- `progress_callback` : Callback pour barre de progression
- `api_mode` : "here", "google", "osm", ou "multi"

**Retour** : DataFrame enrichi avec colonnes :
- `latitude` : Latitude
- `longitude` : Longitude
- `formatted_address` : Adresse formatée par l'API
- `status` : "OK" ou code d'erreur
- `error_message` : Message d'erreur
- `api_used` : API ayant réussi
- `precision_level` : Niveau de précision
- `timestamp` : Horodatage

**Optimisations** :
- Multi-threading pour performance
- Callback pour UI temps réel
- Gestion d'erreurs robuste

##### Modes API

- `"here"` : HERE uniquement
- `"google"` : Google uniquement
- `"osm"` : OSM uniquement
- `"multi"` : Cascade HERE → Google → OSM

**Logique fallback (mode multi)** :

```
1. Essayer HERE
   ├─ Succès → Retourner résultat
   └─ Échec → Continuer
2. Essayer Google
   ├─ Succès → Retourner résultat
   └─ Échec → Continuer
3. Essayer OSM
   ├─ Succès → Retourner résultat
   └─ Échec → Retourner erreur finale
```

##### `geocode_with_here(address)`

Géocode avec HERE Maps API.

**Endpoint** : `https://geocode.search.hereapi.com/v1/geocode`

**Paramètres de requête** :
- `q` : Adresse à géocoder
- `apiKey` : Clé API HERE
- `limit` : 1 (meilleur résultat)

**Mapping des précisions** :

```python
"houseNumber" → "ROOFTOP"
"street" → "RANGE_INTERPOLATED"
"district" → "GEOMETRIC_CENTER"
"city" → "APPROXIMATE"
```

##### `geocode_with_google(address)`

Géocode avec Google Maps Geocoding API.

**Endpoint** : `https://maps.googleapis.com/maps/api/geocode/json`

**Paramètres de requête** :
- `address` : Adresse
- `key` : Clé API Google

**Mapping des précisions** :

```python
"ROOFTOP" → "ROOFTOP"
"RANGE_INTERPOLATED" → "RANGE_INTERPOLATED"
"GEOMETRIC_CENTER" → "GEOMETRIC_CENTER"
"APPROXIMATE" → "APPROXIMATE"
```

##### `geocode_with_osm(address)`

Géocode avec OpenStreetMap Nominatim.

**Endpoint** : `https://nominatim.openstreetmap.org/search`

**Paramètres de requête** :
- `q` : Adresse
- `format` : json
- `limit` : 1
- `email` : Email de contact (requis)

**Headers** :
- `User-Agent` : Custom (respect de la policy)

**Mapping des précisions** :

```python
"house" → "ROOFTOP"
"street" → "RANGE_INTERPOLATED"
"suburb", "neighbourhood" → "GEOMETRIC_CENTER"
Autres → "APPROXIMATE"
```

##### `create_job_entry(job_id, total_rows)`

Crée une entrée de job pour l'historique.

**Retour** : Dictionnaire avec :
- `job_id` : ID unique
- `start_time` : Horodatage de début
- `total_rows` : Nombre de lignes
- `status` : "in_progress"

##### `finalize_job(job, enriched_df)`

Finalise un job avec statistiques.

**Mise à jour** :
- `end_time` : Horodatage de fin
- `success` : Nombre de succès
- `failed` : Nombre d'échecs
- `precision_counts` : Distribution des précisions
- `details_df` : DataFrame complet
- `status` : "completed"

---

### 📄 `geocoding_retry.py` - Relance intelligente

**Rôle** : Ré-essai des échecs avec variantes d'adresses et toutes les APIs

#### Stratégie de relance

```
Échec initial
    ↓
Génération de variantes
    ├─ Adresse reformatée
    ├─ Adresse simplifiée
    └─ Adresse structurée
    ↓
Test avec toutes les APIs
    ├─ HERE
    ├─ Google
    └─ OSM
    ↓
Sélection du meilleur résultat
```

#### Fonctions principales

##### `retry_geocode_row(df, address_column, max_workers, progress_callback)`

Point d'entrée de la relance intelligente.

**Différences avec géocodage standard** :
1. Teste **toutes** les APIs systématiquement
2. Génère **plusieurs variantes** d'adresse
3. Sélectionne le **meilleur résultat** selon précision
4. Marque les **améliorations** (`improved` column)

##### `generate_alternative_addresses(row)`

Génère des variantes d'adresse pour maximiser les chances de succès.

**Variantes générées** :
1. **Adresse originale** : `full_address` tel quel
2. **Adresse reformatée** : Sans nom, composants réorganisés
3. **Adresse structurée** : Composants séparés

**Exemple** :

```
Original: "Restaurant X, 123 Rue Y, 75001 Paris, Île-de-France, France"

Variantes:
1. "Restaurant X, 123 Rue Y, 75001 Paris, Île-de-France, France"
2. "123 Rue Y, 75001, Paris, France"
3. {"street": "123 Rue Y", "postal_code": "75001", "city": "Paris", ...}
```

##### `intelligent_retry_geocode(row, index, target_precision)`

Teste toutes les variantes avec toutes les APIs.

**Algorithme** :

```python
meilleur_résultat = None
meilleure_précision = APPROXIMATE

pour chaque variante:
    pour chaque API (here, google, osm):
        résultat = géocoder(variante, API)
        si résultat.succès:
            si résultat.précision > meilleure_précision:
                meilleur_résultat = résultat
                meilleure_précision = résultat.précision

retourner meilleur_résultat
```

**Hiérarchie de précision** :

```
ROOFTOP (4) > RANGE_INTERPOLATED (3) > GEOMETRIC_CENTER (2) > APPROXIMATE (1)
```

##### `is_better_precision(new_result, current_best)`

Sélectionne le meilleur résultat parmi les tentatives.

**Critères de sélection** :
1. Priorité au résultat avec la meilleure précision
2. En cas d'égalité, préférence à HERE, puis Google, puis OSM
3. Marque `improved=True` si précision améliorée

---

### 📄 APIs - Modules de géocodage

#### `apis/here.py`

**Configuration** :

```python
BASE_URL = "https://geocode.search.hereapi.com/v1/geocode"
```

**Fonctionnalités** :
- Géocodage avec plusieurs niveaux de détail
- Gestion des adresses structurées
- Support des composants optionnels

**Limites** :
- 250 000 requêtes/mois (plan gratuit)
- Rate limit: 5 requêtes/seconde

#### `apis/google.py`

**Configuration** :

```python
BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
```

**Fonctionnalités** :
- Précision maximale
- Données les plus fiables
- Support multilingue

**Limites** :
- Payant après 40 000 requêtes/mois
- Rate limit: 50 requêtes/seconde

#### `apis/osm.py`

**Configuration** :

```python
BASE_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "GeocoderBot/1.0"
```

**Fonctionnalités** :
- Gratuit et open-source
- Pas de limite de requêtes
- Données communautaires

**Limites** :
- Précision variable
- Rate limit: 1 requête/seconde (policy)
- Nécessite email de contact

**Particularités** :
- Délai de 1 seconde entre requêtes (respect policy)
- User-Agent obligatoire
- Données OSM parfois incomplètes

---

## 5. Pages de l'application

### 📄 Page 1 : Géocodage (`page_geocoding.py`)

#### 🎯 Objectif

Géocoder en masse des adresses avec configuration flexible et suivi en temps réel.

#### 📋 Sections

##### 1. Chargement du fichier

```
📁 Chargement du fichier
├─ Upload widget (CSV, TXT)
├─ Métriques :
│  ├─ 📄 Lignes totales
│  ├─ 📊 Colonnes
│  └─ ✅/⚠️ Full Address (statut)
└─ 👀 Aperçu des données (collapsible)
```

**Fonctionnalités** :
- Détection automatique du séparateur
- Support UTF-8 et ISO-8859-1
- Persistance entre changements de page
- Message si fichier déjà chargé

**États possibles** :
- ❌ Aucun fichier → Message d'information
- 📂 Fichier en mémoire → Message + métriques
- ✅ Nouveau fichier → Chargement + affichage

##### 2. Mapping des colonnes

```
🧩 Mapping des Colonnes
├─ Colonne 1 : name → [Sélection]
├─ Colonne 2 : street → [Sélection]
├─ Colonne 3 : postal_code → [Sélection]
├─ Colonne 4 : city → [Sélection]
├─ Colonne 5 : governorate → [Sélection]
├─ Colonne 6 : country → [Sélection]
├─ Colonne 7 : complement → [Sélection]
└─ ✅ Valider le mapping
```

**Champs disponibles** :
- `name` : Nom du lieu (optionnel)
- `street` : Numéro et nom de rue
- `postal_code` : Code postal
- `city` : Ville
- `governorate` : Région/Gouvernorat
- `country` : Pays
- `complement` : Informations complémentaires

**Processus** :
1. Sélectionner les colonnes correspondantes
2. Cliquer sur "Valider le mapping"
3. Génération automatique de `full_address`
4. Concaténation : `name, street, postal_code, city, governorate, country, complement`

**Exemple** :

```
Colonnes source : nom, adresse, cp, ville, pays

Mapping :
  name → nom
  street → adresse
  postal_code → cp
  city → ville
  country → pays

full_address générée :
"Restaurant Le Bon Coin, 123 Rue de la Paix, 75001, Paris, France"
```

##### 3. Configuration du géocodage

```
📍 Configuration du Géocodage
├─ Métriques :
│  ├─ 📄 Total lignes : 10,000
│  ├─ Début : 0
│  ├─ Fin : 1000
│  └─ Taille batch : 1000
├─ Configuration :
│  ├─ Nombre de batches : 3
│  └─ 📊 Résumé : 3,000 lignes sur 3 batches
├─ 🔧 Mode de Géocodage :
│  ○ HERE uniquement
│  ○ Google uniquement
│  ○ OSM uniquement
│  ● Multi-API (HERE → Google → OSM)
└─ 🚀 Lancer le Géocodage
```

**Paramètres configurables** :

| Paramètre | Description | Min | Max | Défaut |
|-----------|-------------|-----|-----|--------|
| **Ligne de départ** | Index de la première ligne | 0 | N-1 | 0 |
| **Ligne de fin** | Index de la dernière ligne (exclu) | 1 | N | 1000 |
| **Taille batch** | Nombre de lignes par batch | 10 | 10000 | 1000 |
| **Nombre de batches** | Batches à exécuter | 1 | Total | 3 |

**Modes de géocodage** :

| Mode | Description | Use case |
|------|-------------|----------|
| **HERE uniquement** | Utilise uniquement HERE Maps | Adresses européennes, rapidité |
| **Google uniquement** | Utilise uniquement Google Maps | Précision maximale, budget |
| **OSM uniquement** | Utilise uniquement OSM Nominatim | Gratuit, pas de limite |
| **Multi-API** | Cascade HERE → Google → OSM | Taux de réussite maximal |

**Calcul automatique** :

```
Lignes sélectionnées = fin - début
Total batches possibles = ⌈lignes_sélectionnées / taille_batch⌉
Lignes à traiter = min(nombre_batches × taille_batch, lignes_sélectionnées)
```

##### 4. Processus de géocodage en temps réel

```
🔄 Géocodage en cours - Mode: Multi-API
├─ Barre de progression globale : [████████░░] 80%
├─ Statut : 📦 Traitement du batch 4/5 (1000 lignes)...
├─ Barre de progression du batch : [██████████] 100%
└─ ✅ Batch 4 terminé : 950/1000 succès (95%)
```

**Informations affichées** :
- Mode API utilisé
- Progression globale (tous batches)
- Batch en cours de traitement
- Progression du batch actuel
- Stats instantanées par batch

**Finalisation** :
- 🎉 Ballons de célébration
- Message de succès avec total traité
- Enregistrement dans l'historique des jobs
- Mise à jour du DataFrame enrichi

##### 5. Résultats du géocodage

```
📊 Résultats du Géocodage
├─ Métriques :
│  ├─ 📄 Total : 3,000
│  ├─ ✅ Succès : 2,850 (95%)
│  ├─ ❌ Échecs : 150 (5%)
│  └─ 🎯 ROOFTOP : 2,400 (84.2%)
├─ Tabs :
│  ├─ 📋 Tous les résultats
│  │  ├─ 🎯 Précision (gauche)
│  │  ├─ 🔌 APIs (droite)
│  │  └─ DataFrame complet
│  ├─ ✅ Succès
│  │  └─ 2,850 lignes réussies
│  └─ ❌ Échecs
│     └─ 150 lignes en échec
```

**Colonnes du DataFrame enrichi** :
- Toutes les colonnes originales
- `latitude` : Coordonnée Y
- `longitude` : Coordonnée X
- `formatted_address` : Adresse retournée par l'API
- `status` : "OK" ou code d'erreur
- `error_message` : Message d'erreur si échec
- `api_used` : API ayant réussi (here/google/osm)
- `precision_level` : ROOFTOP/RANGE/GEOMETRIC/APPROXIMATE
- `timestamp` : Date et heure du géocodage

**Statistiques de précision** :
- Pourcentage par niveau
- Nombre absolu
- Uniquement sur les succès

**Statistiques d'APIs** :
- Répartition par API utilisée
- Pourcentage du total

##### 6. Relancer les échecs

```
🔁 Relancer les Échecs (150 lignes)
├─ ⚠️ 150 lignes ont échoué
├─ Mode de relance :
│  ● Multi-API (HERE → Google → OSM)
│  ○ HERE uniquement
│  ○ Google uniquement
│  ○ OSM uniquement
└─ 🔄 Relancer les échecs
```

**Processus de relance** :
1. Reformulation des adresses (sans nom)
2. Nettoyage des colonnes de géocodage
3. Re-géocodage avec mode sélectionné
4. Affichage des stats
5. Mise à jour automatique du DataFrame

**Résultat** :
- Stats de la relance (succès/échecs)
- DataFrame des lignes relancées
- Fusion automatique avec les succès précédents

##### 7. Export des résultats

```
📥 Exporter les Résultats
├─ Format : [csv ▼]
├─ Séparateur : [,]
├─ ☐ JSON ligne par ligne (si JSON)
└─ 📄 Générer et télécharger
```

**Formats disponibles** :
- **CSV** : Séparateur personnalisable
- **JSON** : Format standard ou ligne par ligne
- **TXT** : Comme CSV avec séparateur

**Nom du fichier** :

```
geocodage_result_YYYY-MM-DD_HH-MM.{format}
```

##### 8. Historique des jobs

```
📜 Historique des Jobs
├─ Tableau récapitulatif :
│  ├─ Job ID
│  ├─ Lignes
│  ├─ Succès
│  ├─ Échecs
│  ├─ Taux
│  └─ Statut
├─ 📥 Télécharger l'historique PDF
└─ Détails par job (5 derniers) :
   ├─ 🕒 Début / 🏁 Fin
   ├─ 📄 Total / ✅ Succès
   ├─ 🎯 Précisions
   └─ Preview DataFrame
```

**Informations par job** :
- ID unique avec timestamp
- Dates de début et fin
- Nombre de lignes traitées
- Taux de réussite
- Distribution des précisions
- Preview des 5 premières lignes

---

### 📄 Page 2 : Relance (`page_retry.py`)

#### 🎯 Objectif

Relancer intelligemment les échecs avec variantes d'adresses et test de toutes les APIs.

#### 📋 Sections

##### 1. Chargement du fichier

```
📂 Chargement du Fichier
├─ Upload widget (CSV déjà géocodé)
├─ Métriques :
│  ├─ 📄 Lignes totales : 500
│  ├─ ❌ Échecs : 50
│  └─ 🎯 APPROXIMATE : 30
└─ 👀 Aperçu des données
```

**Prérequis fichier** :
- Colonne `status` obligatoire
- Colonne `full_address` obligatoire
- Optionnel : `precision_level`, `api_used`

**Validation** :
- Vérification de la colonne `status`
- Message d'erreur si manquante

##### 2. Critères de sélection

```
🎯 Critères de Sélection
├─ 📌 Statuts à relancer :
│  ☑ ERROR
│  ☑ ZERO_RESULTS
│  ☑ OVER_QUERY_LIMIT
├─ 🎯 Précisions à améliorer :
│  ☑ APPROXIMATE
│  ☑ GEOMETRIC_CENTER
├─ 🆔 Colonne identifiant :
│  [-- Aucun --]
├─ 🔎 150 lignes sélectionnées pour relance
└─ 👀 Aperçu des lignes sélectionnées
```

**Filtres disponibles** :

| Filtre | Options | Description |
|--------|---------|-------------|
| **Statuts** | ERROR, ZERO_RESULTS, OVER_QUERY_LIMIT, etc. | Lignes en échec à relancer |
| **Précisions** | APPROXIMATE, GEOMETRIC_CENTER, etc. | Lignes à améliorer |
| **ID unique** | Colonnes du fichier | Pour déduplication |

**Logique de sélection** :

```python
Sélection = (lignes avec statut dans filtres) ∪ (lignes avec précision dans filtres)
Déduplication par ID ou full_address
```

**Cas d'usage** :
1. **Relance des échecs purs** : Sélectionner uniquement les statuts d'erreur
2. **Amélioration de précision** : Sélectionner APPROXIMATE et GEOMETRIC_CENTER
3. **Combinaison** : Erreurs + précisions faibles

##### 3. Configuration de la relance

```
🔧 Configuration de la Relance
├─ 🎯 Objectif de précision :
│  ● ROOFTOP
│  ○ RANGE_INTERPOLATED
│  ○ GEOMETRIC_CENTER
└─ 🧠 Stratégie :
   ✅ Toutes les APIs testées
   ✅ Variantes d'adresse générées
   ✅ Meilleur résultat retourné
   ✅ APIs déjà testées évitées
```

**Objectif de précision** :
- Niveau minimum souhaité
- Affecte le scoring des résultats
- Utilisé dans `select_best_result()`

**Stratégie intelligente** :
1. Génère 3 variantes d'adresse
2. Teste avec HERE, Google, OSM
3. Compare précisions
4. Retourne le meilleur résultat
5. Marque les améliorations

##### 4. Lancement et progression

```
🚀 Relance en cours...
├─ Barre de progression : [████████░░] 80%
├─ Traitement: 120/150 lignes...
└─ 🔄 Géocodage en cours...
```

**Processus** :
1. Nettoyage des anciennes colonnes de géocodage
2. Génération des variantes d'adresses
3. Test avec toutes les APIs
4. Sélection du meilleur résultat
5. Mise à jour du DataFrame

##### 5. Résultats de la relance

```
📊 Résultats de la Relance
├─ Métriques :
│  ├─ 📄 Traitées : 150
│  ├─ ✅ Succès : 130 (86.7%)
│  ├─ ❌ Échecs : 20 (13.3%)
│  └─ 🎉 Améliorées : 120
├─ Détails :
│  ├─ 🎯 Précision (gauche)
│  └─ 🔌 APIs (droite)
└─ Tabs :
   ├─ 📋 Tous
   ├─ ✅ Succès
   └─ ❌ Échecs
```

**Nouvelle colonne** :
- `improved` : True si précision améliorée

**Statistiques** :
- Taux de réussite de la relance
- Distribution des précisions
- APIs ayant réussi
- Nombre d'améliorations

##### 6. Export des résultats

```
📥 Export des Résultats
├─ 📄 Résultats de la relance
│  └─ 💾 Télécharger CSV (relance)
└─ 📦 Fichier complet mis à jour
   └─ 💾 Télécharger CSV (complet)
```

**Deux options d'export** :
1. **CSV relance uniquement** : Lignes relancées
2. **CSV complet** : Fichier original + résultats relance

**Fusion automatique** :
- Par ID si spécifié
- Sinon par `full_address`
- Keep="last" pour les doublons

---

### 📄 Page 3 : Analytics (`page_analytics.py`)

#### 🎯 Objectif

Analyser les résultats de géocodage avec visualisations et statistiques détaillées.

#### 📋 Sections

##### 1. Chargement du fichier

```
📁 Chargement du Fichier
├─ Upload widget (CSV enrichi)
├─ Métriques :
│  ├─ 📄 Lignes totales : 10,000
│  ├─ ✅ Succès : 9,500 (95%)
│  ├─ ❌ Échecs : 500 (5%)
│  └─ 🎯 ROOFTOP : 8,000 (84.2%)
└─ 👀 Aperçu des données
```

**Prérequis** :
- Colonne `status` obligatoire
- Colonnes optionnelles : `precision_level`, `api_used`

##### 2. Statistiques détaillées

```
📌 Statistiques Détaillées
├─ 🎯 Niveaux de précision (gauche) :
│  ├─ 🎯 ROOFTOP : 8,000 (84.2%)
│  ├─ 📍 RANGE_INTERPOLATED : 1,000 (10.5%)
│  ├─ 📌 GEOMETRIC_CENTER : 400 (4.2%)
│  └─ APPROXIMATE : 100 (1.1%)
└─ 🔌 APIs utilisées (droite) :
   ├─ 🗺️ here : 7,000 (70%)
   ├─ 🌍 google : 2,000 (20%)
   └─ 🌐 osm : 1,000 (10%)
```

**Tri automatique** :
- Précisions dans l'ordre de qualité
- Pourcentages calculés automatiquement

##### 3. Visualisations

```
📈 Visualisations
├─ Graphique 1 (haut gauche) :
│  └─ 🥧 Camembert des statuts
├─ Graphique 2 (haut droite) :
│  └─ 📊 Barres des précisions
├─ Graphique 3 (bas gauche) :
│  └─ 📊 Barres horizontales des APIs
└─ Graphique 4 (bas droite) :
   └─ 🍩 Donut du taux de succès
```

**Graphiques générés** :

| Position | Type | Contenu | Couleurs |
|----------|------|---------|----------|
| **Haut gauche** | Camembert | Distribution des statuts | Vert/Rouge/Jaune/Gris |
| **Haut droite** | Barres verticales | Niveaux de précision | Vert→Rouge (qualité) |
| **Bas gauche** | Barres horizontales | APIs utilisées | Bleu/Vert/Cyan |
| **Bas droite** | Donut | Taux de réussite global | Vert/Rouge |

**Personnalisation** :
- Valeurs affichées sur les barres
- Pourcentages dans les camemberts
- Taux au centre du donut
- Grille alpha=0.3

**Persistance** :
- Graphique stocké dans `st.session_state.analytics_fig`
- Pas de régénération si déjà créé
- Reset lors du chargement d'un nouveau fichier

##### 4. Filtres et téléchargement

```
📥 Filtres et Téléchargement
├─ Filtres :
│  ├─ 📌 Filtrer par statut : [OK, ERROR, ...]
│  ├─ 🎯 Filtrer par précision : [ROOFTOP, ...]
│  └─ 🔌 Filtrer par API : [here, google, osm]
├─ 🔍 8,500 lignes correspondent aux filtres
└─ Téléchargements :
   ├─ 📄 CSV filtré
   ├─ 📄 CSV complet
   └─ 📊 Rapport PDF
```

**Filtres combinés** :

```python
DataFrame filtré = (
    lignes où statut dans filtres_statut
    ET précision dans filtres_précision
    ET API dans filtres_API
)
```

**Export CSV filtré** :
- Uniquement les lignes filtrées
- Format : `filtered_data_YYYY-MM-DD_HH-MM-SS.csv`

**Export CSV complet** :
- Toutes les lignes
- Format : `full_data_YYYY-MM-DD_HH-MM-SS.csv`

**Rapport PDF** :
- Page 1 : 4 graphiques
- Page 2 : Statistiques détaillées en texte
- Métadonnées : Titre, Auteur, Date
- Format : `rapport_analytics_YYYY-MM-DD_HH-MM-SS.pdf`

---

## 6. APIs de géocodage

### 🗺️ HERE Maps API

#### Caractéristiques

- **Provider** : HERE Technologies
- **Endpoint** : `https://geocode.search.hereapi.com/v1/geocode`
- **Authentification** : API Key dans query params
- **Format** : JSON

#### Limites

| Plan | Requêtes/mois | Requêtes/seconde | Coût |
|------|--------------|------------------|------|
| Freemium | 250,000 | 5 | Gratuit |
| Pay-as-you-go | Illimité | 10 | $1/1000 requêtes |

#### Paramètres de requête

```json
{
    "q": "123 Rue de la Paix, 75001 Paris, France",
    "apiKey": "YOUR_API_KEY",
    "limit": 1
}
```

#### Structure de réponse

```json
{
  "items": [
    {
      "title": "123 Rue de la Paix, 75001 Paris, France",
      "address": {
        "label": "123 Rue de la Paix, 75001 Paris, France",
        "countryCode": "FRA",
        "city": "Paris",
        "street": "Rue de la Paix",
        "houseNumber": "123",
        "postalCode": "75001"
      },
      "position": {
        "lat": 48.8698,
        "lng": 2.3309
      },
      "resultType": "houseNumber"
    }
  ]
}
```

#### Mapping des types de résultats

```python
"houseNumber" → "ROOFTOP"          # Numéro exact
"street" → "RANGE_INTERPOLATED"     # Rue sans numéro
"district" → "GEOMETRIC_CENTER"     # Quartier
"city" → "APPROXIMATE"              # Ville
"administrativeArea" → "APPROXIMATE" # Région
"country" → "APPROXIMATE"           # Pays
```

#### Gestion d'erreurs

```python
Status 200 → items vide → ZERO_RESULTS
Status 401 → Unauthorized → INVALID_API_KEY
Status 429 → Too Many Requests → OVER_QUERY_LIMIT
Status 500 → Internal Server Error → ERROR
Timeout → REQUEST_DENIED
```

---

### 🌍 Google Maps Geocoding API

#### Caractéristiques

- **Provider** : Google Cloud
- **Endpoint** : `https://maps.googleapis.com/maps/api/geocode/json`
- **Authentification** : API Key dans query params
- **Format** : JSON

#### Limites

| Plan | Requêtes/mois | Requêtes/seconde | Coût |
|------|--------------|------------------|------|
| Free tier | 40,000 | 50 | Gratuit |
| Pay-as-you-go | Illimité | 50 | $5/1000 requêtes |

#### Paramètres de requête

```json
{
    "address": "123 Rue de la Paix, 75001 Paris, France",
    "key": "YOUR_API_KEY"
}
```

#### Structure de réponse

```json
{
  "results": [
    {
      "formatted_address": "123 Rue de la Paix, 75001 Paris, France",
      "geometry": {
        "location": {
          "lat": 48.8698,
          "lng": 2.3309
        },
        "location_type": "ROOFTOP"
      },
      "place_id": "ChIJd8BlQ2FZwokRRT2JwsL-wZ8",
      "address_components": [...]
    }
  ],
  "status": "OK"
}
```

#### Mapping des location_type

```python
"ROOFTOP" → "ROOFTOP"                    # Précision maximale
"RANGE_INTERPOLATED" → "RANGE_INTERPOLATED" # Interpolation
"GEOMETRIC_CENTER" → "GEOMETRIC_CENTER"     # Centre géométrique
"APPROXIMATE" → "APPROXIMATE"               # Approximatif
```

#### Statuts possibles

```python
"OK" → Succès
"ZERO_RESULTS" → Aucun résultat
"OVER_QUERY_LIMIT" → Quota dépassé
"REQUEST_DENIED" → Clé invalide
"INVALID_REQUEST" → Requête malformée
"UNKNOWN_ERROR" → Erreur serveur
```

---

### 🌐 OpenStreetMap Nominatim API

#### Caractéristiques

- **Provider** : OpenStreetMap Foundation
- **Endpoint** : `https://nominatim.openstreetmap.org/search`
- **Authentification** : Email requis (pas de clé)
- **Format** : JSON
- **License** : Open Data (ODbL)

#### Limites

| Aspect | Limite | Note |
|--------|--------|------|
| Requêtes/seconde | 1 | Policy stricte |
| Requêtes/jour | Illimité | Respect du délai |
| Coût | Gratuit | Contributions bienvenues |
| User-Agent | Obligatoire | Identification requise |

#### Paramètres de requête

```json
{
    "q": "123 Rue de la Paix, 75001 Paris, France",
    "format": "json",
    "limit": 1,
    "email": "your_email@example.com"
}

Headers:
{
    "User-Agent": "GeocoderBot/1.0 (your_email@example.com)"
}
```

#### Structure de réponse

```json
[
  {
    "place_id": 123456,
    "licence": "Data © OpenStreetMap contributors, ODbL 1.0",
    "osm_type": "way",
    "osm_id": 789012,
    "lat": "48.8698",
    "lon": "2.3309",
    "display_name": "123, Rue de la Paix, ...",
    "class": "place",
    "type": "house",
    "importance": 0.85
  }
]
```

#### Mapping des types

```python
"house" → "ROOFTOP"                 # Bâtiment
"street" → "RANGE_INTERPOLATED"     # Rue
"suburb" → "GEOMETRIC_CENTER"       # Quartier
"neighbourhood" → "GEOMETRIC_CENTER" # Voisinage
"city" → "APPROXIMATE"              # Ville
"town" → "APPROXIMATE"              # Ville
"village" → "APPROXIMATE"           # Village
"county" → "APPROXIMATE"            # Comté
"state" → "APPROXIMATE"             # État
"country" → "APPROXIMATE"           # Pays
```

#### Bonnes pratiques

1. **Délai entre requêtes** : 1 seconde minimum
2. **User-Agent** : Toujours spécifier
3. **Email** : Fournir un contact valide
4. **Cache** : Mettre en cache les résultats
5. **Bulk requests** : Éviter les requêtes massives simultanées

#### Gestion d'erreurs

```python
Liste vide → ZERO_RESULTS
Status 403 → REQUEST_DENIED (User-Agent manquant)
Status 429 → OVER_QUERY_LIMIT (trop rapide)
Status 500 → ERROR
Timeout → ERROR
```

---

## 7. Flux de données

### 🔄 Flux de géocodage standard

```
┌─────────────────────────────────────────────────────┐
│ 1. CHARGEMENT                                       │
├─────────────────────────────────────────────────────┤
│ Upload fichier CSV/TXT                              │
│    ↓                                                │
│ ingestion.detect_separator()                        │
│    ↓                                                │
│ ingestion.read_file() → DataFrame                   │
│    ↓                                                │
│ st.session_state.df = DataFrame                     │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 2. MAPPING                                          │
├─────────────────────────────────────────────────────┤
│ Sélection des colonnes (name, street, city, ...)    │
│    ↓                                                │
│ Validation du mapping                               │
│    ↓                                                │
│ Génération de full_address                          │
│ = name + ", " + street + ", " + postal_code + ...   │
│    ↓                                                │
│ st.session_state.df["full_address"] = ...           │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 3. CONFIGURATION                                    │
├─────────────────────────────────────────────────────┤
│ Sélection plage (start_line, end_line)              │
│ Définition batch_size                               │
│ Nombre de batches                                   │
│ Mode API (here/google/osm/multi)                    │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 4. GÉOCODAGE PAR BATCH                              │
├─────────────────────────────────────────────────────┤
│ Pour chaque batch:                                  │
│   ↓                                                 │
│ parallel_geocode_row(batch_df, mode)                │
│   ├─ ThreadPoolExecutor (10 workers)                │
│   ├─ Pour chaque ligne:                             │
│   │   ↓                                             │
│   │ geocode_single_row(row, api_mode)               │
│   │   ├─ Mode "here" → geocode_with_here()          │
│   │   ├─ Mode "google" → geocode_with_google()      │
│   │   ├─ Mode "osm" → geocode_with_osm()            │
│   │   └─ Mode "multi":                              │
│   │       ├─ Essayer HERE                           │
│   │       ├─ Si échec → Essayer Google              │
│   │       └─ Si échec → Essayer OSM                 │
│   │   ↓                                             │
│   │ Retour: {lat, lng, status, precision, ...}      │
│   ├─ Callback progress_callback()                   │
│   └─ Agrégation des résultats                       │
│   ↓                                                 │
│ enriched_batch (DataFrame)                          │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 5. FINALISATION                                     │
├─────────────────────────────────────────────────────┤
│ Concat tous les batches → selected_enriched_df      │
│    ↓                                                │
│ Création job entry                                  │
│    ↓                                                │
│ Calcul des statistiques                             │
│    ├─ Total succès/échecs                           │
│    ├─ Distribution précisions                       │
│    └─ Distribution APIs                             │
│    ↓                                                │
│ st.session_state.last_selected_enriched_df = ...    │
│ st.session_state.job_history.append(job)            │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 6. AFFICHAGE & EXPORT                               │
├─────────────────────────────────────────────────────┤
│ Affichage des résultats (métriques, tabs)           │
│    ↓                                                │
│ Option: Relance des échecs                          │
│    ↓                                                │
│ Export CSV/JSON/TXT                                 │
│    ↓                                                │
│ Export PDF historique                               │
└─────────────────────────────────────────────────────┘
```

### 🔁 Flux de relance intelligente

```
┌─────────────────────────────────────────────────────┐
│ 1. CHARGEMENT FICHIER GÉOCODÉ                       │
├─────────────────────────────────────────────────────┤
│ Upload CSV avec colonnes:                           │
│ - status, full_address, precision_level, ...        │
│    ↓                                                │
│ st.session_state.retry_df = DataFrame               │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 2. SÉLECTION DES LIGNES                             │
├─────────────────────────────────────────────────────┤
│ Filtres:                                            │
│ - Statuts: [ERROR, ZERO_RESULTS, ...]               │
│ - Précisions: [APPROXIMATE, GEOMETRIC_CENTER]       │
│    ↓                                                │
│ df_filtered = union(statuts, précisions)            │
│    ↓                                                │
│ Déduplication par ID ou full_address                │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 3. GÉNÉRATION DE VARIANTES                          │
├─────────────────────────────────────────────────────┤
│ Pour chaque ligne:                                  │
│   ↓                                                 │
│ generate_address_variants(row)                      │
│   ├─ Variante 1: Adresse originale                  │
│   ├─ Variante 2: Adresse reformatée (sans nom)      │
│   └─ Variante 3: Adresse structurée (composants)    │
│   ↓                                                 │
│ Liste de 3 variantes par ligne                      │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 4. TEST AVEC TOUTES LES APIs                        │
├─────────────────────────────────────────────────────┤
│ Pour chaque variante:                               │
│   Pour chaque API (here, google, osm):              │
│     ↓                                               │
│   geocode_with_api(variante, api)                   │
│     ↓                                               │
│   Résultat: {lat, lng, precision, api}              │
│     ↓                                               │
│   Ajout à la liste des résultats                    │
│   ↓                                                 │
│ Liste de tous les résultats (max 9 par ligne)       │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 5. SÉLECTION DU MEILLEUR RÉSULTAT                   │
├─────────────────────────────────────────────────────┤
│ select_best_result(results, original_precision)     │
│   ↓                                                 │
│ Critères (ordre de priorité):                       │
│ 1. Meilleure précision                              │
│    ROOFTOP > RANGE > GEOMETRIC > APPROXIMATE        │
│ 2. Si égalité: HERE > Google > OSM                  │
│   ↓                                                 │
│ Comparaison avec précision originale                │
│   ↓                                                 │
│ Si amélioration → improved = True                   │
│   ↓                                                 │
│ Retour: meilleur résultat + flag improved           │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 6. FINALISATION                                     │
├─────────────────────────────────────────────────────┤
│ retried_df = concat(tous les meilleurs résultats)   │
│    ↓                                                │
│ Mise à jour du DataFrame principal:                 │
│ - Suppression des anciennes lignes échecs           │
│ - Ajout des nouvelles lignes relancées              │
│    ↓                                                │
│ st.session_state.retry_updated_df = updated_df      │
│    ↓                                                │
│ Affichage stats + export                            │
└─────────────────────────────────────────────────────┘
```

### 📊 Flux d'analytics

```
┌─────────────────────────────────────────────────────┐
│ 1. CHARGEMENT FICHIER ENRICHI                       │
├─────────────────────────────────────────────────────┤
│ Upload CSV géocodé                                  │
│    ↓                                                │
│ Validation colonne "status" obligatoire             │
│    ↓                                                │
│ st.session_state.analytics_df = DataFrame           │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 2. CALCUL DES STATISTIQUES                          │
├─────────────────────────────────────────────────────┤
│ total_rows = len(df)                                │
│ total_success = (df["status"] == "OK").sum()        │
│ total_failed = total_rows - total_success           │
│ success_rate = (total_success / total_rows) * 100   │
│    ↓                                                │
│ precision_counts = df["precision_level"].value_counts()│
│ api_counts = df["api_used"].value_counts()          │
│    ↓                                                │
│ Affichage des métriques (st.metric)                 │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 3. GÉNÉRATION DES GRAPHIQUES                        │
├─────────────────────────────────────────────────────┤
│ create_analytics_plots(df)                          │
│   ↓                                                 │
│ fig = plt.subplots(2, 2)                            │
│   ├─ [0,0] Camembert des statuts                    │
│   ├─ [0,1] Barres des précisions                    │
│   ├─ [1,0] Barres horizontales des APIs             │
│   └─ [1,1] Donut du taux de succès                  │
│   ↓                                                 │
│ st.session_state.analytics_fig = fig                │
│   ↓                                                 │
│ st.pyplot(fig)                                      │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 4. APPLICATION DES FILTRES                          │
├─────────────────────────────────────────────────────┤
│ Filtres multiselect:                                │
│ - selected_status                                   │
│ - selected_precision                                │
│ - selected_apis                                     │
│    ↓                                                │
│ df_filtered = df[                                   │
│   (df["status"].isin(selected_status)) &            │
│   (df["precision_level"].isin(selected_precision)) &│
│   (df["api_used"].isin(selected_apis))              │
│ ]                                                   │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 5. EXPORT                                           │
├─────────────────────────────────────────────────────┤
│ Option 1: CSV filtré                                │
│   df_filtered.to_csv()                              │
│    ↓                                                │
│ Option 2: CSV complet                               │
│   df.to_csv()                                       │
│    ↓                                                │
│ Option 3: Rapport PDF                               │
│   generate_pdf_report(df, fig, stats)               │
│   ├─ Page 1: Graphiques (4 subplots)                │
│   └─ Page 2: Statistiques texte formaté             │
└─────────────────────────────────────────────────────┘
```

---

## 8. Guide utilisateur

### 🚀 Démarrage rapide

#### Scénario 1 : Premier géocodage

**Objectif** : Géocoder 5000 adresses avec HERE

1. **Lancer l'application**
   ```bash
   streamlit run main.py
   ```

2. **Page Géocodage**
   - Cliquer sur "📁 Chargement du fichier"
   - Glisser-déposer `adresses.csv`
   - Attendre chargement → ✅ Fichier chargé

3. **Mapping**
   - Cliquer sur "🧩 Mapping des Colonnes"
   - Mapper :
     * street → colonne "adresse"
     * postal_code → colonne "cp"
     * city → colonne "ville"
     * country → colonne "pays"
   - Cliquer "✅ Valider le mapping"
   - Vérifier l'aperçu de `full_address`

4. **Configuration**
   - Section "📍 Configuration du Géocodage"
   - Garder défauts :
     * Début: 0
     * Fin: 1000
     * Taille batch: 1000
     * Nombre de batches: 3
   - Sélectionner "HERE uniquement"
   - Cliquer "🚀 Lancer le Géocodage"

5. **Attendre traitement**
   - Observer progression en temps réel
   - Voir stats par batch
   - Attendre message "🎉 Géocodage terminé !"

6. **Consulter résultats**
   - Section "📊 Résultats du Géocodage"
   - Vérifier métriques :
     * Total: 3000
     * Succès: 2850 (95%)
     * Échecs: 150 (5%)
   - Explorer les tabs

7. **Exporter**
   - Section "📥 Exporter les Résultats"
   - Sélectionner "csv"
   - Séparateur: ","
   - Cliquer "📄 Générer et télécharger"
   - Cliquer "💾 Télécharger CSV"

**Résultat** : Fichier `geocodage_result_2024-11-14_15-30.csv` téléchargé

---

#### Scénario 2 : Relance des échecs

**Objectif** : Améliorer les 150 échecs avec relance intelligente

1. **Page Relance**
   - Naviguer vers "Relance" dans la sidebar

2. **Charger résultats**
   - Section "📂 Chargement du Fichier"
   - Glisser-déposer `geocodage_result_2024-11-14_15-30.csv`
   - Vérifier métriques :
     * Lignes: 3000
     * Échecs: 150

3. **Filtrer**
   - Section "🎯 Critères de Sélection"
   - Statuts: Garder tous les erreurs cochés
   - Précisions: Décocher tout (on veut juste les erreurs pures)
   - Vérifier : "🔎 150 lignes sélectionnées"

4. **Configurer**
   - Section "🔧 Configuration de la Relance"
   - Objectif de précision: ROOFTOP
   - Stratégie: Info-box visible

5. **Lancer**
   - Cliquer "🚀 Lancer la Relance Intelligente"
   - Attendre progression
   - Observer : "Traitement: 150/150 lignes..."

6. **Analyser résultats**
   - Section "📊 Résultats de la Relance"
   - Métriques :
     * Traitées: 150
     * Succès: 130 (86.7%)
     * Améliorées: 130
   - Nouveau taux global : (2850 + 130) / 3000 = 99.3% !

7. **Exporter**
   - Section "📥 Export des Résultats"
   - Cliquer "💾 Télécharger CSV (complet)"
   - Obtenir fichier avec 2980 succès / 20 échecs

**Résultat** : Taux de succès passé de 95% à 99.3% ! 🎉

---

#### Scénario 3 : Analytics et rapport

**Objectif** : Générer un rapport PDF avec graphiques

1. **Page Analytiques**
   - Naviguer vers "Analytiques"

2. **Charger données**
   - Glisser-déposer `complete_updated_2024-11-14_15-45.csv`
   - Vérifier métriques :
     * Total: 3000
     * Succès: 2980 (99.3%)
     * ROOFTOP: 2500 (83.9%)

3. **Explorer statistiques**
   - Section "📌 Statistiques Détaillées"
   - Voir distribution précisions (gauche)
   - Voir distribution APIs (droite)

4. **Visualiser**
   - Section "📈 Visualisations"
   - Observer les 4 graphiques
   - Analyser :
     * Camembert statuts : 99.3% vert !
     * Barres précisions : Majorité ROOFTOP
     * APIs : HERE domine
     * Donut : 99.3% au centre

5. **Filtrer**
   - Section "📥 Filtres et Téléchargement"
   - Sélectionner uniquement :
     * Statuts: OK
     * Précisions: ROOFTOP
     * APIs: here, google
   - Résultat : 2300 lignes

6. **Exporter rapport**
   - Cliquer "📊 Rapport PDF"
   - Cliquer "💾 Télécharger PDF"
   - Obtenir `rapport_analytics_2024-11-14_15-50.pdf`

7. **Ouvrir le PDF**
   - Page 1 : 4 graphiques colorés
   - Page 2 : Statistiques détaillées en texte

**Résultat** : Rapport professionnel prêt à présenter ! 📊

---

### 💡 Cas d'usage avancés

#### Amélioration progressive

**Processus** :
1. Géocodage initial avec HERE (rapide, 85% succès)
2. Relance des échecs avec Multi-API → 95% succès
3. Nouvelle relance des échecs restants → 99% succès
4. Filtrer les APPROXIMATE
5. Relance pour améliorer → 80% deviennent ROOFTOP

**Résultat** : 99% succès avec 95%+ ROOFTOP

#### Monitoring de qualité

**Indicateurs à surveiller** :
- Taux de succès global : **> 85%**
- Taux ROOFTOP : **> 60%**
- Taux APPROXIMATE : **< 20%**
- API dominante : Varie selon région
- Temps moyen : ~0.5s par ligne

**Alertes** :
- Taux succès < 60% → Problème qualité données
- Taux APPROXIMATE > 40% → Adresses trop vagues
- Échecs > 30% → Vérifier clés API

---

## 9. Développement et maintenance

### 🛠️ Structure du code

#### Conventions de nommage

**Fichiers** :
- `snake_case.py` pour les modules
- `PascalCase` pour les classes
- Préfixe `page_` pour les pages Streamlit

**Fonctions** :
- `snake_case()` pour toutes les fonctions
- Préfixe `render_` pour les fonctions UI
- Préfixe `geocode_` pour le géocodage
- Préfixe `export_` pour l'export

**Variables** :
- `snake_case` pour variables locales
- `UPPER_CASE` pour constantes
- Préfixe `df_` pour DataFrames

#### Organisation des imports

```python
# 1. Standard library
import os
from datetime import datetime

# 2. Third-party
import streamlit as st
import pandas as pd

# 3. Local
from src.config import GOOGLE_API_KEY
from src.geocoding import parallel_geocode_row
```

---

### 🧪 Tests

#### Tests unitaires

Fichier : `tests/test_geocoding.py`

```python
import pytest
from src.geocoding import geocode_with_here, geocode_with_google

def test_geocode_with_here_success():
    address = "123 Rue de la Paix, 75001 Paris, France"
    result = geocode_with_here(address)
    
    assert result["status"] == "OK"
    assert result["latitude"] is not None
    assert result["longitude"] is not None
    assert result["precision_level"] in ["ROOFTOP", "RANGE_INTERPOLATED"]

def test_geocode_with_here_invalid_address():
    address = "INVALID_ADDRESS_XYZ_123"
    result = geocode_with_here(address)
    
    assert result["status"] == "ZERO_RESULTS"
    assert result["latitude"] is None

def test_geocode_with_google_timeout():
    # Simuler un timeout
    import time
    address = "123 Test St"
    
    with pytest.raises(TimeoutError):
        geocode_with_google(address, timeout=0.001)
```

**Lancer les tests** :

```bash
pytest tests/ -v
```

---

### 📝 Logging

Configuration dans `src/logger.py` :

```python
import logging
import os
from datetime import datetime

def setup_logger(name, log_file=None, level=logging.INFO):
    """Configure un logger."""
    
    if log_file is None:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"geocoder_{datetime.now().strftime('%Y%m%d')}.log")
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    return logger
```

**Utilisation** :

```python
from src.logger import setup_logger

logger = setup_logger(__name__)

logger.info("Début du géocodage")
logger.warning("API HERE lente")
logger.error("Échec géocodage", exc_info=True)
```

---

### 🔧 Configuration avancée

#### Variables d'environnement

Fichier `.env` complet :

```env
# APIs
HERE_API_KEY=your_here_key
GOOGLE_API_KEY=your_google_key
OSM_EMAIL=your_email@example.com

# Performance
MAX_WORKERS=10
BATCH_SIZE=1000
TIMEOUT=30

# Retry
MAX_RETRIES=3
RETRY_DELAY=1

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs

# Export
EXPORT_DIR=data/output
```

#### Configuration dynamique

Fichier `src/config.py` étendu :

```python
from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # APIs
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OSM_EMAIL = os.getenv("OSM_EMAIL")
    HERE_API_KEY = os.getenv("HERE_API_KEY")
    
    # Performance
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))
    TIMEOUT = int(os.getenv("TIMEOUT", "30"))
    
    # Retry
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "1"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    
    # Export
    EXPORT_DIR = os.getenv("EXPORT_DIR", "data/output")
```

---

### 🚀 Déploiement

#### Streamlit Cloud

1. **Préparer le repository**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push gitlab main
   ```

2. **Créer app sur Streamlit Cloud**
   - Aller sur https://streamlit.io/cloud
   - New app → From existing repo
   - Sélectionner repository
   - Branch: main
   - Main file: main.py

3. **Configurer secrets**
   - App settings → Secrets
   - Ajouter :
   ```toml
   HERE_API_KEY = "your_key"
   GOOGLE_API_KEY = "your_key"
   OSM_EMAIL = "your_email"
   ```

4. **Déployer**
   - Save → Deploy
   - Attendre ~5 minutes
   - App disponible sur `<app-name>.streamlit.app`

---

#### Docker

Fichier `Dockerfile` :

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Build et run** :

```bash
docker build -t geocoder-bot .
docker run -p 8501:8501 --env-file .env geocoder-bot
```

---

### 📊 Monitoring en production

#### Métriques à surveiller

```python
import time
from functools import wraps

def monitor_performance(func):
    """Décorateur pour mesurer performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        duration = end_time - start_time
        logger.info(f"{func.__name__} took {duration:.2f}s")
        
        return result
    return wrapper

@monitor_performance
def parallel_geocode_row(df, ...):
    # Code de géocodage
    pass
```

---

### 🐛 Debugging

#### Problèmes courants

| Problème | Cause | Solution |
|----------|-------|----------|
| **"INVALID_API_KEY"** | Clé API invalide/expirée | Vérifier `.env`, régénérer clé |
| **"OVER_QUERY_LIMIT"** | Quota dépassé | Attendre reset ou upgrade plan |
| **Timeout** | Réseau lent ou API down | Augmenter timeout, vérifier status API |
| **ZERO_RESULTS** | Adresse invalide | Vérifier format, essayer Multi-API |
| **OSM trop lent** | Délai 1s obligatoire | Normal, utiliser autre API si urgent |
| **Fichier non lu** | Encoding ou séparateur | Vérifier encoding, forcer séparateur |
| **Mémoire saturée** | Fichier trop gros | Réduire batch_size ou diviser fichier |
| **Persistance perdue** | Session_state non init | Vérifier `initialize_*_state()` appelée |

#### Mode debug

Ajouter dans `main.py` :

```python
import streamlit as st

# Mode debug
DEBUG = st.sidebar.checkbox("🐛 Mode Debug")

if DEBUG:
    st.sidebar.json({
        "session_state": {k: type(v).__name__ for k, v in st.session_state.items()},
        "df_shape": st.session_state.df.shape if st.session_state.df is not None else None,
    })
```

---

## 📚 Ressources

### Documentation APIs

- **HERE** : https://developer.here.com/documentation/geocoding-search-api/
- **Google** : https://developers.google.com/maps/documentation/geocoding/
- **OSM** : https://nominatim.org/release-docs/latest/api/Search/

---

## 📞 Support

### FAQ

**Q : Combien coûte le géocodage ?**  
R : HERE et Google offrent un tier gratuit. Ensuite payant selon usage. OSM est toujours gratuit.

**Q : Quelle API choisir ?**  
R : Mode Multi-API recommandé pour maximiser taux de succès.

**Q : Combien de temps pour 100k adresses ?**  
R : ~1-2 heures avec Multi-API (fallback), ~45min avec une seule API.

**Q : Puis-je interrompre un géocodage ?**  
R : Non actuellement. Prévu dans version future.

**Q : Les données sont-elles sauvegardées ?**  
R : Oui dans `data/output/`. Pensez à exporter régulièrement.

---

**Version** : 2.0  
**Dernière mise à jour** : Novembre 2024  
**Auteur** : Rabah TAALBI - EXPERT SKILLS4MIND

---
