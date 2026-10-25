import numpy as np
from typing import Tuple, List, Dict
from .schemas import DynamicTemplate, ConsumerDef

def _build_mapping_recursive(consumers: Dict[str, 'ConsumerDef'], parent_path: str = "") -> List[Tuple[str, str]]:
    mapping = []
    for c_name, consumer in consumers.items():
        current_path = f"{parent_path}.{c_name}" if parent_path else c_name
        for r_name in consumer.requirements.keys():
            mapping.append((current_path, r_name))
        mapping.extend(_build_mapping_recursive(consumer.subconsumers, current_path))
    return mapping

def build_gene_mapping(template: DynamicTemplate) -> List[Tuple[str, str]]:
    """Returns a list of (consumer_path, resource_name) for each gene."""
    return _build_mapping_recursive(template.consumers)

def decode_to_absolute(
    genes: np.ndarray,
    template: DynamicTemplate,
    mapping: List[Tuple[str, str]],
    available_resources: Dict[str, np.ndarray] | None = None,
) -> np.ndarray:
    """Decodes proportional [0,1] genes into absolute allocations using top-down hierarchical distribution."""
    pop_size = len(genes)
    abs_pop = np.zeros_like(genes)
    
    # 1. Total available resources at root (accounting for crises)
    resource_pools = {}
    for r_name, r_def in template.resources.items():
        base_val = r_def.value
        total_impact = 0.0
        if template.crisis_factors:
            for crisis in template.crisis_factors.values():
                if crisis.impact_resource and r_name in crisis.impact_resource:
                    total_impact += crisis.intensity * crisis.impact_resource[r_name]
        if available_resources is not None and r_name in available_resources:
            resource_pools[r_name] = np.broadcast_to(available_resources[r_name], (pop_size,)).copy()
        else:
            resource_pools[r_name] = np.full(pop_size, max(0.0, base_val * (1.0 + total_impact)))
        
    def distribute(consumers: Dict[str, ConsumerDef], pools: Dict[str, np.ndarray], parent_path: str = ""):
        child_pools = {c_name: {} for c_name in consumers.keys()}
        
        for r_name, pool in pools.items():
            children_req = [(c_name, c) for c_name, c in consumers.items() if c.requirements and r_name in c.requirements]
            if not children_req: continue
            
            weights = []
            gene_indices = []
            for c_name, consumer in children_req:
                path = f"{parent_path}.{c_name}" if parent_path else c_name
                idx = mapping.index((path, r_name))
                gene_indices.append(idx)
                # Priority (0.0 to 1.0) dictates the weight of the request
                weights.append(genes[:, idx] * consumer.priority_weight)
                
            weights = np.column_stack(weights)
            sum_weights = np.sum(weights, axis=1)
            # If sum > 1.0, scale down. If sum <= 1.0, they get the exact percentage they asked for.
            norm_factor = np.maximum(1.0, sum_weights)
            
            for i, (c_name, consumer) in enumerate(children_req):
                alloc = pool * (weights[:, i] / norm_factor)
                abs_pop[:, gene_indices[i]] = alloc
                child_pools[c_name][r_name] = alloc
                
        # Recurse to subconsumers
        for c_name, consumer in consumers.items():
            if consumer.subconsumers and child_pools[c_name]:
                path = f"{parent_path}.{c_name}" if parent_path else c_name
                distribute(consumer.subconsumers, child_pools[c_name], path)
                
    distribute(template.consumers, resource_pools)
    return abs_pop

class GeneticAlgorithm:
    def __init__(self, template: DynamicTemplate):
        self.template = template
        self.pop_size = template.population_size
        self.mutation_rate = template.mutation_rate
        self.mutation_strength = template.mutation_strength
        self.crossover_rate = template.crossover_rate
        self.elitism_count = min(template.elitism_count, max(1, self.pop_size - 1))
        self.tournament_size = min(template.tournament_size, self.pop_size)
        self.mapping = build_gene_mapping(template)
        self.num_genes = len(self.mapping)
        self.population = np.zeros((self.pop_size, self.num_genes))
        self.fitness = np.zeros(self.pop_size)
        self.generation = 0

    def _evaluate(self, pop: np.ndarray):
        from .fitness import evaluate_population
        abs_pop = decode_to_absolute(pop, self.template, self.mapping)
        return evaluate_population(abs_pop, self.template, self.mapping, gene_population=pop)

    def initialize_population(self):
        # Genes represent proportional allocation (0.0 to 1.0)
        self.population = np.random.uniform(0.0, 1.0, (self.pop_size, self.num_genes))
        self.fitness, self.viable_mask = self._evaluate(self.population)

    def evolve_one_generation(self):
        new_population = np.zeros_like(self.population)
        
        # Preserve the configured number of strongest individuals.
        elite_indices = np.argsort(self.fitness)[-self.elitism_count:][::-1]
        new_population[:self.elitism_count] = self.population[elite_indices]
        
        # Fill the rest
        for i in range(self.elitism_count, self.pop_size):
            p1 = self._tournament_select()
            p2 = self._tournament_select()
            child = self._crossover(self.population[p1], self.population[p2])
            child = self._mutate(child)
            new_population[i] = child
            
        self.population = new_population
        self.fitness, self.viable_mask = self._evaluate(self.population)
        self.generation += 1

    def _tournament_select(self) -> int:
        idx = np.random.choice(self.pop_size, self.tournament_size, replace=False)
        return idx[np.argmax(self.fitness[idx])]

    def _crossover(self, p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
        if np.random.random() > self.crossover_rate:
            return p1.copy()
        alpha = np.random.uniform(0, 1)
        return alpha * p1 + (1 - alpha) * p2

    def _mutate(self, ind: np.ndarray) -> np.ndarray:
        if np.random.random() < self.mutation_rate:
            ind += np.random.normal(0, self.mutation_strength, self.num_genes)
            ind = np.clip(ind, 0.0, 1.0)
        return ind

    def get_avg_fitness(self) -> float:
        return float(np.mean(self.fitness))

    def get_max_fitness(self) -> float:
        return float(np.max(self.fitness))
        
    def get_viable_count(self) -> int:
        return int(np.sum(self.viable_mask))
