SELECT
    g.id,
    g.name,
    g.description,
    g.created,
    g.modified
FROM content.genre AS g
WHERE g.id = %s;