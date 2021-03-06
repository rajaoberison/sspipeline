<!-- markdownlint-disable MD033 -->
<!-- markdownlint-disable MD022 -->

# SSPipeline Example

## Motivation

Here is a demo for our SSPipeline package. These examples use the [Wilmington, North Carolina,
USA](https://uhslc.soest.hawaii.edu/rqds/atlantic/doc/qa750a.dmt) and [Grand Isle, Louisiana,
USA](https://uhslc.soest.hawaii.edu/rqds/atlantic/doc/qa765a.dmt) datasets from the University of Hawaii Sea
Level Center (UHSLC). The example only takes 2-3 minutes (per dataset) to run on an average computer.

## Directory Structure

./

- example "home" directory

[`./configs/`](configs)

- home of the different configuration files for the example

[`./data/`](data)

- directory for the data set used in the example

[`./output/`](output)

- output directory for the example

## Usage

The [`bootstrap.sh`](bootstrap.sh) file is the script that you will want to run everything from. To see exactly what this script does, you can run the following to get the usage message:

```sh
bash bootstrap.sh --help
```

If you want to just solely run the example:

```sh
bash bootstrap.sh run
```

Note that if you want to play around with the parameters with which the example uses to fit the data set, check out all three of the examples configurations files [here](configs).

## Results

<details><summary>Wilmington, North Carolina, USA</summary>

**Diagnostic Plots:** [link](output/h750a/plots/diagnostic_plots.png)

![Diagnostic Plot](output/h750a/plots/diagnostic_plots.png)

**Other Plots:** [link to folder](output/h750a/plots)

- [ACF Function](output/h750a/plots/acf_function.png)
- [Annual Maximum](output/h750a/plots/annual_maximum.png)
- [Cleaned Data](output/h750a/plots/cleaned_data.png)
- [GR Diagnostic](output/h750a/plots/gr_diagnostic.png)
- [History Plots](output/h750a/plots/history_plots.png)
- [Parameter Pool](output/h750a/plots/params_pool.png)

**Calibrated Parameters:** [link to folder](output/h750a/parameters)

- [Parameter 1](output/h750a/parameters/parameter-1.txt)
- [Parameter 2](output/h750a/parameters/parameter-2.txt)
- [Parameter 3](output/h750a/parameters/parameter-3.txt)

**Return Levels:** [link](output/h750a/return_levels.csv)

**Log:** [link](output/h750a/sspipeline.log)

</details>

<details><summary>Grand Isle, Louisiana, USA</summary>

**Diagnostic Plots:** [link](output/h765a/plots/diagnostic_plots.png)

![Diagnostic Plot](output/h765a/plots/diagnostic_plots.png)

**Other Plots:** [link to folder](output/h765a/plots)

- [ACF Function](output/h765a/plots/acf_function.png)
- [Annual Maximum](output/h765a/plots/annual_maximum.png)
- [Cleaned Data](output/h765a/plots/cleaned_data.png)
- [GR Diagnostic](output/h765a/plots/gr_diagnostic.png)
- [History Plots](output/h765a/plots/history_plots.png)
- [Parameter Pool](output/h765a/plots/params_pool.png)

**Calibrated Parameters:** [link to folder](output/h765a/parameters)

- [Parameter 1](output/h765a/parameters/parameter-1.txt)
- [Parameter 2](output/h765a/parameters/parameter-2.txt)
- [Parameter 3](output/h765a/parameters/parameter-3.txt)

**Return Levels:** [link](output/h765a/return_levels.csv)

**Log:** [link](output/h765a/sspipeline.log)

</details>
