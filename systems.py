#!/usr/bin/env python3

from typing import List, Callable, Optional


"Describe how a Flows affect Stocks, Source -> Sink"
FlowFn = Callable[[Optional['Stock'], Optional['Stock']], None]


class Flow:
    "Something that pumps or drains a Stock"
    def __init__(
        self,
        source: Optional['Stock'],
        sink: Optional['Stock'],
        updatefn: FlowFn
    ) -> None:
        self.source = source
        self.sink = sink
        self.updatefn = updatefn

    def tick(self) -> None:
        self.updatefn(self.source, self.sink)


class Stock:
    def __init__(self, name: str, value: float) -> None:
        self.name = name
        self.value = value


class System:
    def __init__(self) -> None:
        self.stocks: List[Stock] = []
        self.flows: List[Flow] = []

    def add_stock(self, stock: Stock) -> None:
        self.stocks.append(stock)

    def add_flow(self, flow: Flow) -> None:
        self.flows.append(flow)

    def tick(self) -> None:
        for flow in self.flows:
            flow.tick()

    def __str__(self) -> str:
        return '\n'.join(f'{s.name}: {s.value:.2f}' for s in self.stocks)


if __name__ == "__main__":
    # Setup a scenario
    # A fishing company that makes its capital grow by selling fish
    # It reinvests part of its capital in better equipment
    # Equipment deteriorates (is amortized) over 20 years
    #
    fishing_co = System()

    # Fish stock is the pool of fishes the company works on
    fishes = Stock('fish', 2000.0)
    fishing_co.add_stock(fishes)
    # Capital owned by the company
    capital = Stock('capital', 500.0)
    fishing_co.add_stock(capital)

    # new fish born from existent at 1% per cycle (could be stochastic)
    def _new_fish(source, sink) -> None:
        if fishes.value <= 1.0e4:
            sink.value *= 1.0001
    fishing_co.add_flow(Flow(None, fishes, _new_fish))

    # fish sale will lead to capital growth
    def _fish_sale(source, sink) -> None:
        fished = source.value * 0.008
        source.value -= fished
        sink.value += fished * 1.25  # $1.25 per fish sold
    fishing_co.add_flow(Flow(fishes, capital, _fish_sale))

    print(fishing_co)
    for cycle in range(5000):
        fishing_co.tick()
        print(fishing_co)

    # equipment_cost = StockFlow()
    # fish sales can grow by investing part of captial back into equipment
    # fish_sales = StockFlow()
