SELECT * FROM cache_mediciones 
    WHERE synced = FALSE 
    ORDER BY sample_index ASC
    LIMIT 1000;