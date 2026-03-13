SELECT
    g.id,
    g.name,
    g.description,
    g.created,
    g.modified
FROM content.genre AS g
WHERE g.modified > %s {}
ORDER BY g.modified
LIMIT %s OFFSET %s;
