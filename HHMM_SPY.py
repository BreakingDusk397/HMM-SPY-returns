# A rough implementation of a hierarchal hidden markov model based on yfinance data


import numpy as np
import pandas as pd
from matplotlib import cm, pyplot as plt
from hmmlearn.hmm import GaussianHMM
import scipy
import yfinance as yf
import seaborn as sns
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


sns.set()

import warnings
warnings.filterwarnings("ignore")

# Brute force modelling
def get_best_hmm_model(X, max_states, max_iter = 10000):
    best_score = -(10 ** 10)
    best_state = 0
    
    for state in range(1, max_states + 1):
        hmm_model = GaussianHMM(n_components = state, random_state = None,
                                covariance_type = "diag", n_iter = max_iter).fit(X)
        if hmm_model.score(X) > best_score:
            best_score = hmm_model.score(X)
            best_state = state
    
    best_model = GaussianHMM(n_components = best_state, random_state = None,
                                covariance_type = "diag", n_iter = max_iter).fit(X)
    return best_model

# Normalized st. deviation
def std_normalized(vals):
    return np.std(vals) / np.mean(vals)

# Ratio of diff between last price and mean value to last price
def ma_ratio(vals):
    return (vals[-1] - np.mean(vals)) / vals[-1]

# z-score for volumes and price
def values_deviation(vals):
    return (vals[-1] - np.mean(vals)) / np.std(vals)

# General plots of hidden states
def plot_hidden_states(hmm_model, data, X, column_price):
    plt.figure(figsize=(15, 15))
    fig, axs = plt.subplots(hmm_model.n_components, 3, figsize = (15, 15))
    colours = cm.prism(np.linspace(0, 1, hmm_model.n_components))
    hidden_states = hmm_model.predict(X)
    
    for i, (ax, colour) in enumerate(zip(axs, colours)):
        mask = hidden_states == i
        ax[0].plot(data.index, data[column_price], c = 'grey')
        ax[0].plot(data.index[mask], data[column_price][mask], '.', c = colour)
        ax[0].set_title("{0}th hidden state".format(i))
        ax[0].grid(True)
        
        ax[1].hist(data["future_return"][mask], bins = 30)
        ax[1].set_xlim([-0.1, 0.1])
        ax[1].set_title("future return distrbution at {}th hidden state, \n {}".format(i, (data["future_return"][mask]).mean()))
        ax[1].grid(True)
        
        ax[2].plot(data["future_return"][mask].cumsum(), c = colour)
        ax[2].set_title("cummulative future return at {0}th hidden state".format(i))
        ax[2].grid(True)
        
    plt.tight_layout()
    plt.show()


def mean_confidence_interval(vals, confidence):
    a = 1.0 * np.array(vals)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
    return m - h, m, m + h

def compare_hidden_states(hmm_model, cols_features, conf_interval, iters = 1000):
    plt.figure(figsize=(15, 15))
    fig, axs = plt.subplots(len(cols_features), hmm_model.n_components, figsize = (15, 15))
    colours = cm.prism(np.linspace(0, 1, hmm_model.n_components))
    
    for i in range(0, hmm_model.n_components):
        mc_df = pd.DataFrame()
    
        # Samples generation
        for j in range(0, iters):
            row = np.transpose(hmm_model._generate_sample_from_state(i))
            mc_df = mc_df.append(pd.DataFrame(row).T)
        mc_df.columns = cols_features
    
        for k in range(0, len(mc_df.columns)):
            axs[k][i].hist(mc_df[cols_features[k]], color = colours[i])
            axs[k][i].set_title(cols_features[k] + " (state " + str(i) + "): " + str(np.round(mean_confidence_interval(mc_df[cols_features[k]], conf_interval), 3)))
            axs[k][i].grid(True)
            
    plt.tight_layout()
    plt.show()




# get historical market data
spy = yf.Ticker("SPY")
spy.info
df = spy.history(period="max")

df = df.resample('M').agg({'Open':'first', 'High':'max', 
                                      'Low': 'min', 'Close':'last', 'Volume':'sum'})

column_price = 'Close'
column_high = 'High'
column_low = 'Low'
column_volume = 'Volume'

