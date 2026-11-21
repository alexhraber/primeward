# Faster exact extraction: odd tails and residual state

This note supplies the finite bounds used by `FastAnalyticSuccessor`. The
underlying Euler-product identity is the same one used by the original
analytic engine. The changes reduce its exponent, extend an epoch only when
the numerical state certifies that extension, and store the residual directly.

## State and notation

Let `p` be the current prime, `q` its immediate successor, and `s > 1` an
integer exponent. For a complete prefix of primes through `p`, define

$$
F = \zeta(s)\prod_{r\le p,\ r\ \mathrm{prime}}(1-r^{-s}),
\qquad R=F-1.
$$

The residual is the sum of `n^-s` over integers greater than one with no
prime divisor at most `p`. Its least term index is `q`. In particular,
`R > q^-s`: `q` contributes, and `q^2` also contributes.

Once `p >= 2`, every surviving integer is odd. The proofs below use this
parity condition; the identity start at one retains the original ceiling
argument at exponent four.

## A sharper tail bound

For `s > 1`, the function `x^-s` is strictly convex. Its value at the midpoint
of an interval of width two is less than the average value over that interval.
Applying this to the intervals centered at `q+2`, `q+4`, and so on gives

$$
\sum_{k\ge1}(q+2k)^{-s}
<\frac12\int_{q+1}^{\infty}x^{-s}\,dx
=\frac{(q+1)^{1-s}}{2(s-1)}.
$$

Including every odd integer after `q` can only increase the actual residual,
so

$$
q^{-s}<R<q^{-s}+\frac{(q+1)^{1-s}}{2(s-1)}.
$$

The original proof bounded the tail using every positive integer. This bound
uses the already established exclusion of even integers.

## Half the former sufficient exponent

For odd `q >= 3`, it is sufficient that

$$
s\ge\frac{q+3}{2}.
$$

Under this condition,

$$
Rq^s
<1+\frac{q}{2(s-1)}\left(\frac{q}{q+1}\right)^{s-1}
<1+e^{-1/2}.
$$

The final inequality follows from `2(s-1) >= q+1` and
`log(1-x) < -x` for `0 < x < 1`. On the other hand,

$$
\left(\frac{q}{q-1}\right)^s
>e^{s/q}>e^{1/2}>1+e^{-1/2}.
$$

Here `log(q/(q-1)) > 1/q`. The last numerical comparison needs no floating
point assumption: `exp(1/2) > 1 + 1/2 + 1/8 = 13/8`, and `13/8` exceeds
the positive root of `x^2-x-1`.

Combining the inequalities proves

$$
q^{-s}<R<(q-1)^{-s},
\qquad q-1<R^{-1/s}<q.
$$

Thus the existing nearest-odd decoder remains exact. The entire Arb root
enclosure must lie in the appropriate rounding cell; a midpoint estimate
alone is insufficient. The lower margin can be bounded uniformly:

$$
q-R^{-1/s}<2\log(1+e^{-1/2})<1.
$$

The former sufficient condition was `s >= q`. This proof permits every odd
successor `q <= 2s-3`.

## Certifying an epoch from its residual

Set

$$
L=2s-1,
\qquad T_s=L^{-s}+\frac{(L+1)^{1-s}}{2(s-1)}.
$$

If the unknown successor satisfied `q >= L`, the same odd-tail bound would
give `R < T_s`. Therefore the full-enclosure comparison

$$
R>T_s
$$

certifies `q < L`, or equivalently `q <= 2s-3`. This establishes the
precondition of the extraction lemma without knowing or testing `q`.

The comparison also has a useful exact separation. If `q <= L-2`, then
`R >= (L-2)^-s`, and

$$
\left(\frac{L}{L-2}\right)^s>e^{2s/L}>e,
\qquad
T_sL^s<1+\frac{L}{2(s-1)}\le\frac52<e.
$$

Consequently `(L-2)^-s > T_s`. In exact arithmetic the gate accepts every
successor in its stated range. With intervals, an inconclusive comparison
does not establish either inequality; the implementation must rebuild or
increase precision before returning another successor.

At an epoch beginning with current prime `p >= 2`, the implementation chooses
the least even integer at least `p+2`:

$$
s=2\left\lceil\frac{p+2}{2}\right\rceil.
$$

Bertrand's postulate gives `q < 2p`, hence `q <= 2s-3`, so the first step
meets the lemma. Rounding upward to an even exponent preserves every bound
above and permits the arithmetic library's even-integer zeta path. Later
steps reuse that exponent while the residual gate continues to certify it.
This replaces the former initial exponent `4p` and its conservative
current-prime cutoff. It does not assume a particular prime gap or a constant
number of steps per epoch.

## Updating the residual directly

After accepting `q`, put `a=q^-s`. The exact next residual is

$$
R'=(1+R)(1-a)-1=R-a-Ra.
$$

This is the same Euler-factor update as before, expressed using small
quantities. It avoids repeatedly multiplying a number close to one at the
full absolute precision needed to resolve its tiny residual.

Initialization still has to evaluate the zeta value and the complete finite
Euler product accurately enough to subtract one. Subsequent residual updates
can use a lower relative precision. Cancellation between `R` and `a` consumes
accuracy as the sequence advances, so the interval radius remains part of
the state. A nominal precision budget is a performance choice; the positive
residual, epoch gate, and rounding-cell comparisons determine acceptance.

For initialization, the full working budget is an enclosing upper integer
bound on `s*log2(2s-3)`, plus guard bits. For the Euler correction at a past
prime `r`, a lower integer bound on `s*log2(r)` is subtracted from that budget
to choose the correction's relative precision. Both logarithmic estimates
use Arb enclosures. Rounding the near-one input value to this correction
precision widens its enclosure, which is retained in the correction and in
the subsequent subtraction.

The initial residual budget is approximately `s` plus guard bits. Each
transition uses at most that budget and otherwise follows the relative
accuracy still present in the residual, with extra guard bits. This reduces
work as cancellation consumes accuracy. The full initialization budget and
the smaller residual and transition budgets are reported separately.

If a precision limit is reached, no successor is returned. Lower precision
must never be justified by replacing an enclosure with its midpoint.

## Scope of the improvement

The state still needs a complete preceding prime prefix and high-precision
initialization. These changes reduce work within the existing construction;
their speed and memory effects must be measured with initialization included.
No statement here establishes an advantage over sieving or removes the
dependence on the numerical size of the starting prime.

The argument uses the real zeta function for `s > 1`, elementary inequalities,
Bertrand's postulate for initialization, and enclosing arithmetic. It does
not assume the Riemann Hypothesis.

## References

- [S. W. Golomb, *Formulas for the next prime* (1976)](https://msp.org/pjm/1976/63-2/pjm-v63-n2-p11-p.pdf),
  especially the residual identity in equation (9).
- [FLINT: ball arithmetic](https://flintlib.org/doc/guide/types/ball-arithmetic.html),
  for enclosure semantics, precision, and the distinction between a false
  predicate and an inconclusive interval comparison.
- [FLINT: zeta evaluation algorithms](https://flintlib.org/doc/polylogarithms.html),
  for the specialized Bernoulli-number or Euler-product evaluation at positive
  even integers.
- [Original prototype argument](theory_review.md).
