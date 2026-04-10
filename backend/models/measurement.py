from    pydantic    import  BaseModel

# Modelo de datos recibido
class Measurement(BaseModel):
    VoltajeEntrada: float
    VoltajeDiodo: float
    VoltajeSalida: float
    CorrienteEntrada: float
    CorrienteInductor: float
    CorrienteDiodo: float
    CorrienteSalida: float
    PotenciaEntrada: float
    PotenciaSalida: float
