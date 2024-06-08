from breach_check.breach_factory.base import ResultSchema
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
        return sorted({key for dictionary in results.__dict__ for key in dictionary.keys()})

    def generate_result_cols(self) -> list[Column]:
        return [Column(header=col_header, overflow='fold') for col_header in ResultSchema.get_fields()]

    def _represent_results(self, results: list[ResultSchema]):
        formatted_results = []
        for result in results:
            
            breaches = result.breaches
            if not breaches:
                breaches = ['[green]-[/green]']

            formatted_result = {
                'email': result.email,
                'breaches': ','.join(breaches),
                'total': result.total
            }
            formatted_results.append(formatted_result)

        return formatted_results

    def generate_result_table(self, results: list[ResultSchema]):
        results:list[dict] = self._represent_results(results=results)
        cols = self.generate_result_cols()
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
    def generate_table(results: list[ResultSchema], table_width_percentage: float = 98.0):
        table_handler = ResultTableHandler(
            table_width_percentage=table_width_percentage
        )

        table = table_handler.generate_result_table(results=results)
        console.print(table)
