CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    gender VARCHAR(20),
    degree_program VARCHAR(100),
    batch INT,
    committee VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS organizations (
    org_id INT AUTO_INCREMENT PRIMARY KEY,
    org_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS org_roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS memberships (
    membership_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    org_id INT NOT NULL,
    role_id INT NOT NULL,
    status VARCHAR(30) NOT NULL,
    semester VARCHAR(10) NOT NULL,         -- "1st" or "2nd"
    academic_year INT NOT NULL,            -- e.g. 2024
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (org_id) REFERENCES organizations(org_id),
    FOREIGN KEY (role_id) REFERENCES org_roles(role_id)
);

INSERT INTO org_roles (role_name) VALUES ('President');
INSERT INTO org_roles (role_name) VALUES ('Vice President');
INSERT INTO org_roles (role_name) VALUES ('Secretary');
INSERT INTO org_roles (role_name) VALUES ('Treasurer');
INSERT INTO org_roles (role_name) VALUES ('Member');

CREATE TABLE IF NOT EXISTS fees (
    fee_id INT AUTO_INCREMENT PRIMARY KEY,
    org_id INT,
    student_id INT,
    membership_id INT,
    amount DECIMAL(10,2),
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    fee_status VARCHAR(20),
    due_date DATE,
    date_paid DATE,
    CONSTRAINT fk_org FOREIGN KEY (org_id) REFERENCES organizations(org_id),
    CONSTRAINT fk_student FOREIGN KEY (student_id) REFERENCES students(student_id),
    CONSTRAINT fk_membership FOREIGN KEY (membership_id) REFERENCES memberships(membership_id)
);