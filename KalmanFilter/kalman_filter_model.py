#This module implements a kalman filter from scratch to be used to measure market sensitivity to news
#Target will be market volatility
#Measurement: Sentiment Score from Bloomberg news
#Latent Variable Market sensitivity to news
import logging
import numpy as np
import math

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class KalmanFilter():
    def __init__(self, param_dict):
        pass

if __name__ == "__main__":
    x = np.array([1,2,3])
    print(x)