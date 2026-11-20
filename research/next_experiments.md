# Next research decisions

The completed work separates three questions that were previously combined:
whether an exact successor can be represented, whether the representation can
be updated, and whether it is computationally economical. The first two now
have an executable example. The third remains the central problem.

## Priority one: expose the answer with fewer bits

The Euler-product remainder contains the exact successor, but it is tiny. A
large numerical precision budget hides inside the apparent single-state value.
The mixed-precision implementation reduces wasted evaluation effort; it does
not remove the asymptotic size of the state.

Investigate weight families or representations in which neighboring possible
successors produce well-separated, efficiently computable outputs. Any proposal
must include both an extraction theorem and a method to construct its state
without already knowing the answer.

Acceptance condition: record a proved enclosure or exact arithmetic invariant,
the bits retained, the cost of initialization, the work of every state update,
and the cost of decoding. An infinite limit, huge integer, lookup table, or
high-precision constant is not a free computational primitive.

## Priority two: initialize at an arbitrary large prime

The present analytic setup reconstructs the complete preceding prime prefix.
The user specifically wants useful arbitrary entry. A new initialization
method must eliminate or substantially reduce that prehistory cost.

Compare arithmetic block summaries, recursively grouped Euler factors, and
prime-counting or rough-number counting methods. These are candidate research
directions, not established shortcuts. Measure cold starts as well as long runs
from a retained state. A warm-state speedup cannot stand in for a cheap entry.

## Priority three: test history representations against exact arithmetic controls

The first weighted-history experiment found a small difference against a fitted
residue predictor but lost to the first elementary sieve survivor on exact
successor accuracy. This is evidence about those features and ranges only.

Before testing new transformations, reserve a new magnitude block and freeze
the hypotheses and scoring. Keep the elementary divisibility control. Separate
one-step prediction with true past history from repeated generation using the
method's own output. An exact generator needs a proof of minimality, not merely
high prediction accuracy.

The next useful feature investigation would need to explain why its information
cannot be obtained more cheaply by ordinary arithmetic. Adding more weights
without this comparison risks rediscovering a sieve at a higher cost.

## What would count as the requested advance

A state with an explicit mathematical invariant, affordable construction from
the available starting information, affordable updates, and exact immediate
successors. It must account for skipped composites by reasoning intrinsic to
the method. Its complete measured cost must improve on strong established
methods in a stated regime, or its proven complexity must improve a relevant
bound. A preliminary implementation alone cannot establish a worldwide
priority claim.

The present package is the first experimental iteration toward that target.
