import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import chardet
import io
from langchain_groq import ChatGroq

# ── Page Setup ──────────────────────────────────────
st.set_page_config(page_title="AI EDA Agent", page_icon="🤖")
st.title("🤖 Agentic AI EDA Pipeline")
st.write("Upload any CSV file and AI will analyze it automatically!")

# ── Sidebar API Key ──────────────────────────────────
st.sidebar.title("⚙️ Settings")
st.sidebar.write("Get free API key at groq.com")
groq_api_key = st.sidebar.text_input(
    "🔑 Enter Groq API Key",
    type="password",
    placeholder="gsk_xxxxxxxxxxxx"
)

# ── File Upload ──────────────────────────────────────
uploaded_file = st.file_uploader("📁 Upload your CSV file", type=["csv"])

if uploaded_file and groq_api_key:

    try:
        # Auto detect encoding
        raw_data = uploaded_file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding'] or 'utf-8'

        # Try reading with flexible settings
        try:
            df = pd.read_csv(
                io.BytesIO(raw_data),
                encoding=encoding,
                on_bad_lines='skip',
                engine='python',
                sep=None
            )
        except Exception:
            df = pd.read_csv(
                io.BytesIO(raw_data),
                encoding='latin-1',
                on_bad_lines='skip',
                engine='python'
            )

        st.success(f"✅ Dataset loaded! Shape: {df.shape}")

        # Show Data Preview
        st.subheader("📊 Data Preview")
        st.dataframe(df.head())

        # Show Missing Values
        st.subheader("❓ Missing Values")
        st.dataframe(df.isnull().sum())

        # Connect to Groq
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=groq_api_key
        )

        if st.button("🤖 Run AI Analysis!"):

            # ── Chart 1: Distributions ───────────────
            st.subheader("📊 Distributions of Numerical Columns")
            numeric_cols = df.select_dtypes(include='number').columns

            if len(numeric_cols) > 0:
                for col in numeric_cols:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    sns.histplot(x=col, data=df, ax=ax,
                                kde=True, color='steelblue')
                    ax.set_title(f"Distribution of {col}")
                    st.pyplot(fig)
                    plt.close(fig)
            else:
                st.warning("⚠️ No numerical columns found!")

            # ── Chart 2: Correlation Heatmap ─────────
            st.subheader("🔥 Correlation Heatmap")
            numeric_df = df.select_dtypes(include='number')

            if len(numeric_df.columns) > 1:
                fig, ax = plt.subplots(figsize=(10, 8))
                corr = numeric_df.corr()
                sns.heatmap(corr, annot=True,
                           cmap='coolwarm', ax=ax)
                ax.set_title("Correlation Heatmap")
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.warning("⚠️ Not enough numerical columns!")

            # ── Chart 3: Missing Values ───────────────
            st.subheader("❓ Missing Values Chart")
            missing = df.isnull().sum()
            missing = missing[missing > 0]

            if len(missing) > 0:
                fig, ax = plt.subplots(figsize=(8, 4))
                sns.barplot(x=missing.values,
                           y=missing.index,
                           ax=ax, color='salmon')
                ax.set_title("Missing Values Per Column")
                ax.set_xlabel("Missing Count")
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.success("✅ No missing values found!")

            # ── Chart 4: Summary Statistics ──────────
            st.subheader("📈 Summary Statistics")
            st.dataframe(df.describe())

            # ── Analyst Agent ─────────────────────────
            st.subheader("🧠 AI Insights")
            with st.spinner("🤖 AI is thinking... Please wait!"):
                try:
                    analysis_summary = df.describe(
                        include="all").to_string()

                    insight_prompt = f"""
                    You are a senior data scientist.
                    Here are the statistics:
                    {analysis_summary}

                    Explain in simple words:
                    - Key patterns
                    - Data quality issues
                    - Important columns
                    - Recommendations for ML model
                    """

                    insight_response = llm.invoke(insight_prompt)
                    insights = insight_response.content

                    # Show insights
                    st.success("✅ AI Analysis Complete!")
                    st.write(insights)

                    # Copyable text box
                    st.subheader("📋 Copy AI Insights:")
                    st.text_area(
                        label="AI Generated Insights",
                        value=insights,
                        height=400
                    )

                    # Download Report
                    report = f"""
=== EDA REPORT ===

Dataset Shape: {df.shape}

=== SUMMARY STATISTICS ===

{df.describe(include='all').to_string()}

=== AI INSIGHTS ===

{insights}
                    """
                    st.download_button(
                        label="📄 Download Full Report",
                        data=report,
                        file_name="eda_report.txt",
                        mime="text/plain"
                    )

                except Exception as e:
                    st.error(f"❌ AI Error: {str(e)}")
                    st.write("Check your Groq API key!")

    except Exception as e:
        st.error(f"❌ Could not read CSV: {str(e)}")
        st.warning("💡 Try opening your CSV in Excel → Save As → CSV UTF-8")

elif uploaded_file and not groq_api_key:
    st.warning("⚠️ Please enter Groq API Key in sidebar!")

elif not uploaded_file and groq_api_key:
    st.info("📁 Please upload a CSV file!")

else:
    st.info("👈 Enter API Key in sidebar + Upload CSV file to begin!")