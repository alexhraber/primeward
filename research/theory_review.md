# Mathematical review of the successor prototype

## What has been achieved

The analytic prototype implements an exact successor calculation from a reusable arithmetic state. During an ordinary transition it performs no primality tests on future candidates and does not walk through the intervening integers. A single additional Euler factor updates its state after each new prime.

This is an implementation within an established analytic family, with a finite extraction bound and interval arithmetic. It is not a claim of a new prime-generating theorem or a faster general-purpose prime generator. Its expensive initialization and numerical precision remain central limitations. Whether the particular finite bound or rounding presentation has appeared elsewhere has not been established.

The argument does not assume the Riemann Hypothesis.

## Established starting point

Solomon W. Golomb's 1976 paper explains how to recover a successor from a weighted distribution after excluding multiples of the preceding primes. One of his constructions multiplies the zeta function by the Euler factors of those primes and removes the contribution of the integer one. An inverse-power limit then recovers the smallest remaining integer, which is the successor. The paper also places Gandhi's earlier geometric-weight construction in this framework.

Artur Kawalec's later preprint develops related analytic recurrences and numerical evaluations. It provides additional context, but a computational advantage over sieving does not follow from the existence of these formulas.

Sources:

- [Solomon W. Golomb, Formulas for the next prime, Pacific Journal of Mathematics, 1976](https://msp.org/pjm/1976/63-2/pjm-v63-n2-p11-p.pdf).
- [Artur Kawalec, The recurrence formulas for primes and non-trivial zeros of the Riemann zeta function, version three, 2021](https://arxiv.org/abs/2009.02640).

## The exact state

Fix a positive integer exponent greater than one. Take the zeta function at that exponent and multiply it by one Euler factor for every prime at or below the current prime. Each factor is one minus that prime raised to the negative exponent.

The resulting state has an exact interpretation: it is the sum of inverse powers of all positive integers having no prime factor at or below the current prime. The integer one contributes exactly one. It is preserved explicitly as the multiplicative identity.

Subtract that unit contribution. The smallest integer remaining in the sum is the immediate next prime. Every composite integer smaller than that prime would have a smaller prime factor, which would already have been excluded.

After extracting the successor, multiply the state by its Euler factor. This excludes all multiples of the newly discovered prime and restores precisely the same invariant for the next transition.

## A finite exponent suffices

For this paragraph, call the unknown successor the successor and call the chosen integer exponent the exponent. The proof requires the exponent to be at least the successor.

The residual sum is strictly larger than the inverse exponent power of the successor, because further surviving integers also contribute positive terms. The square of the successor is one such further integer.

An upper bound is obtained by adding the inverse powers of every integer larger than the successor, even those that would actually be excluded. The integral test bounds this tail by the successor raised to one minus the exponent, divided by one less than the exponent.

Consequently, the residual is no larger than the inverse exponent power of the successor, multiplied by one plus the successor divided by one less than the exponent.

Bernoulli's inequality shows that this upper bound is strictly smaller than the inverse exponent power of one less than the successor. To check the required comparison, raise the ratio of the successor to one less than the successor to the exponent. Bernoulli gives a value strictly greater than one plus the exponent divided by one less than the successor. The assumption that the exponent is at least the successor makes this latter increment at least the successor divided by one less than the exponent.

Taking the reciprocal exponent root reverses these bounds. The extracted real number lies strictly between one less than the successor and the successor itself. Its ceiling therefore equals the successor exactly.

For a current prime of at least two, Bertrand's postulate places the successor below twice the current prime. It is therefore sufficient to choose an integer exponent at least twice the current prime. This choice is conservative and is justified without knowing the successor in advance.

## A stable extraction rule after the first prime

The direct ceiling rule is numerically inconvenient. The extracted real number can be extremely close to the successor from below, so an otherwise accurate interval may straddle the integer and fail to certify its ceiling.

Every successor after the current prime two is odd. The same finite-exponent proof therefore permits rounding the extracted real number to the nearest odd integer. In executable terms, halve the extracted interval, certify a unique integer floor, double that floor, and add one.

This uses no primality test. It uses the known parity of the successor together with the proved interval location.

The conditioning improvement is quantitative. For an odd successor of at least three, the extracted real number lies above the successor minus the natural logarithm of two and a half. It is therefore more than approximately 0.0837 above the lower even boundary of its rounding cell. It lies below the successor, leaving more than one unit to the upper even boundary. In contrast, its distance from the successor itself can be extremely small.

To derive that uniform margin, use the elementary lower bound for an exponential: the exponential of a negative positive quantity is greater than one minus that quantity. Apply it to the lower bound on the extracted root from the preceding section. The difference from the successor is then less than the successor divided by the exponent, multiplied by the logarithm of one plus the successor divided by one less than the exponent. The first multiplier is at most one. For a successor of at least three, the logarithm's argument is at most two and a half.

The initial state at one uses the original ceiling extraction. It computes two from the same residual construction. One is never reclassified as a prime. The nearest-odd decoder is an optimization applicable after that initial transition.

## Reusing an epoch

The implemented epoch starts with an exponent four times the current prime, or four for the unit state. It can reuse that exponent while the current prime is at most half of it. Bertrand's postulate then continues to guarantee that the next prime is below the exponent.

Within an epoch, the zeta value is reused and each advance adds only one new Euler factor. When the current prime passes the epoch threshold, the implementation chooses a larger exponent and rebuilds the numerical product from its stored prime prefix.

The fixed exponent is necessary: a product evaluated at one exponent cannot simply be treated as a product evaluated at another. The rebuild is real work and must be included in measurements.

## Numerical certification

The implementation uses Arb ball arithmetic. A ball encloses the exact real result, accounting for arithmetic and special-function approximation errors. The residual enclosure must be strictly positive. The complete extracted enclosure must fit inside a single permitted rounding cell. A midpoint or a printed decimal approximation alone is insufficient.

Working precision is increased and the state rebuilt if the enclosure does not establish a unique result. An explicit resource limit causes refusal rather than a guessed answer.

The initial precision budget is a magnitude estimate, not a proof that every operation has enough precision. Interval containment is the acceptance test.

Correctness relies on the mathematical invariant and extraction argument, completeness of the prime prefix used for initialization, and correctness of the arithmetic library. The returned human-readable enclosure summaries are diagnostic records, not standalone formal proofs independently replayable by a theorem prover.

## Why this is expensive

The residual being extracted is approximately the inverse exponent power of the successor. Directly subtracting it from a state near one requires working precision on the order of the exponent multiplied by the successor's binary logarithm. The chosen exponent grows proportionally to the numerical starting point.

Thus a modest number of digits in the starting prime can require an enormous working-precision budget. For this implementation, that budget grows exponentially with the input's digit length. Stable nearest-odd rounding avoids one extra source of ill-conditioning, but it does not remove the cost of resolving the tiny residual.

Initialization also enumerates every prime at or below the starting prime, and the implementation retains that list. A compact numerical product is therefore not the entire stored state. Its creation, updates, precision, and later rebuilds must all be counted.

These limitations leave the user's central computational goal open: cheaply initialize at a large arbitrary prime and then maintain a small state that yields exact successors faster than strong existing methods.

## The exact block alternative

A separate stateful method maintains a bounded interval of potential successors. For each prime up to the square root of the interval's upper endpoint, it clears the arithmetic progression of that prime's composite multiples. Multiples begin at the prime's square when necessary, so a prime is not removed as its own multiple. The integer one is excluded from primality explicitly.

The first surviving position is prime. Every earlier position has a small divisor supplied by one of the cleared progressions, providing the minimality argument. A bit operation can select the first surviving position without a loop of individual primality tests.

This method can reuse positions and residues, but it remains a sieve. Its work processes arithmetic progressions in blocks; it must not be described as a new closed successor law. The relevant evidence is measured total cost against capable implementations, including its initialization and coverage construction.

## What weighted history would need to accomplish

The current integer already determines its successor mathematically. Historical state can still be computationally valuable by retaining work that would otherwise need to be repeated.

A weighted or recursively transformed history becomes an exact algorithm only after an invariant shows that its output is the immediate successor. Successful predictions on a finite sample do not supply that invariant. Conversely, the failure of a tested feature family does not prove that every possible representation fails.

State size must be measured in bits, not merely in the number of variables. One arbitrarily precise number can hide a very large amount of information. Initialization, updating, decoding, and certification all belong in the computation budget.

## Independent implementation review

The reviewed analytic implementation follows the invariant above: it constructs the complete prefix, preserves the unit term, enforces the exponent epoch, uses enclosing arithmetic, applies the parity decoder after the initial transition, and appends only the certified successor. The state update has the correct Euler-factor sign and exponent. Its explicit precision limit fails closed.

The proof establishes immediate succession, including the absence of an intervening prime, through the residual's least surviving integer. No separate scan of the future interval is mathematically required by this analytic method. The missing advance is computational efficiency, not correctness of the successor identity.