dataset = df.shift(1)

# Feature params
future_period = 1
std_period = 10
ma_period = 10
price_deviation_period = 10
volume_deviation_period = 10

# Create features 
cols_features = ['last_return', 'std_normalized', 'ma_ratio', 'price_deviation', 'volume_deviation', ]
dataset['last_return'] = dataset[column_price].pct_change()
dataset['std_normalized'] = dataset[column_price].rolling(std_period).apply(std_normalized)
dataset['ma_ratio'] = dataset[column_price].rolling(ma_period).apply(ma_ratio)
dataset['price_deviation'] = dataset[column_price].rolling(price_deviation_period).apply(values_deviation)
dataset['volume_deviation'] = dataset[column_volume].rolling(volume_deviation_period).apply(values_deviation)


dataset["future_return"] = dataset[column_price].pct_change(future_period).shift(-future_period)


dataset = dataset.replace([np.inf, -np.inf], np.nan)
dataset = dataset.dropna()

# Split the data on sets
train_ind = 1931
train_set = dataset[cols_features].values[:train_ind]
test_set = dataset[cols_features].values[train_ind:]


plt.tight_layout()

model = get_best_hmm_model(X = train_set, max_states = 3, max_iter = 100000000000000000000000000000)
print("Best model with {0} states ".format(str(model.n_components)))
df1 = pd.DataFrame(model.transmat_)
print("\n The best model transition matrix: \n ",df1)





plot_hidden_states(model, dataset[:train_ind].reset_index(), train_set, column_price)
#compare_hidden_states(hmm_model=model, cols_features=cols_features, conf_interval=0.95)

# Recreate today's data in another data frame
df['last_return'] = df[column_price].pct_change()
df['std_normalized'] = df[column_price].rolling(std_period).apply(std_normalized)
df['ma_ratio'] = df[column_price].rolling(ma_period).apply(ma_ratio)
df['price_deviation'] = df[column_price].rolling(price_deviation_period).apply(values_deviation)
df['volume_deviation'] = df[column_volume].rolling(volume_deviation_period).apply(values_deviation)
df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna()

last_row = df[-1:]
last_row = df[cols_features].values[-1:]
result = model.predict(last_row)
print("\n This month's hidden state: ", result)

df['m_states'] = model.predict(df[cols_features])



df_m_states = df['m_states']
df_m_states_copy = df['m_states']
df_m_states = df_m_states.resample('W').ffill()
#print(df_m_states)

spy = yf.Ticker("SPY")
spy.info
df = spy.history(period="max")

df = df.resample('W').agg({'Open':'first', 'High':'max', 
                                      'Low': 'min', 'Close':'last', 'Volume':'sum'})


df = pd.merge_asof(df, df_m_states, left_index=True, right_index=True, direction='nearest')

print(df)

###############################################################################################################################

dataset = df

std_period = 15
ma_period = 15
price_deviation_period = 15
volume_deviation_period = 15

# Create features 
cols_features = ['last_return', 'std_normalized', 'ma_ratio', 'price_deviation', 'volume_deviation', ]
dataset['last_return'] = dataset[column_price].pct_change()
dataset['std_normalized'] = dataset[column_price].rolling(std_period).apply(std_normalized)
dataset['ma_ratio'] = dataset[column_price].rolling(ma_period).apply(ma_ratio)
dataset['price_deviation'] = dataset[column_price].rolling(price_deviation_period).apply(values_deviation)
dataset['volume_deviation'] = dataset[column_volume].rolling(volume_deviation_period).apply(values_deviation)


dataset["future_return"] = dataset[column_price].pct_change(future_period).shift(-future_period)


dataset = dataset.replace([np.inf, -np.inf], np.nan)
dataset = dataset.dropna()

# Split the data on sets
train_ind = 1572
train_set = dataset[cols_features].values[:train_ind]
test_set = dataset[cols_features].values[train_ind:]


plt.tight_layout()

model = get_best_hmm_model(X = train_set, max_states = 5, max_iter = 100000000000000000000000000000)
print("Best model with {0} states ".format(str(model.n_components)))
df1 = pd.DataFrame(model.transmat_)
print("\n The best model transition matrix: \n ",df1)





