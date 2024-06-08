from asyncio import run
from argparse import ArgumentParser

from breach_check.breach import BreachChecker, BreachCheckerBackendChoices
from breach_check.results import Results
from breach_check.utils import generate_unique_filename, extract_emails


def main():
    parser = ArgumentParser('breach-check')
    parser.add_argument(
        '-i',
        '--input',
        dest='input_file',
        help='input file containing emails on each line',
        type=str,
        required=True
    )
    parser.add_argument(
        '-o',
        '--output',
        dest='output_file',
        help='output json file path',
        required=False,
        default=generate_unique_filename(),
        type=str
    )
    parser.add_argument(
        '-b',
        '--backend',
        dest='backend',
        required=False,
        default=BreachCheckerBackendChoices.LEAKCHECK,
        choices=list(BreachCheckerBackendChoices),
        type=BreachCheckerBackendChoices
    )
    parser.add_argument(
        '-r',
        '--rate-limit',
        dest='rate_limit',
        help='rate limit for making HTTP requests per second',
        required=False,
        default=60,
        type=int
    )

    args = parser.parse_args()

    emails = extract_emails(args.input_file)
    result_handler = Results()

    if not emails:
        exit(-1)

    breach_checker = BreachChecker(
        rate_limit=args.rate_limit,
        backend=args.backend
    )
    results = run(breach_checker.mass_check(emails=emails))

    result_handler.write_json_results_to_file(
        output_file=args.output_file,
        results=results
    )

    result_handler.generate_table(results=breach_checker.result_schemas)


if __name__ == '__main__':
    main()
