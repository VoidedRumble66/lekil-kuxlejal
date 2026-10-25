"""Auditoría EXTERNA de supuestos diarios: NO modifica el motor genético.

Todas las cantidades proceden del llamador y no representan telemetría.
La generación se acredita una vez al inicio de cada periodo de 24 h;
el modelo no representa la potencia instantánea ni las horas de oscuridad.
"""
from dataclasses import dataclass
from math import isfinite
from typing import Mapping, Sequence


@dataclass(frozen=True)
class DiaEnergia:
    dia: int
    inventario_inicial_kwh: float
    generacion_bruta_kwh: float
    generacion_disponible_kwh: float
    energia_limitada_por_capacidad_kwh: float
    energia_consumida_kwh: float
    demanda_no_cubierta_kwh: float
    inventario_final_kwh: float


def _numero_no_negativo(value: float, nombre: str) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{nombre} debe ser numérico") from exc
    if not isfinite(value) or value < 0:
        raise ValueError(f"{nombre} debe ser finito y no negativo")
    return value


def auditar_energia_24h(
    *,
    energia_inicial_kwh: float,
    capacidad_almacenamiento_kwh: float,
    generacion_bruta_diaria_kwh: Sequence[float],
    demanda_diaria_kwh: Sequence[float],
    reduccion_generacion: float = 0.0,
    reserva_protegida_kwh: float = 0.0,
    periodo_horas: int = 24,
) -> list[DiaEnergia]:
    """Balance diario de una batería hipotética.

    La energía solar entra en un inventario limitado antes de atender cargas.
    Eso deliberadamente NO representa consumo solar instantáneo directo.
    """
    if periodo_horas != 24:
        raise ValueError("Auditoría 2026 configurada para periodos de 24 horas")
    inicial = _numero_no_negativo(energia_inicial_kwh, "energia_inicial_kwh")
    capacidad = _numero_no_negativo(capacidad_almacenamiento_kwh, "capacidad_almacenamiento_kwh")
    reserva = _numero_no_negativo(reserva_protegida_kwh, "reserva_protegida_kwh")
    reduccion = _numero_no_negativo(reduccion_generacion, "reduccion_generacion")
    if reduccion > 1:
        raise ValueError("reduccion_generacion debe estar entre 0 y 1")
    if inicial > capacidad or reserva > capacidad:
        raise ValueError("Inventario inicial y reserva no pueden superar la capacidad")
    if not generacion_bruta_diaria_kwh or len(generacion_bruta_diaria_kwh) != len(demanda_diaria_kwh):
        raise ValueError("Se requiere el mismo número de días de generación y demanda")

    inventario = inicial
    resultados: list[DiaEnergia] = []
    for i, (generation, demand) in enumerate(zip(generacion_bruta_diaria_kwh, demanda_diaria_kwh), start=1):
        bruta = _numero_no_negativo(generation, f"generacion dia {i}")
        demanda = _numero_no_negativo(demand, f"demanda dia {i}")
        generacion = bruta * (1.0 - reduccion)
        sin_tope = inventario + generacion
        disponible = min(capacidad, sin_tope)
        vertido = max(0.0, sin_tope - disponible)
        consumible = max(0.0, disponible - reserva)
        consumo = min(demanda, consumible)
        restante = disponible - consumo
        resultados.append(DiaEnergia(i, inventario, bruta, generacion, vertido, consumo,
                                    demanda - consumo, restante))
        inventario = restante
    return resultados


@dataclass(frozen=True)
class MinimoDeclarado:
    nodo: str
    recurso: str
    cantidad_por_dia: float
    etapa: str
    fuente: str
    unidad: str

    def __post_init__(self):
        if not self.nodo or not self.recurso or not self.etapa or not self.unidad or not self.fuente:
            raise ValueError("El mínimo exige nodo, recurso, etapa, unidad y procedencia")
        _numero_no_negativo(self.cantidad_por_dia, f"minimo de {self.nodo}.{self.recurso}")

    @property
    def clave(self) -> str:
        return f"{self.nodo}.{self.recurso}"


@dataclass(frozen=True)
class RevisionMinimos:
    estado: str  # no_evaluable / factible_bajo_supuestos / no_factible
    infracciones: tuple[str, ...]
    faltantes: tuple[str, ...]


def revisar_minimos_por_dia(
    reglas: Sequence[MinimoDeclarado],
    asignaciones_por_dia: Sequence[Mapping[str, float]],
) -> RevisionMinimos:
    """Valida propuestas dadas, NO genera asignaciones ni deduce valores del ESP32.

    El mínimo se compara con cada día. Si falta una lectura/asignación, no se
    interpreta automáticamente como cero (no puede certificarse factibilidad).
    """
    if not reglas or not asignaciones_por_dia:
        return RevisionMinimos("no_evaluable", (), ("sin mínimos o sin periodos definidos",))
    if len({r.clave for r in reglas}) != len(reglas):
        raise ValueError("Mínimos repetidos para el mismo nodo y recurso")
    incumplimientos: list[str] = []
    ausencias: list[str] = []
    for day, asignaciones in enumerate(asignaciones_por_dia, 1):
        for regla in reglas:
            if regla.clave not in asignaciones:
                ausencias.append(f"día {day}: no se informó {regla.clave}")
                continue
            asignada = _numero_no_negativo(asignaciones[regla.clave], f"asignación día {day}: {regla.clave}")
            if asignada + 1e-8 < regla.cantidad_por_dia:
                incumplimientos.append(
                    f"día {day}: {regla.clave}: {asignada:g} {regla.unidad} < "
                    f"mínimo declarado {regla.cantidad_por_dia:g} {regla.unidad} ({regla.fuente})"
                )
    estado = ("no_factible" if incumplimientos else
              "no_evaluable" if ausencias else "factible_bajo_supuestos")
    return RevisionMinimos(estado, tuple(incumplimientos), tuple(ausencias))
