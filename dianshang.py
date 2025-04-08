import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from zhdate import ZhDate
from datetime import datetime, timedelta
import re
#分析框架：5w2h、增长率法
#IDE:pycharm
#TODO: 1、指标梳理
df_info=pd.read_csv('baby_info.csv')
df_history=pd.read_csv('baby_trade_history.csv')
#结果指标：buy_mount 购买次数
#维度指标：user_id；cat1(商品大类)；cat_id(商品小类)；day-birthday（婴儿年龄）；gender(性别)
print(df_history.dtypes)
#TODO: 2、数据清洗
df_history['buy_mount'].describe()
plt.hist(df_history['buy_mount'], bins=10, edgecolor='black')  # `bins` 参数控制直方图的柱数
plt.title("Histogram")
#销售数量异常值删除
#以行业报告作为补充对异常值进行划分
#分析：利用四分位和方差对销量数据情况进行了解，确定异常值范围。站在统计学的角度，把超过平均值3倍标准差的销量（即2.54+64*3=194.54罐）作为异常值是常规的做法，但站在业务的角度则不合理。
#通过对婴儿奶粉推荐量的估算，发现0-1岁孩子最多一年消耗81罐奶粉。根据国双2018年本土婴幼儿奶粉电商消费研究的数据，在电商平台购买婴幼儿奶粉的消费者年均购买次数约为27次，“双十一”、“618”两个购物节是囤货高峰。
#假设用户除“双十一”、“618”外其他时间每次只购买1罐，那么两个购物节平均需要承担28罐奶粉，向上取整后，以单笔销量超过30罐奶粉作异常值处理。
df_history_new=df_history[df_history['buy_mount']<=30]
plt.hist(df_history_new['buy_mount'], bins=10, edgecolor='black')  # `bins` 参数控制直方图的柱数
plt.title("Histogram")
#TODO: 3、提出分析维度，确立标准
#在没有任何指标的情况下，可以采用趋势分析来确定指标，这里的标准定为当月同比增速必须高于上年同期同比增速或上年整体同比增速。
df_history_new['year']=df_history_new['day'].astype(str).str[:4]
year_buy=df_history_new.groupby('year')['buy_mount'].sum()
growth_rate=year_buy/year_buy.shift(1)-1
print(growth_rate)
#发现年销量同比增速逐年降低，2015年增速小于2014年的50.54%，需要将销量增速提至50.54%以上。
#TODO: 4、先找灰犀牛，再寻黑天鹅
#多维度的分析，应该是一个金字塔式的分析路径：从一个维度的整体到局部，再引入另外一个维度的整体再到局部，而不是在多个维度间反复横跳。
'''发现年销量同比增速逐年降低
初步规划的分析路径如下：
1 观察各年度每月销量情况走势
2 2015年1-2月的销量走势对比13年和14年，判断销量的好或差？
3 如果销量差，问题出在什么地方
4 如果销量差，还有多少缺口，有多少时间挽救，重要的挽救时间节点是什么时候？
5 如果要冲销量，推广什么品类？
'''
#1 计算每年月销量，对比各月销量变化情况
df_history_new['year_month']=df_history_new['day'].astype(str).str[:6]
yearmonth_buy=pd.DataFrame()
yearmonth_buy['buy_mount']=df_history_new.groupby('year_month')['buy_mount'].sum()
yearmonth_buy['year']=yearmonth_buy.index.str[:4]
yearmonth_buy['month']=yearmonth_buy.index.str[4:6]
#计算月同比增长率
yearmonth_buy['month_rate'] =(yearmonth_buy['buy_mount']/yearmonth_buy['buy_mount'].shift(12)-1)*100
yearlable=list(dict.fromkeys(yearmonth_buy['year'].values))
for i in yearlable:
    df=yearmonth_buy[yearmonth_buy['year']==i]
    plt.plot(df.index.str[4:6].astype(int),df['buy_mount'])
plt.legend(yearlable)
plt.xticks(list(range(1, 13)))
plt.grid(True)
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.title('月销量情况')
plt.xlabel("月份")
plt.ylabel("销量(件)")
plt.savefig('月销量情况.png', dpi=300)

for i in yearlable:
    df=yearmonth_buy[yearmonth_buy['year']==i]
    plt.plot(df.index.str[4:6].astype(int),df['month_rate'])
