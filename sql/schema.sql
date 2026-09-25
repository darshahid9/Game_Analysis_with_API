-- Tennis Analytics: SportRadar Data Warehouse
-- MySQL 8.x

CREATE DATABASE IF NOT EXISTS tennis_analytics;
USE tennis_analytics;

-- 1. Categories
CREATE TABLE IF NOT EXISTS categories (
    category_id     VARCHAR(50) PRIMARY KEY,
    category_name   VARCHAR(100) NOT NULL
);

-- 2. Competitions
CREATE TABLE IF NOT EXISTS competitions (
    competition_id      VARCHAR(50) PRIMARY KEY,
    competition_name    VARCHAR(100) NOT NULL,
    parent_id            VARCHAR(50) NULL,
    type                  VARCHAR(20) NOT NULL,
    gender                VARCHAR(10) NOT NULL,
    category_id           VARCHAR(50) NOT NULL,
    CONSTRAINT fk_competition_category
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- 3. Complexes
CREATE TABLE IF NOT EXISTS complexes (
    complex_id     VARCHAR(50) PRIMARY KEY,
    complex_name   VARCHAR(100) NOT NULL
);

-- 4. Venues
CREATE TABLE IF NOT EXISTS venues (
    venue_id        VARCHAR(50) PRIMARY KEY,
    venue_name      VARCHAR(100) NOT NULL,
    city_name       VARCHAR(100) NOT NULL,
    country_name    VARCHAR(100) NOT NULL,
    country_code    CHAR(3) NOT NULL,
    timezone        VARCHAR(100) NOT NULL,
    complex_id      VARCHAR(50) NOT NULL,
    CONSTRAINT fk_venue_complex
        FOREIGN KEY (complex_id) REFERENCES complexes(complex_id)
);

-- 5. Competitors
CREATE TABLE IF NOT EXISTS competitors (
    competitor_id   VARCHAR(50) PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    country         VARCHAR(100) NOT NULL,
    country_code    CHAR(3) NOT NULL,
    abbreviation    VARCHAR(10) NOT NULL
);

-- 6. Competitor_Rankings
-- rank_type/gender/year/week are not in the original spec table but are required
-- to make sense of a weekly doubles ranking snapshot (see README "Schema notes").
CREATE TABLE IF NOT EXISTS competitor_rankings (
    rank_id               INT AUTO_INCREMENT PRIMARY KEY,
    `rank`                 INT NOT NULL,
    movement              INT NOT NULL,
    points                INT NOT NULL,
    competitions_played   INT NOT NULL,
    competitor_id         VARCHAR(50) NOT NULL,
    rank_type             VARCHAR(20) NOT NULL DEFAULT 'doubles',
    gender                VARCHAR(10) NOT NULL,
    year                  INT NOT NULL,
    week                  INT NOT NULL,
    CONSTRAINT fk_ranking_competitor
        FOREIGN KEY (competitor_id) REFERENCES competitors(competitor_id),
    UNIQUE KEY uq_competitor_week (competitor_id, gender, year, week)
);

CREATE INDEX idx_competitions_category ON competitions(category_id);
CREATE INDEX idx_competitions_parent ON competitions(parent_id);
CREATE INDEX idx_venues_complex ON venues(complex_id);
CREATE INDEX idx_venues_country ON venues(country_name);
CREATE INDEX idx_rankings_competitor ON competitor_rankings(competitor_id);
CREATE INDEX idx_rankings_week ON competitor_rankings(year, week);

SHOW INDEX FROM competitions;
SHOW INDEX FROM complexes;
SHOW INDEX FROM venues;
SHOW INDEX FROM competitor_rankings;