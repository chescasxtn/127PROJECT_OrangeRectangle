from flask import Flask, render_template, request, redirect, url_for
import sqlite3

# Initialize Flask
app = Flask(__name__)
DB = 'cmsc127_project.db'

# Utility function to connect to the SQLite database
def get_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# Home route: Displays all memberships and supporting data for forms
@app.route('/')
def index():
    conn = get_connection()
    # Get all membership records with joined student, org, and role details
    memberships = conn.execute("""
        SELECT m.membership_id, s.student_id, s.first_name || ' ' || s.last_name AS student_name,
               s.gender, s.degree_program, s.batch, s.committee,
               o.org_id, o.org_name, r.role_id, r.role_name, m.status
        FROM memberships m
        JOIN students s ON m.student_id = s.student_id
        JOIN organizations o ON m.org_id = o.org_id
        JOIN org_roles r ON m.role_id = r.role_id
    """).fetchall()
    # Get all students for dropdowns
    students = conn.execute("SELECT student_id, first_name || ' ' || last_name AS full_name FROM students").fetchall()
    # Get all organizations for dropdowns
    orgs = conn.execute("SELECT org_id, org_name FROM organizations").fetchall()
    # Get all roles for dropdowns
    roles = conn.execute("SELECT role_id, role_name FROM org_roles").fetchall()
    conn.close()
    # Render the main template with all data
    return render_template('index.html', memberships=memberships, students=students, orgs=orgs, roles=roles)

# Route to handle adding a new member and their membership
@app.route('/add_member', methods=['POST'])
def add_member():
    # Get form data for student and membership details
    first_name = request.form['first_name'].strip()
    last_name = request.form['last_name'].strip()
    gender = request.form['gender']
    degree_program = request.form['degree_program'].strip()
    batch = request.form['batch']
    committee = request.form['committee'].strip()
    org_name = request.form['org_name'].strip()
    role_id = request.form['role_id']
    status = request.form['status']
    semester = request.form['semester']
    academic_year = request.form['academic_year']

    conn = get_connection()
    cur = conn.cursor()

    # 1. Insert or get student
    cur.execute(
        "SELECT student_id FROM students WHERE first_name=? AND last_name=? AND gender=? AND degree_program=? AND batch=? AND committee=?",
        (first_name, last_name, gender, degree_program, batch, committee)
    )
    student = cur.fetchone()
    if student:
        student_id = student['student_id']
    else:
        cur.execute(
            "INSERT INTO students (first_name, last_name, gender, degree_program, batch, committee) VALUES (?, ?, ?, ?, ?, ?)",
            (first_name, last_name, gender, degree_program, batch, committee)
        )
        student_id = cur.lastrowid

    # 2. Insert or get organization
    cur.execute("SELECT org_id FROM organizations WHERE org_name=?", (org_name,))
    org = cur.fetchone()
    if org:
        org_id = org['org_id']
    else:
        cur.execute("INSERT INTO organizations (org_name) VALUES (?)", (org_name,))
        org_id = cur.lastrowid

    # 3. Insert membership record
    cur.execute(
        "INSERT INTO memberships (student_id, org_id, role_id, status, semester, academic_year) VALUES (?, ?, ?, ?, ?, ?)",
        (student_id, org_id, role_id, status, semester, academic_year)
    )

    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Route to delete a membership record
@app.route('/delete/<int:membership_id>')
def delete(membership_id):
    conn = get_connection()
    conn.execute("DELETE FROM memberships WHERE membership_id=?", (membership_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Route to update a membership record (not yet implemented properly T T)
@app.route('/update/<int:membership_id>', methods=['POST'])
def update(membership_id):
    student_id = request.form['student_id']
    org_id = request.form['org_id']
    role_id = request.form['role_id']
    status = request.form['status']
    conn = get_connection()
    conn.execute(
        "UPDATE memberships SET student_id=?, org_id=?, role_id=?, status=? WHERE membership_id=?",
        (student_id, org_id, role_id, status, membership_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Route to search memberships by student
@app.route('/search')
def search():
    student_id = request.args.get('student_id')
    conn = get_connection()
    memberships = conn.execute("""
        SELECT m.membership_id, s.student_id, s.first_name || ' ' || s.last_name AS student_name,
               s.gender, s.degree_program, s.batch, s.committee,
               o.org_id, o.org_name, r.role_id, r.role_name, m.status, m.semester, m.academic_year
        FROM memberships m
        JOIN students s ON m.student_id = s.student_id
        JOIN organizations o ON m.org_id = o.org_id
        JOIN org_roles r ON m.role_id = r.role_id
        WHERE m.student_id = ?
    """, (student_id,)).fetchall()
    students = conn.execute("SELECT student_id, first_name || ' ' || last_name AS full_name FROM students").fetchall()
    orgs = conn.execute("SELECT org_id, org_name FROM organizations").fetchall()
    roles = conn.execute("SELECT role_id, role_name FROM org_roles").fetchall()
    conn.close()
    return render_template('index.html', memberships=memberships, students=students, orgs=orgs, roles=roles)

if __name__ == '__main__':
    app.run(debug=True)