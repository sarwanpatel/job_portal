from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

# =========================
# SECRET KEY
# =========================

app.secret_key = "job_portal_secret_key"


# =========================
# DATABASE CONNECTION
# =========================

def get_db_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="job_portal"
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM jobs
        ORDER BY created_at DESC
    """)

    jobs = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "index.html",
        jobs=jobs
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        hashed_password = generate_password_hash(password)

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            query = """
                INSERT INTO users
                (name, email, password, role)
                VALUES (%s, %s, %s, %s)
            """

            values = (
                name,
                email,
                hashed_password,
                role
            )

            cursor.execute(query, values)

            connection.commit()

            flash(
                "Registration successful! Please login."
            )

            return redirect(
                url_for("login")
            )

        except mysql.connector.IntegrityError:

            connection.rollback()

            flash(
                "Email already registered."
            )

        finally:

            cursor.close()
            connection.close()

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]

            flash("Login successful!")

            if user["role"] == "recruiter":

                return redirect(
                    url_for("recruiter_dashboard")
                )

            elif user["role"] == "admin":

                return redirect(
                    url_for("admin_dashboard")
                )

            else:

                return redirect(
                    url_for("candidate_dashboard")
                )

        else:

            flash(
                "Invalid email or password."
            )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out."
    )

    return redirect(
        url_for("home")
    )


# =========================================================
# CANDIDATE DASHBOARD
# =========================================================

@app.route("/candidate/dashboard")
def candidate_dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "candidate":

        return redirect(
            url_for("home")
        )

    return render_template(
        "candidate_dashboard.html"
    )


# =========================================================
# RECRUITER DASHBOARD
# =========================================================

@app.route("/recruiter/dashboard")
def recruiter_dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "recruiter":

        return redirect(
            url_for("home")
        )

    return render_template(
        "recruiter_dashboard.html"
    )


# =========================================================
# RECRUITER - VIEW MY JOBS
# =========================================================

@app.route("/recruiter/jobs")
def recruiter_jobs():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "recruiter":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM jobs
        WHERE recruiter_id = %s
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    )

    jobs = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "recruiter_jobs.html",
        jobs=jobs
    )


# =========================================================
# RECRUITER - ADD JOB
# =========================================================

@app.route(
    "/recruiter/jobs/add",
    methods=["GET", "POST"]
)
def add_job():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "recruiter":

        return redirect(
            url_for("home")
        )

    if request.method == "POST":

        title = request.form["title"]
        company = request.form["company"]
        location = request.form["location"]
        category = request.form["category"]
        salary = request.form["salary"]
        description = request.form["description"]
        requirements = request.form["requirements"]

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO jobs
            (
                recruiter_id,
                title,
                company,
                location,
                category,
                salary,
                description,
                requirements
            )
            VALUES
            (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """

        values = (
            session["user_id"],
            title,
            company,
            location,
            category,
            salary,
            description,
            requirements
        )

        cursor.execute(
            query,
            values
        )

        connection.commit()

        cursor.close()
        connection.close()

        flash(
            "Job posted successfully!"
        )

        return redirect(
            url_for("recruiter_jobs")
        )

    return render_template(
        "add_job.html"
    )


# =========================================================
# RECRUITER - EDIT JOB
# =========================================================

@app.route(
    "/recruiter/jobs/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_job(id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "recruiter":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM jobs
        WHERE id = %s
        AND recruiter_id = %s
        """,
        (
            id,
            session["user_id"]
        )
    )

    job = cursor.fetchone()

    if job is None:

        cursor.close()
        connection.close()

        flash(
            "Job not found."
        )

        return redirect(
            url_for("recruiter_jobs")
        )

    if request.method == "POST":

        title = request.form["title"]
        company = request.form["company"]
        location = request.form["location"]
        category = request.form["category"]
        salary = request.form["salary"]
        description = request.form["description"]
        requirements = request.form["requirements"]

        query = """
            UPDATE jobs

            SET
                title = %s,
                company = %s,
                location = %s,
                category = %s,
                salary = %s,
                description = %s,
                requirements = %s

            WHERE id = %s
            AND recruiter_id = %s
        """

        values = (
            title,
            company,
            location,
            category,
            salary,
            description,
            requirements,
            id,
            session["user_id"]
        )

        cursor.execute(
            query,
            values
        )

        connection.commit()

        cursor.close()
        connection.close()

        flash(
            "Job updated successfully!"
        )

        return redirect(
            url_for("recruiter_jobs")
        )

    cursor.close()
    connection.close()

    return render_template(
        "edit_job.html",
        job=job
    )


# =========================================================
# RECRUITER - DELETE JOB
# =========================================================

@app.route(
    "/recruiter/jobs/delete/<int:id>"
)
def delete_job(id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "recruiter":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM jobs
        WHERE id = %s
        AND recruiter_id = %s
        """,
        (
            id,
            session["user_id"]
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    flash(
        "Job deleted successfully!"
    )

    return redirect(
        url_for("recruiter_jobs")
    )


# =========================================================
# CANDIDATE - JOB SEARCH
# =========================================================

@app.route("/jobs")
def jobs():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "candidate":

        return redirect(
            url_for("home")
        )

    search = request.args.get(
        "search",
        ""
    )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    search_value = "%" + search + "%"

    query = """
        SELECT *
        FROM jobs

        WHERE
            title LIKE %s
            OR company LIKE %s
            OR location LIKE %s
            OR category LIKE %s

        ORDER BY created_at DESC
    """

    cursor.execute(
        query,
        (
            search_value,
            search_value,
            search_value,
            search_value
        )
    )

    jobs = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "jobs.html",
        jobs=jobs,
        search=search
    )


# =========================================================
# JOB DETAILS
# =========================================================

@app.route("/jobs/<int:id>")
def job_details(id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "candidate":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM jobs
        WHERE id = %s
        """,
        (id,)
    )

    job = cursor.fetchone()

    cursor.close()
    connection.close()

    if job is None:

        flash(
            "Job not found."
        )

        return redirect(
            url_for("jobs")
        )

    return render_template(
        "job_details.html",
        job=job
    )


# =========================================================
# APPLY FOR JOB
# =========================================================

@app.route(
    "/jobs/<int:id>/apply",
    methods=["GET", "POST"]
)
def apply_job(id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "candidate":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Check job
    cursor.execute(
        """
        SELECT *
        FROM jobs
        WHERE id = %s
        """,
        (id,)
    )

    job = cursor.fetchone()

    if job is None:

        cursor.close()
        connection.close()

        flash(
            "Job not found."
        )

        return redirect(
            url_for("jobs")
        )

    if request.method == "POST":

        cover_letter = request.form[
            "cover_letter"
        ]

        try:

            cursor.execute(
                """
                INSERT INTO applications
                (
                    job_id,
                    candidate_id,
                    cover_letter
                )

                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    id,
                    session["user_id"],
                    cover_letter
                )
            )

            connection.commit()

            flash(
                "Application submitted successfully!"
            )

            cursor.close()
            connection.close()

            return redirect(
                url_for(
                    "candidate_applications"
                )
            )

        except mysql.connector.IntegrityError:

            connection.rollback()

            flash(
                "You have already applied for this job."
            )

    cursor.close()
    connection.close()

    return render_template(
        "apply.html",
        job=job
    )


