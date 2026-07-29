CREATE TABLE IF NOT EXISTS countries (
    id INTEGER PRIMARY KEY,
    iso2 TEXT NOT NULL UNIQUE,
    iso3 TEXT UNIQUE,
    name_en TEXT NOT NULL,
    name_local TEXT
);

CREATE TABLE IF NOT EXISTS treaties (
    id INTEGER PRIMARY KEY,
    country_a_id INTEGER NOT NULL,
    country_b_id INTEGER NOT NULL,
    treaty_type TEXT NOT NULL DEFAULT 'DTT',
    signed_date TEXT,
    effective_from TEXT,
    effective_to TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    FOREIGN KEY (country_a_id) REFERENCES countries(id),
    FOREIGN KEY (country_b_id) REFERENCES countries(id)
);

CREATE TABLE IF NOT EXISTS treaty_versions (
    id INTEGER PRIMARY KEY,
    treaty_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    source_file TEXT,
    is_authentic INTEGER NOT NULL DEFAULT 0,
    valid_from TEXT,
    valid_to TEXT,
    FOREIGN KEY (treaty_id) REFERENCES treaties(id)
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY,
    treaty_version_id INTEGER NOT NULL,
    article_number INTEGER NOT NULL,
    title TEXT,
    FOREIGN KEY (treaty_version_id) REFERENCES treaty_versions(id)
);

CREATE TABLE IF NOT EXISTS paragraphs (
    id INTEGER PRIMARY KEY,
    article_id INTEGER NOT NULL,
    paragraph_number TEXT,
    text TEXT NOT NULL,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);

CREATE TABLE IF NOT EXISTS rules (
    id INTEGER PRIMARY KEY,
    article_id INTEGER NOT NULL,
    transaction_type TEXT NOT NULL,
    withholding_rate REAL,
    currency TEXT,
    notes TEXT,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);

CREATE TABLE IF NOT EXISTS rule_conditions (
    id INTEGER PRIMARY KEY,
    rule_id INTEGER NOT NULL,
    condition_type TEXT NOT NULL,
    operator TEXT NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (rule_id) REFERENCES rules(id)
);

