

class CL_CONTROLLER():
    def __init__(self, db):
        self.db = db
    
    def esp32_data(self, data):
        """Recibe datos de la ESP32"""
        try:
            if self.db.current_measurement_id is None:
                return {
                    "status": "rejected",
                    "message": "No hay una medición activa. Los datos han sido ignorados."
                }
            
            sample_index = self.db.save_measurement(data)
            
            return {
                "status": "ok",
                "measurement_id": self.db.current_measurement_id,
                "sample_index": sample_index,
                "total_samples": self.db.measurement_sample_counter
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_data(limit: int = 200):
        """Obtiene datos para las gráficas"""
        try:
            # Primero intentar desde SQLite
            measurements = self.db.get_recent_data(limit)
            
            if measurements:
                return {
                    "measurements": measurements,
                    "count": len(measurements),
                    "last_update": measurements[-1]["rowid"] if measurements else None,
                    "source": "sqlite_cache"
                }
            else:
                # Fallback a PostgreSQL
                data = self.db.get_recent_data_from_db(limit)
                return {
                    "measurements": data[-limit:] if len(data) > limit else data,
                    "count": len(data),
                    "last_update": data[-1]["rowid"] if data else None,
                    "source": "postgresql"
                }
            
        except Exception as e:
            print(f"?Error en /data: {str(e)}")
            return {
                "measurements": [],
                "count": 0,
                "last_update": None,
                "error": str(e)
            }
    
    def start_measurement(self):
        """Inicia una nueva medición"""
        try:
            if self.db.current_measurement_id is None:
                measurement_id = self.db.start_measurement()
                return {"status": "ok", "measurement_id": measurement_id}
            else:
                return {
                    "status": "rejected",
                    "message": "Ya hay una medición activa."
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def end_measurement(self):
        """Finaliza la medición actual"""
        try:
            if self.db.current_measurement_id is None:
                print("Aviso: Intento de cerrar medición, pero no hay ninguna activa.")
                return {
                    "status": "rejected",
                    "message": "No hay una medición activa."
                }
            
            self.db.sync_all_data()
            
            measurement_id = self.db.current_measurement_id
            total_samples = self.db.measurement_sample_counter
            
            self.db.end_measurement()
            
            return {
                "status": "measurement_closed",
                "measurement_id": measurement_id,
                "total_samples": total_samples
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def delete_measurement_sample(self, measurement_id: int):
        """Elimina una medicion por su ID"""
        try:
            # El parámetro de la consulta debe ser una tupla: (measurement_id,)
            parametro = (measurement_id,)
            
            with self.db.get_postgres_cursor() as cur:
                # 1. Eliminar de VOLTAJES
                delete_voltajes = """
                    DELETE FROM VOLTAJES
                    WHERE ID_Mediciones = %s
                """
                cur.execute(delete_voltajes, parametro)
                
                # 2. Eliminar de CORRIENTES
                delete_corrientes = """
                    DELETE FROM CORRIENTES
                    WHERE ID_Mediciones = %s
                """
                cur.execute(delete_corrientes, parametro)
                
                # 3. Eliminar de POTENCIAS
                delete_potencias= """
                    DELETE FROM POTENCIAS
                    WHERE ID_Mediciones = %s
                """
                cur.execute(delete_potencias, parametro)
                
                # 4. Eliminar de MEDICIONES (la tabla principal)
                delete_medicion = """
                    DELETE FROM MEDICIONES
                    WHERE ID_Mediciones = %s
                """
                cur.execute(delete_medicion, parametro)
                
                self.db.current_measurement_id = None
                
            return {
                "status": "ok",
                "message": f"Medición con ID {measurement_id} eliminada correctamente."
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def list_measurements(self):
        """Lista todas las mediciones"""
        try:
            return self.db.list_measurements()
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    