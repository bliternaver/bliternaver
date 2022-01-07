import datetime
import decimal
import logging
import sys
import pandas as pd
import pyupbit
import sys
import pyupbit
import time
from indicators import send_request
from upbitpy import Upbitpy
from PyQt5.QtWidgets import *
from upbitpy import Upbitpy
import requests
import telegram
import math
from decimal import Decimal
#access = "HxHLPLB9rcmxWdgLZeZ7YgQe5bD62WByQxwSZG8l"          # 본인 값으로 변경
#secret = "dkWZxehSdcruJ1Gk5OxpvXAxfxxxVe6qO85mUXs6"          # 본인 값으로 변경
#upbit = pyupbit.Upbit(access, secret)



bot = telegram.Bot(token='5010813220:AAE6tmzwXz0EHhSY_8BR0SIArmYOru3c-IM')
chat_id = -1001553463477
server_url = 'https://api.upbit.com'


krw_market_list = []
krw_market_listname = ""
krw_market_acc_list = []
krw_market_list_str = ""


url = "https://api.upbit.com/v1/market/all?isDetails=true"
resp = requests.get(url)
ticks = resp.json()
#print(ticks['korean_name'])
for tick in ticks:
    val="KRW-" in tick["market"]
    if val:
    
     #print(tick["market"][4:])
     krw_market_list_str +=tick["market"]+","
     #print(krw_market_list_str)
     krw_market_list.append(tick["market"][4:]);
     krw_market_listname +=tick["korean_name"]+","
#print(pyupbit.get_tickers(fiat="KRW"))

suz=len(krw_market_list_str)
suz=suz-1
krw_market_list_str.strip()
krw_market_list_str = krw_market_list_str[0:suz]
#print(krw_market_list_str)
cur_befor_acc_list = [];
before_acc_list = [];
cur_acc_list = [];

# -----------------------------------------------------------------------------
# - Name : get_candle
# - Desc : 캔들 조회
# - Input
#   1) target_item : 대상 종목
#   2) tick_kind : 캔들 종류 (1, 3, 5, 10, 15, 30, 60, 240 - 분, D-일, W-주, M-월)
#   3) inq_range : 조회 범위
# - Output
#   1) 캔들 정보 배열
# -----------------------------------------------------------------------------
def get_candle(target_item, tick_kind, inq_range):
    try:
 
        # ----------------------------------------
        # Tick 별 호출 URL 설정
        # ----------------------------------------
        # 분붕
        if tick_kind == "1" or tick_kind == "3" or tick_kind == "5" or tick_kind == "10" or tick_kind == "15" or tick_kind == "30" or tick_kind == "60" or tick_kind == "240":
            target_url = "minutes/" + tick_kind
        # 일봉
        elif tick_kind == "D":
            target_url = "days"
        # 주봉
        elif tick_kind == "W":
            target_url = "weeks"
        # 월봉
        elif tick_kind == "M":
            target_url = "months"
        # 잘못된 입력
        else:
            raise Exception("잘못된 틱 종류:" + str(tick_kind))
 
        print(target_url+'======================================')
 
        # ----------------------------------------
        # Tick 조회
        # ----------------------------------------
        querystring = {"market": target_item, "count": inq_range}
        res = send_request("GET", server_url + "/v1/candles/" + target_url, querystring, "")
        candle_data = res.json()
 
        logging.debug(candle_data)
 
        return candle_data
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise
# -----------------------------------------------------------------------------
# - Name : get_indicators
# - Desc : 보조지표 조회
# - Input
#   1) target_item : 대상 종목
#   2) tick_kind : 캔들 종류 (1, 3, 5, 10, 15, 30, 60, 240 - 분, D-일, W-주, M-월)
#   3) inq_range : 캔들 조회 범위
#   4) loop_cnt : 지표 반복계산 횟수
# - Output
#   1) RSI
#   2) MFI
#   3) MACD
#   4) BB
#   5) WILLIAMS %R
# -----------------------------------------------------------------------------
def get_indicators(target_item, tick_kind, inq_range, loop_cnt):
    try:
 
        # 보조지표 리턴용
        indicator_data = []
 
        # 캔들 데이터 조회용
        candle_datas = []
 
        # 캔들 추출
        candle_data = get_candle(target_item, tick_kind, inq_range)
        # print('length=='+str(len(candle_data)))
        # print('loop_cntlength=='+str(loop_cnt))
        if len(candle_data) >= 30:
 
            # 조회 횟수별 candle 데이터 조합
            for i in range(0, int(loop_cnt)):
                candle_datas.append(candle_data[i:int(len(candle_data))])
 
            # RSI 정보 조회
            rsi_data = get_rsi(candle_datas)

            
            # MACD 정보 조회
            macd_data = get_macd(candle_datas, loop_cnt)
 
            
            # print('rsi_data=='+str(len(rsi_data)))
            if len(rsi_data) > 0:
                indicator_data.append(rsi_data)
            # print('macd_data=='+str(len(macd_data)))
            if len(macd_data) > 0:
                indicator_data.append(macd_data)
 
 
        return indicator_data
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise

