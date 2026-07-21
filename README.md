# Recruitment Automation: RPA + Agentic AI

H9IAPA Continuous Assessment, MSc AI, National College of Ireland.
Name:Esvanth Mohankumar
Student Id:24311073

Github Link:

Automates candidate intake and shortlisting for a Junior Data Analyst role
at a fictional company, Brightline Analytics. Two distinct automation types:

1. **RPA layer** (deterministic): polls a mailbox, extracts CV attachments,
   logs to an Excel tracker, dispatches approved emails via SMTP.
2. **Agentic layer** (AI-driven): parses each CV, scores it against the JD
   using Groq's Llama 3.3 70B with JSON mode, ranks candidates, drafts
   personalised emails.

A Streamlit dashboard sits between the two for human-in-the-loop approval.

## Quick start

```bash
pip install -r requirements.txt
# edit .env and add your GROQ_API_KEY
python main.py
streamlit run dashboard/app.py
```

Get a free Groq key at https://console.groq.com/keys.

## Project layout

```
recruitment_automation/
  rpa/                  RPA layer (deterministic)
  agentic/              Agentic AI layer (Groq + Pydantic)
  dashboard/            Streamlit human-in-the-loop UI
  data/                 JD, sample CVs, mock inbox
  docs/                 Video script and deployment guide
  main.py               Pipeline orchestrator
  requirements.txt
```
