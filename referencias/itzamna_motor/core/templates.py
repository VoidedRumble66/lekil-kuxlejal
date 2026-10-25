from .schemas import DynamicTemplate

UNIVERSAL_TEMPLATE = {
    "template_id": "colonia_marciana_universal",
    "name": "Simulación Global de la Colonia",
    "description": "Simulación con estructura estricta en cascada para validar la jerarquía de recursos.",
    "crisis_factors": {},
    "resources": {
        "AGUA_L": {"value": 1000},
        "ENERGIA_KWH": {"value": 2000},
        "COMIDA_KG": {"value": 500},
        "ESTABILIDAD_SISTEMICA": {"value": 10}
    },
    "consumers": {
        "INVERNADERO": {
            "priority_weight": 0.8,
            "requirements": {
                "AGUA_L": {"value": 200},
                "ENERGIA_KWH": {"value": 300}
            },
            "subconsumers": {
                "CULTIVO_PAPAS": {
                    "priority_weight": 0.9,
                    "requirements": {
                        "AGUA_L": {"value": 150},
                        "ENERGIA_KWH": {"value": 150}
                    }
                },
                "CULTIVO_SOYA": {
                    "priority_weight": 0.7,
                    "requirements": {
                        "AGUA_L": {"value": 50},
                        "ENERGIA_KWH": {"value": 150}
                    }
                }
            }
        },
        "HABITAT": {
            "priority_weight": 0.95,
            "requirements": {
                "AGUA_L": {"value": 800},
                "ENERGIA_KWH": {"value": 1700},
                "COMIDA_KG": {"value": 500}
            },
            "subconsumers": {
                "AGUA_PARA_BEBER": {
                    "priority_weight": 1.0,
                    "requirements": {
                        "AGUA_L": {"value": 300}
                    }
                },
                "BUNKER_RADIACION": {
                    "priority_weight": 0.9,
                    "requirements": {
                        "AGUA_L": {"value": 100},
                        "ENERGIA_KWH": {"value": 500}
                    }
                },
                "CALEFACCION": {
                    "priority_weight": 0.85,
                    "requirements": {
                        "AGUA_L": {"value": 200},
                        "ENERGIA_KWH": {"value": 800}
                    }
                },
                "COMEDOR": {
                    "priority_weight": 0.95,
                    "requirements": {
                        "COMIDA_KG": {"value": 500}
                    }
                },
                "OPERACIONES_BASE_HABITAT": {
                    "priority_weight": 0.8,
                    "requirements": {
                        "AGUA_L": {"value": 200},
                        "ENERGIA_KWH": {"value": 400}
                    }
                }
            }
        }
    },
    "population_size": 200,
    "max_generations": 50,
    "emit_every_n": 5
}