# -----------------------------------------------------------------------------
# - Name : get_rsi
# - Desc : RSI 조회
# - Input
#   1) candle_data : 캔들 정보
# - Output
#   1) RSI 값
# -----------------------------------------------------------------------------   
def get_rsi(candle_datas):
    try:
 
        # RSI 데이터 리턴용
        rsi_data = []
 
        # 캔들 데이터만큼 수행
        for candle_data_for in candle_datas:
 
            df = pd.DataFrame(candle_data_for)
            dfDt = df['candle_date_time_kst'].iloc[::-1]
            df = df.reindex(index=df.index[::-1]).reset_index()
 
            df['close'] = df["trade_price"]
 
            # RSI 계산
            def rsi(ohlc: pd.DataFrame, period: int = 14):
                ohlc["close"] = ohlc["close"]
                delta = ohlc["close"].diff()
 
                up, down = delta.copy(), delta.copy()
                up[up < 0] = 0
                down[down > 0] = 0
 
                _gain = up.ewm(com=(period - 1), min_periods=period).mean()
                _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
 
                RS = _gain / _loss
                return pd.Series(100 - (100 / (1 + RS)), name="RSI")
 
            rsi = round(rsi(df, 14).iloc[-1], 4)
            rsi_data.append({"type": "RSI", "DT": dfDt[0], "RSI": rsi})
 
        return rsi_data
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise

# -----------------------------------------------------------------------------
# - Name : get_macd
# - Desc : MACD 조회
# - Input
#   1) candle_datas : 캔들 정보
#   2) loop_cnt : 반복 횟수
# - Output
#   1) MACD 값
# -----------------------------------------------------------------------------
def get_macd(candle_datas, loop_cnt):
    try:
 
        # MACD 데이터 리턴용
        macd_list = []
 
        df = pd.DataFrame(candle_datas[0])
        df = df.iloc[::-1]
        df = df['trade_price']
 
        # MACD 계산
        exp1 = df.ewm(span=12, adjust=False).mean()
        exp2 = df.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        exp3 = macd.ewm(span=9, adjust=False).mean()
 
        for i in range(0, int(loop_cnt)):
            macd_list.append(
                {"type": "MACD", "DT": candle_datas[0][i]['candle_date_time_kst'], "MACD": round(macd[i], 4),
                 "SIGNAL": round(exp3[i], 4),
                 "OCL": round(macd[i] - exp3[i], 4)})
 
        return macd_list
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise


