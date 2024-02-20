import sys
import numpy as np # for array operations

from sklearn.model_selection import train_test_split # for splitting the data
from sklearn.metrics import mean_squared_error # for calculating the cost function
from sklearn.metrics import mean_absolute_percentage_error # for calculating the cost function
from sklearn.ensemble import RandomForestRegressor # for building the model

from space import Space
from linalg import matmul

s = Space()
m = matmul(A="A",B="B",C="C",i=512,j=512,k=512)

ml = m.loop_nest()
mlt = s.min_tiling_of_untiled_dims(ml)

# sys.exit(0)
# rml = s.random_implementation(mlt)
# rml1 = s.mutate(rml)
# rml2 = s.mutate(rml1)
for i in range(100):
    impl = s.random_implementation(mlt)
    s.eval(impl)

dataset = s.to_data_frame()

x = dataset.drop('time', axis = 1) # Features
y = dataset['time']  # Target

# Splitting the dataset into training and testing set (80/20)
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size = 0.2, random_state = 28)

# Initializing the Random Forest Regression model with 10 decision trees
model = RandomForestRegressor(n_estimators = 10, random_state = 0)

# Fitting the Random Forest Regression model to the data
model.fit(x_train, y_train) 

# Predicting the target values of the test set
y_pred = model.predict(x_test)

for label,pred in zip(y_test, y_pred):
    print(f"{label} measure, {pred} estimate")

# RMSE (Root Mean Square Error)
rmse = float(format(np.sqrt(mean_squared_error(y_test, y_pred)),'.3f'))
relative = float(format(mean_absolute_percentage_error(y_test,y_pred), '.3f'))
print("\nRMSE:\n",rmse)
print("\nMAPE:\n",relative)
