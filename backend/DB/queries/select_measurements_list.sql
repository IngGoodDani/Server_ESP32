SELECT 
    m.ID_Mediciones as id,
    m.Fecha,
    m.Hora_Inicio,
    m.Hora_Termino,
    COUNT(v.ID_Voltajes) as num_samples
FROM MEDICIONES m
LEFT JOIN VOLTAJES v ON m.ID_Mediciones = v.ID_Mediciones
GROUP BY m.ID_Mediciones, m.Fecha, m.Hora_Inicio, m.Hora_Termino
ORDER BY m.ID_Mediciones DESC
LIMIT 100;