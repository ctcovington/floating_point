import cc_snap
import cc_laplace
import numpy as np
import pandas as pd
import os
import shutil
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import rpy2.robjects
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

def test(distribution, mean, sd, bound_sd, epsilon, n, r_object):
    """"""
    # generate simulated data
    if distribution == 'normal':
        data = generate_gaussian_data(mean, sd, n)
    elif distribution == 'lognormal':
        data = generate_lognormal_data(mean, sd, n)

    # use -/+ <bound_sd> std_dev as the lower/upper bounds we imagine the user could set
    lower_bound = mean - bound_sd * sd # NOTE: mean should be 0, but kept general in case we want to make changes later
    upper_bound = mean + bound_sd * sd # NOTE: mean should be 0, but kept general in case we want to make changes later
    B = max(abs(lower_bound), abs(upper_bound))

    # clip data
    data_clipped = np.clip(data, lower_bound, upper_bound)
    observed_mean_of_clipped = np.mean(data_clipped)
    sensitivity = (upper_bound - lower_bound) / n

    # generate private means using all mechanisms
    private_mean_laplace = cc_laplace.add_laplace_noise(observed_mean_of_clipped, sensitivity, epsilon)
    private_mean_snapped = cc_snap.add_snapped_laplace_noise(observed_mean_of_clipped, sensitivity, epsilon, B)
    private_mean_snapped_gk_object = r_object.slaplace(observed_mean_of_clipped, sensitivity, epsilon, -B, B)
    private_mean_snapped_gk = next(private_mean_snapped_gk_object.items())[1] # NOTE: this should work?

    # NOTE: not sure if this is exactly the right error metric -- should they be compared to the observed mean?
    private_mean_laplace_error = abs(private_mean_laplace - observed_mean_of_clipped)
    private_mean_snapped_error = abs(private_mean_snapped - observed_mean_of_clipped)
    private_mean_snapped_gk_error = abs(private_mean_snapped_gk - observed_mean_of_clipped)
    laplace_snapped_diff = abs(private_mean_laplace - private_mean_snapped)

    # return list of information about the test
    return([distribution, mean, sd, bound_sd, lower_bound, upper_bound, epsilon, n, observed_mean_of_clipped, sensitivity,
            private_mean_laplace, private_mean_snapped, private_mean_snapped_gk,
            private_mean_laplace_error, private_mean_snapped_error, private_mean_snapped_gk_error, laplace_snapped_diff])

def create_df(results_list):
    """
    create standard dataframe from list of results
    """
    return(pd.DataFrame(results_list,
                              columns = ['distribution', 'mean', 'sd', 'bound_sd', 'lower_bound', 'upper_bound',
                                         'epsilon', 'n', 'observed_mean_of_clipped',
                                         'sensitivity', 'private_mean_laplace', 'private_mean_snapped', 'private_mean_snapped_gk',
                                         'private_mean_laplace_error', 'private_mean_snapped_error', 'private_mean_snapped_gk_error',
                                         'laplace_snapped_diff']))

def multihist(x, hue, n_bins = 30, color = None, **kws):
    """"""
    bins = np.linspace(0, np.max(x), n_bins)
    for name, x_i in x.groupby(hue):
        sns.distplot(x_i, bins = bins, label = name, **kws)
    return(None)

