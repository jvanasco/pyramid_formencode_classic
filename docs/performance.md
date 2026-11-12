# Form validation and reprinting performance

The November 12, 2026 baseline measured commit `06d05ae` during 1.00 release
preparation. The run used CPython 3.14.6 on x86-64 macOS with FormEncode 2.1.1,
Pyramid 2.1, and WebOb 1.8.11.

## Reproduce the benchmark

From the repository root, with the package dependencies and test extras
available in the active Python environment, run:

```sh
PYTHONPATH=src python docs/benchmark_forms.py
```

The [benchmark script](benchmark_forms.py) checks each fixture, warms it up with
500 calls, and reports the median and range across nine timed runs of 3,000
calls. It then profiles 3,000 calls per case with `cProfile`. Profile times
include profiler overhead and are used to identify where time is spent.

Validation reuses requests, schemas, and submitted data. The reprint fixture
creates a fresh response from fixed HTML each time and clears the stash's
reprint history between calls. These measurements cover the package calls
outside the full HTTP request and template-rendering cycle.

## Baseline results

| Scenario | Median per call | Range across runs |
| --- | ---: | ---: |
| Valid email and username submission | 52.9 µs | 46.4–111.2 µs |
| Rejected submission with four repeated values, two invalid | 297.4 µs | 183.2–353.2 µs |
| Reprint a two-field HTML form with a field error | 524.3 µs | 415.5–658.8 µs |

FormEncode schema conversion accounted for roughly 80% of profiled validation
time in both validation cases. FormEncode's HTML filling accounted for about
two-thirds of profiled reprint time, mostly in parsing and rewriting markup.
The timing spread limits the precision of small comparisons.

Optimization was deferred for 1.00 because all three median times were below
one millisecond and most of the measured work was in FormEncode. If
performance becomes a concern, repeat the benchmark on representative forms
and compare profiles under the same conditions.
