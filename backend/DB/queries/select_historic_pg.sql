SELECT 
    v.ID_Voltajes as rowid,
    v.Entrada as VoltajeEntrada,
    v.Diodo as VoltajeDiodo,
    v.Salida as VoltajeSalida,
    c.Entrada as CorrienteEntrada,
    c.Inductor as CorrienteInductor,
    c.Diodo as CorrienteDiodo,
    c.Salida as CorrienteSalida,
    p.Entrada as PotenciaEntrada,
    p.Salida as PotenciaSalida,
    v.Marca_Tiempo as Marca_Tiempo
    
    FROM VOLTAJES v
    JOIN CORRIENTES c ON v.ID_Mediciones = c.ID_Mediciones
    JOIN POTENCIAS p ON v.ID_Mediciones = p.ID_Mediciones
    WHERE v.ID_Mediciones = %s
    ORDER BY v.ID_Voltajes ASC
    LIMIT %s