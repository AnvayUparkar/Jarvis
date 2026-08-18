# Jarvis – AI-Powered Virtual Assistant for Educational and Productivity Automation

## Overview
Jarvis is an AI-powered virtual assistant developed to automate educational, productivity, and communication tasks through intelligent workflows and integrated digital services. The system is designed to assist users in generating academic resources such as lesson plans, worksheets, presentations, and feedback, while also supporting automation-based operations such as messaging, content generation, and task assistance.

Jarvis leverages **Gemini AI**, **Google APIs**, and **Google Slides integration** to deliver intelligent responses and automate repetitive processes. The assistant also supports multilingual content generation and communication workflows, making it suitable for educational and administrative use cases.


## Key Features

### 1. AI-Powered Academic Content Generation
Jarvis can generate a wide range of educational content, including:
- Lesson plans
- Worksheets
- Student feedback
- Academic summaries
- Structured presentation content

### 2. Presentation Automation
The assistant integrates with **Google Slides** to automate the creation and management of presentation-related content, reducing the time required for manual slide preparation.

### 3. Voice and Text-Based Interaction
Jarvis supports both **voice commands** and **text input**, enabling a flexible and user-friendly interaction experience.

### 4. Multilingual Content Support
The system can generate content in **local and regional languages**, improving accessibility and usability in diverse educational environments.

### 5. Intelligent Task Assistance
Using **Gemini AI**, Jarvis can understand user requests, provide contextual responses, and automate multiple assistant-based operations.

### 6. Communication and Alert Automation
Jarvis can support communication workflows such as:
- Smart notifications
- WhatsApp-based messaging
- Parent or user alerts
- Automated communication assistance

### 7. Productivity and Workflow Automation
The system is designed to reduce repetitive effort by automating common digital tasks, thereby improving efficiency and workflow management.


## Technology Stack

### Programming Languages
- Python
- JavaScript
- HTML
- CSS

### AI and APIs
- Gemini AI API
- Google Forms APIs
- Google Slides API
- Google Mail API
- Pollination Image Generation API
- Google Sheets API 

### Integrations and Functional Modules
- Voice Recognition / Speech Processing
- WhatsApp Automation
- Web-based Automation
- Presentation Automation
- Educational Content Generation


## System Workflow

The overall working of Jarvis can be summarized as follows:

1. The user provides a request through **voice input** or **text input**.
2. The request is processed and interpreted using **Gemini AI**.
3. Based on the type of request, Jarvis performs one or more actions such as:
   - Generating educational content
   - Creating presentation material
   - Providing intelligent responses
   - Triggering communication or alert workflows
4. The generated output is delivered through the interface or associated integrated services.


## Applications and Use Cases

Jarvis can be used in multiple scenarios, including:

- Academic content preparation for teachers
- Educational assistance for students
- Automation of repetitive academic tasks
- Multilingual educational support
- Presentation preparation
- Communication support for parents and institutions
- General productivity and assistant-based workflow automation


## Installation and Setup

### Step 1: Clone the Repository
```bash``
git clone https://github.com/AnvayUparkar/Jarvis.git
cd Jarvis

### Step 2: Create a Virtual Environment (Optional but Recommended)
python -m venv venv

### Step 3: Activate the Virtual Environment
On Windows
venv\Scripts\activate
On macOS / Linux
source venv/bin/activate

### Step 4: Install Dependencies
pip install -r requirements.txt

### Step 5: Run the Application
python main.py

Note: Update the run command if the project entry point differs in your local setup.

### Environment Configuration

Create a .env file in the root directory and configure the required environment variables as shown below:

GEMINI_API_KEY=your_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SLIDES_API_KEY=your_slides_api_key_here
WHATSAPP_CONFIG=your_whatsapp_config_here
