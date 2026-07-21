"""Generate 6 synthetic CV PDFs for the demo dataset."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT
import os

OUT_DIR = "data/sample_cvs"
os.makedirs(OUT_DIR, exist_ok=True)
styles = getSampleStyleSheet()
name_style = ParagraphStyle("name", parent=styles["Heading1"], fontSize=18, spaceAfter=4, alignment=TA_LEFT)
section_style = ParagraphStyle("section", parent=styles["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=4, alignment=TA_LEFT)
body_style = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, spaceAfter=4, alignment=TA_LEFT)


def make_cv(filename, name, email, phone, summary, education, skills, experience, projects):
    path = os.path.join(OUT_DIR, filename)
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    story = [Paragraph(name, name_style), Paragraph(f"{email} | {phone}", body_style), Spacer(1, 0.3*cm)]
    story.append(Paragraph("Summary", section_style))
    story.append(Paragraph(summary, body_style))
    story.append(Paragraph("Education", section_style))
    for line in education: story.append(Paragraph(line, body_style))
    story.append(Paragraph("Skills", section_style))
    story.append(Paragraph(skills, body_style))
    story.append(Paragraph("Experience", section_style))
    for role in experience: story.append(Paragraph(role, body_style))
    story.append(Paragraph("Projects", section_style))
    for proj in projects: story.append(Paragraph(proj, body_style))
    doc.build(story)
    print(f"Wrote {path}")


make_cv("cv_aoife_kelly.pdf", "Aoife Kelly", "aoife.kelly@example.com", "+353 87 555 0101",
    "Recent BSc Data Science graduate with hands-on experience in Python, SQL, and Power BI.",
    ["BSc Data Science, University College Dublin, 2021 to 2024, First Class Honours"],
    "Python (pandas, NumPy, matplotlib), SQL (PostgreSQL), Power BI, Tableau, Git, statistical methods.",
    ["Data Analyst Intern, FastFleet Logistics, Jan to Jun 2024. Built six operational dashboards in Power BI.",
     "Tutor, UCD Computer Science Society, 2023 to 2024."],
    ["Customer churn predictor: logistic regression and random forest, ROC-AUC 0.82.",
     "Dublin Bikes usage dashboard in Tableau."])

make_cv("cv_rohan_mehta.pdf", "Rohan Mehta", "rohan.mehta@example.com", "+353 89 555 0202",
    "Data analyst with two years of professional experience in retail analytics.",
    ["BSc Statistics, Trinity College Dublin, 2019 to 2022, 2.1"],
    "Python (pandas, NumPy, scikit-learn), SQL (advanced: CTEs, window functions), Tableau, Looker, Git, GCP BigQuery.",
    ["Data Analyst, Greenline Retail, 2022 to present. Owned weekly promotions reporting.",
     "Analytics Intern, Dublin City Council Smart Cities, summer 2021."],
    ["Promotions uplift model using difference-in-differences.",
     "BigQuery cost optimiser: cut monthly bill by 28 percent."])

make_cv("cv_emma_obrien.pdf", "Emma O'Brien", "emma.obrien@example.com", "+353 86 555 0303",
    "Business graduate with self-taught Python and SQL. Looking to move into a data analyst role.",
    ["BBS Business Studies, Dublin Business School, 2019 to 2023, 2.2"],
    "Excel (advanced), Python (basic), SQL (basic), Power BI (some exposure).",
    ["Finance Operations Analyst, Provincia Insurance, 2023 to present.",
     "Customer Service Representative, AIB, 2018 to 2019."],
    ["DataCamp Python Data Analyst track: completed 20 courses, January 2025.",
     "Personal project: budget tracker in Google Sheets."])

make_cv("cv_liam_dunne.pdf", "Liam Dunne", "liam.dunne@example.com", "+353 85 555 0404",
    "Recent graduate seeking opportunities in technology.",
    ["BA English Literature, Maynooth University, 2020 to 2024"],
    "Microsoft Word, Microsoft Excel (basic), good communication skills, team player.",
    ["Bartender, The Gravediggers Pub, 2022 to 2024.",
     "Retail Assistant, Dunnes Stores, 2020 to 2022."],
    ["University essay collection: collated a class anthology."])

make_cv("cv_priya_raman.pdf", "Priya Raman", "priya.raman@example.com", "+353 83 555 0505",
    "Senior data engineer with eight years of experience. Looking for a change and open to junior roles.",
    ["MEng Computer Engineering, IIT Madras, 2014 to 2016", "BE Electronics, Anna University, 2010 to 2014"],
    "Python, Java, Scala, Spark, Kafka, Airflow, SQL (expert), PostgreSQL, Snowflake, AWS, Docker.",
    ["Senior Data Engineer, Stripe Ireland, 2020 to 2024.",
     "Data Engineer, AWS Dublin, 2017 to 2020.",
     "Software Engineer, Infosys Bangalore, 2014 to 2017."],
    ["Real-time fraud signal pipeline: Spark Streaming and Kafka.",
     "Open-source contributor to Apache Airflow."])

make_cv("cv_sean_murphy.pdf", "Sean Murphy", "sean.murphy@example.com", "+353 87 555 0606",
    "Computer Science student in final year. Interested in working with data.",
    ["BSc Computer Science, Munster Technological University, 2022 to 2026 (in progress, expected 2.1)"],
    "Java (university courses), Python (intermediate), HTML and CSS, some SQL, basic Git.",
    ["Part-time IT support, MTU library, 2024 to present."],
    ["Final year project (in progress): Flask web app for tracking gym workouts.",
     "Hackathon entry: chatbot for local bus schedules."])

print("All 6 CVs generated.")
