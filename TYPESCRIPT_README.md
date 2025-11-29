# Hephaestus (README for TypeScript Fuzzing)

- Run `uv sync` to fetch the dependencies.
- Run `uv run python hephaestus.py --batch 30 -s <no-of-seconds-to-run> -t <number-of-transformations> -w <parallelism> --language typescript --disable-use-site-variance --error-filter-patterns regex.txt --trace --print-stacktrace` to run the fuzzer for typescript. This will run the fuzzer for `no-of-seconds-to-run` seconds, with using `parallelism` threads. After every `30` programs, it'll run the checks against the typescript compiler. The `number-of-transformations` controls the number of transformations in each round. 

In our experiments, we ran the following command:
```
uv run python hephaestus.py --batch 30 -s 86400 -t 5 -w 8 --language typescript --disable-use-site-variance --error-filter-patterns regex.txt --trace --print-stacktrace
```
We would run the fuzzer for a day(86400 seconds), and would check the results the next day.

The `README.md` file has more hephaestus related information.
