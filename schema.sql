CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT,
    degree_program TEXT,
    batch INTEGER,
    committee TEXT
);

CREATE TABLE IF NOT EXISTS organizations (
    org_id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS org_roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memberships (
    membership_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    org_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    semester TEXT NOT NULL,         -- "1st" or "2nd"
    academic_year INTEGER NOT NULL, -- e.g. 2024
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (org_id) REFERENCES organizations(org_id),
    FOREIGN KEY (role_id) REFERENCES org_roles(role_id)
);
