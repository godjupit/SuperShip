# Four independent direction screens

RTX4090 / public200 reference / same complete worker protocol. These sequential screens are not causal speedup estimates; beginning/end baseline medians differ. All55outputs byte-identical; AP50=0.7809, validation/hidden=null.

| Case | Three rounds ms | Median ms |
| --- | --- | ---: |
|formal-baseline|251.709695/260.319735/249.659454|251.709695|
|formal-cpu|260.230415/256.146072/258.700938|258.700938|
|formal-gpu|255.685603/265.632975/255.544081|255.685603|
|formal-exit|269.883890/285.210258/258.996330|269.883890|
|formal-output|264.462374/259.108275/260.065426|260.065426|
|formal-baseline-end|268.812619/260.910024/256.942258|260.910024|

| Confirmation | Baseline median ms | Candidate median ms | Wins | Exact paired sign-flip p |
| --- | ---: | ---: | --- | ---: |
|cpu|257.600508|260.544697|3/8|0.640625|
|gpu|257.714756|256.471031|4/8|0.687500|

## Individual pairs

### cpu

| Pair | Order | Baseline ms | Candidate ms |
| --- | --- | ---: | ---: |
|1|AB|256.899455|251.522610|
|2|BA|263.699639|265.931351|
|3|AB|253.283531|268.643758|
|4|BA|258.301561|260.029351|
|5|AB|252.908421|266.158104|
|6|BA|253.945435|255.619519|
|7|AB|267.150987|261.060043|
|8|BA|263.416507|253.071986|

### gpu

| Pair | Order | Baseline ms | Candidate ms |
| --- | --- | ---: | ---: |
|1|AB|255.441180|256.099238|
|2|BA|261.460020|254.126058|
|3|AB|259.988331|257.533030|
|4|BA|261.041862|262.834962|
|5|AB|251.634817|256.842824|
|6|BA|295.830573|253.764728|
|7|AB|254.891395|254.462531|
|8|BA|254.869517|265.597555|

