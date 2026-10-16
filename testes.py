"""Testes manuais do problema do entregador. Execute: python testes.py"""

from aigyminsper.search.search_algorithms import BuscaLargura

from delivery_problem import MOVES, DeliveryState, cell_cost, generate_world, solve


def make_world(n, agent, package, destination, obstacles=(), tolls=()):
    return {
        "n": n,
        "agent": agent,
        "package": package,
        "destination": destination,
        "obstacles": set(obstacles),
        "tolls": set(tolls),
    }


def check_plan(world, result):
    """Simula o plano passo a passo pelas regras do enunciado e confere o custo."""
    row, col = world["agent"]
    has_package = False
    delivered = False
    total = 0
    for action in result["actions"]:
        total += cell_cost(world, row, col)  # custo da célula ANTES da ação
        if action in MOVES:
            d_row, d_col = MOVES[action]
            row, col = row + d_row, col + d_col
            assert 0 <= row < world["n"] and 0 <= col < world["n"], "saiu do grid"
            assert (row, col) not in world["obstacles"], "atravessou obstáculo"
        elif action == "pegar pacote":
            assert (row, col) == world["package"] and not has_package
            has_package = True
        elif action == "entregar pacote":
            assert (row, col) == world["destination"] and has_package
            has_package = False
            delivered = True
    assert delivered, "pacote não foi entregue"
    assert result["actions"][-1] == "entregar pacote"
    assert total == result["cost"] == sum(result["step_costs"])


def show(title, result):
    print(f"\n== {title} ==")
    if result is None:
        print("Não existe solução para este mundo.")
        return
    print(f"Custo total: {result['cost']}  |  Ações: {len(result['actions'])}")
    print(" -> ".join(result["actions"]))


def teste_1_simples():
    world = make_world(3, agent=(0, 0), package=(0, 2), destination=(2, 2))
    result = solve(world)
    show("TESTE 1 - simples", result)
    check_plan(world, result)
    assert "pegar pacote" in result["actions"] and "entregar pacote" in result["actions"]
    assert result["actions"].index("pegar pacote") < result["actions"].index("entregar pacote")
    assert result["cost"] == 6


def teste_2_obstaculos():
    # Parede na coluna 1 (linhas 0 a 2): o agente precisa contornar por baixo.
    walls = [(0, 1), (1, 1), (2, 1)]
    world = make_world(4, agent=(0, 0), package=(0, 2), destination=(3, 3), obstacles=walls)
    result = solve(world)
    show("TESTE 2 - obstáculos", result)
    check_plan(world, result)
    assert not set(result["cells"]) & world["obstacles"]
    assert result["cost"] == 14


def teste_3_impossivel():
    # Pacote cercado por obstáculos.
    world = make_world(3, agent=(2, 2), package=(0, 0), destination=(2, 0), obstacles=[(0, 1), (1, 0)])
    result = solve(world)
    show("TESTE 3a - pacote isolado", result)
    assert result is None

    # Agente cercado por obstáculos.
    world = make_world(3, agent=(0, 0), package=(2, 2), destination=(2, 0), obstacles=[(0, 1), (1, 0)])
    result = solve(world)
    show("TESTE 3b - agente isolado", result)
    assert result is None


def teste_4_pedagio():
    # P T T D   <- caminho curto (6 ações) passando por 2 pedágios: custo 10
    # A . . .   <- desvio (8 ações) sem pedágio: custo 8
    world = make_world(4, agent=(1, 0), package=(0, 0), destination=(0, 3), tolls=[(0, 1), (0, 2)])
    result = solve(world)
    show("TESTE 4a - pedágio x desvio", result)
    check_plan(world, result)
    assert result["cost"] == 8
    assert not set(result["cells"]) & world["tolls"]

    # Busca em Largura (mesma biblioteca) escolhe o caminho com menos ações, mas mais caro.
    row, col = world["agent"]
    bfs_node = BuscaLargura().search(DeliveryState(world, row, col, False, False, "inicio", 0), pruning="general")
    print(f"   Busca em Largura: {bfs_node.depth} ações, custo {bfs_node.g}")
    assert bfs_node.depth == 6 and bfs_node.g == 10

    # Corredor sem desvio: o pedágio é obrigatório e deve somar +2.
    # A P T D
    walls = [(r, c) for r in range(1, 4) for c in range(4)]
    world = make_world(4, agent=(0, 0), package=(0, 1), destination=(0, 3), obstacles=walls, tolls=[(0, 2)])
    result = solve(world)
    show("TESTE 4b - pedágio obrigatório", result)
    check_plan(world, result)
    print("   Custo por ação:", result["step_costs"])
    assert len(result["actions"]) == 5 and result["cost"] == 5 + 2
    assert result["step_costs"] == [1, 1, 1, 3, 1]


def teste_5_aleatorio():
    print("\n== TESTE 5 - geração aleatória ==")
    for n in [2, 3, 5, 8]:
        solved = unsolved = 0
        for _ in range(100):
            world = generate_world(n)
            specials = {world["agent"], world["package"], world["destination"]}
            assert len(specials) == 3
            assert not specials & world["obstacles"]
            assert not specials & world["tolls"]
            assert not world["obstacles"] & world["tolls"]
            assert all(0 <= r < n and 0 <= c < n for r, c in specials | world["obstacles"] | world["tolls"])
            result = solve(world)
            if result is None:
                unsolved += 1
            else:
                check_plan(world, result)
                solved += 1
        print(f"   {n}x{n}: {solved} com solução, {unsolved} sem solução (100 mundos)")

    try:
        generate_world(1)
        assert False, "deveria recusar n < 2"
    except ValueError:
        print("   n=1 recusado corretamente")


if __name__ == "__main__":
    teste_1_simples()
    teste_2_obstaculos()
    teste_3_impossivel()
    teste_4_pedagio()
    teste_5_aleatorio()
    print("\nTodos os testes passaram.")
