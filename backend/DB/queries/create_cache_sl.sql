CREATE TABLE IF NOT EXISTS cache_mediciones (
    sample_index        INTEGER     PRIMARY KEY     AUTOINCREMENT,
    measurement_id      INTEGER,
    VoltajeEntrada      REAL,
    VoltajeDiodo        REAL,
    VoltajeSalida       REAL,
    CorrienteEntrada    REAL,
    CorrienteInductor   REAL,
    CorrienteDiodo      REAL,
    CorrienteSalida     REAL,
    PotenciaEntrada     REAL,
    PotenciaSalida      REAL,
    
    timestamp   DATETIME    DEFAULT CURRENT_TIMESTAMP,
    synced      BOOLEAN     DEFAULT FALSE);
    
CREATE INDEX IF NOT EXISTS idx_measurement 
ON cache_mediciones(measurement_id);

CREATE INDEX IF NOT EXISTS idx_sample_index 
ON cache_mediciones(sample_index);

CREATE INDEX IF NOT EXISTS idx_synced 
ON cache_mediciones(synced);