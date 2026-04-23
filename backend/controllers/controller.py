samplingTime: int = 1
timeUnit: str = "s"

class CL_CONTROLLER():
    def __init__(self, obj_db):
        self.obj_db = obj_db
    
    def esp32_data(self, data):
        """Recibe datos de la ESP32"""
        try:
            if self.obj_db.current_measurement_id is None:
                return {
                    "status": "rejected",
                    "message": "No hay una medición activa. Los datos han sido ignorados."
                }
            
            sample_index = self.obj_db.save_measurement(data)
            
            return {
                "status": "ok",
                "measurement_id": self.obj_db.current_measurement_id,
                "sample_index": sample_index,
                "total_samples": self.obj_db.measurement_sample_counter
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_data(self, limit: int = 200):
        """Obtiene datos para las gráficas"""
        try:
            # Primero intentar desde SQLite
            measurements = self.obj_db.get_recent_data(limit)
            
            if measurements:
                return {
                    "event": "new_measurement",
                    "measurements": measurements,
                    "count": len(measurements),
                    "last_update": measurements[-1]["rowid"] if measurements else None,
                    "source": "sqlite_cache"
                }
            else:
                # Fallback a PostgreSQL
                data = self.obj_db.get_recent_data_from_db(limit)
                return {
                    "event": "new_measurement",
                    "measurements": data[-limit:] if len(data) > limit else data,
                    "count": len(data),
                    "last_update": data[-1]["rowid"] if data else None,
                    "source": "postgresql"
                }
            
        except Exception as e:
            print(f"?Error en /data: {str(e)}")
            return {
                "event": "new_measurement",
                "measurements": [],
                "count": 0,
                "last_update": None,
                "error": str(e)
            }
    
    def get_measurement_data_paginated(self,
        measurement_id: int,
        page: int = 1,
        page_size: int = 1000,
        use_cache: bool = True):
        """Obtiene datos de medición paginados"""
        try:
            # Primero intentar desde SQLite
            if use_cache:
                result = self.obj_db.get_paginated_data(measurement_id, page, page_size)
                
                if result.get("status") == "ok" and result["measurements"]:
                    result["source"] = "sqlite_cache"
                    return result
            
            # Si no hay datos en cache, obtener de PostgreSQL
            measurements = self.obj_db.get_measurement_from_postgres(measurement_id, page, page_size)
            
            return measurements
            
        except Exception as e:
            return {"status": "error", "message": str(e), "measurements": []}
    
    def start_measurement(self):
        """Inicia una nueva medición"""
        try:
            if self.obj_db.current_measurement_id is None:
                measurement_id = self.obj_db.start_measurement()
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
            if self.obj_db.current_measurement_id is None:
                print("Aviso: Intento de cerrar medición, pero no hay ninguna activa.")
                return {
                    "status": "rejected",
                    "message": "No hay una medición activa."
                }
            
            self.obj_db.sync_all_data()
            
            measurement_id = self.obj_db.current_measurement_id
            total_samples = self.obj_db.measurement_sample_counter
            
            self.obj_db.end_measurement()
            
            return {
                "status": "measurement_closed",
                "measurement_id": measurement_id,
                "total_samples": total_samples
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def put_sampling_time(self, samplingTime, timeUnit):
        try:
            self.samplingTime = samplingTime
            self.timeUnit = timeUnit
            return {"status": "ok", "message": "sampleTime_updated"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_sampling_time(self):
        try:
            return {"event": "response_sample_time", "status": "ok", "samplingTime": self.samplingTime, "timeUnit": self.timeUnit }
        except Exception as e:
            return {"event": "response_sample_time", "status": "error", "message": str(e)}
        
    def delete_measurement_sample(self, measurement_id: int):
        """Elimina una medicion por su ID"""
        try:
            # El parámetro de la consulta debe ser una tupla: (measurement_id,)
            parametro = (measurement_id,)
            
            with self.obj_db.get_postgres_cursor() as cur:
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
                
                self.obj_db.current_measurement_id = None
                
            return {
                "status": "ok",
                "message": f"Medición con ID {measurement_id} eliminada correctamente."
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def list_measurements(self):
        """Lista todas las mediciones"""
        try:
            return self.obj_db.list_measurements()
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    