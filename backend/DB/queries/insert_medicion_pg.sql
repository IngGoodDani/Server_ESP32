INSERT INTO MEDICIONES (
    Fecha, 
    Hora_Inicio, 
    Hora_Termino)
    
  VALUES (
    CURRENT_DATE, 
    CURRENT_TIME, 
    CURRENT_TIME)
    
  RETURNING ID_Mediciones;