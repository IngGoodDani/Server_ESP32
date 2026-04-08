SELECT * FROM cache_mediciones 
    WHERE measurement_id = ? 
    ORDER BY sample_index DESC 
    LIMIT ?;