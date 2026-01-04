from services.finanzas_service import generar_excel_ffmm_anual

if __name__ == "__main__":
    anio = 2025
    mes = 12

    ruta = f"ffmm_{anio}_{mes:02d}.xlsx"

    generar_excel_ffmm_anual(anio, ruta)

    print("Excel FFMM generado:", ruta)