"""Solo casos HIPOTÉTICOS; ninguna prueba representa mediciones del domo."""
import pytest
from auditoria_2026.balances_diarios import (
    MinimoDeclarado, auditar_energia_24h, revisar_minimos_por_dia,
)


def _balance(rows):
    for x in rows:
        assert x.inventario_final_kwh == pytest.approx(
            x.inventario_inicial_kwh + x.generacion_disponible_kwh
            - x.energia_limitada_por_capacidad_kwh - x.energia_consumida_kwh
        )


def test_sin_recarga_se_agota_en_primer_dia():
    r = auditar_energia_24h(energia_inicial_kwh=3000, capacidad_almacenamiento_kwh=3000,
                            generacion_bruta_diaria_kwh=[0]*5, demanda_diaria_kwh=[3000]*5)
    assert [x.energia_consumida_kwh for x in r] == [3000, 0, 0, 0, 0]
    assert r[-1].demanda_no_cubierta_kwh == pytest.approx(3000)
    _balance(r)


def test_generacion_diaria_cubre_demanda_sin_agotar_bateria():
    r = auditar_energia_24h(energia_inicial_kwh=2, capacidad_almacenamiento_kwh=5,
                            generacion_bruta_diaria_kwh=[2]*5, demanda_diaria_kwh=[2]*5)
    assert all(x.demanda_no_cubierta_kwh == 0 for x in r)
    assert all(x.inventario_final_kwh == pytest.approx(2) for x in r)
    _balance(r)


def test_crisis_cuarenta_por_ciento_afecta_generacion_no_inventario():
    r = auditar_energia_24h(energia_inicial_kwh=2, capacidad_almacenamiento_kwh=5,
                            generacion_bruta_diaria_kwh=[3, 3], demanda_diaria_kwh=[2, 2],
                            reduccion_generacion=0.4)
    assert r[0].inventario_inicial_kwh == pytest.approx(2)
    assert [x.generacion_disponible_kwh for x in r] == pytest.approx([1.8, 1.8])
    assert r[-1].inventario_final_kwh == pytest.approx(1.6)
    _balance(r)


def test_limite_de_capacidad_desperdicia_excedente_de_la_generacion():
    r = auditar_energia_24h(energia_inicial_kwh=4, capacidad_almacenamiento_kwh=5,
                            generacion_bruta_diaria_kwh=[3], demanda_diaria_kwh=[2])
    assert r[0].energia_limitada_por_capacidad_kwh == pytest.approx(2)
    assert r[0].inventario_final_kwh == pytest.approx(3)
    _balance(r)


def test_reserva_protegida_no_se_consume():
    r = auditar_energia_24h(energia_inicial_kwh=2, capacidad_almacenamiento_kwh=5,
                            generacion_bruta_diaria_kwh=[0], demanda_diaria_kwh=[5],
                            reserva_protegida_kwh=1)
    assert r[0].energia_consumida_kwh == pytest.approx(1)
    assert r[0].inventario_final_kwh == pytest.approx(1)
    assert r[0].demanda_no_cubierta_kwh == pytest.approx(4)
    _balance(r)


def test_rechaza_configuraciones_invalidas():
    with pytest.raises(ValueError):
        auditar_energia_24h(energia_inicial_kwh=10, capacidad_almacenamiento_kwh=5,
                            generacion_bruta_diaria_kwh=[0], demanda_diaria_kwh=[1])
    with pytest.raises(ValueError):
        auditar_energia_24h(energia_inicial_kwh=1, capacidad_almacenamiento_kwh=5,
                            generacion_bruta_diaria_kwh=[2], demanda_diaria_kwh=[1],
                            reduccion_generacion=1.1)
    with pytest.raises(ValueError):
        auditar_energia_24h(energia_inicial_kwh=1, capacidad_almacenamiento_kwh=5,
                            generacion_bruta_diaria_kwh=[2], demanda_diaria_kwh=[1],
                            periodo_horas=12)


def _regla():
    return MinimoDeclarado(nodo="LECHUGAS_HIDROPONICAS", recurso="AGUA_L",
                           cantidad_por_dia=2.0, etapa="ensayo hipotético",
                           fuente="supuesto no validado", unidad="L/24h")


def test_minimo_por_dia_cumplido_es_factible_solo_bajo_supuestos():
    r = revisar_minimos_por_dia([_regla()], [{"LECHUGAS_HIDROPONICAS.AGUA_L": 3},
                                              {"LECHUGAS_HIDROPONICAS.AGUA_L": 2}])
    assert r.estado == "factible_bajo_supuestos"
    assert not r.infracciones


def test_no_factible_si_alguna_jornada_incumple_minimo():
    r = revisar_minimos_por_dia([_regla()], [{"LECHUGAS_HIDROPONICAS.AGUA_L": 3},
                                              {"LECHUGAS_HIDROPONICAS.AGUA_L": 1.5}])
    assert r.estado == "no_factible"
    assert "día 2" in r.infracciones[0]


def test_no_evaluable_sin_reglas_o_sin_asignaciones():
    assert revisar_minimos_por_dia([], [{"nodo.AGUA_L": 1}]).estado == "no_evaluable"
    assert revisar_minimos_por_dia([_regla()], [{}]).estado == "no_evaluable"


def test_no_permite_duplicados_ni_valores_no_finitos():
    with pytest.raises(ValueError):
        revisar_minimos_por_dia([_regla(), _regla()], [{"LECHUGAS_HIDROPONICAS.AGUA_L": 1}])
    with pytest.raises(ValueError):
        revisar_minimos_por_dia([_regla()], [{"LECHUGAS_HIDROPONICAS.AGUA_L": float('nan')}])


def test_motor_original_interpreta_crisis_como_recorte_de_inventario_inicial():
    """Caracteriza motor base: no hay generación energética periódica declarada."""
    from core.templates import get_templates
    from core.schemas import CrisisDef
    from core.genetic_algorithm import build_gene_mapping
    from core.simulation import simulate_preferences
    template = next(t.model_copy(deep=True) for t in get_templates()
                    if t.template_id == "domo_bioagricola_inteligente")
    template.crisis_factors = {"HIPOTESIS": CrisisDef(
        name="Recorte inicial del 40%", description="Prueba aislada",
        intensity=1, impact_resource={"ENERGIA_KWH": -0.4})}
    mapping = build_gene_mapping(template)
    resultado = simulate_preferences(
        template, {f"{nodo}.{recurso}": .95 for nodo, recurso in mapping})
    assert len(resultado.periods) == 5
    assert resultado.periods[0]["available_resources"]["ENERGIA_KWH"][0] == pytest.approx(3000)
    assert [x["available_resources"]["ENERGIA_KWH"][0] for x in resultado.periods[1:]] == pytest.approx([0] * 4)
