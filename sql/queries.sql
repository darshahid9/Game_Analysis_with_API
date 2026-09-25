USE tennis_analytics;

-- ============ COMPETITIONS ============

-- 1) List all competitions along with their category name
SELECT c.competition_id, c.competition_name, c.type, c.gender, cat.category_name
FROM competitions c
JOIN categories cat ON c.category_id = cat.category_id;

-- 2) Count the number of competitions in each category
SELECT cat.category_name, COUNT(*) AS competition_count
FROM competitions c
JOIN categories cat ON c.category_id = cat.category_id
GROUP BY cat.category_name
ORDER BY competition_count DESC;

-- 3) Find all competitions of type 'doubles'
SELECT competition_id, competition_name, gender, category_id
FROM competitions
WHERE type = 'doubles';

-- 4) Get competitions that belong to a specific category (e.g., ITF Men)
SELECT c.competition_id, c.competition_name, c.type, c.gender
FROM competitions c
JOIN categories cat ON c.category_id = cat.category_id
WHERE cat.category_name = 'ITF Men';

-- 5) Identify parent competitions and their sub-competitions
SELECT parent.competition_name AS parent_competition,
       child.competition_name  AS sub_competition
FROM competitions child
JOIN competitions parent ON child.parent_id = parent.competition_id
ORDER BY parent.competition_name;

-- 6) Analyze the distribution of competition types by category
SELECT cat.category_name, c.type, COUNT(*) AS total
FROM competitions c
JOIN categories cat ON c.category_id = cat.category_id
GROUP BY cat.category_name, c.type
ORDER BY cat.category_name, total DESC;

-- 7) List all competitions with no parent (top-level competitions)
SELECT competition_id, competition_name, type, gender
FROM competitions
WHERE parent_id IS NULL;

-- ============ COMPLEXES / VENUES ============

-- 1) List all venues along with their associated complex name
SELECT v.venue_name, v.city_name, v.country_name, cx.complex_name
FROM venues v
JOIN complexes cx ON v.complex_id = cx.complex_id;

-- 2) Count the number of venues in each complex
SELECT cx.complex_name, COUNT(*) AS venue_count
FROM venues v
JOIN complexes cx ON v.complex_id = cx.complex_id
GROUP BY cx.complex_name
ORDER BY venue_count DESC;

-- 3) Get details of venues in a specific country (e.g., Chile)
SELECT venue_name, city_name, country_name, timezone
FROM venues
WHERE country_name = 'Chile';

-- 4) Identify all venues and their timezones
SELECT venue_name, city_name, country_name, timezone
FROM venues
ORDER BY timezone;

-- 5) Find complexes that have more than one venue
SELECT cx.complex_name, COUNT(*) AS venue_count
FROM venues v
JOIN complexes cx ON v.complex_id = cx.complex_id
GROUP BY cx.complex_name
HAVING COUNT(*) > 1
ORDER BY venue_count DESC;

-- 6) List venues grouped by country
SELECT country_name, COUNT(*) AS venue_count, GROUP_CONCAT(venue_name SEPARATOR ', ') AS venues
FROM venues
GROUP BY country_name
ORDER BY venue_count DESC;

-- 7) Find all venues for a specific complex (e.g., Nacional)
SELECT v.venue_name, v.city_name, v.country_name
FROM venues v
JOIN complexes cx ON v.complex_id = cx.complex_id
WHERE cx.complex_name = 'Nacional';

-- ============ COMPETITORS / RANKINGS ============

-- 1) Get all competitors with their rank and points
SELECT comp.name, comp.country, r.rank, r.points, r.year, r.week
FROM competitor_rankings r
JOIN competitors comp ON r.competitor_id = comp.competitor_id;

-- 2) Find competitors ranked in the top 5
SELECT comp.name, comp.country, r.rank, r.points
FROM competitor_rankings r
JOIN competitors comp ON r.competitor_id = comp.competitor_id
WHERE r.rank <= 5
ORDER BY r.rank;

-- 3) List competitors with no rank movement (stable rank)
SELECT comp.name, comp.country, r.rank, r.movement
FROM competitor_rankings r
JOIN competitors comp ON r.competitor_id = comp.competitor_id
WHERE r.movement = 0;

-- 4) Get the total points of competitors from a specific country (e.g., Croatia)
SELECT comp.country, SUM(r.points) AS total_points
FROM competitor_rankings r
JOIN competitors comp ON r.competitor_id = comp.competitor_id
WHERE comp.country = 'Croatia'
GROUP BY comp.country;

-- 5) Count the number of competitors per country
SELECT country, COUNT(DISTINCT competitor_id) AS competitor_count
FROM competitors
GROUP BY country
ORDER BY competitor_count DESC;

-- 6) Find competitors with the highest points in the current week
SELECT comp.name, comp.country, r.points, r.year, r.week
FROM competitor_rankings r
JOIN competitors comp ON r.competitor_id = comp.competitor_id
WHERE (r.year, r.week) = (
    SELECT year, week FROM competitor_rankings ORDER BY year DESC, week DESC LIMIT 1
)
ORDER BY r.points DESC
LIMIT 10;
