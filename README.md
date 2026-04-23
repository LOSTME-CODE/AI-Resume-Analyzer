
## 📌 Table of Contents

- <a href="#problem-statement">Problem Statement</a>
- <a href="#Demo">Demo</a>
- <a href="#tools--technologies">Tools & Technologies</a>
- <a href="#Methodology">Methodology</a>
- <a href="#Deployment">Deployment</a>
- <a href="# Key-Insights">Key Insights</a>

- <a href="#future-work">Future Work</a>


# **AI Resume Analyzer**

AI Resume Analyzer is a smart resume evaluation tool built using Streamlit + Google Gemini API. It helps users understand how their resume performs in real-world hiring scenarios by providing structured insights such as strengths, weaknesses, ATS compatibility, and job match score.

The system extracts text from PDF resumes using OCR and processes it through AI models to generate actionable feedback.

## *Problem statement* 
Recruiters often use Applicant Tracking Systems (ATS) to filter resumes, but candidates lack visibility into:

Why their resume gets rejected
Missing keywords or skills
ATS compatibility issues
Alignment with job descriptions

This leads to missed opportunities despite having the right skills.

<h3><a class="anchor" id="Demo"></a>Demo</h3>

https://github.com/user-attachments/assets/34ee5ec5-cebf-45ac-a383-b6fce4212f55

![App Screenshot](https://github.com/LOSTME-CODE/AI-Resume-Analyzer/blob/2685108c8c428f336898bb76cbdc4efd51fe9c16/1.png)

![App Screenshot](https://github.com/LOSTME-CODE/AI-Resume-Analyzer/blob/2685108c8c428f336898bb76cbdc4efd51fe9c16/2.png)

![App Screenshot](https://github.com/LOSTME-CODE/AI-Resume-Analyzer/blob/2685108c8c428f336898bb76cbdc4efd51fe9c16/3.png)

![App Screenshot](https://github.com/LOSTME-CODE/AI-Resume-Analyzer/blob/2685108c8c428f336898bb76cbdc4efd51fe9c16/4.png)

![App Screenshot](https://github.com/LOSTME-CODE/AI-Resume-Analyzer/blob/2685108c8c428f336898bb76cbdc4efd51fe9c16/5.png)

![App Screenshot](https://github.com/LOSTME-CODE/AI-Resume-Analyzer/blob/2685108c8c428f336898bb76cbdc4efd51fe9c16/6.png)




<h3><a class="anchor" id="tools--technologies"></a>Tools & Technologies</h3>
- Frontend/UI: Streamlit
- Backend: Python
- AI Model: Google Gemini API (Generative AI)
- OCR: Tesseract OCR
- PDF Processing: pdf2image, PIL



 <h3><a class="anchor" id="Methodology"></a>Methodology</h3>
- Resume Upload (PDF)
- PDF → Images Conversion
- OCR Extraction (Tesseract)
- AI Processing using Gemini
- Structured JSON Output Parsing
- Visualization using Streamlit UI

## Key Insights Provided

<h3><a class="anchor" id=" Key-Insights"></a> Key Insights</h3>

- Candidate summary & HR impression
- Strengths & weaknesses
- Key skills detected
- Missing keywords
- ATS score (0–100)
- Resume formatting issues
- Job description match score
- Skill gap analysis

## *Output Dashboard*
- Circular score indicators (ATS & JD Match)
- Skill tags & keyword highlights
- Structured cards for insights
- Improvement suggestions
 
<h3><a class="anchor" id="Deployment"></a>Deployment</h3>

  1. Clone the Repository

  2. Install Dependencies
```
 pip install -r requirements.txt
```
3. Add Your API Key

Create a .env file in the root directory:


```
GOOGLE_API_KEY=your_api_key_here
  
```
- Users must provide their own Google Gemini API key


4. Install Required Tools

- Install Tesseract OCR

- Install Poppler (for PDF processing)

- Update paths in code:

```
POPPLER_PATH = "your_poppler_path" 
TESSERACT_PATH = "your_tesseract_path"
  
```


Run the App

```
 streamlit run app.py
  
```
<h3><a class="anchor" id="future-work"></a>Future Work</h3>
- Multi-format resume support (DOCX, TXT)
- Resume rewriting using AI
- LinkedIn profile analysis
- Resume ranking system for recruiters
- Deployment on cloud (AWS/GCP)- - Batch resume analysis for HR teams
- Integration with job portals


## *Note*
- Users must add their own API key
- OCR accuracy depends on resume quality
- AI outputs may vary slightly
