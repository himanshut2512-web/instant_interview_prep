"""Sample inputs for the "Try a sample" button. The candidate and JD are fictional/illustrative."""

SAMPLE_RESUME = """AARAV MEHTA (fictional sample candidate)
Data Scientist | Bengaluru, India | aarav.mehta@example.com

SUMMARY
Data Scientist with 4 years of experience building forecasting, churn and NLP solutions for retail and CPG
clients. Comfortable owning problems end to end: scoping with business stakeholders, building features in
SQL/PySpark, modelling in Python and deploying with MLflow and Docker on Azure.

EXPERIENCE
Data Scientist - Northwind Retail Analytics (Jul 2022 - Present)
- Built a SKU-store demand forecasting system (LightGBM + hierarchical reconciliation) for 1,200 stores;
  cut forecast error (WAPE) from 31% to 22% and reduced stock-outs by 9%.
- Designed a customer churn model (XGBoost, SHAP) for a subscription grocery client; targeted retention
  campaigns saved an estimated INR 3.2 Cr annually.
- Built a RAG assistant over 40k product and policy documents using Azure OpenAI, LangChain and a FAISS
  vector store; added evaluation with a golden question set and reduced hallucinated answers by 35%.
- Productionised models with MLflow model registry, Docker and Azure ML pipelines; set up drift monitoring.
- Mentored two junior analysts; ran weekly model-review sessions.

Associate Data Analyst - BrightPath Consulting (Jun 2020 - Jun 2022)
- Wrote complex SQL (window functions, CTEs) on Snowflake to build marketing-mix and campaign dashboards.
- Built Power BI dashboards used by 60+ sales managers; automated weekly reporting with Python.
- Ran A/B tests for pricing experiments; designed sample sizes and analysed results with t-tests and CUPED.

SKILLS
Python (pandas, NumPy, scikit-learn, XGBoost, LightGBM, PyTorch basics), SQL, PySpark, Databricks,
Statistics & A/B testing, Time-series forecasting, NLP, LLMs (RAG, prompt engineering), Azure ML, MLflow,
Docker, Git, Power BI

EDUCATION
B.Tech, Computer Science - 2020

CERTIFICATIONS
Microsoft Azure Data Scientist Associate (DP-100)
"""

SAMPLE_JD = """Senior Data Scientist (illustrative sample JD) - Analytics consulting

About the role
You will work with Fortune 500 clients in retail, CPG and BFSI to solve complex business problems using data
science and AI. You will own the full lifecycle: problem framing with client stakeholders, data exploration,
feature engineering, modelling, deployment and communicating insights to senior leadership.

Responsibilities
- Translate ambiguous business problems into analytical approaches and deliver measurable impact.
- Build and deploy machine learning models (classification, regression, forecasting, clustering) at scale.
- Design and run experiments (A/B tests) and causal analyses to measure impact.
- Build Generative AI solutions (LLMs, RAG, agents) for client use cases and evaluate them rigorously.
- Write production-quality Python and SQL; work with Spark/Databricks on large datasets.
- Deploy models on cloud (Azure/AWS/GCP) with MLOps best practices (CI/CD, monitoring, retraining).
- Present findings to client leadership and mentor junior data scientists.

Requirements
- 3-6 years of experience in data science / machine learning.
- Strong Python, SQL and statistics; solid grasp of ML algorithms and model evaluation.
- Experience with time-series forecasting, customer analytics or pricing is a plus.
- Hands-on experience with PySpark/Databricks and at least one cloud platform.
- Exposure to LLMs, prompt engineering and RAG pipelines.
- Excellent communication and stakeholder-management skills; consulting mindset.
"""

SAMPLE_INPUT = {
    "company": "Tiger Analytics",
    "role": "Senior Data Scientist",
    "years_experience": 4,
    "resume_text": SAMPLE_RESUME,
    "job_description": SAMPLE_JD,
    "extra_notes": "I have heard there is a SQL + Python coding round, an ML case study round and a "
    "client-facing/managerial round. I want extra focus on GenAI and forecasting.",
}
