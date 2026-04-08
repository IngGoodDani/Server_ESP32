INSERT INTO VOLTAJES (
    ID_Mediciones,
    Entrada,
    Diodo,
    Salida,
    Marca_Tiempo)
    
    VALUES (%s, %s, %s, %s, CURRENT_TIME)
    RETURNING ID_Voltajes;