plot_hidden_states(model, dataset[:train_ind].reset_index(), train_set, column_price)
#compare_hidden_states(hmm_model=model, cols_features=cols_features, conf_interval=0.95)

# Recreate today's data in another data frame
df['last_return'] = df[column_price].pct_change()
df['std_normalized'] = df[column_price].rolling(std_period).apply(std_normalized)
df['ma_ratio'] = df[column_price].rolling(ma_period).apply(ma_ratio)
df['price_deviation'] = df[column_price].rolling(price_deviation_period).apply(values_deviation)
df['volume_deviation'] = df[column_volume].rolling(volume_deviation_period).apply(values_deviation)
df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna()

last_row = df[-1:]
last_row = df[cols_features].values[-1:]
result = model.predict(last_row)
print("\n This week's hidden state: ", result)

df['w_states'] = model.predict(df[cols_features])


df_m_states = pd.DataFrame(df_m_states)
df_m_states = df_m_states.join(df['w_states'])

df_w_states = df_m_states.resample('D').ffill()
#print(df_w_states)

spy = yf.Ticker("SPY")
spy.info
df = spy.history(period="max")



df = pd.merge_asof(df, df_w_states, left_index=True, right_index=True, direction='nearest')

df = df.dropna(subset=['Close', 'w_states'])

#print(df)


##########################################################################################################


dataset = df

std_period = 15
ma_period = 15
price_deviation_period = 15
volume_deviation_period = 15

# Create features 
cols_features = ['last_return', 'std_normalized', 'ma_ratio', 'price_deviation', 'volume_deviation', ]
dataset['last_return'] = dataset[column_price].pct_change()
dataset['std_normalized'] = dataset[column_price].rolling(std_period).apply(std_normalized)
dataset['ma_ratio'] = dataset[column_price].rolling(ma_period).apply(ma_ratio)
dataset['price_deviation'] = dataset[column_price].rolling(price_deviation_period).apply(values_deviation)
dataset['volume_deviation'] = dataset[column_volume].rolling(volume_deviation_period).apply(values_deviation)


dataset["future_return"] = dataset[column_price].pct_change(future_period).shift(-future_period)


dataset = dataset.replace([np.inf, -np.inf], np.nan)
dataset = dataset.dropna()

# Split the data on sets
train_ind = 7582
train_set = dataset[cols_features].values[:train_ind]
test_set = dataset[cols_features].values[train_ind:]


plt.tight_layout()

model = get_best_hmm_model(X = train_set, max_states = 2, max_iter = 100000000000000000000000000000)
print("Best model with {0} states ".format(str(model.n_components)))
df1 = pd.DataFrame(model.transmat_)
print("\n The best model transition matrix: \n ",df1)





plot_hidden_states(model, dataset[:train_ind].reset_index(), train_set, column_price)
#compare_hidden_states(hmm_model=model, cols_features=cols_features, conf_interval=0.95)

# Recreate today's data in another data frame
df['last_return'] = df[column_price].pct_change()
df['std_normalized'] = df[column_price].rolling(std_period).apply(std_normalized)
df['ma_ratio'] = df[column_price].rolling(ma_period).apply(ma_ratio)
df['price_deviation'] = df[column_price].rolling(price_deviation_period).apply(values_deviation)
df['volume_deviation'] = df[column_volume].rolling(volume_deviation_period).apply(values_deviation)
df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna()

last_row = df[-1:]
last_row = df[cols_features].values[-1:]
result = model.predict(last_row)
print("\n Today's hidden state: ", result)

"""df['w_states'] = model.predict(df[cols_features])


df_m_states = pd.DataFrame(df_m_states)
df_m_states = df_m_states.join(df['w_states'])

df_w_states = df_m_states.resample('D').ffill()
#print(df_w_states)

spy = yf.Ticker("SPY")
spy.info
df = spy.history(period="max")



df = pd.merge_asof(df, df_w_states, left_index=True, right_index=True, direction='nearest')

df = df.dropna(subset=['Close', 'w_states'])

print(df)
"""

##########################################################################################################
