# Snapping Mechanism
# Author: Georgios Kellaris
# Year: 2016

library("Rmpfr")
library("gmp")
library("plyr")

BinToDec <- function(x, y)
  sum(2^(which(rev(unlist(strsplit(as.character(x), "")) == 1))-1))*2^y

clamp <- function(x, u, l){
  if(x>u)
    x<-u
  else if(x<l)
    x<-l
  else
    x
}


epsilon <- function(eps,l,u){
  B<-(u-l)
  eta<-2^-53
  pre<-mpfr(B*eta*exp(16)/eps,52)
  y<-asNumeric(ceiling(log2(pre)))
  pre<-2^y
  eprime<-log((exp(eps*(2*B*eta+pre))-exp(-3.1*B*eta*eps))/(exp(pre*eps)-1))*2^4
  eprime
}


#' @title Snapping Mechanism
#' @description [Ilya Mironov. "On Significance of the Least Significant Bits For Differential Privacy"]
#' @param x The original value
#' @param s The sensitivity
#' @param eps epsilon value for DP
#' @param l The minimum possible value
#' @param u The maximum possible value
#' @return The x value perturb with Laplace noise of scale s/eps
#' @export
#' @examples slaplace(50,1,1)

slaplace <- function(x, s, eps, l=-2^20, u=2^20){
  S<-c(1,-1)
  l<-l/s
  u<-u/s
  B<-(u-l)
  eta<-2^-53
  pre<-mpfr(B*eta*exp(16)/eps,52)
  x<-x/s
  y<-asNumeric(ceiling(log2(pre)))
  eps<-(eps-epsilon(eps,l,u))
  clamp(round_any(clamp(x,u,l)+asNumeric(1.0/eps*log(mpfr(BinToDec(c(1,rbinom(52,1,0.5)),-rgeom(1,0.5)-53),52))*sample(S,1)),2^y)*s,u*s,l*s)
}

snaptest <-function(x,s,eps,times,l=-2^20, u=2^20){
  library(e1071)
values <- runif(times, 0.0, 1.0)
for(i in 1:times)
  values[i]=slaplace(x,s,eps,l,u)
values<-sort(values)
hist(values,times)
print(paste0("Experimental Var: ",var(values)," Theoretical Var: ", 2*(s/eps)^2))
print(paste0("Experimental Kurt: ",kurtosis(values,type=1)," Theoretical Kurt: ", 3))

}

laptest <-function(x,s,eps,times,l=-2^20, u=2^20){
  library(e1071)
  library(VGAM)
  values <- runif(times, 0.0, 1.0)
  for(i in 1:times)
    values[i]=clamp(x+rlaplace(1,s=s/eps),u,l) # NOTE: CC thinks this might be wrong? clamping happens on x before it is used here and shouldn't
                                               # happen after as far as he knows
    # values[i] = x + rlaplace(1, s = s/eps)
  values<-sort(values)
  hist(values,times)
  print(paste0("Experimental Var: ",var(values)," Theoretical Var: ", 2*(s/eps)^2))
  print(paste0("Experimental Kurt: ",kurtosis(values,type=1)," Theoretical Kurt: ", 3))

}
