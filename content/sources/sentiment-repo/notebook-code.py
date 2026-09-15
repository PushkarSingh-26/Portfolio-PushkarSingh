# --- cell 1 ---
import warnings
warnings.filterwarnings('ignore')

import math
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns

from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout, Dense, Activation

import nltk
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import subjectivity
from nltk.sentiment import SentimentAnalyzer
from nltk.sentiment.util import *

from sklearn import preprocessing, metrics
from sklearn.preprocessing import MinMaxScaler
# --- cell 2 ---
from google.colab import drive
drive.mount('/content/drive')
# --- cell 3 ---
drive.mount("/content/drive", force_remount=True)
# --- cell 5 ---
stock_price = pd.read_csv('/content/drive/MyDrive/^BSESN.csv')
stock_headlines = pd.read_csv('/content/drive/MyDrive/india-news-headlines.csv')

# --- cell 7 ---
stock_price.head()

# --- cell 8 ---
stock_headlines.head()

# --- cell 9 ---
# displaying number of records in both stock_price and stock_headlines datasets
len(stock_price), len(stock_headlines)
# --- cell 10 ---
# checking for null values in both the datasets
stock_price.isna().any(), stock_headlines.isna().any()
# --- cell 12 ---
# dropping duplicates
stock_price = stock_price.drop_duplicates()

# coverting the datatype of column 'Date' from type object to type 'datetime'
stock_price['Date'] = pd.to_datetime(stock_price['Date']).dt.normalize()

# filtering the important columns required
stock_price = stock_price.filter(['Date', 'Close', 'Open', 'High', 'Low', 'Volume'])

# setting column 'Date' as the index column
stock_price.set_index('Date', inplace= True)

# sorting the data according to the index i.e 'Date'
stock_price = stock_price.sort_index(ascending=True, axis=0)
stock_price
# --- cell 14 ---
# dropping duplicates
stock_headlines = stock_headlines.drop_duplicates()

# Assuming the date column is named 'Date'
# If it's different, replace 'Date' with the actual column name
# Check if the 'date' column exists in your DataFrame
if 'date' in stock_headlines.columns:
    stock_headlines['publish_date'] = stock_headlines['date'].astype(str)
else:
    # Handle case where 'date' column doesn't exist
    # You might need to identify the actual date column name
    # and adjust the code accordingly.
    # For example, if your date column is named 'publish_date':
    stock_headlines['publish_date'] = stock_headlines['publish_date'].astype(str)
    # Or, if your date column is something else, replace with the correct column name.

# If the DataFrame is empty or if the 'date' column doesn't exist,
# print a message to the user and stop the process
if stock_headlines.empty:
    print("Warning: stock_headlines DataFrame is empty.")
    # Handle the empty DataFrame: e.g., raise an exception, load data again, etc.
    raise ValueError("stock_headlines DataFrame is empty. Check your data and filtering.")

# coverting the datatype of column 'Date' from type string to type 'datetime'
# Fixing the date string creation to handle potential errors
stock_headlines['publish_date'] = stock_headlines['publish_date'].apply(
    lambda x: pd.to_datetime(x, format='%Y%m%d', errors='coerce').strftime('%Y-%m-%d')
    if len(x) == 8 and x.isdigit() else pd.NaT
)

# Drop rows with invalid dates (NaT)
stock_headlines.dropna(subset=['publish_date'], inplace=True)

# Convert 'publish_date' to datetime
stock_headlines['publish_date'] = pd.to_datetime(stock_headlines['publish_date']).dt.normalize()


# filtering the important columns required
# Ensure 'headline_text' is a valid column in your original CSV
# If not, replace it with the correct column name
stock_headlines = stock_headlines.filter(['publish_date', 'headline_text'])

# Check if stock_headlines is empty after filtering
if stock_headlines.empty:
    print("Warning: stock_headlines DataFrame is empty after filtering.")
    # Handle the empty DataFrame: e.g., raise an exception, load data again, etc.
    raise ValueError("stock_headlines DataFrame is empty. Check your data and filtering.")

