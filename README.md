ai-oriki-system/
│
├── app/                        # Main application
│   ├── main.py                # Streamlit frontend (UI)
│   ├── config.py              # API keys (YarnGPT, etc.)
│
│   ├── services/              # Core logic
│   │   ├── oriki_service.py   # Handles CSV + generation
│   │   ├── translation.py     # Translation logic
│   │   ├── tts_service.py     # YarnGPT TTS integration
│
│   ├── utils/
│   │   ├── loader.py          # Load CSV files
│   │   ├── generator.py       # Combine/generate Oríkì
│
│   ├── data/                  # Your datasets
│   │   ├── yoruba.csv
│   │   ├── igbo.csv
│   │   ├── hausa.csv
│
│   ├── models/ (optional later)
│
├── requirements.txt
├── README.md