SELECT
    p.id,
    p.full_name,
    p.created,
    p.modified
FROM content.person AS p
WHERE p.id = %s;
