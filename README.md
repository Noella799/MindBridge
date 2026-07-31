MindBridge

MindBridge is a role-based mental-health education platform for children, parents, teachers, and counsellors.

Live Website
https://mindbridge-noella.onrender.com

GitHub Repository
https://github.com/Noella799/MindBridge

SRS Document
https://docs.google.com/document/d/1hLpb_hgLP8WLwHn_V9bzMG-_bAwIchE9R3qGurv5sHg/edit?usp=sharing

Main Features

User signup and login
Child learning videos and booklets
Progress tracking
Feelings check-ins and support requests
Parent and teacher monitoring
Counsellor advice
PostgreSQL database storage
Role-based dashboards

Technologies

Python and FastAPI
PostgreSQL and SQLAlchemy
HTML, CSS, and JavaScript
Render and GitHub

Run the Project Locally

1. Install the required software
Install:
Python 3
Git
PostgreSQL
Check the installations:
python3 --version
git --version
psql --version

2. Download the project
git clone https://github.com/Noella799/MindBridge.git
cd MindBridge

4. Create and activate a virtual environment
macOS or Linux
python3 -m venv venv
source venv/bin/activate
Windows
python -m venv venv
venv\Scripts\activate

5. Install the packages
pip install -r requirements.txt

6. Create the PostgreSQL database
Make sure PostgreSQL is running, then run:
createdb mindbridge

7. Create the environment file
Create a file named .env in the project folder.
Example without a PostgreSQL password:
DATABASE_URL=postgresql+psycopg2://YOUR_USERNAME@localhost:5432/mindbridge
SECRET_KEY=your-private-secret-key
Example with a PostgreSQL password:
DATABASE_URL=postgresql+psycopg2://YOUR_USERNAME:YOUR_PASSWORD@localhost:5432/mindbridge
SECRET_KEY=your-private-secret-key
Replace the username and password with your own PostgreSQL details.
Do not upload the .env file to GitHub.

8. Start the application
uvicorn main:app --reload

9. Open the application
Open:
http://127.0.0.1:8000

The database tables and demo accounts are created automatically when the application starts.
Demo Accounts
Password for all accounts:
1234
Role
Email
Child
child@mindbridge.test
Parent
parent@mindbridge.test
Teacher
teacher@mindbridge.test
Counsellor
counsellor@mindbridge.test

Test the System
Log in as the child.
Complete a learning resource.
Submit a feelings check-in.
Log in as a parent or teacher to view progress.
Log in as a counsellor to share advice.
Return to the child account to view the advice.
Render Deployment Settings
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Add these environment variables in Render:
DATABASE_URL = Render Internal Database URL
SECRET_KEY = a private secret value
Author
Uwera Noella
