from dataclasses import dataclass
from typing import Dict, Optional
from services import rrhh_service
from datetime import date



@dataclass
class InputLiquidacion:
    periodo: str

    # Base trabajador
    sueldo_base: float
    haberes_imponibles: dict[str, float]
    haberes_no_imponibles: dict[str, float]
    imm: float  # 👈 obligatorio

    # Previsión
    afp_nombre: str 
    afp_tasa_txt: str 
    afp_tasa: float
    salud_porcentaje: float
    salud_plan_fijo: float | None

    # Retroactivo
    retro_antiguo: float
    retro_actual: float

    dias_trabajados: float = 0
    numero_horas_extras: float = 0
    observaciones: str = ""

@dataclass
class ResultadoLiquidacion:
    montos_por_concepto: dict[str, float]

    base_imponible: float
    base_tributable: float
    

    total_haberes_imponibles: float
    total_haberes_no_imponibles: float
    total_haberes: float

    total_descuentos_previsionales: float
    total_descuentos_otros: float
    total_descuentos_general: float

    liquido_pagar: float



class MotorCalculoLiquidacion:

    def calcular_gratificacion_mensual(self, sueldo_imponible: float, imm: float) -> float:
        if sueldo_imponible <= 0:
            return 0

        grat_25 = sueldo_imponible * 0.25
        tope_mensual = (4.75 * imm) / 12
        return round(min(grat_25, tope_mensual))


    def calcular(self, data: InputLiquidacion) -> ResultadoLiquidacion:

        retro = max(data.retro_actual - data.retro_antiguo, 0)

        total_impon_base = sum(data.haberes_imponibles.values())
        total_no_impon = sum(data.haberes_no_imponibles.values())

        gratificacion = self.calcular_gratificacion_mensual(
            sueldo_imponible=total_impon_base,
            imm=data.imm
        )

        total_imponible = total_impon_base + retro + gratificacion
        base_imponible = total_imponible
        total_haberes = total_imponible + total_no_impon

        monto_afp = round(base_imponible * data.afp_tasa)

        salud_legal = base_imponible * data.salud_porcentaje
        if data.salud_plan_fijo is not None:
            monto_salud = max(salud_legal, data.salud_plan_fijo)
            adicional_isapre = round(monto_salud - salud_legal)
        else:
            monto_salud = salud_legal
            adicional_isapre = 0

        monto_salud = round(monto_salud)

        total_desc_prev = monto_afp + monto_salud
        liquido = total_haberes - total_desc_prev

        # 👇 CÓDIGOS REALES DE BD
        montos = {
            "GRATIFICACION": gratificacion,
            "RETROACTIVO": retro,
            "FONDO_PENSIONES": monto_afp,
            "PREVISION_7": monto_salud,
            "ADICIONAL_ISAPRE": adicional_isapre,
        }

        return ResultadoLiquidacion(
            montos_por_concepto=montos,
            base_imponible=base_imponible,
            base_tributable=base_imponible,
            total_haberes_imponibles=total_imponible,
            total_haberes_no_imponibles=total_no_impon,
            total_haberes=total_haberes,
            total_descuentos_previsionales=total_desc_prev,
            total_descuentos_otros=0,
            total_descuentos_general=total_desc_prev,
            liquido_pagar=liquido,
        )



@dataclass
class ResultadoPersistenciaLiquidacion:
    datos_cabecera: dict
    detalle: dict
    snapshot: dict

class MotorPersistenciaLiquidacion:

    def __init__(self, rrhh_service):
        self.rrhh_service = rrhh_service

    def construir(
        self,
        data: InputLiquidacion,
        resultado: ResultadoLiquidacion,
        trabajador: dict,
        periodo: str
    ) -> ResultadoPersistenciaLiquidacion:

        datos_cabecera = {
            "trabajador_rut": trabajador["rut"],
            "periodo": periodo,
            "fecha_emision": date.today().isoformat(),

            "dias_trabajados": data.dias_trabajados,
            "numero_horas_extras": data.numero_horas_extras,

            "base_imponible": resultado.base_imponible,
            "base_tributable": resultado.base_tributable,

            "afp_id": trabajador.get("afp_id"),
            "afp_nombre": trabajador.get("afp_nombre"),
            "afp_tasa": data.afp_tasa,

            "sistema_salud_id": trabajador.get("sistema_salud_id"),
            "porcentaje_salud": data.salud_porcentaje,

            "retro_antiguo": data.retro_antiguo,
            "retro_actual": data.retro_actual,
            "retro_diferencia": max(data.retro_actual - data.retro_antiguo, 0),

            "observaciones": data.observaciones,
        }

        # 1) Obtener catálogo
        _, por_codigo = self.rrhh_service._obtener_catalogo_conceptos()

        if not por_codigo:
            raise ValueError("No se pudo obtener el catálogo de conceptos")

        # 2) Construir detalle con TODOS los haberes y descuentos
        detalle = []

        # 👉 Haberes imponibles (sueldo base, horas extras, bonos, etc)
        for codigo, monto in data.haberes_imponibles.items():
            if codigo not in por_codigo:
                raise ValueError(f"Concepto no existe en catálogo: {codigo}")

            detalle.append({
                "concepto_id": por_codigo[codigo]["id"],
                "monto": round(float(monto), 2)
            })

        # 👉 Haberes no imponibles
        for codigo, monto in data.haberes_no_imponibles.items():
            if codigo not in por_codigo:
                raise ValueError(f"Concepto no existe en catálogo: {codigo}")

            detalle.append({
                "concepto_id": por_codigo[codigo]["id"],
                "monto": round(float(monto), 2)
            })

        # 👉 Conceptos automáticos (gratificación, retroactivo, descuentos)
        for codigo, monto in resultado.montos_por_concepto.items():
            if codigo not in por_codigo:
                raise ValueError(f"Concepto no existe en catálogo: {codigo}")

            detalle.append({
                "concepto_id": por_codigo[codigo]["id"],
                "monto": round(float(monto), 2)
            })

        snapshot = {
            "input": {
                "haberes_imponibles": data.haberes_imponibles,
                "haberes_no_imponibles": data.haberes_no_imponibles,
                "afp_tasa": data.afp_tasa,
                "salud_porcentaje": data.salud_porcentaje,
                "salud_plan_fijo": data.salud_plan_fijo,
                "imm": data.imm,
            },
            "resultado": resultado.__dict__,
        }

        return ResultadoPersistenciaLiquidacion(
            datos_cabecera=datos_cabecera,
            detalle=detalle,
            snapshot=snapshot,
        )
