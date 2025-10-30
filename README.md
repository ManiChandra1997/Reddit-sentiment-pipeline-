Reddit Sentiment Analysis & Automation Pipeline

End-to-End Data Engineering & Analytics Project
Built with Apache Airflow, PostgreSQL, PRAW, and Streamlit — this pipeline automates data ingestion from Reddit, performs sentiment analysis, stores insights in a database, and visualizes them in an interactive dashboard.

🚀 Project Overview

This project automates the process of fetching Reddit comments related to government policies, analyzing their sentiment (Positive, Negative, Neutral), storing results in a PostgreSQL database, and visualizing insights in a Streamlit dashboard.
It demonstrates a complete data engineering pipeline — from ingestion to analytics to deployment — orchestrated using Apache Airflow.

🧠 Key Features

✅ Automated Reddit data extraction using PRAW (Python Reddit API Wrapper)
✅ Real-time sentiment classification using pre-trained transformer models
✅ Scalable data orchestration with Apache Airflow DAGs
✅ Persistent storage in PostgreSQL
✅ Interactive Streamlit dashboard for analytics & trend visualization
✅ Containerized setup with Docker + docker-compose
✅ Secure configuration using Airflow Variables and .env management

🧩 Project Architecture
               ┌────────────────────┐
               │      Reddit API     │
               └─────────┬───────────┘
                         │
                   (1) Ingestion via PRAW
                         │
               ┌─────────▼───────────┐
               │     Airflow DAGs     │
               │  (ETL Orchestration) │
               └─────────┬───────────┘
                         │
                   (2) Load Data
                         │
               ┌─────────▼───────────┐
               │     PostgreSQL DB    │
               └─────────┬───────────┘
                         │
                   (3) Analysis / Query
                         │
               ┌─────────▼───────────┐
               │   Streamlit Dashboard│
               │ (Visualization Layer)│
               └──────────────────────┘

🛠️ Tech Stack
Component	Tool / Library
Workflow Orchestration	Apache Airflow
Data Storage	PostgreSQL
API Source	Reddit (via PRAW)
Sentiment Analysis	Hugging Face Transformers / VADER
Dashboard / Visualization	Streamlit
Containerization	Docker + docker-compose
Environment Management	.env + Airflow Variables
⚙️ Project Setup
1️⃣ Clone the Repository
git clone https://github.com/yourusername/reddit-sentiment-pipeline.git
cd reddit-sentiment-pipeline

2️⃣ Create Environment File

Create a .env file by copying the provided template:

cp .env.example .env


Then fill in your Reddit API credentials:

REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=reddit_sentiment_app/0.1

3️⃣ Build and Start the Docker Containers
docker-compose up -d


This spins up:

PostgreSQL Database

Apache Airflow (Webserver, Scheduler, Worker)

Streamlit Dashboard

4️⃣ Access the Services
Service	URL
Airflow Web UI	http://localhost:8080

Streamlit Dashboard	http://localhost:8501

PostgreSQL	localhost:5432
📅 Airflow DAGs
DAG Name	Description
reddit_ingestion_dag	Fetches Reddit posts/comments via API
sentiment_analysis_dag	Analyzes comment sentiment and stores results
data_cleaning_dag	Cleans & transforms data before dashboard use
daily_refresh_dag	Refreshes dashboard datasets automatically
🧮 ETL Logic

1️⃣ Extract: Fetch Reddit comments using PRAW
2️⃣ Transform: Clean text, detect language, compute sentiment score
3️⃣ Load: Insert processed results into PostgreSQL

📊 Streamlit Dashboard

Interactive dashboard visualizes:

Sentiment distribution (Positive / Negative / Neutral)

Time-series trends

Subreddit-level comparison

Keyword heatmaps

Launch it manually (if outside Docker):

streamlit run dashboard/app.py

🔒 Security & Credential Management

✅ No secrets in code — all credentials are stored as:

Airflow Variables (inside the web UI)

Local .env (excluded via .gitignore)

✅ .env.example provided for reproducibility
✅ .gitignore ensures .env, __pycache__, venv/, and logs are never committed

📁 Folder Structure
reddit-sentiment-pipeline/
│
├── dags/                      # Airflow DAG definitions
├── etl_scripts/               # ETL and analysis scripts
├── dashboard/                 # Streamlit dashboard app
│
├── docker-compose.yml         # Docker orchestration
├── requirements.txt           # Python dependencies
├── .env.example               # Template env file
├── .gitignore
├── README.md
└── LICENSE

🧰 Requirements

Docker & Docker Compose

Reddit Developer Account (to get API keys)

Basic understanding of Airflow and SQL

📦 Deployment

For cloud deployment (optional):

Push Docker images to Docker Hub

Deploy on AWS EC2, GCP VM, or Azure Container App

Use Airflow Cloud Composer or Astronomer for managed orchestration

📈 Future Enhancements

🧠 Integrate topic modeling (LDA / BERTopic) And scale to other social media platforms

🔔 Add alert system for negative sentiment spikes

☁️ Deploy dashboard on Streamlit Cloud

🗓️ Automate report generation (PDF/Email)

🤝 Contributing

Pull requests are welcome! For major changes, open an issue first to discuss what you’d like to modify.

📄 License

This project is licensed under the MIT License — feel free to use and modify with attribution.

🌟 Author

👨‍💻 Mani Chandra
Data Scientist | certified RA
📬 LinkedIn 
 • GitHub
