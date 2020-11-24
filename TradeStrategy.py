#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import pandas as pd


INVEST_THRESH = 0.005 # pick the suitable threshold
STOP_LOSS_THRESH = -0.05 # close position when loss reach threshold
WINDOW = 50  # observation period


parser = argparse.ArgumentParser(
    prog='Stock Drawdown Strategy',
    description='A tool to analyze stock drawdown and trade strategy')
parser.add_argument('dir', type=str, help='Path contain data dictionary info')
args = parser.parse_args()

# Get the max drawdown for the observation period
def max_drawdown(lst,obs):
    obs_lst = lst[:obs+1]
    peak = max(obs_lst)
    max_draw_lst = [1-peak/i for i in obs_lst]
    max_draw = min(max_draw_lst)

    return max_draw

# Get the max reverse drawdown for the observation period
def max_reverse(lst,obs):
    obs_lst = lst[:obs+1]
    peak = min(obs_lst)
    max_rev_lst = [1 - peak / i for i in obs_lst]
    max_rev = min(max_rev_lst)

    return max_rev

# Get the market investment stability
def inv_stability(lst,window): # lst: stock price list
                               # window: number of obsercation period (minute)
    drawdown_lst = []
    reverse_lst = []

    # calculate the max drawdown/reverse drawdown for each period with window
    for i in range(window):
        drawdown_lst.append(max_drawdown(lst,i))
        reverse_lst.append(max_reverse(lst,i))

    # calcuate the average max drawdown/reverse
    avg_drawdown = sum(drawdown_lst)/window
    avg_reverse = sum(reverse_lst)/window

    mkt_stb = -min(avg_reverse,avg_drawdown)
    return mkt_stb


# Calculate annual return for different trade decision
def trade(inv_stb,start_open,cur_close,end_close):
    # start_open: first open price for current day
    # cur_close:  trade price
    # end_close: close price for current day

    if inv_stb > INVEST_THRESH:
        return 0
    elif cur_close > start_open:
        profit = (end_close - cur_close)/cur_close *250/100
        return max(profit,STOP_LOSS_THRESH)
    else:
        profit = (cur_close - end_close)/cur_close *250/100
        return max(profit,STOP_LOSS_THRESH)



if __name__ == "__main__":
    df = pd.read_csv(args.dir)
    df.rename(columns={df.columns[0]:'time'},inplace=True) # rename the first column
    df[['date','time']] = df['time'].str.split(' ',1,expand=True) # split the first column
    # Get the unique trade day
    day_lst = list(set(df['date']))

    # Get the data for each trade day
    dt_dict = dict()
    for day in day_lst:
        tmp = df[df['date'].isin([day])].reset_index()
        mkt_stb = inv_stability(tmp['close'],WINDOW)
        dt_dict[day] = [mkt_stb,tmp['open'][0],tmp['close'][WINDOW],tmp['close'][len(tmp['close'])-1]]
        continue
    # print (dt_dict)

    # Arrange all data to dataframe
    df2 = pd.DataFrame.from_dict(dt_dict,orient='index',columns=['mkt_stb','start_open','cur_close','end_close'])
    df2['date'] = list(df2.index.values)
    df2['date'] = pd.to_datetime(df2['date'])
    df2 = df2.sort_values(by='date',ascending=True).reset_index()
    df2 = df2.drop('index',axis=1)
    print(df2)

    # Trade and get annual yield
    yield_dict = dict()
    for index,row in df2.iterrows():
        annual_yield = trade(row[0],row[1],row[2],row[3])
        yield_dict[row[4]] = annual_yield
    #print(yield_dict)

    # Write the annual yield into excel
    yield_df = pd.DataFrame.from_dict(yield_dict,orient='index',columns=['annual yield'])
    yield_df.to_excel('annual_yield.xlsx')








