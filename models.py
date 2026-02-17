from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ======================
# User Model
# ======================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20), nullable=False)  # admin / company / student

    approval_status = db.Column(db.String(20), default="Pending")
    is_blacklisted = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship("Company", backref="user", uselist=False)
    student = db.relationship("Student", backref="user", uselist=False)


# ======================
# Company Profile
# ======================
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    company_name = db.Column(db.String(150), nullable=False)
    hr_contact = db.Column(db.String(100))
    website = db.Column(db.String(200))
    description = db.Column(db.Text)

    drives = db.relationship("PlacementDrive", backref="company", lazy=True)


# ======================
# Student Profile
# ======================
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    department = db.Column(db.String(100))
    cgpa = db.Column(db.Float)
    contact = db.Column(db.String(20))
    resume_path = db.Column(db.String(200))

    applications = db.relationship("Application", backref="student", lazy=True)


# ======================
# Placement Drive
# ======================
class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)

    job_title = db.Column(db.String(150), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligibility = db.Column(db.String(200), nullable=False)
    application_deadline = db.Column(db.Date, nullable=False)

    status = db.Column(db.String(50), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship("Application", backref="drive", lazy=True)


# ======================
# Application Model
# ======================
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drive.id"), nullable=False)

    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="Applied")

    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="unique_application"),
    )
