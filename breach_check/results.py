from breach_check.logger import console
from breach_check.utils import write_json_file
from rich.table import Table, Column


class ResultTableHandler:
    def __init__(self, table_width_percentage: float = 98, ) -> None:
        self.console = console
        self.table_width_percentage = table_width_percentage

    def print_table(self, table: Table):
        terminal_width = console.width
        table_width = int(terminal_width * (self.table_width_percentage / 100))
        table.width = table_width

        self.console.print(table)
        self.console.rule()

    def extract_result_table_cols(self, results: list[dict]) -> list[str]:
        return sorted({key for dictionary in results for key in dictionary.keys()})

    def generate_result_cols(self, results_list: list[dict]) -> list[Column]:
        return [Column(header=col_header, overflow='fold') for col_header in self.extract_result_table_cols(results_list)]

    def _represent_results(self, results: list):
        formatted_results = []
        for result in results:
            email = result.get('email')
            breaches = filter(
                lambda domain: domain.strip() if domain else '',
                [breach.get('Domain', '').strip()
                 for breach in result.get('breaches')]
            )
            total = result.get('total')

            formatted_result = {
                'email': email,
                'breaches': ','.join(breaches),
                'total': total
            }
            formatted_results.append(formatted_result)

        return formatted_results

    def generate_result_table(self, results: list):
        results = self._represent_results(results=results)
        cols = self.generate_result_cols(results)
        table = Table(*cols)

        for result in results:
            table_row = []
            for col in cols:
                table_row.append(
                    str(result.get(col.header, '[red]:bug: - [/red]')))
            table.add_row(*table_row)

        return table


class Results:
    @staticmethod
    def write_json_results_to_file(output_file, results):
        if not write_json_file(output_file, results):
            console.print('Results:')
            console.print(results)

    @staticmethod
    def generate_table(results: list[str], table_width_percentage: float = 98.0):
        table_handler = ResultTableHandler(
            table_width_percentage=table_width_percentage
        )

        table = table_handler.generate_result_table(results=results)
        console.print(table)