# grouping the news headlines according to 'Date'
stock_headlines = stock_headlines.groupby(['publish_date'])['headline_text'].apply(lambda x: ','.join(x)).reset_index()

# setting column 'Date' as the index column
stock_headlines.set_index('publish_date', inplace=True)

# sorting the data according to the index i.e 'Date'
stock_headlines = stock_headlines.sort_index(ascending=True, axis=0)
stock_headlines
# --- cell 16 ---
# concatenating the datasets stock_price and stock_headlines
stock_data = pd.concat([stock_price, stock_headlines], axis=1)

# dropping the null values if any
stock_data.dropna(axis=0, inplace=True)

# displaying the combined stock_data
stock_data
# --- cell 17 ---
#alternate way is to use merge funtion and inner join operation
pd.merge(stock_price, stock_headlines, left_index=True, right_index=True, how='inner')
# --- cell 19 ---
# adding empty sentiment columns to stock_data for later calculation
stock_data['compound'] = ''
stock_data['negative'] = ''
stock_data['neutral'] = ''
stock_data['positive'] = ''
stock_data.head()
# --- cell 20 ---
import nltk
nltk.download('vader_lexicon')
# --- cell 21 ---
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import unicodedata

# instantiating the Sentiment Analyzer
sid = SentimentIntensityAnalyzer()

# calculating sentiment scores
stock_data['compound'] = stock_data['headline_text'].apply(lambda x: sid.polarity_scores(x)['compound'])
stock_data['negative'] = stock_data['headline_text'].apply(lambda x: sid.polarity_scores(x)['neg'])
stock_data['neutral'] = stock_data['headline_text'].apply(lambda x: sid.polarity_scores(x)['neu'])
stock_data['positive'] = stock_data['headline_text'].apply(lambda x: sid.polarity_scores(x)['pos'])

# displaying the stock data
stock_data.head()
# --- cell 22 ---
# dropping the 'headline_text' which is unwanted now
stock_data.drop(['headline_text'], inplace=True, axis=1)

# rearranging the columns of the whole stock_data
stock_data = stock_data[['Close', 'compound', 'negative', 'neutral', 'positive', 'Open', 'High', 'Low', 'Volume']]

# set the index name
stock_data.index.name = 'Date'

# displaying the final stock_data
stock_data.head()
# --- cell 23 ---
# writing the prepared stock_data to disk
stock_data.to_csv('stock_data.csv')
# --- cell 25 ---
# displaying the shape i.e. number of rows and columns of stock_data
stock_data.shape
# --- cell 26 ---
# checking for null values
stock_data.isna().any()
# --- cell 27 ---
# displaying stock_data statistics
stock_data.describe(include='all')
# --- cell 28 ---
# displaying stock_data information
stock_data.info()
# --- cell 29 ---
# setting figure size
plt.figure(figsize=(20,10))

# plotting close price
stock_data['Close'].plot()

# setting plot title, x and y labels
plt.title("Close Price")
plt.xlabel('Date')
plt.ylabel('Close Price ($)')
# --- cell 30 ---
# calculating 7 day rolling mean
stock_data.rolling(7).mean().head(20)
# --- cell 31 ---
# setting figure size
plt.figure(figsize=(16,10))

# plotting the close price and a 30-day rolling mean of close price
stock_data['Close'].plot()
stock_data.rolling(window=30).mean()['Close'].plot()
# --- cell 34 ---
# calculating data_to_use
percentage_of_data = 1.0
data_to_use = int(percentage_of_data*(len(stock_data)-1))

# using 80% of data for training
train_end = int(data_to_use*0.8)
total_data = len(stock_data)
start = total_data - data_to_use

# printing number of records in the training and test datasets
print("Number of records in Training Data:", train_end)
print("Number of records in Test Data:", total_data - train_end)
# --- cell 35 ---
# predicting one step ahead
steps_to_predict = 1

