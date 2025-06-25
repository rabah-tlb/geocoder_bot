# geocoder_bot

# 🗺️ Robot de Géocodage Multi-API

Ce projet permet de géocoder automatiquement des adresses à partir de fichiers CSV/TXT via une application Streamlit. Il utilise plusieurs APIs (HERE et Google Maps) pour maximiser la précision.

---

## 🛠️ Installation

### 1. Cloner le dépôt

```bash
    git clone https://github.com/ton-org/robot-geocodage.git
    cd robot-geocodage

2. Créer un environnement virtuel

    python -m venv venv
    source venv/bin/activate  # Sur Linux/Mac
    venv\Scripts\activate     # Sur Windows

3. Installer les dépendances
    pip install -r requirements.txt

4. Configurer les clés API
    Copier le fichier .env.example en .env :
        cp .env.example .env
    
    Remplir les clés API dans .env :
        GOOGLE_API_KEY=your_google_key
        OSM_EMAIL=your_email@domain.com
        HERE_API_KEY=your_here_key
        
    Lancer l'application :  
        streamlit run main.py
    
    L'application sera accessible dans votre navigateur à l’adresse : http://localhost:8501

```