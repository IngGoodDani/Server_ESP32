import  sqlite3
from    sqlite3         import Error as SQLiteError
from    pathlib         import Path
from    typing          import Optional
from    contextlib      import contextmanager
import  psycopg2
from    psycopg2.extras import RealDictCursor
from    dotenv          import load_dotenv
import  os
import  threading


# ----------------------------------------------------------------------
# Configuración de la base de datos
# ----------------------------------------------------------------------
# Configuración de PostgreSQL
load_dotenv()

POSTGRES_CONFIG = {
    "dbname":   os.getenv("POSTGRES_DB"),
    "user":     os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host":     os.getenv("POSTGRES_HOST"),
    "port":     os.getenv("POSTGRES_PORT")
}

# Configuración de SQLite
SQLITE_DB_PATH = "cache_mediciones.db"
BASE_PATH = Path(__file__).parent

def load_query(filename):
    path = BASE_PATH / "queries" / filename
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# Consultas
queries = {
    "create_cache_sl":              load_query("create_cache_sl.sql"),
    "insert_cache_mediciones_sl":   load_query("insert_cache_mediciones_sl.sql"),
    "insert_medicion_pg":           load_query("insert_medicion_pg.sql"),
    "insert_voltajes_pg":           load_query("insert_voltajes_pg.sql"),
    "insert_corrientes_pg":         load_query("insert_corrientes_pg.sql"),
    "insert_potencias_pg":          load_query("insert_potencias_pg.sql"),
    "update_hora_termino_pg":       load_query("update_hora_termino_pg.sql"),
    "select_cache_med_desc_mid_sl": load_query("select_cache_med_desc_mid_sl.sql"),
    "select_cache_med_asc_mid_sl":  load_query("select_cache_med_asc_mid_sl.sql"),
    "select_cache_mediciones_sl":   load_query("select_cache_mediciones_sl.sql"),
    "count_all_sl":                 load_query("count_all_sl.sql"),
    "select_historic_pg":           load_query("select_historic_pg.sql"),
    "select_measurements_list":     load_query("select_measurements_list.sql")
}


