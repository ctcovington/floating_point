import cc_snap
import cc_laplace
import numpy as np
import pandas as pd
import os
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
# import plotly, plotly.express

def generate_gaussian_data(mean, sd, n):
    """"""
    return(np.random.normal(loc = mean, scale = sd, size = n))

def generate_lognormal_data(mean, sd, n):
    """
    NOTE: mean and sigma are the parameters from the associated normal distribution
          https://docs.scipy.org/doc/numpy/reference/generated/numpy.random.lognormal.html
    """
    return(np.random.lognormal(mean = mean, sigma = sd, size = n))

def test(dist, mean, sd, bound_sd, epsilon, n):
    """"""
    # generate simulated data
    if dist == 'normal':
        data = generate_gaussian_data(mean, sd, n)
    elif dist == 'lognormal':
        data = generate_lognormal_data(mean, sd, n)

    # use -/+ 3 std_dev as the lower/upper bounds we imagine the user could set
    lower_bound = mean - bound_sd * sd # NOTE: mean should be 0, but kept general in case we want to make changes later
    upper_bound = mean + bound_sd * sd # NOTE: mean should be 0, but kept general in case we want to make changes later
    B = max(abs(lower_bound), abs(upper_bound))

    # clip data
    data_clipped = np.clip(data, lower_bound, upper_bound)
    observed_mean_of_clipped = np.mean(data_clipped)
    sensitivity = (upper_bound - lower_bound) / n

    # generate private means using both the laplace and snapping mechanisms
    private_mean_laplace = cc_laplace.add_laplace_noise(observed_mean_of_clipped, sensitivity, epsilon)
    private_mean_snapped = cc_snap.add_snapped_laplace_noise(observed_mean_of_clipped, sensitivity, epsilon, B)

    # calculate mean squared error
    # laplace_mse = np.mean((data - private_mean_laplace)**2)
    # snapped_mse = np.mean((data - private_mean_snapped)**2)

    # NOTE: not sure if this is exactly the right error metric -- should they be compared to the observed mean?
    private_mean_laplace_error = abs(private_mean_laplace - observed_mean_of_clipped)
    private_mean_snapped_error = abs(private_mean_snapped - observed_mean_of_clipped)
    laplace_snapped_diff = abs(private_mean_laplace - private_mean_snapped)

    # return list of information about the test
    return([dist, mean, sd, lower_bound, upper_bound, epsilon, n, observed_mean_of_clipped, sensitivity,
            private_mean_laplace, private_mean_snapped, private_mean_laplace_error, private_mean_snapped_error, laplace_snapped_diff])

def create_df(results_list):
    return(pd.DataFrame(results_list,
                              columns = ['distribution', 'mean', 'sd', 'lower_bound', 'upper_bound',
                                         'epsilon', 'n', 'observed_mean_of_clipped',
                                         'sensitivity', 'private_mean_laplace', 'private_mean_snapped',
                                         'private_mean_laplace_error', 'private_mean_snapped_error',
                                         'laplace_snapped_diff']))

