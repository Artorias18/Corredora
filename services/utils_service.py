def validar_rut(rut: str) -> bool:
    """
    Valida un RUT chileno usando el cálculo oficial del dígito verificador.
    Retorna True si el RUT es válido, False si no.
    """
    if not rut:
        return False

    rut = rut.replace(".", "").replace("-", "").upper()
    if len(rut) < 2:
        return False

    cuerpo = rut[:-1]
    dv = rut[-1]

    if not cuerpo.isdigit():
        return False

    suma = 0
    multiplicador = 2

    for c in reversed(cuerpo):
        suma += int(c) * multiplicador
        multiplicador += 1
        if multiplicador > 7:
            multiplicador = 2

    resto = suma % 11
    dv_calculado = 11 - resto

    if dv_calculado == 11:
        dv_calculado = "0"
    elif dv_calculado == 10:
        dv_calculado = "K"
    else:
        dv_calculado = str(dv_calculado)

    return dv == dv_calculado