def plot_results(results_list, output_dir, distribution, sd_bound_sd_name):
    """"""
    # create output subdirectory
    inner_output_dir = os.path.join(output_dir, distribution, sd_bound_sd_name)
    if not os.path.exists(inner_output_dir):
        os.makedirs(inner_output_dir)

    # create pandas dataframe of results
    results_df = create_df(results_list)

    # create new variable denoting which mechanism had lower error
    mechanism_comparison_conditions = [results_df['private_mean_laplace_error'] < results_df['private_mean_snapped_error'],
                                       results_df['private_mean_laplace_error'] == results_df['private_mean_snapped_error'],
                                       results_df['private_mean_laplace_error'] > results_df['private_mean_snapped_error']]
    mechanism_comparison_choices = ['laplace', 'tie', 'snapped']
    results_df['lower_error_mechanism'] = np.select(mechanism_comparison_conditions, mechanism_comparison_choices)

    # save results dataframe
    results_df.to_csv(os.path.join(inner_output_dir, 'test_results.csv'))

    '''
    histograms of laplace_snapped_diff by epsilon and n
    '''
    plot = sns.FacetGrid(results_df, row = 'epsilon', col = 'n',
                         sharex = False, sharey = False, margin_titles = True, legend_out = True)
    plot.map(multihist, 'laplace_snapped_diff', 'lower_error_mechanism', kde = False, hist_kws = dict(edgecolor = 'black', linewidth = 1))
    plot.add_legend()
    for row in plot.axes:
        for subplot in row:
            plt.sca(subplot)
            plt.xticks(size = 5.5, rotation = -30)
    plot.fig.subplots_adjust(bottom = 0.05)
    plot.savefig(os.path.join(inner_output_dir, 'laplace_snapped_difference_dist.png'))
    plt.close()

    '''
    histograms of error for each mechanism
    '''
    long_df = pd.melt(results_df, id_vars = ['epsilon', 'n'], value_vars = ['private_mean_laplace_error', 'private_mean_snapped_error', 'private_mean_snapped_gk_error'],
                      var_name = 'mechanism', value_name = 'error')
    long_df['mechanism'] = long_df['mechanism'].replace({'private_mean_laplace_error': 'laplace',
                                                         'private_mean_snapped_error': 'snapping_cc',
                                                         'private_mean_snapped_gk_error': 'snapping_gk'})
    plot = sns.FacetGrid(long_df, row = 'epsilon', col = 'n',
                         sharex = False, sharey = False, margin_titles = True, legend_out = True)
    plot.map(multihist, 'error', 'mechanism', kde = False, hist_kws = dict(edgecolor = 'black', linewidth = 1))
    plot.add_legend()
    for row in plot.axes:
        for subplot in row:
            plt.sca(subplot)
            plt.xticks(size = 5.5, rotation = -30)
    plot.fig.subplots_adjust(bottom = 0.05)
    plot.savefig(os.path.join(inner_output_dir, 'error_dist_by_mechanism.png'))
    plt.close()

    # '''
    # histograms of laplace_snapped_diff, separated by lower_error_mechanism by epsilon and n
    # '''
    # plot = sns.FacetGrid(results_df, row = 'epsilon', col = 'n', sharex = False, sharey = False, margin_titles = True)
    # plot.map(sns.distplot, 'laplace_snapped_diff', bins = 30, kde = False, hist_kws = dict(edgecolor = 'black', linewidth = 1))
    # for row in plot.axes:
    #     for subplot in row:
    #         plt.sca(subplot)
    #         plt.xticks(size = 7, rotation = -30)
    # plot.fig.tight_layout()
    # plot.savefig(os.path.join(inner_output_dir, 'laplace_snapped_difference_dist.png'))

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
    """"""
    # build results dataframe
    results = []

    # initialize rpy2 object to call R functions
    r_object = rpy2.robjects.r
    r_object.source('gk_snap.R')

    # create grid of parameters
    distributions = ['normal', 'lognormal']
    mean = 0
    sds = [10**n for n in range(-1, 3)]
    bound_sds = [1,2,3]
    epsilons = [0.1, 0.3, 0.5, 0.7, 0.9]
    ns = [10**n for n in range(2, 5)]
    n_tests = len(distributions) * len(sds) * len(bound_sds) * len(epsilons) * len(ns)

    test_num = 0
    for distribution in distributions:
        for sd in sds:
            for bound_sd in bound_sds:
                sd_bound_sd_combination_results = []
                sd_bound_sd_name = 'sd_{0}_bound_sd_{1}'.format(sd, bound_sd)
                for epsilon in epsilons:
                    for n in ns:
                        epsilon_n_name = 'epsilon_{0}_n_{1}'.format(epsilon, n)
                        test_num += 1
                        print('test {0} of {1}'.format(test_num, n_tests))
                        for i in range(1000):
                            # test combination of parameters
                            test_results = test(distribution, mean, sd, bound_sd, epsilon, n, r_object)
                            sd_bound_sd_combination_results.append(test_results)

                # plot results at level of distribution/sd/bound_sd
                plot_results(sd_bound_sd_combination_results, output_dir, distribution, sd_bound_sd_name)

                # add results to overall results list
                results.extend(sd_bound_sd_combination_results)

    # create overall dataframe
    overall_df = create_df(results)

    # get statistics by group
    grouped_df = overall_df.groupby(['distribution', 'sd', 'bound_sd', 'epsilon', 'n'])
    grouped_df_statistics = grouped_df.describe()
    grouped_df_statistics.to_csv(os.path.join(output_dir, 'overall_statistics.csv'))

    # show boxplots of log10_laplace_snapped_diff by sensitivity/distribution
    overall_df['rounded_sensitivity'] = round(overall_df['sensitivity'], 3)
    overall_df['log10_laplace_snapped_diff'] = np.log10(overall_df['laplace_snapped_diff'])
    plt.figure()
    plot = sns.boxplot(x = 'rounded_sensitivity', y = 'log10_laplace_snapped_diff', hue = 'distribution', data = overall_df)
    plt.xticks(size = 7, rotation = -30)
    plot.xaxis.set_label_text('sensitivity (rounded to 3 significant figures)')
    plot.yaxis.set_label_text('log10(|estimate_from_laplace - estimate_from_snapped|)')
    plot_fig = plot.get_figure()
    plot_fig.savefig(os.path.join(output_dir, 'log10_laplace_snapped_diff_boxplots.png'))
    plt.close()

    return(None)

def main():
    # Stop plots from displaying
    mpl.use('Agg')

    # set output location
    output_dir = os.path.join('mean_release_output')
    shutil.rmtree(output_dir)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # run tests
    run_tests(output_dir)

if __name__ == '__main__':
    main()
