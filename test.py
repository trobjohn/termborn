# %%
import termborn as sns
import numpy as np
rng = np.random.default_rng()



x = rng.normal(loc=1.0, scale=1.5, size=(100, 1))
group = rng.choice(['a','b','c'],100)
x[group=='b']=rng.normal(loc=2.0,scale=.5,size=(len(x[group=='b']),1))
x[group=='c']=rng.normal(loc=3.0,scale=.5,size=(len(x[group=='c']),1))

y = x ** 2

sns.scatterplot(x=x,y=y)
sns.histplot(x=x)
sns.kdeplot(y)
sns.kdeplot(y,hue=group)
sns.ecdfplot(x, hue = group)

z = rng.normal(loc=1.0, scale=1.0, size=(1000, 1000))
group = rng.choice(['a','b','c'],1000)
sns.scatterplot(x=z[:,0],y=z[:,1],hue=group)

sns.histplot(x=z[:,0],y=z[:,1])



# %%

sns.heatmap(z[:9,:9])
# %%
