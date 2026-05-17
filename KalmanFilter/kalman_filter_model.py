#This module implements a kalman filter from scratch to be used to measure market sensitivity to news
#Target will be market volatility
#Measurement: Sentiment Score from Bloomberg news
#Latent Variable Market sensitivity to news

#https://web.mit.edu/kirtley/kirtley/binlustuff/literature/control/Kalman%20filter.pdf
import logging
import numpy as np
import math

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class KalmanFilter():
    def __init__(self, param_dict):
        self.param_dict = param_dict

#------------------Forward Pass and Helper Functions
    #Main Method
    def ForwardPass(self,):
        #Compute Kalman Gain
        H = self.param_dict["H"] #Design matrix for state variable
        P_prev = self.param_dict["P"] #Covariance matrix of the states (sentiment score vector)
        R = self.ComputeR(X) #Covariance matrix of the error of the measurement linear model
        self._ComputeKalmanGain()
        pass


    #Computing the covariance matrix of the error of the measurements
    def _ComputeR(self, X):
        B = self.param_dict["B"]

        z_estimate = X @ B #X : Design Matrix (sentiment scores), B : market sensitivity coefficients  

        R = np.cov(z_estimate)
        return R

    
    #Compute Kalman Gain
    def _ComputeKalmanGain(self, H, P_prev, R):
        S = H @ P_prev @ H.T + R
        A = np.linalg.solve(S.T, H).T
        KG = P_prev @ A

        return KG

    #Update Estimates
    def _UpdateEstimate(self,):
        UE = X_prev + KG @ (Z - H @ X_prev)
        return UE

    #Update Covariance
    def _UpdateCovariance(self,):
        A = K @ H
        I = np.identity(A.shape[0])
        UC = (I - A) @ P_prev

    #Project into k+1
    def _ProjectForward(self,):
        X_next = phi @ X_curr
        P_next = phi @ phi.T + Q

if __name__ == "__main__":
    param_dict = {
        "H" : None, #Design matrix for latent state variable
    }



"""
For the Kalman filter implementation update the latent state transition matrix using a previous
matrix with forward data. For Future predictions the transition matrix will always be a lagged version. 

"""