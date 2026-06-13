class TransactionStatistics:

    def calculate(self, latencies):
        sorted_values = sorted(latencies)

        count = len(sorted_values)
        average = sum(sorted_values) / count
        minimum = sorted_values[0]
        maximum = sorted_values[-1]

        p95_index = int(count * 0.95)

        if p95_index >= count:
            p95_index = count - 1

        p95 = sorted_values[p95_index]

        return {
            "count": count,
            "average": average,
            "minimum": minimum,
            "maximum": maximum,
            "p95": p95,
        }