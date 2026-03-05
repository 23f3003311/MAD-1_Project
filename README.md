# Placement Portal

This is a Flask-based web application for a Placement Portal. It includes features for user authentication, role management (Admin, Company, and Student), and managing placement-related activities.

## Core Features
### 1. Authentication
- Login system for **Admin**, **Company**, and **Student**.
- Registration is allowed only for **Company** and **Student**.
- Admin must pre-exist in the database (no admin registration).

### 2. Admin Functionalities
- The admin dashboard displays the total number of students, total number of companies, applications, and the total number of placement drives.
- Admin can approve or reject company registrations.
- Admin can approve or reject placement drives.
- Admin can view all placement drives and applications.
- Admin can search students by name, ID, or contact information.
- Admin can search companies by name.
- Admin can blacklist or deactivate student and company accounts.

### 3. Company Functionalities
- Company registration and profile management.
- The company dashboard displays company details, created placement drives, and the number of applicants per drive.
- Companies can create (only after approval from admin), edit, remove, or close placement drives.
- Companies can view student applications.
- Companies can shortlist students and update selection status (Shortlisted / Selected / Rejected).

### 4. Student Functionalities
- Students have to self-register and login.
- The student's dashboard displays all approved placement drives, applied placement drives, and their status.
- Students can apply for placement drives.
- Students can view application status.
- Students can view past placement history.
- Students can edit their profile and upload a resume.

---

## How to Run the Project

Follow these steps to set up and run the application on your local machine.

### 1. Extract the Files
Once you open or extract the ZIP file, open your terminal and navigate to the project folder:
```bash
cd placement_portal
```

### 2. Create a Virtual Environment
Create a Python virtual environment to manage dependencies securely. Run the following command:
```bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment
Activate the environment so that packages are installed locally:

- **On macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```
- **On Windows:**
  ```bash
  venv\Scripts\activate
  ```

### 4. Install Requirements
With the virtual environment activated, install the required Python packages from the `requirements.txt` file. This includes Flask, SQLAlchemy, and others:
```bash
pip install -r requirements.txt
```

### 5. Run the Application
Start the Flask server by executing:
```bash
python app.py
```

After running this command, the server will start securely. Open your web browser and go to `http://127.0.0.1:5000` to view the Placement Portal.

> **Note:** On the first run, the database will be created automatically. A default admin user is initialized into the database with the email `admin@portal.com` and password `admin123`.
