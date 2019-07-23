# Floating Point Problem
Attempts to implement a solution to the floating point vulnerability in the Laplacian mechanism described in [Mironov (2012)](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.366.5957&rep=rep1&type=pdf).

### Snapping Mechanism
First task was to look at an earlier attempt at a solution, located [here](snapping_mechanism/gk_snap.R).

##### Oddities
<!-- - Functions didn't always return correctly (I think). -->
- `clamp` function was defined such that lower and upper bounds could be anything. Seems like the Mironov paper requires that the bounds for `clamp` be `{-B, B}`. See pg. 11, Section 5.2 of [Mironov (2012)](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.366.5957&rep=rep1&type=pdf). Not sure yet to what extent this matters, but the level of DP does depend on `B` (so I think it matters some).
- No idea how (or if) original code was sampling floating point numbers with probability equal to [ulp](https://en.wikipedia.org/wiki/Unit_in_the_last_place#Language_support). I think this is required for the method.
    - NOTE: My original thought was that this would require some real work on our part, but I think it may already be a consequence of samplers that approximate sampling from the reals.

##### Questions
- LN in paper requires exact rounding, but not sure if `log` function in R does this
    - Florent de Dinechin, Christoph Quirin Lauter, and Jean-Michel Muller.  Fast and correctly rounded logarithms in double-precision.Theoretical Informatics and Applications, 41(1):85–102, 2007.
    - Correctly rounded mathematical library.http://lipforge.ens-lyon.fr/www/crlibm/
- For `U*`, is it sufficient to use a standard uniform random number generator?
- Privacy guarantee holds when sensitivity of `f` is 1 and they say you can just scale `f` in proportion to its sensitivity otherwise. Does that work for our case? Can we just scale `f`?
    - If not, need to figure out exactly how sensitivity changes results. Seems possible that new privacy guarantee becomes sensitivity/lambda + 2^-49*B/lambda
- Does not seem like we can generate standalone `snapped Laplacian noise` -- only a `snapped private estimate` (from which we should be able to back out the `snapped Laplacian noise`?)
- Need to better understand where we are getting sensitivity, bounds, and epsilon
    - Don't think this could be written as something that the Laplace mechanism can just call. I think it would have to be a fully separate mechanism. In fact, the snapping mechanism could work by calling the Laplace mechanism.
- Could the floating point issue be mitigated by using arbitrary precision calculations? Would this be feasible in an actual software implementation.

##### Immediate TODO
- Rounding to closest multiple of Lambda is likely implemented incorrectly -- it's giving very coarse answers

##### Questions with James
- What is utility loss for switching to snapping from Laplace?
    - Look into CS208 experimentation code and try some experiments
