import streamlit as st
import os
import json
import re
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from evaluator import (
    load_weights,
    extract_text_from_pdf,
    extract_sections,
    score_sections_with_optional_gemini,
)
from db import save_api_key, get_api_key

OUTPUTS_DIR = "outputs"
PROPOSALS_DIR = "proposals"
API_SERVICE_NAME = "google_gemini"

def save_uploaded_file(uploaded_file, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def plot_bar_chart(df):
    fig, ax = plt.subplots()
    categories = ['cost_score', 'technical_merit_score', 'past_performance_score']
    vendors = df['vendor']
    bar_width = 0.2
    indices = np.arange(len(vendors))
    for i, category in enumerate(categories):
        ax.bar(indices + i * bar_width, df[category], bar_width, label=category)
    ax.set_xticks(indices + bar_width)
    ax.set_xticklabels(vendors, rotation=45, ha='right')
    ax.set_ylabel('Scores')
    ax.set_title('Proposal Scores by Category')
    ax.legend()
    plt.tight_layout()
    return fig

def plot_radar_chart(df):
    categories = ['cost_score', 'technical_merit_score', 'past_performance_score']
    labels = np.array(categories)
    num_vars = len(categories)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    for idx, row in df.iterrows():
        values = row[categories].tolist()
        values += values[:1]
        ax.plot(angles, values, label=row['vendor'])
        ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_yticklabels([])
    ax.set_title('Proposal Scores Radar Chart')
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    plt.tight_layout()
    return fig

def main():
    st.title("AI-Based Proposal Evaluation Assistant")

    st.markdown("""
    Welcome to the AI-Based Proposal Evaluation Assistant. This app allows you to upload 2-3 PDF proposal documents, extract key sections, and evaluate them using heuristic scoring or optionally with Google Gemini AI.

    **Instructions:**
    1. Upload 2-3 PDF proposal files using the uploader below.
    2. Enter your Google Gemini API key in the sidebar if you want to use advanced AI scoring.
    3. Save your API key securely.
    4. Use the checkbox to enable or disable Gemini scoring.
    5. Optionally, request detailed Gemini explanations and insights about each proposal.
    6. View the ranked results, visual charts, and download the evaluation reports.

    **Note:** Gemini scoring and explanations require a valid API key and internet connection.
    """)

    # Sidebar for Gemini API key input
    st.sidebar.header("Gemini API Key")
    stored_key = get_api_key(API_SERVICE_NAME)
    api_key_input = st.sidebar.text_input(
        "Enter Gemini API Key", value=stored_key if stored_key else "", type="password"
    )
    if st.sidebar.button("Save API Key"):
        if api_key_input.strip():
            save_api_key(API_SERVICE_NAME, api_key_input.strip())
            st.sidebar.success("API Key saved securely.")
        else:
            st.sidebar.error("API Key cannot be empty.")

    use_gemini = False
    use_gemini_explain = False
    if stored_key:
        st.sidebar.markdown("### Gemini Scoring Options")
        use_gemini = st.sidebar.checkbox("Use Gemini Scoring", value=False)
        if use_gemini:
            use_gemini_explain = st.sidebar.checkbox("Get Gemini Explanations and Insights", value=False)

    st.header("Upload 2-3 Proposal PDFs")
    uploaded_files = st.file_uploader(
        "Upload PDF proposals", type=["pdf"], accept_multiple_files=True
    )

    if uploaded_files and 2 <= len(uploaded_files) <= 3:
        weights = load_weights()
        results = []
        gemini_explanations = []
        st.info("Processing proposals...")

        all_costs = []
        for uploaded_file in uploaded_files:
            file_path = save_uploaded_file(uploaded_file, PROPOSALS_DIR)
            text = extract_text_from_pdf(file_path)
            sections = extract_sections(text)
            numbers = re.findall(r"\$?([\d,]+(?:\.\d+)?)", sections.get("cost", "").replace(",", ""))
            costs = [float(num) for num in numbers if num.replace('.', '', 1).isdigit()]
            all_costs.append(min(costs) if costs else None)

        for idx, uploaded_file in enumerate(uploaded_files):
            file_path = os.path.join(PROPOSALS_DIR, uploaded_file.name)
            text = extract_text_from_pdf(file_path)
            sections = extract_sections(text)
            # Remove all_costs argument as it is not accepted by score_sections_with_optional_gemini
            scores = score_sections_with_optional_gemini(
                sections, weights, api_key=stored_key if use_gemini else None
            )
            results.append({
                "vendor": uploaded_file.name,
                "cost_score": scores["cost_score"],
                "technical_merit_score": scores["technical_merit_score"],
                "past_performance_score": scores["past_performance_score"],
                "final_score": scores["final_score"],
                "summary": "\n\n".join([sections.get("cost", ""), sections.get("technical_merit", ""), sections.get("past_performance", "")])
            })

            if use_gemini and use_gemini_explain:
                try:
                    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
                    headers = {
                        "Content-Type": "application/json",
                        "X-goog-api-key": stored_key
                    }
                    prompt_text = f"""Provide a concise, bullet-point summary of key insights about the following proposal sections. Keep it short and to the point.\n\nCost:\n{sections.get('cost', '')}\n\nTechnical Approach:\n{sections.get('technical_merit', '')}\n\nPast Performance:\n{sections.get('past_performance', '')}"""
                    data = {
                        "contents": [
                            {
                                "parts": [
                                    {"text": prompt_text}
                                ]
                            }
                        ]
                    }
                    response = requests.post(url, headers=headers, json=data)
                    response.raise_for_status()
                    explanation_raw = response.json().get("candidates", [{}])[0].get("content", "No explanation available.")
                    if isinstance(explanation_raw, str):
                        explanation = explanation_raw.strip()
                    elif isinstance(explanation_raw, dict) and "parts" in explanation_raw:
                        # Join parts text if content is structured
                        explanation = "\n".join(part.get("text", "") for part in explanation_raw["parts"])
                    else:
                        explanation = str(explanation_raw)
                    gemini_explanations.append({"vendor": uploaded_file.name, "explanation": explanation})
                except Exception as e:
                    gemini_explanations.append({"vendor": uploaded_file.name, "explanation": f"Error fetching explanation: {e}"})

        if results:
            df = pd.DataFrame(results)
            df["rank"] = df["final_score"].rank(ascending=False, method="min").astype(int)
            df = df.sort_values("rank")

            st.subheader("Evaluation Results")
            st.dataframe(df[["vendor", "cost_score", "technical_merit_score", "past_performance_score", "final_score", "rank"]])

            st.subheader("Score Visualizations")
            st.pyplot(plot_bar_chart(df))
            st.pyplot(plot_radar_chart(df))

            if use_gemini and use_gemini_explain:
                st.subheader("Gemini Explanations and Insights")
                for item in gemini_explanations:
                    st.markdown(f"### {item['vendor']}")
                    st.write(item["explanation"])

            os.makedirs(OUTPUTS_DIR, exist_ok=True)
            excel_path = os.path.join(OUTPUTS_DIR, "ranked_output.xlsx")
            json_path = os.path.join(OUTPUTS_DIR, "ranked_output.json")
            df.to_excel(excel_path, index=False)
            df.to_json(json_path, orient="records", indent=2)

            with open(excel_path, "rb") as f:
                st.download_button("Download Excel", data=f, file_name="ranked_output.xlsx")
            with open(json_path, "rb") as f:
                st.download_button("Download JSON", data=f, file_name="ranked_output.json")
        else:
            st.warning("No results to display.")
    elif uploaded_files:
        st.error("Please upload between 2 and 3 PDF files.")
    else:
        st.info("Upload 2-3 PDF proposal files to begin evaluation.")

if __name__ == "__main__":
    main()