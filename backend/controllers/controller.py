

class Controller():
    def __init__(self, db):
        self.db = db
    
    def esp32_data(self, data):
        """Recibe datos de la ESP32"""
        try:
            if db.current_measurement_id is None:
                return {
                    "status": "rejected",
                    "message": "No hay una medición activa. Los datos han sido ignorados."
                }
            
            sample_index = db.save_measurement(data)
            
            return {
                "status": "ok",
                "measurement_id": db.current_measurement_id,
                "sample_index": sample_index,
                "total_samples": db.measurement_sample_counter
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def start_measurement():
        """Inicia una nueva medición"""
        try:
            if db.current_measurement_id is None:
                measurement_id = db.start_measurement()
                return {"status": "ok", "measurement_id": measurement_id}
            else:
                return {
                    "status": "rejected",
                    "message": "Ya hay una medición activa."
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def end_measurement():
        """Finaliza la medición actual"""
        try:
            if db.current_measurement_id is None:
                print("Aviso: Intento de cerrar medición, pero no hay ninguna activa.")
                return {
                    "status": "rejected",
                    "message": "No hay una medición activa."
                }
            
            db.sync_all_data()
            
            measurement_id = db.current_measurement_id
            total_samples = db.measurement_sample_counter
            
            db.end_measurement()
            
            return {
                "status": "measurement_closed",
                "measurement_id": measurement_id,
                "total_samples": total_samples
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def delete_measurement_sample(measurement_id: int):
        """Elimina una medicion por su ID"""
        try:
            # El parámetro de la consulta debe ser una tupla: (measurement_id,)
            parametro = (measurement_id,)
            
            with db.get_postgres_cursor() as cur:
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
                
                db.current_measurement_id = None
                
            return {
                "status": "ok",
                "message": f"Medición con ID {measurement_id} eliminada correctamente."
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    