while True:
    try:

        
        upbit = Upbitpy()
        datalist = krw_market_list_str.split(",")
        namelist = krw_market_listname.split(",")
        all_info = upbit.get_ticker(datalist)
        #print(all_info)
        #print('len(all_info): ' +str(len(all_info)))    
        
        
        for idx,ticker in enumerate(all_info):
                
                korname = namelist[idx]
                rsi_val = False
                ocl_val = False
                rsi_val2 = False
                ocl_val2 = False
                # if 'KRW-BORA'==ticker['market'] :
                #     bot.sendMessage(chat_id=chat_id, text='bot test')
                indicators_data = get_indicators(ticker['market'], '5', 30, 6)
                indicators_data2 = get_indicators(ticker['market'], '240', 30, 6)
                    # print('11=='+str(len(indicators_data)))
                if len(indicators_data) < 1:
                    print('- 캔들 데이터 부족으로 매수 대상에서 제외....[' + str(ticker['market']) + ']')
                    continue
                print('- ris==1==[' + str(ticker['market']) + ']'+(str(indicators_data[0][0]['RSI']))+'==='+(str(indicators_data[0][0]['DT'])))        
                print('- ris==2==[' + str(ticker['market']) + ']'+(str(indicators_data[0][1]['RSI']))+'==='+(str(indicators_data[0][1]['DT'])))        
                print('- ris==3==[' + str(ticker['market']) + ']'+(str(indicators_data[0][2]['RSI']))+'==='+(str(indicators_data[0][2]['DT'])))        
                print('- ris==4==[' + str(ticker['market']) + ']'+(str(indicators_data[0][3]['RSI']))+'==='+(str(indicators_data[0][3]['DT'])))        
                print('- ocl_val==1==[' + str(ticker['market']) + ']'+(str(indicators_data[1][0]['OCL']))+'==='+(str(indicators_data[1][0]['DT']))+'==='+(str(indicators_data[1][0]['MACD']))+'==='+(str(indicators_data[1][0]['SIGNAL'])))        
                print('- ocl_val==2==[' + str(ticker['market']) + ']'+(str(indicators_data[1][1]['OCL']))+'==='+(str(indicators_data[1][1]['DT']))+'==='+(str(indicators_data[1][1]['MACD']))+'==='+(str(indicators_data[1][1]['SIGNAL'])))        
                print('- ocl_val==3==[' + str(ticker['market']) + ']'+(str(indicators_data[1][2]['OCL']))+'==='+(str(indicators_data[1][2]['DT']))+'==='+(str(indicators_data[1][2]['MACD']))+'==='+(str(indicators_data[1][2]['SIGNAL'])))        
                print('- ocl_val==4==[' + str(ticker['market']) + ']'+(str(indicators_data[1][3]['OCL']))+'==='+(str(indicators_data[1][3]['DT']))+'==='+(str(indicators_data[1][3]['MACD']))+'==='+(str(indicators_data[1][3]['SIGNAL'])))        
                if (Decimal(str(indicators_data[0][0]['RSI'])) > Decimal(str(indicators_data[0][1]['RSI']))
                    and Decimal(str(indicators_data[0][1]['RSI'])) > Decimal(str(indicators_data[0][2]['RSI']))
                    and Decimal(str(indicators_data[0][3]['RSI'])) > Decimal(str(indicators_data[0][2]['RSI']))
                    and Decimal(str(indicators_data[0][2]['RSI'])) < Decimal(str(35))):
                    
                    rsi_val = True
                    print('- ris==1==[' + str(ticker['market']) + ']'+str(indicators_data[0][0]['RSI'])+'=='+str(rsi_val))

                if (Decimal(str(indicators_data[1][0]['OCL'])) > Decimal(str(indicators_data[1][1]['OCL']))
                    and Decimal(str(indicators_data[1][1]['OCL'])) > Decimal(str(indicators_data[1][2]['OCL']))
                    and Decimal(str(indicators_data[1][3]['OCL'])) > Decimal(str(indicators_data[1][2]['OCL']))
                    and Decimal(str(indicators_data[1][1]['OCL'])) < Decimal(str(0))
                    and Decimal(str(indicators_data[1][2]['OCL'])) < Decimal(str(0))
                    and Decimal(str(indicators_data[1][3]['OCL'])) < Decimal(str(0))):
                
                    ocl_val = True
                    print('- ocl_val==1==[' + str(ticker['market']) + ']'+str(indicators_data[1][0]['OCL'])+'=='+str(ocl_val))
                print('- ocl_val==5분봉==[' + str(ticker['market']) + ']'+str(rsi_val)+'=='+str(ocl_val))
                if rsi_val and ocl_val:
                    print('- result==5분봉==[' + str(ticker['market']) + ']=='+str(rsi_val2)+'=='+str(ocl_val2))
                    changetxt = str(indicators_data[0][0]['DT'])+'==('+str(korname)+')==현재RSI=='+str(indicators_data[0][0]['RSI'])+'==현재MACD=='+str(indicators_data[1][0]['OCL'])+'==5분봉골드크로시 직전!'
                    bot.sendMessage(chat_id=chat_id, text=changetxt)
               

                if len(indicators_data2) < 1:
                    print('- 4시간캔들 데이터 부족으로 매수 대상에서 제외....[' + str(ticker['market']) + ']')
                    continue
                # print('- ris==4시간캔들==[' + str(ticker['market']) + ']'+(str(indicators_data2[0][0]['RSI']))+'==='+(str(indicators_data2[0][0]['DT'])))        
          
                if (Decimal(str(indicators_data2[0][0]['RSI'])) > Decimal(str(indicators_data2[0][1]['RSI']))
                    and Decimal(str(indicators_data2[0][1]['RSI'])) > Decimal(str(indicators_data2[0][2]['RSI']))
                    and Decimal(str(indicators_data2[0][3]['RSI'])) > Decimal(str(indicators_data2[0][2]['RSI']))
                    and Decimal(str(indicators_data2[0][2]['RSI'])) < Decimal(str(30))):
                    
                    rsi_val2 = True
                    print('- ris==4시간봉==[' + str(ticker['market']) + ']'+str(indicators_data2[0][0]['RSI'])+'=='+str(rsi_val))

                if (Decimal(str(indicators_data2[1][0]['OCL'])) > Decimal(str(indicators_data2[1][1]['OCL']))
                    and Decimal(str(indicators_data2[1][1]['OCL'])) > Decimal(str(indicators_data2[1][2]['OCL']))
                    and Decimal(str(indicators_data2[1][3]['OCL'])) > Decimal(str(indicators_data2[1][2]['OCL']))
                    and Decimal(str(indicators_data2[1][1]['OCL'])) < Decimal(str(0))
                    and Decimal(str(indicators_data2[1][2]['OCL'])) < Decimal(str(0))
                    and Decimal(str(indicators_data2[1][3]['OCL'])) < Decimal(str(0))):
                
                    ocl_val2 = True
                    print('- ocl_val==4시간봉==[' + str(ticker['market']) + ']'+str(indicators_data[1][0]['OCL'])+'=='+str(ocl_val))
                print('- ocl_val==4시간봉==[' + str(ticker['market']) + ']'+str(rsi_val2)+'=='+str(ocl_val2))
                if rsi_val2 and ocl_val2:
                    print('- result==4시간봉==[' + str(ticker['market']) + ']=='+str(rsi_val2)+'=='+str(ocl_val2))
                    changetxt2 = str(indicators_data2[0][0]['DT'])+'==('+str(korname)+')==현재RSI=='+str(indicators_data2[0][0]['RSI'])+'==현재MACD=='+str(indicators_data2[1][0]['OCL'])+'==4시간봉골드크로시 직전!'
                    bot.sendMessage(chat_id=chat_id, text=changetxt2)
                time.sleep(0.3)    
        
        

    except Exception as e:
        print(e)
        time.sleep(1)




