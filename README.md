![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Streamlit](https://img.shields.io/badge/Streamlit-%23FE4B4B.svg?style=for-the-badge&logo=streamlit&logoColor=white) ![Google Gemini](https://img.shields.io/badge/google%20gemini-8E75B2?style=for-the-badge&logo=google%20gemini&logoColor=white)

# AI-Based Proposal Evaluation Assistant

## Project Overview
This project is an interactive Streamlit app designed to evaluate and rank PDF proposal documents. It extracts key sections from proposals, scores them using heuristic methods or optionally with Google Gemini API for advanced scoring, and displays ranked results with downloadable reports.

## Dependencies and Installation
- Python 3.7+
- Install dependencies with:
  ```
  pip install -r requirements.txt
  ```

## How to Run
Run the Streamlit app with:
```bash
python -m streamlit run app.py
```

## Gemini API Key
- You can enter your Google Gemini API key in the sidebar of the app.
- The key is securely stored locally in a SQLite database for future use.
- If the key is provided, Gemini scoring will be used for Technical Approach and Past Performance sections instead of heuristic scoring.

## Scoring Explanation
- **Heuristic Scoring:** Uses word counts and keyword density for Technical and Past Performance, and normalized cost for Cost.
- **Gemini Scoring:** Uses Google Gemini API to rate Technical and Past Performance sections on a 0-100 scale based on prompts.

## Project Structure
```
ai-based-proposal-evaluation-assistant/
├── app.py                  # Streamlit frontend
├── evaluator.py            # Core extraction & scoring logic
├── db.py                   # SQLite API key management
├── weights_config.json     # JSON with cost/tech/past weight floats
├── requirements.txt
├── proposals/              # Folder for sample or uploaded PDFs
│   └── proposal1.pdf
│   └── proposal2.pdf
├── outputs/
│   ├── ranked_output.xlsx
│   └── ranked_output.json
├── tests/                  # Unit tests (if included)
├── api_key_store.db        # Stored Gemini API key (SQLite)
├── __pycache__/            # Python cache
├── .gitignore
└── README.md
```

## Screenshots (Full View)

### 📥 Main Upload and API Key Sidebar
<img src="Screenshot (8).png" alt="Main Upload and API Key Sidebar" width="100%">

### 📊 Ranked Results and Visualizations
<img src="Screenshot (9).png" alt="Ranked Results and Visualizations" width="100%">

### 🤖 Gemini Explanations and Insights - Part 1
<img src="Screenshot (10).png" alt="Gemini Explanations and Insights Part 1" width="100%">

### 📈 Gemini Explanations and Insights - Part 2
<img src="Screenshot (11).png" alt="Gemini Explanations and Insights Part 2" width="100%">

## Notes
- Ensure you have an active internet connection to use Gemini API features.
- The sample PDFs in the `proposals/` folder are placeholders; upload your own proposals for evaluation.

## .gitignore
Please see the `.gitignore` file in the project root to exclude environment files, outputs, and database files.