# capturing data to be used for each column
close_price = stock_data.iloc[start:total_data,0] #close
compound = stock_data.iloc[start:total_data,1] #compound
negative = stock_data.iloc[start:total_data,2] #neg
neutral = stock_data.iloc[start:total_data,3] #neu
positive = stock_data.iloc[start:total_data,4] #pos
open_price = stock_data.iloc[start:total_data,5] #open
high = stock_data.iloc[start:total_data,6] #high
low = stock_data.iloc[start:total_data,7] #low
volume = stock_data.iloc[start:total_data,8] #volume

# printing close price
print("Close Price:")
print(close_price)
# --- cell 36 ---
# shifting next day close
close_price_shifted = close_price.shift(-1)

# shifting next day compound
compound_shifted = compound.shift(-1)

# concatenating the captured training data into a dataframe
data = pd.concat([close_price, close_price_shifted, compound, compound_shifted, volume, open_price, high, low], axis=1)

# setting column names of the revised stock data
data.columns = ['close_price', 'close_price_shifted', 'compound', 'compound_shifted','volume', 'open_price', 'high', 'low']

# dropping nulls
data = data.dropna()
data.head(10)
# --- cell 38 ---
# setting the target variable as the shifted close_price
y = data['close_price_shifted']
y
# --- cell 39 ---
# setting the features dataset for prediction
cols = ['close_price', 'compound', 'compound_shifted', 'volume', 'open_price', 'high', 'low']
x = data[cols]
x
# --- cell 41 ---
# scaling the feature dataset
scaler_x = preprocessing.MinMaxScaler (feature_range=(-1, 1))
x = np.array(x).reshape((len(x) ,len(cols)))
x = scaler_x.fit_transform(x)

# scaling the target variable
scaler_y = preprocessing.MinMaxScaler (feature_range=(-1, 1))
y = np.array (y).reshape ((len( y), 1))
y = scaler_y.fit_transform (y)

# displaying the scaled feature dataset and the target variable
x, y
# --- cell 43 ---
# preparing training and test dataset
X_train = x[0 : train_end,]
X_test = x[train_end+1 : len(x),]
y_train = y[0 : train_end]
y_test = y[train_end+1 : len(y)]

# printing the shape of the training and the test datasets
print('Number of rows and columns in the Training set X:', X_train.shape, 'and y:', y_train.shape)
print('Number of rows and columns in the Test set X:', X_test.shape, 'and y:', y_test.shape)
# --- cell 44 ---
# reshaping the feature dataset for feeding into the model
X_train = X_train.reshape (X_train.shape + (1,))
X_test = X_test.reshape(X_test.shape + (1,))

# printing the re-shaped feature dataset
print('Shape of Training set X:', X_train.shape)
print('Shape of Test set X:', X_test.shape)
# --- cell 46 ---
# setting the seed to achieve consistent and less random predictions at each execution
np.random.seed(2016)

# setting the model architecture
model=Sequential()
model.add(LSTM(100,return_sequences=True,activation='tanh',input_shape=(len(cols),1)))
model.add(Dropout(0.1))
model.add(LSTM(100,return_sequences=True,activation='tanh'))
model.add(Dropout(0.1))
model.add(LSTM(100,activation='tanh'))
model.add(Dropout(0.1))
model.add(Dense(1))

# printing the model summary
model.summary()
# --- cell 47 ---
# compiling the model
model.compile(loss='mse' , optimizer='adam')

# fitting the model using the training dataset
model.fit(X_train, y_train, validation_split=0.2, epochs=10, batch_size=8, verbose=1)
# --- cell 49 ---
# serialize weights to HDF5
model.save_weights('model.weights.h5') # Changed the filename to include the .weights extension.
print('Model is saved to the disk')
# --- cell 51 ---
# performing predictions
predictions = model.predict(X_test)

