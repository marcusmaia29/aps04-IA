"""Lógica do problema do entregador: estado, sucessores, custos, mundo e busca."""

import random

from aigyminsper.search.graph import State
from aigyminsper.search.search_algorithms import BuscaCustoUniforme

BASE_COST = 1
TOLL_EXTRA = 2
MAX_OBSTACLE_RATIO = 0.35
MAX_TOLL_RATIO = 0.20

MOVES = {
    "cima": (-1, 0),
    "baixo": (1, 0),
    "esquerda": (0, -1),
    "direita": (0, 1),
}


def cell_cost(world, row, col):
    """Custo de executar uma ação estando na célula (row, col)."""
    if (row, col) in world["tolls"]:
        return BASE_COST + TOLL_EXTRA
    return BASE_COST


class DeliveryState(State):
    """Parte dinâmica do problema: posição do agente e situação do pacote.

    O mapa (dimensão, obstáculos, pedágios, pacote e destino) fica em `world`,
    que é compartilhado por todos os estados e nunca é alterado.
    """

    def __init__(self, world, row, col, has_package, delivered, op, step_cost):
        super().__init__(op)
        self.world = world
        self.row = row
        self.col = col
        self.has_package = has_package
        self.delivered = delivered
        self.step_cost = step_cost

    def successors(self):
        successors = []
        pos = (self.row, self.col)

        # Movimentos contra borda/obstáculo deixariam o agente no mesmo estado
        # com custo positivo; esses auto-loops nunca melhoram uma solução
        # ótima, por isso não são gerados.
        for action, (d_row, d_col) in MOVES.items():
            row, col = self.row + d_row, self.col + d_col
            if self.is_free(row, col):
                successors.append(self.next_state(row, col, self.has_package, self.delivered, action))

        if not self.has_package and not self.delivered and pos == self.world["package"]:
            successors.append(self.next_state(self.row, self.col, True, False, "pegar pacote"))

        if self.has_package and pos == self.world["destination"]:
            successors.append(self.next_state(self.row, self.col, False, True, "entregar pacote"))

        return successors

    def next_state(self, row, col, has_package, delivered, op):
        # Pelo enunciado, o pedágio é cobrado da ação executada SOBRE a célula
        # (célula de origem). Aqui o mesmo valor é cobrado ao ENTRAR na célula.
        # Como o agente começa e termina em células sem pedágio, as duas formas
        # dão exatamente o mesmo custo total para qualquer plano completo.
        # Precisamos desta forma porque o pruning="general" da aigyminsper
        # descarta um estado já gerado; isso só preserva a solução ótima se o
        # custo de chegar ao estado depender apenas do próprio estado.
        step_cost = cell_cost(self.world, row, col)
        return DeliveryState(self.world, row, col, has_package, delivered, op, step_cost)

    def is_free(self, row, col):
        n = self.world["n"]
        return 0 <= row < n and 0 <= col < n and (row, col) not in self.world["obstacles"]

    def is_goal(self):
        return self.delivered

    def cost(self):
        return self.step_cost

    def env(self):
        return (self.row, self.col, self.has_package, self.delivered)

    def description(self):
        return "Entregador em grid com obstáculos e pedágios"

    def __str__(self):
        return f"{self.operator} -> ({self.row}, {self.col}) pacote={self.has_package} entregue={self.delivered}"


def generate_world(n):
    """Gera um mundo aleatório N x N. O mundo pode não ter solução."""
    if n < 2:
        raise ValueError("A dimensão deve ser pelo menos 2.")

    cells = [(row, col) for row in range(n) for col in range(n)]
    random.shuffle(cells)

    agent, package, destination = cells[0], cells[1], cells[2]
    free_cells = cells[3:]

    n_obstacles = random.randint(0, int(n * n * MAX_OBSTACLE_RATIO))
    obstacles = set(free_cells[:n_obstacles])

    remaining = free_cells[n_obstacles:]
    n_tolls = random.randint(0, int(n * n * MAX_TOLL_RATIO))
    tolls = set(remaining[:n_tolls])

    return {
        "n": n,
        "agent": agent,
        "package": package,
        "destination": destination,
        "obstacles": obstacles,
        "tolls": tolls,
    }


def solve(world):
    """Executa a Busca de Custo Uniforme. Retorna None se não houver solução."""
    # Garantido por generate_world; necessário para a equivalência de custos acima.
    assert world["agent"] not in world["tolls"] and world["destination"] not in world["tolls"]

    row, col = world["agent"]
    initial = DeliveryState(world, row, col, False, False, "inicio", 0)
    node = BuscaCustoUniforme().search(initial, pruning="general")
    if node is None:
        return None

    total_cost = node.g  # custo acumulado calculado pela própria aigyminsper

    # Reconstrói o plano subindo pelos pais do nó objetivo.
    actions = []
    cells = []
    while node.father_node is not None:
        actions.append(node.state.operator)
        cells.append((node.state.row, node.state.col))
        node = node.father_node
    actions.reverse()
    cells = [world["agent"]] + cells[::-1]

    # Custo de cada ação pela regra do enunciado: célula onde o agente está antes de agir.
    step_costs = [cell_cost(world, row, col) for row, col in cells[:-1]]
    return {"actions": actions, "step_costs": step_costs, "cost": total_cost, "cells": cells}
