CREATE TABLE IF NOT EXISTS users (
    id           SERIAL PRIMARY KEY,
    login        VARCHAR(64) UNIQUE NOT NULL,
    password     VARCHAR(256) NOT NULL,
    role         VARCHAR(32) NOT NULL CHECK (role IN ('student', 'curator', 'teacher', 'admin')),
    is_active    BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS organizations (
    id        SERIAL PRIMARY KEY,
    name      VARCHAR(256) NOT NULL,
    yur_adres VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS kafedras (
    id      SERIAL PRIMARY KEY,
    name    VARCHAR(255) NOT NULL,
    faculty VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS teachers (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    last_name   VARCHAR(64) NOT NULL,
    first_name  VARCHAR(64) NOT NULL,
    middle_name VARCHAR(64),
    position    VARCHAR(100),
    email       VARCHAR(100),
    kafedra_id  INTEGER REFERENCES kafedras(id)
);

CREATE TABLE IF NOT EXISTS curators (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    last_name       VARCHAR(64) NOT NULL,
    first_name      VARCHAR(64) NOT NULL,
    middle_name     VARCHAR(64),
    position        VARCHAR(100),
    email           VARCHAR(100),
    organization_id INTEGER REFERENCES organizations(id)
);

CREATE TABLE IF NOT EXISTS students (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    last_name        VARCHAR(64) NOT NULL,
    first_name       VARCHAR(64) NOT NULL,
    middle_name      VARCHAR(64),
    group_name       VARCHAR(64) NOT NULL,
    specialty        VARCHAR(256),
    email            VARCHAR(255),
    average_grade    NUMERIC(3,2),
    kafedra_id       INTEGER REFERENCES kafedras(id),
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
