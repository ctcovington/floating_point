import cc_snap
import cc_laplace
import numpy as np
import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
import plotly, plotly.express

def generate_gaussian_data(mean, sd, n):
    """"""
    return(np.random.normal(loc = mean, scale = sd, size = n))

def test(mean, sd, epsilon, n):
    """"""
    # generate simulated data
    data = generate_gaussian_data(mean, sd, n)

    # use -/+ 3 std_dev as the lower/upper bounds we imagine the user could set
    lower_bound = mean - 3 * sd
    upper_bound = mean + 3 * sd

    # create two versions of data with separate means -- for laplace noise, the non-private mean is computed on clipped data
    # for the snapping mechanism, the non-private mean is computed on non-clipped data
    data_clipped = data
    data_clipped[data_clipped < lower_bound] = lower_bound
    data_clipped[data_clipped > upper_bound] = upper_bound

    observed_mean = np.mean(data)
    observed_mean_of_clipped = np.mean(data_clipped)

    sensitivity = (upper_bound - lower_bound) / n

    # generate private means using both the laplace and snapping mechanisms
    private_mean_laplace = cc_laplace.add_laplace_noise(observed_mean_of_clipped, sensitivity, epsilon)
    private_mean_snapped = cc_snap.add_snapped_laplace_noise(observed_mean, sensitivity, epsilon, B = max(abs(lower_bound), abs(upper_bound)))

    # calculate normalized root mean-squared deviation for each mechanism
    # https://en.wikipedia.org/wiki/Root-mean-square_deviation#Normalized_root-mean-square_deviation
    laplace_nmrsd = np.sqrt(np.mean((data - private_mean_laplace)**2)) / observed_mean_of_clipped
    snapped_nmrsd = np.sqrt(np.mean((data - private_mean_snapped)**2)) / observed_mean

    # return list of information about the test
    return([mean, sd, epsilon, n, observed_mean, observed_mean_of_clipped, sensitivity,
            private_mean_laplace, private_mean_snapped, laplace_nmrsd, snapped_nmrsd])

def run_tests(output_dir):
    # build results dataframe
    results = []
    num_iter = 10000

    # generate data, test mean release, and store results in dataframe
    for i in range(num_iter):
        if i % 100 == 0:
            print('iteration {0} of {1}'.format(i, num_iter))

        # generate various aspects of test -- mean, sd, and n of data, epsilon for DP-purposes
        mean = np.random.uniform(0, 1e5)
        sd = np.random.uniform(0, 5e4)
        n = np.random.randint(10, 10000)
        epsilon = np.random.uniform(0.1, 1)

        # test combination of parameters and append to list
        results.append(test(mean, sd, epsilon, n))

    # create results dataframe
    results_df = pd.DataFrame(results, columns = ['mean', 'sd', 'epsilon', 'n', 'observed_mean', 'observed_mean_of_clipped', 'sensitivity', 'private_mean_laplace', 'private_mean_snapped', 'laplace_nmrsd', 'snapped_nmrsd'])
    results_df['nrmsd_snapped_performance'] = results_df['laplace_nmrsd'] - results_df['snapped_nmrsd']
    # results_df['log10_nrmsd_snapped_performance'] = np.log10(results_df['nrmsd_snapped_performance'])

    # return results dataframe
    results_df.to_csv(os.path.join(output_dir, 'test_results.csv'))
    return(results_df)

def plot_results(results_df, output_dir):
    # plot nrmsd_snapped_performance by other variables
    x_vars = ['mean', 'epsilon', 'sensitivity']
    for x_var in x_vars:
        # static seaborn png
        plt.figure()
        plot = sns.scatterplot(x = x_var, y = 'nrmsd_snapped_performance', data = results_df)
        plot_fig = plot.get_figure()
        plot_fig.savefig(os.path.join(output_dir, 'nrmsd_snapped_perf_by_{0}.png'.format(x_var)))

        # plotly html
        fig = plotly.express.scatter(results_df, x = x_var, y = 'nrmsd_snapped_performance', hover_data = ['mean', 'sd', 'epsilon', 'n', 'sensitivity', 'nrmsd_snapped_performance'])
        plotly.offline.plot(fig, filename = os.path.join(output_dir, 'nrmsd_snapped_perf_by_{0}.html'.format(x_var)), auto_open=False)

    # plot raw distribution of nrmsd_snapped_performance
    plt.figure()
    plot = sns.distplot(np.clip(results_df.nrmsd_snapped_performance,-5e-4, 5e-4), bins = 30, kde = False, hist_kws = dict(edgecolor='black', linewidth = 1))
    plot_fig = plot.get_figure()
    plot_fig.savefig(os.path.join(output_dir, 'nrmsd_snapped_perf_dist.png'))

    return(None)

def main():
    # set output location
    output_dir = os.path.join('mean_release_output')
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # run tests
    results_df = run_tests(output_dir)

    # plot results
    plot_results(results_df, output_dir)

if __name__ == '__main__':
    main()
