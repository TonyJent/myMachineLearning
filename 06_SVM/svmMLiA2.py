'''
完整Platt SMO
'''

import random
from numpy import *

def kernelTrans(X,A,kTup):
    '''
    径向基核函数
    X:特征数据集
    A:特征数据集的第i行数据
    kTup:核函数信息
    '''
    m,n=shape(X)
    K=mat(zeros((m,1)))
    if kTup[0]=='lin':
        #线性核
        K=X*A.T
    elif kTup[0]=='rbf':
        #高斯核
        for j in range(m):
            deltaRow=X[j,:]-A
            K[j]=deltaRow*deltaRow.T
        K=exp(K/(-1*kTup[1]**2))
    else:
        raise NameError('Houston we have a problem')
    return K

class optStruct:
    '''
    建立一个数据结构使用对象
    '''
    def __init__(self,dataMatIn,classLabels,C,toler,kTup):
        self.X=dataMatIn
        self.labelMat=classLabels
        self.C=C
        self.tol=toler
        self.m=shape(dataMatIn)[0]
        self.alphas=mat(zeros((self.m,1)))
        self.b=0
        #eCache第一列是eCache是否有效的标志位，第二列是实际的E值
        self.eCache=mat(zeros((self.m,2)))
        self.K=mat(zeros((self.m,self.m)))
        for i in range(self.m):
            self.K[:,i]=kernelTrans(self.X,self.X[i,:],kTup)

def loadDataSet(fileName):
    '''
    对文件解析
    '''
    dataMat=[]
    labelMat=[]
    fr=open(fileName)
    for line in fr.readlines():
        lineArr=line.strip().split('\t')
        dataMat.append([float(lineArr[0]),float(lineArr[1])])
        labelMat.append(float(lineArr[2]))
    return dataMat,labelMat

def calcEk(oS,k):
    '''
    计算误差
    '''
    #fXk=float(multiply(oS.alphas,oS.labelMat).T*(oS.X*oS.X[k,:].T))+oS.b
    fXk=float(multiply(oS.alphas,oS.labelMat).T*oS.K[:,k])+oS.b
    Ek=fXk-float(oS.labelMat[k])
    return Ek

def selectJrand(i,m):
    '''
    i:第一个alpha下标
    m:所有alpha数目
    '''
    j=i
    #只要函数值不等于输入值i，函数就会随机选择
    while j==i:
        j=int(random.uniform(0,m))
    return j

def selectJ(i,oS,Ei):
    '''
    通过最大步长获得第二个alpha值
    '''
    maxK=-1
    maxDeltaE=0
    Ej=0
    #首先将输入值Ei在缓存中设置成有效的
    oS.eCache[i]=[1,Ei]
    #返回非0E值对应的alpha值对应的序号
    validEcacheList=nonzero(oS.eCache[:,0].A)[0]
    if len(validEcacheList)>1:
        for k in validEcacheList:
            if k==i:continue
            Ek=calcEk(oS,k)
            deltaE=abs(Ei-Ek)
            if deltaE>maxDeltaE:
                maxK=k
                maxDeltaE=deltaE
                Ej=Ek
        return maxK,Ej
    else:
        j=selectJrand(i,oS.m)
        Ej=calcEk(oS,j)
    return j,Ej

def updateEk(oS,k):
    '''
    计算误差存入缓存
    '''
    Ek=calcEk(oS,k)
    oS.eCache[k]=[1,Ek]

def clipAlpha(aj,H,L):
    '''
    用于调整大于H或小于L的alpha值
    '''
    if aj>H:
        aj=H
    if L>aj:
        aj=L
    return aj

