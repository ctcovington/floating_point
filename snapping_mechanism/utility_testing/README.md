# Utility Testing
This directory contains tests (and associated results) on the utility of the snapping mechanism vs. the traditional laplace.

<hr>

### Timeline/Decisions
- 07/24-25/19: Christian completes first attempt at testing his implementations of the [snapping mechanism](cc_snap.py) vs. the [laplace mechanism](cc_laplace.py) on a mean release. We are still thinking about the best way to test, as there are a number of free parameters. For now, we fix the mean of the underlying data and vary the standard deviation, the extent to which data are clipped, the DP epsilon, and the sample size.

<hr>

### Mean Release
The point of the mean release is to calculate a DP-mean on data. The outcome of interest of the current set of tests is the absolute difference between the mean generated via the Laplace mechanism and the mean generated via the snapping mechanism. We run this test across a grid of parameters with 1000 simulations at each parameter combination. The parameters are explained below:

    - `distribution`: The distribution of the underlying data of which we are taking the mean.
    - `sd`: The standard deviation of the underlying data.
    - `bound_sd`: The number of standard deviations away from the population mean past which we clip.
    - `epsilon`: Standard DP-epsilon.
    - `n`: Sample size of the underlying data.

We do not include a mean parameter because we assume the mean to be 0. We currently look at two different distributions (normal and lognormal) and parameterize them the same way because, in numpy, the lognormal is parameterized with the values from the normal with which it is associated (see [here](https://docs.scipy.org/doc/numpy/reference/generated/numpy.random.lognormal.html)).

Results are located in [mean_release_output](mean_release_output). There is an [overall_statistics.csv](mean_release_output/overall_statistics.csv) file containing general statistics from each set of parameters. 