def create_df_and_plot_results(results_list, output_dir, dist, name):
    # create output subdirectory
    inner_output_dir = os.path.join(output_dir, dist, name)
    if not os.path.exists(inner_output_dir):
        os.makedirs(inner_output_dir)

    # create pandas dataframe of results
    results_df = create_df(results_list)

    # save results dataframe
    results_df.to_csv(os.path.join(inner_output_dir, 'test_results.csv'))

    # histogram of laplace_snapped_diff by epsilon/n
    # xlab_format = lambda x,pos : "${}$".format(f._formatSciNotation('%1.10e' % x))
    plot = sns.FacetGrid(results_df, row = 'epsilon', col = 'n', sharex = False, sharey = False, margin_titles = True)
    plot.map(sns.distplot, 'laplace_snapped_diff', bins = 30, kde = False, hist_kws = dict(edgecolor = 'black', linewidth = 1))
    for row in plot.axes:
        for subplot in row:
            plt.sca(subplot)
            plt.xticks(size = 7, rotation = -30)
    plot.fig.tight_layout()
    plot.savefig(os.path.join(inner_output_dir, 'laplace_snapped_difference_dist.png'))
    #
    # if type == 'overall':
    #     # plot nrmsd_snapped_performance by other variables
    #     x_vars = ['sd', 'bound_sd', 'epsilon', 'n', 'sensitivity']
    #     for x_var in x_vars:
    #         # static seaborn png
    #         plt.figure()
    #         plot = sns.scatterplot(x = x_var, y = 'nrmsd_snapped_performance', data = results_df)
    #         plot_fig = plot.get_figure()
    #         plot_fig.savefig(os.path.join(output_dir, 'nrmsd_snapped_perf_by_{0}.png'.format(x_var)))
    #
    #         # plotly html
    #         fig = plotly.express.scatter(results_df, x = x_var, y = 'nrmsd_snapped_performance', hover_data = ['mean', 'sd', 'epsilon', 'n', 'sensitivity', 'nrmsd_snapped_performance'])
    #         plotly.offline.plot(fig, filename = os.path.join(output_dir, 'nrmsd_snapped_perf_by_{0}.html'.format(x_var)), auto_open=False)
    #
    #     # plot raw distribution of nrmsd_snapped_performance
    #     plt.figure()
    #     plot = sns.distplot(np.clip(results_df.nrmsd_snapped_performance,-5e-4, 5e-4), bins = 30, kde = False, hist_kws = dict(edgecolor='black', linewidth = 1))
    #     plot_fig = plot.get_figure()
    #     plot_fig.savefig(os.path.join(output_dir, 'nrmsd_snapped_perf_dist.png'))

    return(None)

def run_tests(output_dir):
    # build results dataframe
    results = []

    # create grid of parameters
    dists = ['normal', 'lognormal']
    mean = 0
    sds = [10**n for n in range(-2, 3)]
    bound_sds = [1,2,3,4]
    epsilons = [0.1, 0.3, 0.5, 0.7, 0.9]
    ns = [10**n for n in range(1, 5)]
    n_tests = len(dists) * len(sds) * len(bound_sds) * len(epsilons) * len(ns)

    test_num = 0
    for dist in dists:
        for sd in sds:
            for bound_sd in bound_sds:
                sd_bound_sd_combination_results = []
                for epsilon in epsilons:
                    for n in ns:
                        test_num += 1
                        print('test {0} of {1}'.format(test_num, n_tests))
                        for i in range(1000):
                            # test combination of parameters and plot distribution of
                            sd_bound_sd_combination_results.append(test(dist, mean, sd, bound_sd, epsilon, n))
                create_df_and_plot_results(sd_bound_sd_combination_results, output_dir, dist, name = 'sd_{0}_bound_sd_{1}'.format(sd, bound_sd))
                results.extend(sd_bound_sd_combination_results)

    # create overall dataframe
    overall_df = create_df(results)

    # get statistics by group
    grouped_df = overall_df.groupby(['distribution', 'sd', 'lower_bound', 'upper_bound', 'epsilon', 'n'])
    grouped_df_statistics = grouped_df.describe()
    grouped_df_statistics.to_csv(os.path.join(output_dir, 'overall_statistics.csv'))

    # results_df['nrmsd_snapped_performance'] = results_df['laplace_nmrsd'] - results_df['snapped_nmrsd']
    # results_df['log10_nrmsd_snapped_performance'] = np.log10(results_df['nrmsd_snapped_performance'])

    # return results dataframe
    # results_df.to_csv(os.path.join(output_dir, 'test_results.csv'))
    return(None)

def main():
    # Stop plots from displaying
    mpl.use('Agg')

    # set output location
    output_dir = os.path.join('mean_release_output')
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # run tests
    run_tests(output_dir)

if __name__ == '__main__':
    main()
