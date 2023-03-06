# HMM-SPY-returns

Using hmmlearn to identify two latent states and their respective future return distributions for SPY on a daily timeframe. The SPY daily data is retrieved with yfinance. This code is just a stepping-stone and could be improved by utilizing a top-down hierarchical model on data with more granularity. Example: A coarse HMM predicts states on daily data, then another finer HMM predicts states on hourly data.