# unscaling the predictions
predictions = scaler_y.inverse_transform(np.array(predictions).reshape((len(predictions), 1)))

# printing the predictions
print('Predictions:')
predictions[0:5]
# --- cell 53 ---
# Import necessary libraries
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

data = {
    "Date": ["2001-01-02", "2001-01-03", "2001-01-04", "2001-01-05", "2001-01-08"],
    "Close": [4018.879883, 4060.020020, 4115.370117, 4183.729980, 4120.430176]
}

# Create DataFrame
df = pd.DataFrame(data)

# Add Predicted Close Prices (replace this with your actual predicted data)
# For demonstration, we'll add a column with slightly varied values from 'Close'
df["Predicted_Close_Price"] = [4020, 4062, 4110, 4180, 4125]  # Replace with your data

# Calculate metrics
mae = mean_absolute_error(df["Close"], df["Predicted_Close_Price"]) # Now mean_absolute_error is defined
mse = mean_squared_error(df["Close"], df["Predicted_Close_Price"])
rmse = np.sqrt(mse)
r2 = r2_score(df["Close"], df["Predicted_Close_Price"])

# Print metrics
print("Mean Absolute Error (MAE):", mae)
print("Mean Squared Error (MSE):", mse)
print("Root Mean Squared Error (RMSE):", rmse)
print("R-squared (R2):", r2)
# --- cell 55 ---
# unscaling the test feature dataset, x_test
X_test = scaler_x.inverse_transform(np.array(X_test).reshape((len(X_test), len(cols))))

# unscaling the test y dataset, y_test
y_train = scaler_y.inverse_transform(np.array(y_train).reshape((len(y_train), 1)))
y_test = scaler_y.inverse_transform(np.array(y_test).reshape((len(y_test), 1)))


# --- cell 56 ---
# plotting
plt.figure(figsize=(16,10))

# plt.plot([row[0] for row in y_train], label="Training Close Price")
plt.plot(predictions, label="Predicted Close Price")
plt.plot([row[0] for row in y_test], label="Testing Close Price")
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=2)
plt.show()
# --- cell 57 ---
# Adding empty sentiment columns to stock_data for later calculation
stock_data['polarity'] = ''
stock_data['subjectivity'] = ''

# Importing TextBlob
import pandas as pd
from textblob import TextBlob

# Assuming 'headline_text' still exists in your DataFrame
# If it has been removed, you'll need to reload the data
if 'headline_text' in stock_data.columns: # Changed stock_headlines to stock_data
    stock_data['headline_text'].fillna('', inplace=True)

    # Calculating sentiment scores using TextBlob
    # Changed 'df' to 'stock_data'
    stock_data['polarity'] = stock_data['headline_text'].apply(lambda x: TextBlob(x).sentiment.polarity)
    stock_data['subjectivity'] = stock_data['headline_text'].apply(lambda x: TextBlob(x).sentiment.subjectivity)

    # Drop unnecessary columns
    # 'publish_date' likely already dropped, so only drop 'headline_text'
    stock_data.drop(['headline_text'], axis=1, inplace=True) # Changed stock_headlines to stock_data

# If 'headline_text' was already removed, consider this alternative:
else:
    print("Warning: 'headline_text' column not found. Skipping sentiment analysis.")

# Rearranging the columns
# Ensure the columns you're selecting still exist
stock_data = stock_data[['Close', 'polarity', 'subjectivity', 'Open', 'High', 'Low', 'Volume', 'compound', 'negative', 'neutral', 'positive']] # Changed stock_headlines to stock_data and added other columns from original stock_data

# Setting the index name
stock_data.index.name = 'Date' # Changed stock_headlines to stock_data

# Displaying the final stock_data
print(stock_data.head()) # Changed stock_headlines to stock_data

# Writing the prepared stock_data to disk
stock_data.to_csv('stock_data_with_textblob.csv') # Changed stock_headlines to stock_data
