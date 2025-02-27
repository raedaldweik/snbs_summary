import os
import pandas as pd
import streamlit as st
import altair as alt
from dotenv import load_dotenv
import openai

st.set_page_config(page_title="Banking Data Summary", layout="wide")

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

@st.cache_data
def load_data():
    return pd.read_excel("Retail_Bank.xlsx")

df = load_data()

# Language selection
lang = st.radio("Language", ["English", "Arabic"], index=0)
if lang == "Arabic":
    user_prompt_lang = "الرجاء الرد باللغة العربية."
    title_text = "تقرير ملخص البيانات المصرفية"
    button_text = "توليد تقرير موجز"
    intro_text = """
انقر على الزر للحصول على تقرير سردي مفصل ومستنير بالبيانات لمجموعة البيانات المصرفية الأساسية، 
مع تسليط الضوء على الأنماط البارزة والكشف عن النتائج النادرة.
"""
else:
    user_prompt_lang = "Please respond in English."
    title_text = "Banking Data Summary Report"
    button_text = "Generate Summary Report"
    intro_text = """
Click on the button to get a detailed and data-driven narrative summary of the banking dataset,
highlighting key trends and rare insights.
"""

st.title(title_text)
st.write(intro_text)

if st.button(button_text):
    num_rows = len(df)
    num_columns = len(df.columns)
    numerical_cols = df.select_dtypes(include=['int64','float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # Get top values
    top_segments = df['Segment'].value_counts().head(5) if 'Segment' in df.columns else None
    top_credit_types = df['Credit_Type'].value_counts().head(5) if 'Credit_Type' in df.columns else None
    risk_distribution = df['Risk_Segment'].value_counts() if 'Risk_Segment' in df.columns else None
    approval_status_counts = df['Approval_Status'].value_counts() if 'Approval_Status' in df.columns else None
    age_stats = df['Age'].describe() if 'Age' in df.columns else None
    
    rare_categories_info = {}
    for col in categorical_cols:
        counts = df[col].value_counts()
        rare = counts[counts < 5].index.tolist()
        if rare:
            rare_categories_info[col] = rare
    
    primary_color = "#3da47d"
    
    def make_bar_chart(data, x_label, y_label, title):
        if data is not None:
            chart_data = data.reset_index()
            chart_data.columns = [x_label, y_label]
            return alt.Chart(chart_data).mark_bar(color=primary_color).encode(
                x=alt.X(x_label, sort='-y'),
                y=y_label,
                tooltip=[x_label, y_label]
            ).properties(title=title)
        return None
    
    segment_chart = make_bar_chart(top_segments, 'Segment', 'count', "Top 5 Customer Segments")
    credit_chart = make_bar_chart(top_credit_types, 'Credit_Type', 'count', "Top 5 Credit Types")
    risk_chart = make_bar_chart(risk_distribution, 'Risk_Segment', 'count', "Risk Segment Distribution")
    approval_chart = make_bar_chart(approval_status_counts, 'Approval_Status', 'count', "Approval Status Breakdown")
    
    prompt = f"""
{user_prompt_lang}

You are a data expert analyzing a banking dataset with {num_rows} rows and {num_columns} columns.
Categorical columns: {categorical_cols}
Numerical columns: {numerical_cols}

Findings:
- Top 5 customer segments: {top_segments.to_dict() if top_segments is not None else "None"}
- Top 5 credit types: {top_credit_types.to_dict() if top_credit_types is not None else "None"}
- Risk segment distribution: {risk_distribution.to_dict() if risk_distribution is not None else "None"}
- Approval status breakdown: {approval_status_counts.to_dict() if approval_status_counts is not None else "None"}
- Age statistics: {age_stats.to_dict() if age_stats is not None else "None"}
- Rare categories: {rare_categories_info if rare_categories_info else "None"}

In your response:
- Provide a very thorough, detailed, and explanatory analysis that goes beyond generic statements.
- Highlight subtle patterns, anomalies, or rare insights not obvious at first glance.
- Integrate the concept of these visual findings into the narrative.
- Include the following placeholders where you'd like the charts to appear:
  - <<CHART_SEGMENTS>> for Customer Segment Distribution
  - <<CHART_CREDIT>> for Credit Type Breakdown
  - <<CHART_RISK>> for Risk Segment Distribution
  - <<CHART_APPROVAL>> for Approval Status Breakdown

Make the explanation rich in detail, non-generic, and insightful, benefiting both a data analyst and a bank manager.
"""
    
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful and detail-oriented data analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=7000
    )
    
    summary_text = response.choices[0].message["content"].strip()
    
    container = st.container()
    final_text = summary_text
    
    placeholders = [
        ("<<CHART_SEGMENTS>>", segment_chart),
        ("<<CHART_CREDIT>>", credit_chart),
        ("<<CHART_RISK>>", risk_chart),
        ("<<CHART_APPROVAL>>", approval_chart)
    ]
    
    for placeholder, chart in placeholders:
        if placeholder in final_text:
            before, after = final_text.split(placeholder, 1)
            container.write(before)
            if chart is not None:
                container.altair_chart(chart, use_container_width=True)
            else:
                container.write("No data available for this chart.")
            final_text = after
    
    container.write(final_text)
