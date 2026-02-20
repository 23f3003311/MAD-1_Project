from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Company, Student
from functools import wraps
from flask_login import current_user
from flask import abort
from models import User, Company, Student, PlacementDrive, Application
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import jsonify
from sqlalchemy import func


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def register_routes(app):
    app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads", "resumes")
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
    def allowed_file(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route("/")
    def home():
        return redirect(url_for("login"))


    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form["email"]
            password = request.form["password"]

            user = User.query.filter_by(email=email).first()

            if user and check_password_hash(user.password_hash, password):
                if user.is_blacklisted:
                    
                    return redirect(url_for("login"))

                login_user(user)

                if user.role == "admin":
                    return redirect(url_for("admin_dashboard"))
                elif user.role == "company":
                    if user.approval_status != "Approved":
                       
                        return redirect(url_for("login"))
                    else:
                        return redirect(url_for("company_dashboard"))
                else:
                    return redirect(url_for("student_dashboard"))

            

        return render_template("login.html")


    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))


    @app.route("/register/student", methods=["GET", "POST"])
    def register_student():
        if request.method == "POST":
            if User.query.filter_by(email=request.form["email"]).first():
                return "Email already registered.", 400
            user = User(
                name=request.form["name"],
                email=request.form["email"],
                password_hash=generate_password_hash(request.form["password"]),
                role="student",
                approval_status="Approved"
            )
            
            db.session.add(user)
            db.session.commit()

            student = Student(
                user_id=user.id,
                department=request.form["department"],
                cgpa=float(request.form["cgpa"]),
                contact=request.form["contact"]
            )
            db.session.add(student)
            db.session.commit()

           
            return redirect(url_for("login"))

        return render_template("register_student.html")


    @app.route("/register/company", methods=["GET", "POST"])
    def register_company():
        if request.method == "POST":
            if User.query.filter_by(email=request.form["email"]).first():
                return "Email already registered.", 400
            user = User(
                name=request.form["name"],
                email=request.form["email"],
                password_hash=generate_password_hash(request.form["password"]),
                role="company",
                approval_status="Pending"
            )
            db.session.add(user)
            db.session.commit()

            company = Company(
                user_id=user.id,
                company_name=request.form["company_name"],
                hr_contact=request.form["hr_contact"],
                website=request.form["website"],
                description=request.form["description"]
            )
            db.session.add(company)
            db.session.commit()

           
            return redirect(url_for("login"))

        return render_template("register_company.html")


    @app.route("/admin/dashboard")
    @login_required
    @admin_required
    def admin_dashboard():
        total_students = User.query.filter_by(role="student").count()
        total_companies = User.query.filter_by(role="company").count()
        total_drives = PlacementDrive.query.count()
        total_applications = Application.query.count()
        drives = PlacementDrive.query.filter_by(status="Approved").order_by(PlacementDrive.created_at.desc()).all()

        return render_template(
            "admin_dashboard.html",
            total_students=total_students,
            total_companies=total_companies,
            total_drives=total_drives,
            total_applications=total_applications,
            drives=drives
        )
    @app.route("/admin/students")
    @login_required
    @admin_required
    def view_students():
        query = request.args.get("search")

        if query:
            students = Student.query.join(User).filter(
                (User.name.ilike(f"%{query}%")) |
                (Student.contact.ilike(f"%{query}%")) |
                (User.id == int(query) if query.isdigit() else False)
            ).all()
        else:
            students = Student.query.all()

        return render_template("admin_students.html", students=students)


    @app.route("/admin/blacklist/student/<int:id>")
    @login_required
    @admin_required
    def blacklist_student(id):
        student = Student.query.get_or_404(id)
        student.user.is_blacklisted = True
        db.session.commit()
        return redirect("/admin/students")
    @app.route("/admin/companies")
    @login_required
    @admin_required
    def view_companies():
        query = request.args.get("search")

        if query:
            companies = Company.query.filter(
                Company.company_name.ilike(f"%{query}%")
            ).all()
        else:
            companies = Company.query.all()

        return render_template("admin/companies.html", companies=companies)

    @app.route("/admin/approve/company/<int:id>")
    @login_required
    @admin_required
    def approve_company(id):
        company = Company.query.get_or_404(id)
        company.user.approval_status = "Approved"
        db.session.commit()
        return redirect("/admin/companies")

    @app.route("/admin/reject/company/<int:id>")
    @login_required
    @admin_required
    def reject_company(id):
        company = Company.query.get_or_404(id)
        company.user.approval_status = "Rejected"
        db.session.commit()
        return redirect("/admin/companies")

    @app.route("/admin/blacklist/company/<int:id>")
    @login_required
    @admin_required
    def blacklist_company(id):
        company = Company.query.get_or_404(id)
        company.user.is_blacklisted = True
        db.session.commit()
        return redirect("/admin/companies")

    @app.route("/company/dashboard")
    @login_required
    def company_dashboard():
        if current_user.role != "company":
            abort(403)

        if current_user.approval_status != "Approved":
           
            return redirect(url_for("login"))

        company = Company.query.filter_by(user_id=current_user.id).first()

        drives = PlacementDrive.query.filter_by(company_id=company.id).order_by(PlacementDrive.created_at.desc()).all()

        applicant_counts = {}
        for d in drives:
            applicant_counts[d.id] = Application.query.filter_by(drive_id=d.id).count()

        return render_template(
            "company/dashboard.html",
            company=company,
            drives=drives,
            applicant_counts=applicant_counts
        )


    @app.route("/company/drive/<int:drive_id>/applicants")
    @login_required
    def view_applicants(drive_id):
        if current_user.role != "company":
            abort(403)

        drive = PlacementDrive.query.get_or_404(drive_id)

        company = Company.query.filter_by(user_id=current_user.id).first()
        if drive.company_id != company.id:
            abort(403)

        applications = drive.applications

        return render_template(
            "company/view_applicants.html",
            drive=drive,
            applications=applications
        )

    @app.route("/company/application/<int:app_id>/shortlist")
    @login_required
    def shortlist_application(app_id):
        if current_user.role != "company":
            abort(403)

        app_obj = Application.query.get_or_404(app_id)
        app_obj.status = "Shortlisted"
        db.session.commit()
        return redirect(request.referrer)

    @app.route("/company/application/<int:app_id>/select")
    @login_required
    def select_application(app_id):
        if current_user.role != "company":
            abort(403)

        app_obj = Application.query.get_or_404(app_id)
        app_obj.status = "Selected"
        db.session.commit()
        return redirect(request.referrer)

    @app.route("/company/application/<int:app_id>/reject")
    @login_required
    def reject_application_company(app_id):
        if current_user.role != "company":
            abort(403)

        app_obj = Application.query.get_or_404(app_id)
        app_obj.status = "Rejected"
        db.session.commit()
        return redirect(request.referrer)


    @app.route("/company/create-drive", methods=["GET", "POST"])
    @login_required
    def create_drive():
        if current_user.role != "company":
            return "Unauthorized", 403

        if current_user.approval_status != "Approved":
            return "Your account is not approved yet."

        company = Company.query.filter_by(user_id=current_user.id).first()
        if request.method == "POST":
            deadline = datetime.strptime(request.form["deadline"], "%Y-%m-%d").date()

            new_drive = PlacementDrive(
                company_id=company.id,
                job_title=request.form["job_title"],
                job_description=request.form["job_description"],
                eligibility=request.form["eligibility"],
                application_deadline=deadline,
                status="Pending"
            )
            db.session.add(new_drive)
            db.session.commit()
            return redirect(url_for("company_dashboard"))

        return render_template("company/create_drive.html")



    @app.route("/student/apply/<int:drive_id>", methods=["POST"])
    @login_required
    def apply_drive(drive_id):
        if current_user.role != "student":
            abort(403)

        student = Student.query.filter_by(user_id=current_user.id).first_or_404()
        drive = PlacementDrive.query.get_or_404(drive_id)
        today = datetime.utcnow().date()

        if drive.status != "Approved" or drive.application_deadline < today:
            
            return redirect(url_for("student_dashboard"))

        existing = Application.query.filter_by(student_id=student.id, drive_id=drive.id).first()
        if existing:
           
            return redirect(url_for("student_dashboard"))

        db.session.add(Application(student_id=student.id, drive_id=drive.id, status="Applied"))
        db.session.commit()
       
        return redirect(url_for("student_dashboard"))

    @app.route("/admin/drives")
    @login_required
    def admin_view_drives():
        if current_user.role != "admin":
            return "Unauthorized", 403

        drives = PlacementDrive.query.all()
        return render_template("admin/view_drives.html", drives=drives)

    @app.route("/admin/approve/drive/<int:drive_id>")
    @login_required
    def approve_drive(drive_id):
        if current_user.role != "admin":
            return "Unauthorized", 403

        drive = PlacementDrive.query.get_or_404(drive_id)
        drive.status = "Approved"
        db.session.commit()
        return redirect(url_for("admin_view_drives"))

    @app.route("/admin/reject/drive/<int:drive_id>")
    @login_required
    def reject_drive(drive_id):
        if current_user.role != "admin":
            return "Unauthorized", 403

        drive = PlacementDrive.query.get_or_404(drive_id)
        drive.status = "Rejected"
        db.session.commit()
        return redirect(url_for("admin_view_drives"))

    @app.route("/admin/applications")
    @login_required
    def admin_view_applications():
        if current_user.role != "admin":
            return "Unauthorized", 403

        applications = Application.query.all()
        return render_template("admin/view_applications.html", applications=applications)

    @app.route("/student/dashboard")
    @login_required
    def student_dashboard():
        if current_user.role != "student":
            abort(403)

        student = Student.query.filter_by(user_id=current_user.id).first_or_404()
        today = datetime.utcnow().date()

        # show only approved drives that are not expired
        approved_drives = PlacementDrive.query.filter(
            PlacementDrive.status == "Approved",
            PlacementDrive.application_deadline >= today
        ).order_by(PlacementDrive.created_at.desc()).all()

        applications = Application.query.filter_by(student_id=student.id).order_by(
            Application.application_date.desc()
        ).all()

        applied_drive_ids = {a.drive_id for a in applications}
        app_by_drive = {a.drive_id: a for a in applications}

        return render_template(
            "student/dashboard.html",
            student=student,
            approved_drives=approved_drives,
            applications=applications,
            applied_drive_ids=applied_drive_ids,
            app_by_drive=app_by_drive
        )

        
    @app.route("/company/drive/<int:drive_id>/edit", methods=["GET", "POST"])
    @login_required
    def company_edit_drive(drive_id):
        if current_user.role != "company":
            abort(403)

        company = Company.query.filter_by(user_id=current_user.id).first()
        drive = PlacementDrive.query.get_or_404(drive_id)

        if drive.company_id != company.id:
            abort(403)

        if request.method == "POST":
            drive.job_title = request.form["job_title"]
            drive.job_description = request.form["job_description"]
            drive.eligibility = request.form["eligibility"]
            drive.application_deadline = datetime.strptime(request.form["deadline"], "%Y-%m-%d").date()

            drive.status = "Pending"

            db.session.commit()
           
            return redirect(url_for("company_dashboard"))

        return render_template("company/edit_drive.html", drive=drive)

    @app.route("/company/drive/<int:drive_id>/close")
    @login_required
    def company_close_drive(drive_id):
        if current_user.role != "company":
            abort(403)

        company = Company.query.filter_by(user_id=current_user.id).first()
        drive = PlacementDrive.query.get_or_404(drive_id)

        if drive.company_id != company.id:
            abort(403)

        drive.status = "Closed"
        db.session.commit()
       
        return redirect(url_for("company_dashboard"))

    @app.route("/company/drive/<int:drive_id>/delete")
    @login_required
    def company_delete_drive(drive_id):
        if current_user.role != "company":
            abort(403)

        company = Company.query.filter_by(user_id=current_user.id).first()
        drive = PlacementDrive.query.get_or_404(drive_id)

        if drive.company_id != company.id:
            abort(403)

        apps_count = Application.query.filter_by(drive_id=drive.id).count()
        if apps_count > 0:
           
            return redirect(url_for("company_dashboard"))

        db.session.delete(drive)
        db.session.commit()
        
        return redirect(url_for("company_dashboard"))

    @app.route("/company/drive/<int:drive_id>/applications")
    @login_required
    def company_view_drive_applications(drive_id):
        if current_user.role != "company":
            abort(403)

        company = Company.query.filter_by(user_id=current_user.id).first()
        drive = PlacementDrive.query.get_or_404(drive_id)

        if drive.company_id != company.id:
            abort(403)

        applications = Application.query.filter_by(drive_id=drive.id).all()
        return render_template("company/drive_applications.html", drive=drive, applications=applications)

    @app.route("/company/application/<int:app_id>/<status>")
    @login_required
    def company_update_application_status(app_id, status):
        if current_user.role != "company":
            abort(403)

        if status not in ["Shortlisted", "Selected", "Rejected"]:
            abort(400)

        company = Company.query.filter_by(user_id=current_user.id).first()
        app_obj = Application.query.get_or_404(app_id)

        if app_obj.drive.company_id != company.id:
            abort(403)

        app_obj.status = status
        db.session.commit()
        return redirect(url_for("company_view_drive_applications", drive_id=app_obj.drive_id))
    @app.route("/student/applications")
    @login_required
    def student_applications():
        if current_user.role != "student":
            abort(403)

        student = Student.query.filter_by(user_id=current_user.id).first_or_404()

        applications = Application.query.filter_by(student_id=student.id).order_by(
            Application.application_date.desc()
        ).all()

        return render_template("student/applications.html", applications=applications)

    @app.route("/student/history")
    @login_required
    def student_history():
        if current_user.role != "student":
            abort(403)

        student = Student.query.filter_by(user_id=current_user.id).first_or_404()

        selected_apps = Application.query.filter_by(
            student_id=student.id,
            status="Selected"
        ).order_by(Application.application_date.desc()).all()

        return render_template("student/history.html", applications=selected_apps)

    @app.route("/student/profile", methods=["GET", "POST"])
    @login_required
    def student_profile():
        if current_user.role != "student":
            abort(403)

        student = Student.query.filter_by(user_id=current_user.id).first_or_404()

        if request.method == "POST":
            # Update name (User)
            name = request.form.get("name", "").strip()
            if name:
                current_user.name = name

            # Update Student fields
            student.department = request.form.get("department", student.department)
            student.contact = request.form.get("contact", student.contact)

            cgpa_raw = request.form.get("cgpa")
            if cgpa_raw:
                try:
                    student.cgpa = float(cgpa_raw)
                except ValueError:
                   
                    return redirect(url_for("student_profile"))

            # Resume file upload
            file = request.files.get("resume")
            if file and file.filename:
                if not allowed_file(file.filename):
                    
                    return redirect(url_for("student_profile"))

                filename = secure_filename(f"student_{student.id}_{file.filename}")
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(save_path)

                # store relative path under static/
                student.resume_path = f"uploads/resumes/{filename}"

            db.session.commit()
           
            return redirect(url_for("student_dashboard"))

        return render_template("student/profile.html", student=student)

    @app.route("/api/drives", methods=["GET"])
    def api_drives():
        today = datetime.utcnow().date()

        drives = PlacementDrive.query.filter(
            PlacementDrive.status == "Approved",
            PlacementDrive.application_deadline >= today
        ).order_by(PlacementDrive.created_at.desc()).all()

        return jsonify([
            {
                "id": d.id,
                "company": d.company.company_name,
                "job_title": d.job_title,
                "eligibility": d.eligibility,
                "deadline": d.application_deadline.isoformat(),
                "status": d.status,
                "created_at": d.created_at.isoformat()
            }
            for d in drives
        ])
    @app.route("/api/admin/applications", methods=["GET"])
    @login_required
    @admin_required
    def api_admin_applications():
        applications = Application.query.order_by(
            Application.application_date.desc()
        ).all()

        return jsonify([
            {
                "application_id": a.id,
                "student_name": a.student.user.name,
                "student_id": a.student_id,
                "company": a.drive.company.company_name,
                "drive_id": a.drive_id,
                "job_title": a.drive.job_title,
                "status": a.status,
                "applied_at": a.application_date.isoformat()
            }
            for a in applications
        ])

    @app.route("/api/admin/drive/<int:drive_id>/stats", methods=["GET"])
    @login_required
    @admin_required
    def api_drive_stats(drive_id):
        drive = PlacementDrive.query.get_or_404(drive_id)

        rows = (
            db.session.query(Application.status, func.count(Application.id))
            .filter(Application.drive_id == drive_id)
            .group_by(Application.status)
            .all()
        )

        stats = {"Applied": 0, "Shortlisted": 0, "Selected": 0, "Rejected": 0}
        for status, count in rows:
            if status in stats:
                stats[status] = count

        return jsonify({
            "drive_id": drive.id,
            "job_title": drive.job_title,
            "company": drive.company.company_name,
            "stats": stats
        })


