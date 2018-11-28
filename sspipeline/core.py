#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 The MUSSLES Developers
#
# This file is part of MUSSLES.
#
# MUSSLES is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# MUSSLES is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with MUSSLES.  If not, see <http://www.gnu.org/licenses/>.

# Tell module what it's allowed to import
__all__ = [
    "runner",
    "history_plots",
    "final_params_pool",
    "max_ls_parameters",
    "diagnostic_plots",
]

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
from tqdm import tqdm

from .utils import log

plt.style.use("ggplot")
COLORS = ["#34495e", "#95a5a6", "#a76c6e"]


def update_mean(m, X):
    """
    Online adaptation of the mean of the previous MCMC iterates. Used to
    tune the MCMC proposal distribution.
    See Haario et al (2001; https://projecteuclid.org/euclid.bj/1080222083) for
    more information.
    """
    N = len(X[0])
    n = []
    for i in range(len(m)):
        n.append([(m[i][0] * (N - 1) + X[i][-1]) / N])
    return np.array(n)


def update_cov(X, m, Ct, Sd, Id, eps):
    """
    Online adaptation of the covariance of the previous MCMC iterates. Used to
    tune the MCMC proposal distribution.
    See Haario et al (2001; https://projecteuclid.org/euclid.bj/1080222083) for
    more information.
    """
    m1 = update_mean(m, X)
    t = len(X[0]) - 1
    part1 = ((t - 1) / t) * Ct
    part2 = t * np.matmul(m, np.transpose(m))
    part3 = (t + 1) * np.matmul(m1, np.transpose(m1))
    Xt = []
    Xt.append(X[:, -1])
    part4 = np.matmul(np.transpose(Xt), Xt)
    part5 = eps * Id
    cov = part1 + (Sd / t) * (part2 - part3 + part4 + part5)
    return (cov + np.transpose(cov)) / 2, m1


def random_move(current_state, X, Ct, t, t0, stepsize, data_meas, logpost, m, S_d, I_d):
    """
    Proposal step of the Metropolis-Hastings algorithm. This is a multivariate
    normal random draw, given the current Markov chain state and the covariance
    matrix from the `update_cov` above.
    Returns the proposed move and log-posterior score, to be used in the
    Metropolis acceptance probability calculation in the main iteration.
    """
    if t <= t0:
        next_move = stats.multivariate_normal.rvs(current_state, stepsize)
        return next_move, logpost(next_move, data_meas), m, stepsize
    elif t == t0 + 1:
        n = []
        for i in range(len(X)):
            n.append([np.mean(X[i])])
        cov = S_d * np.cov(X) + I_d * 0.0001 * S_d
        next_move = stats.multivariate_normal.rvs(current_state, cov)
        return next_move, logpost(next_move, data_meas), n, cov
    else:
        cov, m1 = update_cov(X, m, Ct, S_d, I_d, 0.0001)
        next_move = stats.multivariate_normal.rvs(current_state, cov)
        return next_move, logpost(next_move, data_meas), m1, cov


def adaptivemcmc(initial_state, n_iter, stepsize, data_meas, logpost, t0):
    """
    Simple adaptive Metropolis-Hastings iteration, as detailed by Haario et al
    (2001; https://projecteuclid.org/euclid.bj/1080222083).
    """
    d = len(initial_state)
    I_d = np.identity(d)
    S_d = (2.4) ** 2 / d
    parameters = []
    current_state = initial_state
    current_value = logpost(initial_state, data_meas)
    for i in range(d):
        parameters.append([])
        parameters[i].append(initial_state[i])
    lpost = [current_value]
    n_accept = 0
    S = 0
    np.seterr(over="ignore")
    cov = stepsize
    m = []
    for t in tqdm(range(n_iter)):
        S += 1
        nextMove, nextValue, m, cov = random_move(
            current_state,
            np.array(parameters),
            cov,
            t,
            t0,
            stepsize,
            data_meas,
            logpost,
            m,
            S_d,
            I_d,
        )
        delta_obj = np.exp(nextValue - lpost[-1])
        if delta_obj > 1:
            n_accept += 1
            for i in range(d):
                parameters[i].append(nextMove[i])
            lpost.append(nextValue)
            current_state = nextMove
            current_value = nextValue
        else:
            p_accept = delta_obj
            accept = np.random.choice([True, False], p=[p_accept, 1 - p_accept])
            if accept:
                n_accept += 1
                for i in range(d):
                    parameters[i].append(nextMove[i])
                lpost.append(nextValue)
                current_state = nextMove
                current_value = nextValue
            else:
                for i in range(d):
                    parameters[i].append(parameters[i][-1])
                lpost.append(lpost[-1])
    return (parameters, lpost, n_accept / S)


