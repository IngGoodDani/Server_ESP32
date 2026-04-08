INSERT INTO CORRIENTES (
    ID_Mediciones,
    Entrada,
    Diodo,
    Inductor,
    Salida,
    Marca_Tiempo)
    
    VALUES (%s, %s, %s, %s, %s, CURRENT_TIME);