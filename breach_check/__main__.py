from argparse import ArgumentParser
from breach_check.breach import BreachChecker
from breach_check.logger import console
from breach_check.utils import generate_unique_filename, extract_emails, write_json_file
from asyncio import run
from sys import exit


def main():
    parser = ArgumentParser('breach-check')
    parser.add_argument('-i', '--input', dest='input_file',
                        help='input file containing emails on each line', type=str, required=True)
    parser.add_argument('-o', '--output', dest='output_file',
                        help='output json file path', required=False, default=generate_unique_filename(), type=str)

    args = parser.parse_args()

    emails = extract_emails(args.input_file)

    if not emails:
        exit(-1)

    results = run(
        BreachChecker().mass_check(emails=emails)
    )

    if not write_json_file(args.output_file, results):
        console.print('Results:')
        console.print(results)


if __name__ == '__main__':
    main()