def runner(m, n_iter, data_meas, logpost, t=1000, stepsize=[10, 2, 0.01]):
    """
    Driver to run `m` separate simulations of the Adaptive Metropolis-Hastings
    algorithm (`adaptivemcmc` above).
    """
    np.seterr(divide="ignore", invalid="ignore")
    loc_est = np.median(data_meas)
    scale_est = (np.percentile(data_meas, 75) - np.percentile(data_meas, 25)) / 2
    shape_est = 0.01
    problems = []
    for i in range(m):
        ui = np.random.randint(low=loc_est, high=loc_est + 100)
        si = np.random.randint(low=scale_est, high=scale_est + 100)
        shapei = shape_est
        theta = [ui, si, shapei]
        problems.append(theta)
    ar, mcmc_chains, ls = [], [], []
    for i in range(m):
        print("INFO : running Chain " + str(i + 1))
        parameters, l, r = adaptivemcmc(
            problems[i], n_iter, stepsize, data_meas, logpost, t
        )
        mcmc_chains.append(parameters)
        ar.append(r)
        ls.append(l)
    return mcmc_chains, ar, ls


def history_plots(mcmc_chains, true_params=None, output_dir="output"):
    """
    Make history plots for the Markov chain output from the `adaptivemcmc`
    simulations.
    """
    m = len(mcmc_chains)
    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(16, 6))
    fig.suptitle("History Plots", fontsize=14)
    # mu parameter
    for j in range(m):
        chain_0j = []
        for k in range(len(mcmc_chains[j][0])):
            chain_0j.append(mcmc_chains[j][0][k] / 1000)
        ax[0].plot(chain_0j, label="Sequence {0}".format(j + 1), color=COLORS[j % 3])
    if true_params is not None:
        ax[0].plot(
            ax[0].get_xbound(),
            [true_params[0], true_params[0]],
            color="black",
            linestyle="dashed",
            label=r"$\mu$ true value",
            linewidth=2.5,
        )
    ax[0].set_xlabel("Iteration", fontsize=14)
    ax[0].set_ylabel(r"$\mu$ Trace [m]", fontsize=14)
    ax[0].legend(loc="best")
    # sigma parameter
    for j in range(m):
        chain_1j = []
        for k in range(len(mcmc_chains[j][1])):
            chain_1j.append(mcmc_chains[j][1][k] / 1000)
        ax[1].plot(chain_1j, label="Sequence {0}".format(j + 1), color=COLORS[j % 3])
    if true_params is not None:
        ax[1].plot(
            ax[1].get_xbound(),
            [true_params[1], true_params[1]],
            color="black",
            linestyle="dashed",
            label=r"$\mu$ true value",
            linewidth=2.5,
        )
    ax[1].set_xlabel("Iteration", fontsize=14)
    ax[1].set_ylabel(r"$\sigma$ Trace [m]", fontsize=14)
    ax[1].legend(loc="best")
    # xi parameter
    for j in range(m):
        ax[2].plot(
            mcmc_chains[j][2], label="Sequence {0}".format(j + 1), color=COLORS[j % 3]
        )
    if true_params is not None:
        ax[2].plot(
            ax[2].get_xbound(),
            [true_params[2], true_params[2]],
            color="black",
            linestyle="dashed",
            label=r"$\mu$ true value",
            linewidth=2.5,
        )
    ax[2].set_xlabel("Iteration", fontsize=14)
    ax[2].set_ylabel(r"$\xi$ Trace", fontsize=14)
    ax[2].legend(loc="best")
    fig.savefig(output_dir + "plots/history_plots.png")


