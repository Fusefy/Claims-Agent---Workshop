-- ============================================
-- ClaimWise Database Schema (Final Version)
-- ============================================

-- ============================================
-- Table 1: User Management (OAuth + Password)
-- ============================================

CREATE TABLE IF NOT EXISTS "user" (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash TEXT,                          -- Nullable for OAuth users
    google_id VARCHAR(255),                      -- Google OAuth ID
    role VARCHAR(20) DEFAULT 'User',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_username ON "user"(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS idx_user_google_id ON "user"(google_id);


-- ============================================
-- Table 2: Proposed Claims
-- ============================================

CREATE TABLE IF NOT EXISTS proposedclaim (
    claim_id VARCHAR(50) PRIMARY KEY,
    claim_name VARCHAR(200),
    customer_id VARCHAR(50) NOT NULL,
    policy_id VARCHAR(50),

    claim_type VARCHAR(50),
    network_status VARCHAR(50),
    date_of_service TIMESTAMP,

    claim_amount DECIMAL(12, 2),
    approved_amount DECIMAL(12, 2) DEFAULT 0.0,

    claim_status VARCHAR(50) DEFAULT 'Pending'
        CHECK (claim_status IN ('Approved', 'Pending', 'Denied')),

    error_type VARCHAR(100),
    ai_reasoning TEXT,

    payment_status VARCHAR(50) DEFAULT 'Pending',

    guardrail_summary JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_claim_customer_id ON proposedclaim(customer_id);
CREATE INDEX IF NOT EXISTS idx_claim_status ON proposedclaim(claim_status);
CREATE INDEX IF NOT EXISTS idx_claim_name ON proposedclaim(claim_name);


-- ============================================
-- Table 3: Human-In-The-Loop (HITL) Queue
-- ============================================

CREATE TABLE IF NOT EXISTS hitlqueue (
    queue_id SERIAL PRIMARY KEY,
    claim_id VARCHAR(50) NOT NULL,
    assigned_to INTEGER,

    status VARCHAR(50) DEFAULT 'Pending'
        CHECK (status IN ('Approved', 'Pending', 'Denied')),

    reviewer_comments TEXT,
    decision VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,

    FOREIGN KEY (claim_id) REFERENCES proposedclaim(claim_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES "user"(user_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_hitl_claim_id ON hitlqueue(claim_id);
CREATE INDEX IF NOT EXISTS idx_hitl_status ON hitlqueue(status);


-- ============================================
-- Table 4: Claim History
-- ============================================

CREATE TABLE IF NOT EXISTS claimhistory (
    history_id SERIAL PRIMARY KEY,
    claim_id VARCHAR(50) NOT NULL,

    old_status VARCHAR(50)
        CHECK (old_status IN ('Approved', 'Pending', 'Denied', 'New')),

    new_status VARCHAR(50)
        CHECK (new_status IN ('Approved', 'Pending', 'Denied')),

    changed_by VARCHAR(100),
    role VARCHAR(20),
    change_reason TEXT,

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (claim_id) REFERENCES proposedclaim(claim_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_history_claim_id ON claimhistory(claim_id);
