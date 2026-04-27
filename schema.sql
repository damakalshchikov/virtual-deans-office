CREATE TABLE IF NOT EXISTS users (
    id           SERIAL PRIMARY KEY,
    login        VARCHAR(64) UNIQUE NOT NULL,
    password     VARCHAR(256) NOT NULL,
    role         VARCHAR(32) NOT NULL CHECK (role IN ('student', 'curator', 'teacher', 'admin')),
    is_active    BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS organizations (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(256) NOT NULL
);

CREATE TABLE IF NOT EXISTS teachers (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    full_name  VARCHAR(128) NOT NULL,
    department VARCHAR(128) NOT NULL
);

CREATE TABLE IF NOT EXISTS curators (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    full_name       VARCHAR(128) NOT NULL,
    organization_id INTEGER REFERENCES organizations(id)
);

CREATE TABLE IF NOT EXISTS students (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    full_name        VARCHAR(128) NOT NULL,
    group_name       VARCHAR(64) NOT NULL,
    specialty        VARCHAR(256) NOT NULL,
    internship_start DATE,
    internship_end   DATE,
    organization_id  INTEGER REFERENCES organizations(id),
    teacher_id       INTEGER REFERENCES teachers(id),
    curator_id       INTEGER REFERENCES curators(id)
);

CREATE TABLE IF NOT EXISTS tasks (
    id         SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    title      VARCHAR(256) NOT NULL,
    status     VARCHAR(32) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'done'))
);