def final_params_pool(mcmc_chains, burnin, lags, output_dir="output", plot=False):
    """
    Take the raw `adaptivemcmc` output, and apply the burn-in (denoting when we
    have evidence that they have reached the stationary distribution) and the
    thinning (lag; denoting how far apart Markov chain iterates must be before
    we believe they are roughly independent draws from the posterior). Results
    in a pool of concomitant parameter sets that represent independent samples
    from the joint posterior distribution of the parameters, given the processed
    tide gauge data.
    """
    m, n = len(mcmc_chains), len(mcmc_chains[0][0])
    params_pool, params_ana = [], [[] for i in range(3)]
    for i in range(m):
        for j in range(burnin, n, lags[i]):
            params_pool.append([])
            for k in range(3):
                params_ana[k].append(mcmc_chains[i][k][j])
                params_pool[-1].append(mcmc_chains[i][k][j])

    if plot:
        fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(16, 6))
        # mu parameter
        params_ana_0 = []
        for i in range(len(params_ana[0])):
            params_ana_0.append(params_ana[0][i] / 1000)
        ax[0].hist(params_ana_0, color="#34495e", edgecolor="white")
        ax[0].set_xlabel(r"$\mu$ [m]")
        ax[0].set_ylabel("Frequency")
        ax[0].grid(alpha=0.5)
        # sigma parameter
        params_ana_1 = []
        for i in range(len(params_ana[1])):
            params_ana_1.append(params_ana[1][i] / 1000)
        ax[1].hist(params_ana_1, color="#34495e", edgecolor="white")
        ax[1].set_xlabel(r"$\sigma$ [m]")
        ax[1].set_ylabel("Frequency")
        ax[1].grid(alpha=0.5)
        # c parameter
        ax[2].hist(params_ana[2], color="#34495e", edgecolor="white")
        ax[2].set_xlabel(r"$\xi$")
        ax[2].set_ylabel("Frequency")
        ax[2].grid(alpha=0.5)
        # output the figure
        fig.savefig(output_dir + "plots/params_pool.png")
    return params_pool


def max_ls_parameters(ls, mcmc_chains, logger, verbose):
    """
    Determine the maximum log-posterior score set of parameters, from the
    `mcmc_chains` output.
    """
    max_indices = []
    maxs = []
    for i in range(len(mcmc_chains)):
        max_indices.append(np.where(np.array(ls[i]) == np.array(ls[i]).max())[0][0])
        maxs.append(np.array(ls[i]).max())
    seqi = np.where(np.array(maxs) == np.array(maxs).max())[0][0]
    iterj = max_indices[seqi]
    max_params = []
    d = len(mcmc_chains[0])
    for i in range(d):
        max_params.append(mcmc_chains[seqi][i][iterj])
    logger = log(
        logger,
        "the parameters with max log-posterior score are: ["
        + str(max_params[0] / 1000)
        + ", "
        + str(max_params[1] / 1000)
        + ", "
        + str(max_params[2])
        + "]",
        verbose,
    )
    return max_params


