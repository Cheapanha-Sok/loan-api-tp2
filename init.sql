-- Seed data: borrowers and loan_applications (Module 1, Lesson 1.7), for PostgreSQL
CREATE TABLE borrowers (
    id            INTEGER PRIMARY KEY,
    full_name     TEXT NOT NULL,
    phone         TEXT,
    province      TEXT
);

CREATE TABLE loan_applications (
    id            INTEGER PRIMARY KEY,
    borrower_id   INTEGER NOT NULL REFERENCES borrowers(id),
    amount_usd    INTEGER NOT NULL CHECK (amount_usd BETWEEN 100 AND 5000),
    term_months   INTEGER NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

INSERT INTO borrowers (id, full_name, phone, province) VALUES
    (1, 'Sok Dara',    '012 345 678', 'Phnom Penh'),
    (2, 'Chan Sophea', '017 222 333', 'Siem Reap'),
    (3, 'Kim Vuthy',   '011 888 999', 'Battambang'),
    (4, 'Heng Malis',  '015 444 555', 'Kampot');

INSERT INTO loan_applications (id, borrower_id, amount_usd, term_months, status) VALUES
    (101, 1, 1500, 12, 'pending'),
    (102, 2,  800,  6, 'approved'),
    (103, 3, 3000, 24, 'rejected'),
    (104, 1,  500,  3, 'approved'),
    (105, 2, 2000, 18, 'pending'),
    (106, 4, 1200, 12, 'pending');
