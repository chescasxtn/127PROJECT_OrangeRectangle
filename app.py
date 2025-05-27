from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector

# Initialize Flask
app = Flask(__name__)

# MariaDB connection settings (update these with your actual credentials)
DB_CONFIG = {
    'user': 'root',        # <-- change this
    'password': '1029pqwo',    # <-- change this
    'host': 'localhost',
    'database': '127project'     # <-- change this
}

# Utility function to connect to the MariaDB database
def get_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn

# Home route: Displays all memberships and supporting data for forms
@app.route('/')
def index():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Fetch all memberships
    cur.execute("""
        SELECT m.membership_id, s.student_id, CONCAT(s.first_name, ' ', s.last_name) AS student_name,
               s.gender, s.degree_program, s.batch, s.committee,
               o.org_id, o.org_name, r.role_id, r.role_name, m.status, m.semester, m.academic_year
        FROM memberships m
        JOIN students s ON m.student_id = s.student_id
        JOIN organizations o ON m.org_id = o.org_id
        JOIN org_roles r ON m.role_id = r.role_id
    """)
    memberships = cur.fetchall()

    # Fetch dropdown data
    cur.execute("SELECT student_id, CONCAT(first_name, ' ', last_name) AS full_name FROM students")
    students = cur.fetchall()

    cur.execute("SELECT org_id, org_name FROM organizations")
    orgs = cur.fetchall()

    cur.execute("SELECT role_id, role_name FROM org_roles")
    roles = cur.fetchall()

    # Conditional: View members with unpaid fees
    members = []
    if 'org_id' in request.args and 'semester' in request.args and 'year' in request.args:
        org_id = request.args.get('org_id')
        semester = request.args.get('semester')
        year = request.args.get('year')

        cur.execute("""
            SELECT s.student_id, CONCAT(s.first_name, ' ', s.last_name) AS full_name,
                   o.org_name, f.fee_status, f.due_date
            FROM students s
            JOIN memberships m ON s.student_id = m.student_id
            JOIN organizations o ON m.org_id = o.org_id
            LEFT JOIN fees f ON m.membership_id = f.membership_id
            WHERE m.org_id = %s AND m.semester = %s AND m.academic_year = %s
              AND (f.fee_status = 'unpaid' OR f.fee_status IS NULL)
        """, (org_id, semester, year))
        members = cur.fetchall()

    # Conditional: Search members by name
    elif 'member_name' in request.args:
        member_name = request.args.get('member_name')
        cur.execute("""
            SELECT s.student_id, CONCAT(s.first_name, ' ', s.last_name) AS full_name,
                   o.org_name
            FROM students s
            JOIN memberships m ON s.student_id = m.student_id
            JOIN organizations o ON m.org_id = o.org_id
            WHERE s.first_name LIKE %s OR s.last_name LIKE %s
        """, (f'%{member_name}%', f'%{member_name}%'))
        members = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'index.html',
        memberships=memberships,
        students=students,
        orgs=orgs,
        roles=roles,
        members=members  # for search/unpaid display
    )

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
    cur = conn.cursor(dictionary=True)

    # 1. Insert or get student
    cur.execute(
        "SELECT student_id FROM students WHERE first_name=%s AND last_name=%s AND gender=%s AND degree_program=%s AND batch=%s AND committee=%s",
        (first_name, last_name, gender, degree_program, batch, committee)
    )
    student = cur.fetchone()
    if student:
        student_id = student['student_id']
    else:
        cur.execute(
            "INSERT INTO students (first_name, last_name, gender, degree_program, batch, committee) VALUES (%s, %s, %s, %s, %s, %s)",
            (first_name, last_name, gender, degree_program, batch, committee)
        )
        student_id = cur.lastrowid

    # 2. Insert or get organization
    cur.execute("SELECT org_id FROM organizations WHERE org_name=%s", (org_name,))
    org = cur.fetchone()
    if org:
        org_id = org['org_id']
    else:
        cur.execute("INSERT INTO organizations (org_name) VALUES (%s)", (org_name,))
        org_id = cur.lastrowid

    # 3. Insert membership record
    cur.execute(
        "INSERT INTO memberships (student_id, org_id, role_id, status, semester, academic_year) VALUES (%s, %s, %s, %s, %s, %s)",
        (student_id, org_id, role_id, status, semester, academic_year)
    )

    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Route to delete a membership record