def diagnostic_plots(
    data_meas, max_params, params_analysis, output_dir="output", plot=False
):
    """
    Generates a set of diagnostic plots, as displayed in the accompanying code
    examples and JOSS manuscript. Includes:
    A) probability plot:  shows the empirical CDF probabilities for each data
       point from the processed data set, along with the corresponding modeled
       estimate associated with those events is.
    B) quantile plot:  shows the observed extreme sea levels, along with the
       corresponding model estimates for sea levels with the same annual
       probability
    C) return level plot:  shows the return periods (x-axis), which denote the
       number of years, on average, we expect to see a storm with the given
       return level (y-axis) in surge height.
    D) density plot:  the estimated distribution of annual maximum sea levels,
       with the histogram of processed data points superimposed
    """
    data = []
    for i in range(len(data_meas)):
        data.append(data_meas[i] / 1000)
    RP = np.arange(2, 501, 1)
    RL = []
    RL_max = []
    percentile_05 = []
    percentile_1 = []
    percentile_2 = []
    percentile_5 = []
    percentile_95 = []
    percentile_98 = []
    percentile_99 = []
    percentile_995 = []
    for i in range(len(RP)):
        RL.append([])
        RL_max.append(
            stats.genextreme.ppf(
                q=(1 - 1 / RP[i]),
                c=-max_params[2],
                loc=max_params[0] / 1000,
                scale=max_params[1] / 1000,
            )
        )
        for j in range(len(params_analysis)):
            RL[i].append(
                stats.genextreme.ppf(
                    q=(1 - 1 / RP[i]),
                    c=-params_analysis[j][2],
                    loc=params_analysis[j][0] / 1000,
                    scale=params_analysis[j][1] / 1000,
                )
            )
    for i in range(len(RL)):
        percentile_95.append(np.percentile((RL[i]), 95))
        percentile_5.append(np.percentile((RL[i]), 5))

        percentile_98.append(np.percentile((RL[i]), 98))
        percentile_2.append(np.percentile((RL[i]), 2))

        percentile_99.append(np.percentile((RL[i]), 99))
        percentile_1.append(np.percentile((RL[i]), 1))

        percentile_995.append(np.percentile((RL[i]), 99.5))
        percentile_05.append(np.percentile((RL[i]), 0.5))

    empirical = [
        stats.genextreme.ppf(
            q=(i + 1) / (len(data) + 1),
            c=-max_params[2],
            loc=max_params[0] / 1000,
            scale=max_params[1] / 1000,
        )
        for i in range(len(data))
    ]
    cdf = [
        stats.genextreme.cdf(
            x=np.sort(data)[i],
            c=-max_params[2],
            loc=max_params[0] / 1000,
            scale=max_params[1] / 1000,
        )
        for i in range(len(data))
    ]
    x_range = np.arange(0, max(data) + 1, 0.0005)
    y_range = [
        stats.genextreme.pdf(
            x=xi, c=-max_params[2], loc=max_params[0] / 1000, scale=max_params[1] / 1000
        )
        for xi in x_range
    ]

    if plot:
        fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(18, 12))

        ax[0, 0].scatter(
            cdf, [(i + 1) / (len(data) + 1) for i in range(len(data))], color="black"
        )
        ax[0, 0].plot(np.arange(0, 1, 0.01), np.arange(0, 1, 0.01), color="steelblue")
        ax[0, 0].set_title("Probability Plot", fontsize=14)
        ax[0, 0].set_xlabel("Model", fontsize=14)
        ax[0, 0].set_ylabel("Empirical", fontsize=14)
        ax[0, 0].annotate("$\mathbf{A}$", xy=(0.0, 1.03), xycoords="axes fraction", fontsize=16)

        ax[0, 1].scatter(empirical, np.sort(data), color="black")
        ax[0, 1].plot(
            np.arange(0, int(round(np.max(data), 0)) + 1),
            np.arange(0, int(round(np.max(data), 0)) + 1),
            color="steelblue",
        )
        ax[0, 1].set_title("Quantile Plot", fontsize=14)
        ax[0, 1].set_xlabel("Model [m]", fontsize=14)
        ax[0, 1].set_ylabel("Empirical [m]", fontsize=14)
        ax[0, 1].set_xlim(ax[0, 1].set_ylim()[0], ax[0, 1].set_ylim()[1])
        ax[0, 1].annotate("$\mathbf{B}$", xy=(0.0, 1.03), xycoords="axes fraction", fontsize=16)

        ax[1, 0].plot(
            np.log10(RP), RL_max, color="r", label="Max Posterior Score Parameter Sets"
        )
        ax[1, 0].scatter(
            np.log10(
                [
                    (len(data) + 1) / (len(data) + 1 - k)
                    for k in np.arange(1, len(data) + 1, 1)
                ]
            ),
            np.sort(data),
            label="Actual Sorted Observations",
            color="black",
            marker="X",
        )
        ax[1, 0].fill_between(
            x=np.log10(RP),
            y1=percentile_95,
            y2=percentile_5,
            alpha=0.3,
            label="90% Credible Interval",
            facecolor="skyblue",
        )
        ax[1, 0].fill_between(
            x=np.log10(RP),
            y1=percentile_995,
            y2=percentile_05,
            alpha=0.27,
            label="99% Credible Interval",
            facecolor="skyblue",
        )
        ax[1, 0].legend(loc="upper left", fontsize=10)
        ax[1, 0].set_xticks(np.log10([1, 2, 5, 10, 20, 100, 200, 500]))
        ax[1, 0].set_xticklabels([1, 2, 5, 10, 20, 100, 200, 500])
        ax[1, 0].set_title("Return Level Plot", fontsize=14)
        ax[1, 0].set_xlabel("Return Period [years]", fontsize=14)
        ax[1, 0].set_ylabel("Return Level [m]", fontsize=14)
        if ax[1, 0].set_ylim()[1] > 10:
            ax[1, 0].set_ylim(0, 10)
        ax[1, 0].annotate("$\mathbf{C}$", xy=(0.0, 1.03), xycoords="axes fraction", fontsize=16)

        ax[1, 1].hist(
            data,
            bins=np.linspace(min(data), max(data)),
            density=True,
            edgecolor="black",
            label="Histogram for Observations",
            color="white",
            alpha=0.4,
        )
        ax[1, 1].plot(x_range, y_range, label="Best Model", color="black")
        ax[1, 1].plot(
            data, np.zeros_like(data), "b+", ms=20, color="black", label="Observations"
        )
        ax[1, 1].legend(loc="best", fontsize=10)
        ax[1, 1].set_yticklabels([])
        ax[1, 1].set_title("Density Plot", fontsize=14)
        ax[1, 1].set_xlabel("Annual Max Sea Level [m]", fontsize=14)
        ax[1, 1].set_ylabel("Density", fontsize=14)
        ax[1, 1].set_xlim(ax[0, 1].set_xlim()[0], ax[0, 1].set_xlim()[1])
        ax[1, 1].annotate("$\mathbf{D}$", xy=(0.0, 1.03), xycoords="axes fraction", fontsize=16)

        fig.savefig(output_dir + "plots/diagnostic_plots.png")

    return (
        percentile_05,
        percentile_1,
        percentile_2,
        percentile_5,
        percentile_95,
        percentile_98,
        percentile_99,
        percentile_995,
    )


def output_parameters(mcmc_chains, burnin, lags, output_dir="output"):
    '''
    Can uncomment the f.write statements below in order to separate out which
    parameters came from which chains.
    '''
    for i in range(len(mcmc_chains[0])):
        with open(output_dir + "parameters/parameter-" + str(i + 1) + ".txt", "w") as f:
            for j in range(len(mcmc_chains)):
                #if j == 0:
                #    f.write("CHAIN " + str(j + 1) + "\n")
                #else:
                #    f.write("\n\nCHAIN " + str(j + 1) + "\n")
                #f.write("==========\n\n")
                for k in range(burnin, len(mcmc_chains[j][i]), lags[j]):
                    f.write(str(mcmc_chains[j][i][k]) + "\n")