plt.legend(yearlable)
plt.xticks(list(range(1, 13)))
plt.grid(True)
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.title('月同比增长')
plt.xlabel("月份")
plt.ylabel("增长率(%)")
plt.savefig('月同比增长.png', dpi=300)
'''
分析：15年2月销量骤降，发现是因为该月内数据记录不全；13年和14年销量走势基本一致；
13年和15年均出现骤降情况，初步判别为春节导致的下降，13年春节为2月9日-2月15日 2014年春节：1月30日-2月6日 2015年春节：2月19日-2月25日
故要求15年2月份销量高于14年2月的同比增速不合理。解决：取春节前30天观察
#
'''
#降采样至日,取各年春节前30天数据
df_history_new['date']=pd.to_datetime(df_history_new["day"],format="%Y%m%d")
df_history_new1=df_history_new.sort_values(by="date", ascending=False)
day_buy=pd.DataFrame()
day_buy['buy_mount']=df_history_new1.groupby(by='date')['buy_mount'].sum()
def convert_to_lunar(date):
    lunar_date = ZhDate.from_datetime(date)
    return re.search(r'\S+', lunar_date.chinese()[5:]).group()
    #return lunar_date.chinese()
# 应用转换函数
day_buy['农历日期'] = day_buy.index.map(convert_to_lunar)

specific_date = datetime(2013, 2, 10)
# 计算特定日期前 30 天的日期
start_date = specific_date - timedelta(days=30)
end_date=specific_date + timedelta(days=6)
# 筛选出特定日期前 30 天的数据
before30_2013= day_buy[(day_buy.index >= start_date) & (day_buy.index <= end_date)]
specific_date = datetime(2014, 1, 31)
# 计算特定日期前 30 天的日期
start_date = specific_date - timedelta(days=30)
end_date=specific_date + timedelta(days=6)
before30_2014= day_buy[(day_buy.index >= start_date) & (day_buy.index <= end_date)]
specific_date = datetime(2015, 2, 19)
# 计算特定日期前 30 天的日期
start_date = specific_date - timedelta(days=30)
end_date=specific_date + timedelta(days=6)
before30_2015= day_buy[(day_buy.index >= start_date) & (day_buy.index <= end_date)]
plt.plot(before30_2014.iloc[:,1],before30_2013.iloc[:,0])#实际上13年无腊月30日，为画图对比前30天的方便，沿用14年农历
plt.plot(before30_2014.iloc[:,1],before30_2014.iloc[:,0])
plt.plot(before30_2015.iloc[:,1],before30_2015.iloc[:,0])
plt.legend([2013,2014,2015])
plt.xticks(rotation=45)
plt.rcParams['font.size'] = 4
plt.grid(True)
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.title('春节前30日销量')
plt.xlabel("日")
plt.ylabel("销量(件)")
plt.savefig('春节前30日销量.png', dpi=300)
'''
计算前30天同比销量增速
'''
buy15_2013=before30_2013['buy_mount'].iloc[:17].sum()
buy15_2014=before30_2014['buy_mount'].iloc[:17].sum()
buy15_2015=before30_2015['buy_mount'].iloc[:17].sum()
rate=[np.nan, buy15_2014/buy15_2013-1,buy15_2015/buy15_2014-1]
'''
分析：2015春节前增速为42.6%，低于2014年的58.5%
'''

'''
计算各品类销量，分析14到15年销量的变化
'''
buy_cat2013=df_history_new[df_history_new['date'].isin(before30_2013.iloc[:17].index)].groupby(by='cat1')['buy_mount'].sum()#多条件分组聚合
buy_cat2014=df_history_new[df_history_new['date'].isin(before30_2014.iloc[:17].index)].groupby(by='cat1')['buy_mount'].sum()#多条件分组聚合
buy_cat2015=df_history_new[df_history_new['date'].isin(before30_2015.iloc[:17].index)].groupby(by='cat1')['buy_mount'].sum()#多条件分组聚合
buy_cat_df=pd.concat([buy_cat2013, buy_cat2014, buy_cat2015], axis=1)
buy_cat_df.columns = [2013, 2014,2015]
buy_cat_df.sum()

# 绘制柱状图
# 使用 Pandas 的 plot 方法绘制柱状图
buy_cat_df.plot(kind='bar')
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.title('春节前30-13天各品类销量')
plt.xlabel('天')
plt.ylabel('销量(件)')
plt.xticks(rotation=45)
# 显示图例
plt.legend(title='Columns')
# 显示图表
plt.show()
plt.savefig('春节前30-13天各品类销量.png', dpi=300)

rate_cat=pd.concat([(buy_cat_df[2014]/buy_cat_df[2013]-1)*100,(buy_cat_df[2015]/buy_cat_df[2014]-1)*100 ],axis=1)
rate_cat.index=rate_cat.index.astype(str)
rate_cat.columns=[2014,2015]
rate_cat.plot()
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.title('春节前30-13日各品类销量增速')
plt.xlabel("日")
plt.ylabel("增速(%)")
plt.show()
plt.savefig('春节前30-13日各品类销量增速.png', dpi=300)
'''
分析：
1、发现2014年品类35增速超出平均值，可能由于其销量少增长空间大，25年明显下降。
2、15年品类168和815销量位居前茅，但增速低于平均值，且低于去年同比，需要重点关注。
3、PEST和4P理论形成逻辑树，通过数据验证销量增长率未达标准的核心原因。
'''
