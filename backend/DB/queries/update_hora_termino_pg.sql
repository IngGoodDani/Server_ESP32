UPDATE MEDICIONES
    SET Hora_Termino = CURRENT_TIME
    WHERE ID_Mediciones = %s;