# ----------------------------------------------------------------------
# Sistema híbrido SQLite + PostgreSQL
# ----------------------------------------------------------------------
class HybridDatabase():
    def __init__(self):
        self.sqlite_conn = None
        self.current_measurement_id = None
        self.measurement_sample_counter = 0
        self.connection_pool = []
        
    def init_sqlite(self):
        """Inicializa la base de datos SQLite"""
        try:
            self.sqlite_conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
            self.sqlite_conn.row_factory = sqlite3.Row
            
            # Crear tablas si no existen
            cursor = self.sqlite_conn.cursor()
            
            cursor.executescript(queries["create_cache_sl"])
            
            self.sqlite_conn.commit()
            print("✅ SQLite cache inicializado")
            
        except SQLiteError as e:
            print(f"❌ Error inicializando SQLite: {str(e)}")
            raise
    
    def init_postgres(self):
        """Inicializa conexión a PostgreSQL"""
        try:
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            print("✅ PostgreSQL inicializado")
        except Exception as e:
            print(f"❌ Error conectando a PostgreSQL: {str(e)}")
            raise
    
    @contextmanager
    def get_postgres_connection(self):
        """Context manager para conexión PostgreSQL"""
        conn = None
        try:
            if self.connection_pool:
                conn = self.connection_pool.pop()
                try:
                    conn.cursor().execute("SELECT 1")
                except:
                    conn = psycopg2.connect(**POSTGRES_CONFIG)
            else:
                conn = psycopg2.connect(**POSTGRES_CONFIG)
            yield conn
        finally:
            if conn:
                self.connection_pool.append(conn)
    
    @contextmanager
    def get_postgres_cursor(self):
        """Context manager para cursor PostgreSQL"""
        with self.get_postgres_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cur
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()
    
    def start_measurement(self):
        """Inicia una nueva medición en ambas bases de datos"""
        try:
            # 1. Iniciar en PostgreSQL
            with self.get_postgres_cursor() as cur:
                cur.execute(queries["insert_medicion_pg"])
                new_id = cur.fetchone()["id_mediciones"]
            
            self.current_measurement_id = new_id
            self.measurement_sample_counter = 0
            
            # 2. Limpiar cache de medición anterior en SQLite
            cursor = self.sqlite_conn.cursor()
            cursor.execute("DELETE FROM cache_mediciones WHERE synced = TRUE")
            self.sqlite_conn.commit()
            
            print(f"🎬 Medición #{new_id} iniciada. Contador: {self.measurement_sample_counter}")
            return new_id
            
        except Exception as e:
            print(f"❌ Error iniciando medición: {str(e)}")
            raise
    
    def save_measurement(self, data):
        """Guarda medición en ambas bases (SQLite primero, PostgreSQL después)"""
        try:
            # Incrementar contador de muestra para esta medición
            self.measurement_sample_counter += 1
            sample_index = self.measurement_sample_counter
            
            # 1. Guardar en SQLite inmediatamente (muy rápido)
            cursor = self.sqlite_conn.cursor()
            cursor.execute(queries["insert_cache_mediciones_sl"], (
                self.current_measurement_id,
                data.VoltajeEntrada,
                data.VoltajeDiodo,
                data.VoltajeSalida,
                data.CorrienteEntrada,
                data.CorrienteInductor,
                data.CorrienteDiodo,
                data.CorrienteSalida,
                data.PotenciaEntrada,
                data.PotenciaSalida
            ))
            self.sqlite_conn.commit()
            
            # 2. Guardar en PostgreSQL en background (asíncrono)
            self._save_to_postgres_async(data, sample_index)
            
            return sample_index
            
        except Exception as e:
            print(f"❌ Error guardando medición: {str(e)}")
            raise
    
    def _save_to_postgres_async(self, data, sample_index):
        """Guarda en PostgreSQL en segundo plano"""
        def save_task():
            try:
                with self.get_postgres_cursor() as cur:
                    # Insertar en VOLTAJES
                    cur.execute(queries["insert_voltajes_pg"], (
                        self.current_measurement_id,
                        data.VoltajeEntrada,
                        data.VoltajeDiodo,
                        data.VoltajeSalida
                    ))
                    
                    # Insertar en CORRIENTES
                    cur.execute(queries["insert_corrientes_pg"], (
                        self.current_measurement_id,
                        data.CorrienteEntrada,
                        data.CorrienteDiodo,
                        data.CorrienteInductor,
                        data.CorrienteSalida
                    ))
                    
                    # Insertar en POTENCIAS
                    cur.execute(queries["insert_potencias_pg"], (
                        self.current_measurement_id,
                        data.PotenciaEntrada,
                        data.PotenciaSalida
                    ))
                    
                    # Acvualiza Hora_Termino
                    cur.execute(queries["update_hora_termino_pg"], (self.current_measurement_id,))
                
                # Marcar como sincronizado en SQLite
                cursor = self.sqlite_conn.cursor()
                cursor.execute("UPDATE cache_mediciones SET synced = TRUE WHERE sample_index = ?", (sample_index,))
                self.sqlite_conn.commit()
                
            except Exception as e:
                print(f"⚠️ Error sincronizando con PostgreSQL: {str(e)}")
        
        threading.Thread(target=save_task, daemon=True).start()
    
    def get_recent_data(self, limit: int = 200, measurement_id: Optional[int] = None):
        """Obtiene datos recientes desde SQLite (muy rápido)"""
        try:
            cursor = self.sqlite_conn.cursor()
            
            if measurement_id:
                cursor.execute(queries["select_cache_med_desc_mid_sl"], (measurement_id, limit))
            else:
                cursor.execute(queries["select_cache_mediciones_sl"], (limit,))
            
            rows = cursor.fetchall()
            
            measurements = []
            for row in reversed(rows):
                measurements.append({
                    "rowid": row["sample_index"],
                    "measurement_id": row["measurement_id"],
                    "VoltajeEntrada": row["VoltajeEntrada"],
                    "VoltajeDiodo": row["VoltajeDiodo"],
                    "VoltajeSalida": row["VoltajeSalida"],
                    "CorrienteEntrada": row["CorrienteEntrada"],
                    "CorrienteInductor": row["CorrienteInductor"],
                    "CorrienteDiodo": row["CorrienteDiodo"],
                    "CorrienteSalida": row["CorrienteSalida"],
                    "PotenciaEntrada": row["PotenciaEntrada"],
                    "PotenciaSalida": row["PotenciaSalida"],
                    "timestamp": row["timestamp"],
                    "synced": bool(row["synced"])
                })
            
            return measurements
            
        except Exception as e:
            print(f"❌ Error obteniendo datos de SQLite: {str(e)}")
            return []
    
    def get_paginated_data(self, measurement_id: int, page: int = 1, page_size: int = 1000):
        """Obtiene datos paginados desde SQLite (muy rápido)"""
        try:
            offset = (page - 1) * page_size
            
            cursor = self.sqlite_conn.cursor()
            cursor.execute(queries["select_cache_med_asc_mid_sl"], (measurement_id, page_size, offset))
            
            rows = cursor.fetchall()
            
            # Contar total
            cursor.execute(queries["count_all_sl"], (measurement_id,))
            total_row = cursor.fetchone()
            total = total_row[0] if total_row else 0
            
            measurements = []
            for row in rows:
                measurements.append({
                    "rowid": row["sample_index"],
                    "measurement_id": row["measurement_id"],
                    "VoltajeEntrada": row["VoltajeEntrada"],
                    "VoltajeDiodo": row["VoltajeDiodo"],
                    "VoltajeSalida": row["VoltajeSalida"],
                    "CorrienteEntrada": row["CorrienteEntrada"],
                    "CorrienteInductor": row["CorrienteInductor"],
                    "CorrienteDiodo": row["CorrienteDiodo"],
                    "CorrienteSalida": row["CorrienteSalida"],
                    "PotenciaEntrada": row["PotenciaEntrada"],
                    "PotenciaSalida": row["PotenciaSalida"],
                    "timestamp": row["timestamp"],
                    "synced": bool(row["synced"])
                })
            
            return {
                "status": "ok",
                "measurements": measurements,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "pages": (total + page_size - 1) // page_size,
                    "has_more": offset + page_size < total
                }
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo datos paginados: {str(e)}")
            return {"status": "error", "message": str(e), "measurements": []}
    
    def get_measurement_from_postgres(self, measurement_id: int, page: int = 1, limit: int = 10000):
        """Obtiene datos históricos desde PostgreSQL"""
        try:
            with self.get_postgres_cursor() as cur:
                cur.execute(queries["select_historic_pg"], (measurement_id, limit))
                rows = cur.fetchall()
            
            measurements = []
            for row in rows:
                measurements.append({
                    "rowid": row["rowid"],
                    "measurement_id": measurement_id,
                    "VoltajeEntrada": float(row["voltajeentrada"]),
                    "VoltajeDiodo": float(row["voltajediodo"]),
                    "VoltajeSalida": float(row["voltajesalida"]),
                    "CorrienteEntrada": float(row["corrienteentrada"]),
                    "CorrienteInductor": float(row["corrienteinductor"]),
                    "CorrienteDiodo": float(row["corrientediodo"]),
                    "CorrienteSalida": float(row["corrientesalida"]),
                    "PotenciaEntrada": float(row["potenciaentrada"]),
                    "PotenciaSalida": float(row["potenciasalida"]),
                    "timestamp": row["marca_tiempo"]
                })
            
            offset = (page - 1) * page_size
            paginated_measurements = measurements[offset:offset + page_size]
        
            return {
                "status": "ok",
                "measurements": paginated_measurements,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": len(measurements),
                    "pages": (len(measurements) + page_size - 1) // page_size,
                    "has_more": offset + page_size < len(measurements)
                },
                "source": "postgresql"
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo datos de PostgreSQL: {str(e)}")
            return []
    
    def get_unsynced_data(self):
        """Obtiene datos no sincronizados con PostgreSQL"""
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute('''
                SELECT * FROM cache_mediciones 
                WHERE synced = FALSE 
                ORDER BY sample_index ASC
                LIMIT 1000
            ''')
            
            rows = cursor.fetchall()
            return rows
            
        except Exception as e:
            print(f"❌ Error obteniendo datos no sincronizados: {str(e)}")
            return []
    
    def sync_all_data(self):
        """Sincroniza todos los datos de SQLite a PostgreSQL"""
        unsynced = self.get_unsynced_data()
        
        for row in unsynced:
            try:
                with self.get_postgres_cursor() as cur:
                    # Insertar en VOLTAJES
                    voltaje_query = """
                        INSERT INTO VOLTAJES (ID_Mediciones, Entrada, Diodo, Salida, Marca_Tiempo)
                        VALUES (%s, %s, %s, %s, CURRENT_TIME)
                        RETURNING ID_Voltajes
                    """
                    cur.execute(voltaje_query, (
                        row["measurement_id"],
                        row["VoltajeEntrada"],
                        row["VoltajeDiodo"],
                        row["VoltajeSalida"]
                    ))
                    
                    # Insertar en CORRIENTES
                    corriente_query = """
                        INSERT INTO CORRIENTES (ID_Mediciones, Entrada, Diodo, Inductor, Salida, Marca_Tiempo)
                        VALUES (%s, %s, %s, %s, %s, CURRENT_TIME)
                    """
                    cur.execute(corriente_query, (
                        row["measurement_id"],
                        row["CorrienteEntrada"],
                        row["CorrienteDiodo"],
                        row["CorrienteInductor"],
                        row["CorrienteSalida"]
                    ))
                
                    # Insertar en POTENCIAS
                    potencias_query = """
                        INSERT INTO POTENCIAS (ID_Mediciones, Entrada, Salida)
                        VALUES (%s, %s, %s)
                    """
                    cur.execute(potencias_query, (
                        row["measurement_id"],
                        row["PotenciaEntrada"],
                        row["PotenciaSalida"]
                    ))
                
                cursor = self.sqlite_conn.cursor()
                cursor.execute("UPDATE cache_mediciones SET synced = TRUE WHERE sample_index = ?", 
                              (row["sample_index"],))
                self.sqlite_conn.commit()
                
            except Exception as e:
                print(f"⚠️ Error sincronizando sample {row['sample_index']}: {str(e)}")
        
        print(f"🎯 Sincronización completa. {len(unsynced)} muestras procesadas.")
    
    def cleanup_old_data(self, days_to_keep: int = 7):
        """Limpia datos antiguos de SQLite (ya sincronizados)"""
        try:
            cursor = self.sqlite_conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                DELETE FROM cache_mediciones 
                WHERE synced = TRUE AND timestamp < ?
            ''', (cutoff_str,))
            
            deleted_count = cursor.rowcount
            self.sqlite_conn.commit()
            
            cursor.execute('VACUUM')
            
            print(f"🧹 Limpiados {deleted_count} registros antiguos de SQLite")
            return deleted_count
            
        except Exception as e:
            print(f"❌ Error limpiando datos antiguos: {str(e)}")
            return 0
    
    def cleanup_all_data(self):
        """Limpia todos los datos de SQLite"""
        try:
            cursor = self.sqlite_conn.cursor()
            
            cursor.execute('''
                DELETE FROM cache_mediciones 
            ''')
            
            deleted_count = cursor.rowcount
            self.sqlite_conn.commit()
            
            cursor.execute('VACUUM')
            
            print(f"🧹 Limpiados {deleted_count} registros antiguos de SQLite")
            return deleted_count
            
        except Exception as e:
            print(f"Error limpiando datos antiguos: {str(e)}")
            return 0

    def end_measurement(self):
        try:
            with self.get_postgres_cursor() as cur:
                cur.execute(queries["update_hora_termino_pg"], (self.current_measurement_id,))
            
            print(f"Medición #{self.current_measurement_id} finalizada. Total muestras: {self.measurement_sample_counter}")
            
            self.current_measurement_id = None
            self.measurement_sample_counter = 0

        except Exception as e:
            print(f"Error terminando medición: {str(e)}")
            return 0

    def list_measurements(self):
        try:
            with self.get_postgres_cursor() as cur:
                cur.execute(queries["select_measurements_list"])
                rows = cur.fetchall()
            
            measurements = []
            for row in rows:
                measurements.append({
                    "id": row["id"],
                    "fecha": row["fecha"].isoformat() if row["fecha"] else None,
                    "hora_inicio": str(row["hora_inicio"]) if row["hora_inicio"] else None,
                    "hora_termino": str(row["hora_termino"]) if row["hora_termino"] else None,
                    "num_samples": row["num_samples"]
                })
            return {
                "status": "ok",
                "measurements": measurements,
                "total": len(measurements)
            }
            
        except Exception as e:
            print(f"Error listando mediciónes: {str(e)}")
            return 0

    def get_recent_data_from_db(self, limit=200):
        """Obtiene datos recientes desde PostgreSQL (para compatibilidad)"""
        try:
            with self.get_postgres_cursor() as cur:
                cur.execute("""
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
                    ORDER BY v.ID_Voltajes DESC
                    LIMIT %s
                """, (limit,))
                rows = cur.fetchall()
            
            measurements = []
            for row in reversed(rows):
                measurements.append({
                    "rowid": row["rowid"],
                    "VoltajeEntrada": float(row["voltajeentrada"]),
                    "VoltajeDiodo": float(row["voltajediodo"]),
                    "VoltajeSalida": float(row["voltajesalida"]),
                    "CorrienteEntrada": float(row["corrienteentrada"]),
                    "CorrienteInductor": float(row["corrienteinductor"]),
                    "CorrienteDiodo": float(row["corrientediodo"]),
                    "CorrienteSalida": float(row["corrientesalida"]),
                    "PotenciaEntrada": float(row["potenciaentrada"]),
                    "PotenciaSalida": float(row["potenciasalida"]),
                    "timestamp": row["marca_tiempo"]
                })
            
            return measurements
        except Exception as e:
            print(f"❌ Error obteniendo datos recientes: {str(e)}")
            return []
class AuxiliaresPG():
    # ----------------------------------------------------------------------
    # 🛠️ Funciones auxiliares para PostgreSQL (compatibilidad)
    # ----------------------------------------------------------------------
    @contextmanager
    def get_db_connection():
        """Context manager para obtener conexión a PostgreSQL"""
        conn = None
        try:
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            yield conn
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_db_cursor():
        """Context manager para obtener cursor PostgreSQL"""
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cur
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()
    
    def get_recent_data_from_db(self, limit=200):
        """Obtiene datos recientes desde PostgreSQL (para compatibilidad)"""
        try:
            with get_db_cursor() as cur:
                cur.execute("""
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
                    ORDER BY v.ID_Voltajes DESC
                    LIMIT %s
                """, (limit,))
                rows = cur.fetchall()
            
            measurements = []
            for row in reversed(rows):
                measurements.append({
                    "rowid": row["rowid"],
                    "VoltajeEntrada": float(row["voltajeentrada"]),
                    "VoltajeDiodo": float(row["voltajediodo"]),
                    "VoltajeSalida": float(row["voltajesalida"]),
                    "CorrienteEntrada": float(row["corrienteentrada"]),
                    "CorrienteInductor": float(row["corrienteinductor"]),
                    "CorrienteDiodo": float(row["corrientediodo"]),
                    "CorrienteSalida": float(row["corrientesalida"]),
                    "PotenciaEntrada": float(row["potenciaentrada"]),
                    "PotenciaSalida": float(row["potenciasalida"]),
                    "timestamp": row["marca_tiempo"]
                })
            
            return measurements
        except Exception as e:
            print(f"❌ Error obteniendo datos recientes: {str(e)}")
            return []