def get_templates():
    DOMO_TEMPLATE = {
        "template_id": "domo_bioagricola_inteligente",
        "name": "Domo Bioagrícola Inteligente",
        "description": "Simulación de Domo con Biorremediación, Aislamiento Térmico y Gobernanza por IA.",
        "crisis_factors": {
            "OLA_DE_CALOR": {
                "name": "Ola de Calor Extrema",
                "description": "Aumenta el consumo de agua y energía térmica.",
                "intensity": 0.5,
                "impact_resource": {"AGUA_L": -0.2, "ENERGIA_KWH": -0.3}
            }
        },
        "resources": {
            "AGUA_L": {"value": 2000},
            "ENERGIA_KWH": {"value": 5000},
            "NUTRIENTES_KG": {"value": 300},
            "COMPUTO_TFLOPS": {"value": 100},
            "ESTABILIDAD_SISTEMICA": {"value": 10},
            "AHORRO_TERMICO": {"value": 0},
            "SUELO_RESTAURADO": {"value": 0},
            "BIOMASA_COMESTIBLE": {"value": 50}
        },
        "consumers": {
            "GOBERNANZA_IA": {
                "priority_weight": 1.0,
                "requirements": {
                    "ENERGIA_KWH": {"value": 500},
                    "COMPUTO_TFLOPS": {"value": 100}
                },
                "outputs": {
                    "ESTABILIDAD_SISTEMICA": {"amount_per_unit": 0.8, "efficiency": 0.9, "available_after_periods": 1}
                },
                "subconsumers": {}
            },
            "DOMO_BIOAGRICOLA": {
                "priority_weight": 0.9,
                "requirements": {
                    "AGUA_L": {"value": 1500},
                    "ENERGIA_KWH": {"value": 4000},
                    "NUTRIENTES_KG": {"value": 300}
                },
                "subconsumers": {
                    "AISLAMIENTO_TERMICO_PASIVO": {
                        "priority_weight": 0.9,
                        "requirements": {
                            "ENERGIA_KWH": {"value": 500}
                        },
                        "outputs": {
                            "AHORRO_TERMICO": {"amount_per_unit": 0.5, "efficiency": 0.95, "available_after_periods": 1}
                        }
                    },
                    "BIORREMEDIACION_SUELO": {
                        "priority_weight": 0.85,
                        "requirements": {
                            "AGUA_L": {"value": 500},
                            "NUTRIENTES_KG": {"value": 200}
                        },
                        "outputs": {
                            "SUELO_RESTAURADO": {"amount_per_unit": 0.6, "efficiency": 0.8, "available_after_periods": 2}
                        }
                    },
                    "SISTEMA_INVERNADEROS": {
                        "priority_weight": 0.95,
                        "requirements": {
                            "AGUA_L": {"value": 800},
                            "ENERGIA_KWH": {"value": 1000},
                            "NUTRIENTES_KG": {"value": 100}
                        },
                        "subconsumers": {
                            "JARDINERA_NORTE_HIDROPONIA": {
                                "priority_weight": 0.9,
                                "requirements": {
                                    "AGUA_L": {"value": 400},
                                    "ENERGIA_KWH": {"value": 600},
                                    "NUTRIENTES_KG": {"value": 40}
                                },
                                "subconsumers": {
                                    "TOMATES_CHERRY": {
                                        "priority_weight": 0.8,
                                        "requirements": {
                                            "AGUA_L": {"value": 250},
                                            "ENERGIA_KWH": {"value": 400},
                                            "NUTRIENTES_KG": {"value": 30}
                                        },
                                        "outputs": {
                                            "BIOMASA_COMESTIBLE": {"amount_per_unit": 0.3, "efficiency": 0.85, "available_after_periods": 3}
                                        }
                                    },
                                    "LECHUGAS_HIDROPONICAS": {
                                        "priority_weight": 0.9,
                                        "requirements": {
                                            "AGUA_L": {"value": 150},
                                            "ENERGIA_KWH": {"value": 200},
                                            "NUTRIENTES_KG": {"value": 10}
                                        },
                                        "outputs": {
                                            "BIOMASA_COMESTIBLE": {"amount_per_unit": 0.2, "efficiency": 0.9, "available_after_periods": 2}
                                        }
                                    }
                                }
                            },
                            "JARDINERA_SUR_SUELO": {
                                "priority_weight": 0.85,
                                "requirements": {
                                    "AGUA_L": {"value": 400},
                                    "ENERGIA_KWH": {"value": 400},
                                    "NUTRIENTES_KG": {"value": 60}
                                },
                                "subconsumers": {
                                    "ZANAHORIAS": {
                                        "priority_weight": 0.8,
                                        "requirements": {
                                            "AGUA_L": {"value": 200},
                                            "ENERGIA_KWH": {"value": 200},
                                            "NUTRIENTES_KG": {"value": 30}
                                        },
                                        "outputs": {
                                            "BIOMASA_COMESTIBLE": {"amount_per_unit": 0.3, "efficiency": 0.8, "available_after_periods": 4}
                                        }
                                    },
                                    "RABANOS": {
                                        "priority_weight": 0.85,
                                        "requirements": {
                                            "AGUA_L": {"value": 200},
                                            "ENERGIA_KWH": {"value": 200},
                                            "NUTRIENTES_KG": {"value": 30}
                                        },
                                        "outputs": {
                                            "BIOMASA_COMESTIBLE": {"amount_per_unit": 0.2, "efficiency": 0.85, "available_after_periods": 2}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "benefit_values": {
            "ESTABILIDAD_SISTEMICA": {"unit_value": 100.0, "target_demand": 50.0, "critical": False, "minimum_reserve": 10.0},
            "AHORRO_TERMICO": {"unit_value": 30.0, "target_demand": 100.0, "critical": False, "minimum_reserve": 0.0},
            "SUELO_RESTAURADO": {"unit_value": 50.0, "target_demand": 100.0, "critical": False, "minimum_reserve": 0.0},
            "BIOMASA_COMESTIBLE": {"unit_value": 200.0, "target_demand": 150.0, "critical": False, "minimum_reserve": 50.0}
        },
        "population_size": 200,
        "max_generations": 50,
        "emit_every_n": 5
    }

    return [
        DynamicTemplate(**UNIVERSAL_TEMPLATE),
        DynamicTemplate(**DOMO_TEMPLATE)
    ]
