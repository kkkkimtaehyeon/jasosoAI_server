-- 1. users 테이블
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    oauth_id VARCHAR(255) UNIQUE,
    oauth_provider VARCHAR(50),
    is_banned BOOLEAN NOT NULL DEFAULT FALSE
);

-- 2. job_posting 테이블
CREATE TABLE job_posting (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    company_name VARCHAR(255),
    position_title VARCHAR(255),
    experience VARCHAR(50),
    position_detail TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    required_qualifications TEXT,
    preferred_qualifications TEXT
);


-- 3. feedback 테이블
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE
);



-- 5. cover_letter 테이블
CREATE TABLE cover_letter (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    type VARCHAR(50) NOT NULL,
    deleted_at TIMESTAMP,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE
);


-- 6. cover_letter_item 테이블
CREATE TABLE cover_letter_item (
    id SERIAL PRIMARY KEY,
    question VARCHAR(500) NOT NULL,
    char_limit INT NOT NULL,
    content TEXT NOT NULL,
    deleted_at TIMESTAMP,
    cover_letter_id INT NOT NULL REFERENCES cover_letter(id) ON DELETE CASCADE
);
