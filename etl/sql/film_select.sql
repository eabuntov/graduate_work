SELECT  fw.id,
        fw.title,
        fw.description,
        fw.rating,
        fw.type,
        array_agg(DISTINCT g.name) AS genres,
        json_agg(DISTINCT jsonb_build_object('id', p.id, 'name', p.full_name, 'role', pfw.role))
            FILTER (WHERE p.id IS NOT NULL) AS persons
FROM content.film_work fw
LEFT JOIN content.genre_film_work gfw ON fw.id = gfw.film_work_id
LEFT JOIN content.genre g ON gfw.genre_id = g.id
LEFT JOIN content.person_film_work pfw ON fw.id = pfw.film_work_id
LEFT JOIN content.person p ON pfw.person_id = p.id
WHERE fw.id = %s
GROUP BY fw.id;