@app.route('/delete/<int:membership_id>')
def delete(membership_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM memberships WHERE membership_id=%s", (membership_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Route to update a membership record (not yet implemented properly)
@app.route('/update/<int:membership_id>', methods=['POST'])
def update(membership_id):
    student_id = request.form['student_id']
    org_id = request.form['org_id']
    role_id = request.form['role_id']
    status = request.form['status']
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE memberships SET student_id=%s, org_id=%s, role_id=%s, status=%s WHERE membership_id=%s",
        (student_id, org_id, role_id, status, membership_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Route to search memberships by student
@app.route('/search')
def search():
    member_name = request.args.get('member_name', '').strip()
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    # Search by first name or last name using LIKE for partial matches
    cur.execute("""
        SELECT m.membership_id, s.student_id, CONCAT(s.first_name, ' ', s.last_name) AS student_name,
            s.gender, s.degree_program, s.batch, s.committee,
            o.org_id, o.org_name, r.role_id, r.role_name, m.status, m.semester, m.academic_year
        FROM memberships m
        JOIN students s ON m.student_id = s.student_id
        JOIN organizations o ON m.org_id = o.org_id
        JOIN org_roles r ON m.role_id = r.role_id
        WHERE CONCAT(s.first_name, ' ', s.last_name) LIKE %s
        OR s.first_name LIKE %s
        OR s.last_name LIKE %s
    """, (f"%{member_name}%", f"%{member_name}%", f"%{member_name}%"))
    memberships = cur.fetchall()
    cur.execute("SELECT student_id, CONCAT(first_name, ' ', last_name) AS full_name FROM students")
    students = cur.fetchall()
    cur.execute("SELECT org_id, org_name FROM organizations")
    orgs = cur.fetchall()
    cur.execute("SELECT role_id, role_name FROM org_roles")
    roles = cur.fetchall()
    conn.close()
    return render_template(
        'index.html',
        memberships=memberships,
        students=students,
        orgs=orgs,
        roles=roles,
        searched=member_name  
    )

@app.route('/view_exec_committee')
def view_exec_committee():
    org_id = request.args.get('org_id')
    academic_year = request.args.get('academic_year')

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    # You may want to adjust the roles considered "executive committee"
    # Here, we assume any role except 'Member' is executive
    cur.execute("""
        SELECT s.student_id, CONCAT(s.first_name, ' ', s.last_name) AS student_name,
               r.role_name, m.semester, m.academic_year
        FROM memberships m
        JOIN students s ON m.student_id = s.student_id
        JOIN org_roles r ON m.role_id = r.role_id
        WHERE m.org_id = %s
          AND m.academic_year = %s
          AND r.role_name != 'Member'
        ORDER BY r.role_name, s.last_name, s.first_name
    """, (org_id, academic_year))
    exec_members = cur.fetchall()
    conn.close()

    return render_template('exec_committee_result.html', exec_members=exec_members)

@app.route('/view_role_by_year')
def view_role_by_year():
    org_id = request.args.get('org_id')
    role_id = request.args.get('role_id')

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Get all members for this org and role, for all years and semesters
    cur.execute("""
        SELECT s.student_id, CONCAT(s.first_name, ' ', s.last_name) AS student_name,
               r.role_name, m.academic_year, m.semester
        FROM memberships m
        JOIN students s ON m.student_id = s.student_id
        JOIN org_roles r ON m.role_id = r.role_id
        WHERE m.org_id = %s AND m.role_id = %s
        ORDER BY m.academic_year DESC, FIELD(m.semester, '2nd', '1st') DESC, s.last_name, s.first_name
    """, (org_id, role_id))
    members = cur.fetchall()
    conn.close()

    # Group by year and semester for the template
    from collections import defaultdict
    grouped = defaultdict(lambda: defaultdict(list))
    years = set()
    for m in members:
        grouped[m['academic_year']][m['semester']].append(m)
        years.add(m['academic_year'])
    years = sorted(years, reverse=True)

    return render_template(
        'role_by_year_result.html',
        years=years,
        grouped=grouped,
        role_name=members[0]['role_name'] if members else '',
    )

@app.route('/view_active_inactive')
def view_active_inactive():
    org_id = request.args.get('org_id')
    n = int(request.args.get('n', 1))

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Get the last n (semester, academic_year) pairs for the org, ordered from most recent
    cur.execute("""
        SELECT DISTINCT semester, academic_year
        FROM memberships
        WHERE org_id = %s
        ORDER BY academic_year DESC, 
                 FIELD(semester, '2nd', '1st') DESC
        LIMIT %s
    """, (org_id, n))
    recent_semesters = cur.fetchall()

    if not recent_semesters:
        conn.close()
        return render_template('active_inactive_result.html', result=None, message="No data found for this organization.")

    # Prepare a list of (semester, academic_year) tuples
    sem_year_pairs = [(row['semester'], row['academic_year']) for row in recent_semesters]

    # Build WHERE clause for these semesters
    where_clauses = " OR ".join(["(semester=%s AND academic_year=%s)" for _ in sem_year_pairs])
    params = []
    for sem, year in sem_year_pairs:
        params.extend([sem, year])

    # Get counts of active and inactive members in those semesters
    cur.execute(f"""
        SELECT status, COUNT(*) as count
        FROM memberships
        WHERE org_id = %s AND ({where_clauses})
        GROUP BY status
    """, (org_id, *params))
    status_counts = cur.fetchall()
    conn.close()

    # Calculate totals
    total = sum(row['count'] for row in status_counts)
    active = sum(row['count'] for row in status_counts if row['status'] == 'active')
    inactive = sum(row['count'] for row in status_counts if row['status'] == 'inactive')

    percent_active = (active / total * 100) if total else 0
    percent_inactive = (inactive / total * 100) if total else 0

    result = {
        'total': total,
        'active': active,
        'inactive': inactive,
        'percent_active': round(percent_active, 2),
        'percent_inactive': round(percent_inactive, 2),
        'semesters': sem_year_pairs
    }

    return render_template('active_inactive_result.html', result=result, message=None)

@app.route('/view_alumni_as_of')
def view_alumni_as_of():
    org_id = request.args.get('org_id')
    academic_year = request.args.get('academic_year')

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT s.student_id, CONCAT(s.first_name, ' ', s.last_name) AS student_name,
               m.status, m.semester, m.academic_year
        FROM memberships m
        JOIN students s ON m.student_id = s.student_id
        WHERE m.org_id = %s
          AND m.status = 'alumni'
          AND m.academic_year = %s
        ORDER BY s.last_name, s.first_name
    """, (org_id, academic_year))
    alumni_members = cur.fetchall()
    conn.close()

    return render_template('alumni_as_of_result.html', alumni_members=alumni_members, academic_year=academic_year)

@app.route('/add_fee', methods=['POST'])
def add_fee():
    membership_id = request.form['membership_id']
    fee_amount = request.form['fee_amount']
    due_date = request.form['due_date']
    date_paid = request.form['date_paid']
    fee_status = request.form['fee_status']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get student_id and org_id from membership_id
    cursor.execute("""
        SELECT student_id, org_id
        FROM memberships
        WHERE membership_id = %s
    """, (membership_id,))
    membership = cursor.fetchone()

    if not membership:
        cursor.close()
        conn.close()
        return "Invalid membership ID", 400

    student_id = membership['student_id']
    org_id = membership['org_id']

    # Insert the fee with all fields
    sql = """
        INSERT INTO fees (org_id, student_id, membership_id, amount, date, due_date, date_paid, fee_status)
        VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s)
    """
    values = (org_id, student_id, membership_id, fee_amount, due_date, date_paid or None, fee_status)
    cursor.execute(sql, values)

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('index'))


@app.route('/get_members/<int:org_id>')
def get_members(org_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Get membership_id and full name of members in the organization
    cur.execute("""
        SELECT m.membership_id, CONCAT(s.first_name, ' ', s.last_name) AS full_name
        FROM students s
        JOIN memberships m ON s.student_id = m.student_id
        WHERE m.org_id = %s
    """, (org_id,))
    
    members = cur.fetchall()
    conn.close()

    # Return as JSON
    return jsonify(members)

@app.route('/view_org_members_unpaid', methods=['POST'])
def view_org_members_unpaid():
    org_id = request.form['org_id']
    semester = request.form['semester']
    year = request.form['year']

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT s.student_id, s.first_name, s.last_name, f.fee_status, f.amount
        FROM fees f
        JOIN students s ON f.student_id = s.student_id
        JOIN memberships m ON f.membership_id = m.membership_id
        WHERE f.org_id = %s
          AND m.semester = %s
          AND m.academic_year = %s
          AND f.fee_status = 'unpaid'
    """
    cur.execute(query, (org_id, semester, year))
    unpaid_members = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('unpaid_members.html', members=unpaid_members)

@app.route('/view_member_unpaid_fees', methods=['POST'])
def view_member_unpaid_fees():
    student_id = request.form['student_id']

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT o.org_name, f.amount, f.fee_status, m.semester, m.academic_year
        FROM fees f
        JOIN memberships m ON f.membership_id = m.membership_id
        JOIN organizations o ON f.org_id = o.org_id
        WHERE f.student_id = %s AND f.fee_status = 'unpaid'
    """
    cur.execute(query, (student_id,))
    unpaid_fees = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('member_unpaid_fees.html', fees=unpaid_fees)

@app.route('/org_fee_summary', methods=['GET'])
def org_fee_summary():
    org_id = request.args.get('org_id')
    as_of_date = request.args.get('as_of_date')  # Format: YYYY-MM-DD

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT f.fee_status, SUM(f.amount) AS total_amount
        FROM fees f
        WHERE f.org_id = %s AND f.date <= %s
        GROUP BY f.fee_status
    """
    cur.execute(query, (org_id, as_of_date))
    fee_summary = cur.fetchall()

    cur.close()
    conn.close()

    # Organize into paid and unpaid totals
    totals = {'paid': 0, 'unpaid': 0}
    for row in fee_summary:
        status = row['fee_status']
        amount = row['total_amount']
        if status in totals:
            totals[status] = amount

    return render_template('org_fee_summary.html', totals=totals, as_of_date=as_of_date)

@app.route('/highest_debt', methods=['GET'])
def highest_debt():
    org_id = request.args['org_id']
    semester = request.args['semester']
    year = request.args['year']

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Get the maximum unpaid debt for members in the org + semester
    query = """
        SELECT s.student_id, s.first_name, s.last_name, SUM(f.amount) AS total_debt
        FROM fees f
        JOIN memberships m ON f.membership_id = m.membership_id
        JOIN students s ON m.student_id = s.student_id
        WHERE m.org_id = %s
          AND m.semester = %s
          AND m.academic_year = %s
          AND f.fee_status = 'unpaid'
        GROUP BY s.student_id, s.first_name, s.last_name
        HAVING total_debt = (
            SELECT MAX(debt) FROM (
                SELECT SUM(f2.amount) AS debt
                FROM fees f2
                JOIN memberships m2 ON f2.membership_id = m2.membership_id
                WHERE m2.org_id = %s
                  AND m2.semester = %s
                  AND m2.academic_year = %s
                  AND f2.fee_status = 'unpaid'
                GROUP BY m2.student_id
            ) AS subquery
        )
    """

    cur.execute(query, (org_id, semester, year, org_id, semester, year))
    top_debtors = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('highest_debt.html', top_debtors=top_debtors, semester=semester, year=year)

if __name__ == '__main__':
    app.run(debug=True)