# =========================================================
# MY APPLICATIONS
# =========================================================

@app.route(
    "/candidate/applications"
)
def candidate_applications():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "candidate":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT

            applications.id,
            applications.cover_letter,
            applications.status,
            applications.applied_at,

            jobs.title,
            jobs.company,
            jobs.location

        FROM applications

        INNER JOIN jobs
        ON applications.job_id = jobs.id

        WHERE
            applications.candidate_id = %s

        ORDER BY
            applications.applied_at DESC
    """

    cursor.execute(
        query,
        (session["user_id"],)
    )

    applications = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "applications.html",
        applications=applications
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin/dashboard")
def admin_dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "admin":

        return redirect(
            url_for("home")
        )

    return render_template(
        "admin_dashboard.html"
    )




# =========================================================
# RECRUITER - VIEW APPLICANTS
# =========================================================

@app.route("/recruiter/jobs/<int:job_id>/applicants")
def view_applicants(job_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "recruiter":
        return redirect(url_for("home"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Check that job belongs to recruiter
    cursor.execute("""
        SELECT *
        FROM jobs
        WHERE id = %s
        AND recruiter_id = %s
    """, (job_id, session["user_id"]))

    job = cursor.fetchone()

    if job is None:

        cursor.close()
        connection.close()

        flash("Job not found.")

        return redirect(
            url_for("recruiter_jobs")
        )

    # Get applications
    cursor.execute("""
        SELECT
            applications.id,
            applications.cover_letter,
            applications.status,
            applications.applied_at,

            users.name,
            users.email

        FROM applications

        INNER JOIN users
        ON applications.candidate_id = users.id

        WHERE applications.job_id = %s

        ORDER BY applications.applied_at DESC
    """, (job_id,))

    applicants = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "applicants.html",
        job=job,
        applicants=applicants
    )


# =========================================================
# RECRUITER - UPDATE APPLICATION STATUS
# =========================================================

@app.route(
    "/recruiter/application/<int:application_id>/status",
    methods=["POST"]
)
def update_application_status(application_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "recruiter":
        return redirect(url_for("home"))

    status = request.form["status"]

    allowed_statuses = [
        "Applied",
        "Shortlisted",
        "Rejected",
        "Selected"
    ]

    if status not in allowed_statuses:

        flash("Invalid application status.")

        return redirect(
            url_for("recruiter_jobs")
        )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Make sure application belongs to
    # a job owned by this recruiter
    cursor.execute("""
        SELECT applications.id
        FROM applications

        INNER JOIN jobs
        ON applications.job_id = jobs.id

        WHERE applications.id = %s
        AND jobs.recruiter_id = %s
    """, (
        application_id,
        session["user_id"]
    ))

    application = cursor.fetchone()

    if application is None:

        cursor.close()
        connection.close()

        flash("Application not found.")

        return redirect(
            url_for("recruiter_jobs")
        )

    cursor.execute("""
        UPDATE applications

        SET status = %s

        WHERE id = %s
    """, (
        status,
        application_id
    ))

    connection.commit()

    cursor.close()
    connection.close()

    flash(
        "Application status updated!"
    )

    return redirect(
        request.referrer
        or url_for("recruiter_jobs")
    )




# =========================================================
# RUN APPLICATION
# IMPORTANT: THIS MUST BE AT THE VERY BOTTOM
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
