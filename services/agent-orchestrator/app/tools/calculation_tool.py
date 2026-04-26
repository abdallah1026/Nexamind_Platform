# calculation tool - does math stuff for agents
# used by finance, operations, sales agents mostly
# 
# NOTE: i know scipy has better statistical functions but 
# wanted to implement manually to understand the math better

import math
import statistics
from typing import Any, Dict, List, Optional


class CalculationTool:
    name = "calculation_tool"
    description = "does statistical and financial calculations"

    def __init__(self, **kwargs):
        pass

    async def execute(self, operation: str, data: Any, **kwargs) -> Dict[str, Any]:
        
        # map operation names to functions
        # TODO: add more operations if needed
        ops = {
            "mean": lambda d: statistics.mean(d),
            "median": lambda d: statistics.median(d),
            "stdev": lambda d: statistics.stdev(d) if len(d) > 1 else 0,
            "variance": lambda d: statistics.variance(d) if len(d) > 1 else 0,
            "min": min,
            "max": max,
            "sum": sum,
            "count": len,
            "percentile": lambda d: self._percentile(d, kwargs.get("p", 50)),
            "moving_average": lambda d: self._moving_avg(d, kwargs.get("window", 3)),
            "growth_rate": lambda d: self._growth_rate(d),
            "cagr": lambda d: self._cagr(d[0], d[-1], len(d) - 1),
            "npv": lambda d: self._npv(kwargs.get("rate", 0.1), d),
            "roi": lambda d: (d[1] - d[0]) / d[0] * 100 if d[0] != 0 else 0,
            "correlation": lambda d: self._correlation(d, kwargs.get("data2", [])),
        }

        if operation not in ops:
            return {"error": f"unknown operation '{operation}'. options: {list(ops.keys())}"}
        
        try:
            result = ops[operation](data)
            return {"result": result, "operation": operation}
        except Exception as e:
            # sometimes data is empty or wrong type
            print(f"calc error in {operation}: {e}")  # for debugging
            return {"error": str(e)}

    def _percentile(self, data: List[float], p: float) -> float:
        # manual percentile calculation
        # learned this from stats class
        sorted_data = sorted(data)
        index = (p / 100) * (len(sorted_data) - 1)
        lower = int(index)
        upper = math.ceil(index)
        if lower == upper:
            return sorted_data[lower]
        # linear interpolation
        return sorted_data[lower] * (upper - index) + sorted_data[upper] * (index - lower)

    def _moving_avg(self, data: List[float], window: int) -> List[float]:
        result = []
        for i in range(len(data)):
            start = max(0, i - window + 1)
            window_data = data[start:i + 1]
            result.append(sum(window_data) / len(window_data))
        return result

    def _growth_rate(self, data: List[float]) -> List[float]:
        # calculate period over period growth
        rates = []
        for i in range(1, len(data)):
            if data[i-1] != 0:
                rate = (data[i] - data[i-1]) / data[i-1] * 100
            else:
                rate = 0
            rates.append(round(rate, 2))
        return rates

    def _cagr(self, start: float, end: float, years: int) -> float:
        # compound annual growth rate
        # formula: (end/start)^(1/n) - 1
        if start <= 0 or years <= 0:
            return 0
        return round(((end / start) ** (1 / years) - 1) * 100, 2)

    def _npv(self, rate: float, cash_flows: List[float]) -> float:
        # net present value
        total = 0
        for i, cf in enumerate(cash_flows):
            total += cf / (1 + rate) ** i
        return round(total, 2)

    def _correlation(self, x: List[float], y: List[float]) -> float:
        # pearson correlation
        if len(x) != len(y) or len(x) < 2:
            return 0
        n = len(x)
        mx = sum(x) / n
        my = sum(y) / n
        numerator = sum((x[i] - mx) * (y[i] - my) for i in range(n))
        denom_x = sum((xi - mx) ** 2 for xi in x)
        denom_y = sum((yi - my) ** 2 for yi in y)
        denom = math.sqrt(denom_x * denom_y)
        if denom == 0:
            return 0
        return round(numerator / denom, 4)
