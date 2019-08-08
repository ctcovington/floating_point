library(reticulate)

main <- function() {
    # import cc_snap module
    cc_snap <- import('cc_snap')

    """
    simulate gaussian data on which we want to release a mean
    """
    # set parameters
    n <- 1e7
    mean <- 0
    sd <- 5
    B <- 10

    # simulate and clip data
    simulated_data <- rnorm(n, mean, sd)
    simulated_data_clipped <- ifelse(simulated_data < -B, -B, simulated_data)
    simulated_data_clipped <- ifelse(simulated_data_clipped > B, B, simulated_data_clipped)

    # instantiate snapping mechanism object
    snapping_mech <- cc_snap$Snapping_Mechanism(mechanism_input = mean(simulated_data_clipped),
                                                sensitivity = 2*B/n,
                                                epsilon = 1e-3,
                                                B = B)
    # get noise from snapping mechanism
    snapped_noise <- snapping_mech$get_snapped_noise()
}

# run main
main()
