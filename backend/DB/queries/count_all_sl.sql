SELECT COUNT(*) as total 
    FROM cache_mediciones
    WHERE measurement_id = ?;