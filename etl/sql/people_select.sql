SELECT
    p.id,
    p.full_name,
    p.created,
    p.modified
FROM content.person AS p
WHERE p.modified > %s {}
ORDER BY p.modified
LIMIT %s OFFSET %s;