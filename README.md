# APS - Entregador em GridWorld

## Objetivo

O projeto implementa um agente que precisa **pegar um pacote** e **entregá-lo em um destino**. Ele se move num mundo em grid N x N com obstáculos (células intransponíveis) e células com pedágio. O agente, o pacote, o destino, os obstáculos e os pedágios são sorteados a cada execução.

## Algoritmo

Foi utilizada a **Busca de Custo Uniforme** (`BuscaCustoUniforme`) da biblioteca `aigyminsper` (versão 0.3.3), com `pruning="general"`.

Como células de pedágio aumentam o custo das ações, caminhos com menos movimentos não necessariamente possuem menor custo. A Busca de Custo Uniforme expande os nós pelo menor custo acumulado g(n) e, como todos os custos são positivos, encontra o plano de menor custo. A Busca em Largura minimiza só a quantidade de ações, então não serve (veja o Teste 4 abaixo).

O plano é extraído do `Node` devolvido pela própria biblioteca: o código sobe por `father_node` lendo `state.operator`, e o custo total é `node.g`.

## Estado

Só o que muda durante a busca fica no estado (`DeliveryState`):

- posição do agente (`row`, `col`);
- se está carregando o pacote (`has_package`);
- se o pacote foi entregue (`delivered`).

O mapa (dimensão, obstáculos, pedágios, posição do pacote e destino) fica num dicionário `world`, compartilhado por todos os estados. Enquanto `has_package` é verdadeiro, o pacote acompanha o agente, então não é preciso guardar a posição dele separadamente. `env()` devolve `(row, col, has_package, delivered)`.

O objetivo (`is_goal`) só é verdadeiro depois da ação **entregar pacote**. Chegar ao destino não basta.

## Ações

- cima
- baixo
- esquerda
- direita
- pegar pacote (só na célula do pacote, se ainda não estiver com ele)
- entregar pacote (só no destino, carregando o pacote)

Mover contra a borda ou um obstáculo deixaria o agente no mesmo estado, gastando custo. Esses movimentos não são gerados como sucessores, porque nunca melhoram uma solução ótima e só aumentariam a árvore de busca.

## Custos

| Célula onde o agente está ao executar a ação | Custo |
|---|---|
| Normal | 1 |
| Pedágio | 1 + 2 = 3 |

Vale para todas as ações, inclusive pegar e entregar.

**Detalhe de implementação:** o `pruning="general"` da `aigyminsper` marca um estado como visitado no momento em que ele é **gerado**. Isso só garante o ótimo se o custo de chegar a um estado for igual vindo de qualquer vizinho. Por isso, internamente, o pedágio é cobrado ao **entrar** na célula, e não ao sair dela. O agente sempre começa e termina em células sem pedágio, então o custo total de qualquer plano completo é exatamente o mesmo nas duas formas. Na interface, o custo de cada ação é mostrado pela regra do enunciado (célula de origem). Testamos com a regra de cobrar na origem: a busca da biblioteca devolveu um plano mais caro que o ótimo em 61 de 400 mundos aleatórios. Com a forma atual, foram 0 de 1200.

## Interface

`main.py` abre uma janela Tkinter. O usuário digita a dimensão N (inteiro ≥ 2) e clica em **Gerar mundo**: o mundo é sorteado e desenhado. Em **Resolver**, a busca é executada e a janela mostra o custo total, o plano numerado (com o custo de cada ação) e o caminho em verde no grid.

Legenda: branco = normal, preto = obstáculo, cinza = pedágio, **A** azul = agente, **P** amarelo = pacote, **X** vermelho = destino.

## Estados sem solução

O mundo **não** é regerado até ter solução. Como pede o enunciado, o estado inicial pode ser impossível, por exemplo com o pacote ou o destino cercado por obstáculos. Nesse caso a busca esgota os estados alcançáveis e a interface mostra **"Não existe solução para este mundo."** A quantidade de obstáculos é sorteada entre 0 e 35% das células e a de pedágios entre 0 e 20%. Com isso, nos testes, cerca de 5 a 9% dos mundos 3x3 a 8x8 saíram sem solução.

## Como executar

```
pip install -r requirements.txt
python main.py
```

Testes:

```
python testes.py
```

## Exemplos

Resultados reais obtidos na execução. Legenda do texto: `A` agente, `P` pacote, `X` destino, `#` obstáculo, `$` pedágio. A linha 0 fica no topo.

**Pedágio x desvio (Teste 4 de `testes.py`)**

```
P $ $ X
A . . .
. . . .
. . . .
```

```
Custo total: 8
cima -> pegar pacote -> baixo -> direita -> direita -> direita -> cima -> entregar pacote
```

A Busca de Custo Uniforme desvia dos pedágios: são 8 ações com custo 8. A Busca em Largura da mesma biblioteca escolhe o caminho pelos pedágios: 6 ações, mas custo 10.

**Mundo aleatório 8x8 com solução (gerado pela interface)**

```
. . . . . . . .
. . . . # . . .
. . A . # . . .
. . . . $ . . .
. . . . . . $ $
. . . . . . # .
. . . . . . X $
. . . # . P . .
```

```
Solução encontrada
Custo total: 12
Plano:
1. baixo  (custo 1)
2. baixo  (custo 1)
3. direita  (custo 1)
4. direita  (custo 1)
5. baixo  (custo 1)
6. baixo  (custo 1)
7. direita  (custo 1)
8. baixo  (custo 1)
9. pegar pacote  (custo 1)
10. direita  (custo 1)
11. cima  (custo 1)
12. entregar pacote  (custo 1)
```

**Mundo aleatório 6x6 sem solução (gerado pela interface)**

```
. . P # . .
. # . # . .
# $ . . # $
. . . # X .
$ # A # . .
. $ # # . $
```

```
Não existe solução para este mundo.
```

O agente alcança o pacote, mas a coluna de obstáculos separa a região dele da região do destino.

## Arquivos

- `delivery_problem.py`: estado, sucessores, custos, geração do mundo e chamada da busca.
- `main.py`: interface Tkinter.
- `testes.py`: cenários de teste (simples, obstáculos, sem solução, pedágio e geração aleatória).