def innerL(i,oS):
    Ei=calcEk(oS,i)
    if ((oS.labelMat[i]*Ei<-oS.tol) and (oS.alphas[i]<oS.C)) or ((oS.labelMat[i]*Ei>oS.tol) and (oS.alphas[i]>0)):
        j,Ej=selectJ(i,oS,Ei)
        alphaIold=oS.alphas[i].copy()
        alphaJold=oS.alphas[j].copy()
        if oS.labelMat[i]!=oS.labelMat[j]:
            L=max(0,oS.alphas[j]-oS.alphas[i])
            H=min(oS.C,oS.C+oS.alphas[j]-oS.alphas[i])
        else:
            L=max(0,oS.alphas[j]+oS.alphas[i]-oS.C)
            H=min(oS.C,oS.alphas[j]+oS.alphas[i])
        if L==H:
            print("L==H")
            return 0
        #eta=2.0*oS.X[i,:]*oS.X[j,:].T-oS.X[i,:]*oS.X[i,:].T-oS.X[j,:]*oS.X[j,:].T
        eta=2.0*oS.K[i,j]-oS.K[i,i]-oS.K[j,j]
        if eta>=0:
            print("eta>=0")
            return 0
        oS.alphas[j]-=oS.labelMat[j]*(Ei-Ej)/eta
        oS.alphas[j]=clipAlpha(oS.alphas[j],H,L)
        updateEk(oS,j)
        if abs(oS.alphas[j]-alphaJold)<0.00001:
            print("j not moving enough")
            return 0
        oS.alphas[i]+=oS.labelMat[j]*oS.labelMat[i]*(alphaJold-oS.alphas[j])
        updateEk(oS,i)
        #b1=oS.b-Ei-oS.labelMat[i]*(oS.alphas[i]-alphaIold)*oS.X[i,:]*oS.X[i,:].T-oS.labelMat[j]*(oS.alphas[j]-alphaJold)*oS.X[i,:]*oS.X[j,:].T
        #b2=oS.b-Ej-oS.labelMat[i]*(oS.alphas[i]-alphaIold)*oS.X[i,:]*oS.X[j,:].T-oS.labelMat[j]*(oS.alphas[j]-alphaJold)*oS.X[j,:]*oS.X[j,:].T
        b1=oS.b-Ei-oS.labelMat[i]*(oS.alphas[i]-alphaIold)*oS.K[i,i]-oS.labelMat[j]*(oS.alphas[j]-alphaJold)*oS.K[i,j]
        b2=oS.b-Ej-oS.labelMat[i]*(oS.alphas[i]-alphaIold)*oS.K[i,j]-oS.labelMat[j]*(oS.alphas[j]-alphaJold)*oS.K[j,j]
        if 0<oS.alphas[i] and oS.C>oS.alphas[i]:
            oS.b=b1
        elif 0<oS.alphas[j] and oS.C>oS.alphas[j]:
            oS.b=b2
        else:
            oS.b=(b1+b2)/2.0
        return 1
    else:
        return 0

def smoP(dataMatIn,classLabels,C,toler,maxIter,kTup=('lin',0)):
    oS=optStruct(mat(dataMatIn),mat(classLabels).transpose(),C,toler,kTup)
    iter=0
    entireSet=True
    alphaPairsChanged=0
    while (iter<maxIter) and ((alphaPairsChanged>0) or (entireSet)):
        alphaPairsChanged=0
        if entireSet:
            for i in range(oS.m):
                alphaPairsChanged+=innerL(i,oS)
                print("fullSet, iter: %d i:%d, pairs changed %d" % (iter,i,alphaPairsChanged))
            iter+=1
        #对已存在alpha对，选出非边界的alpha值，进行优化
        else:
            #遍历所有的非边界alpha值，不在边界0或C上的值
            nonBoundIs=nonzero((oS.alphas.A>0) * (oS.alphas.A<C))[0]
            for i in nonBoundIs:
                alphaPairsChanged+=innerL(i,oS)
                print("non-bound, iter: %d i:%d, pairs changed %d" % (iter,i,alphaPairsChanged))
            iter+=1
        if entireSet:
            entireSet=False
        elif alphaPairsChanged==0:
            entireSet=True
        print("iteration number: %d" % iter)
    return oS.b,oS.alphas



def calsWs(alphas,dataArr,classLabels):
    X=mat(dataArr)
    labelMat=mat(classLabels).transpose()
    m,n=shape(X)
    w=zeros((n,1))
    for i in range(m):
        w+=multiply(alphas[i]*labelMat[i],X[i,:].T)
    return w

def testRbf(k1=1.3):
    '''
    测试核函数
    '''
    dataArr,labelArr=loadDataSet('testSetRBF.txt')
    b,alphas=smoP(dataArr,labelArr,200,0.0001,10000,('rbf',k1))
    dataMat=mat(dataArr)
    labelMat=mat(labelArr).transpose()
    svInd=nonzero(alphas.A>0)[0]
    sVs=dataMat[svInd]
    labelSV=labelMat[svInd]
    print("there are %d support vectors" % shape(sVs)[0])
    m,n=shape(dataMat)
    errorCount=0
    for i in range(m):
        kernelEval=kernelTrans(sVs,dataMat[i,:],('rbf',k1))
        predict=kernelEval.T*multiply(labelSV,alphas[svInd])+b
        if sign(predict)!=sign(labelArr[i]):
            errorCount+=1
    print("the training error rate is: %f" % (float(errorCount)/m))
    dataArr,labelArr=loadDataSet('testSetRBF2.txt')
    errorCount=0
    dataMat,labelMat=mat(dataArr),mat(labelArr).transpose()
    m,n=shape(dataMat)
    for i in range(m):
        kernelEval=kernelTrans(sVs,dataMat[i,:],('rbf',k1))
        predict=kernelEval.T*multiply(labelSV,alphas[svInd])+b
        if sign(predict)!=sign(labelArr[i]):
            errorCount+=1
    print("the test error rate is: %f" % (float(errorCount)/m))



if __name__=='__main__':
    # dataArr,labelArr=loadDataSet('testSet.txt')
    # b,alphas=smoP(dataArr,labelArr,0.6,0.001,40)
    # ws=calsWs(alphas,dataArr,labelArr)
    # dataMat=mat(dataArr)
    # print(dataArr[0]*mat(ws)+b)
    testRbf()