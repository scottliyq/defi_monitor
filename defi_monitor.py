
import string
import time
import os
import requests
from datetime import datetime
import sqlalchemy
import json
import configparser



from orm_models import DefiMonitorBalance, DefiWalletToken

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import logging 
from logging import handlers

from apscheduler.schedulers.background import BackgroundScheduler

# MONITOR_ADDRESS = {"0xeaa7723633cf598e872d611f5ec50a45b65cbc72"}
ZAPPER_API_KEY = "96e0cc51-a62e-42ca-acee-910ea7d2a241"

INVOKER_CONFIG = [
    {
        "address":"0xeaa7723633cf598e872d611f5ec50a45b65cbc72",
        "network":"ethereum",
        "products": ["convex"]
    },
    {
        "address":"0x6e582b207e84d99450be14f68d5d66f686ee3931",
        "network":"ethereum",
        "products": ["convex"]
    },
    {
        "address":"0x8c9a16aed57a88e59b7325011f5125bb9cd95a34",
        "network":"ethereum",
        "products": ["convex"]
    },
    {
        "address":"0x997d1ed51ff7389883913311810176cbdbd5d1d5",
        "network":"ethereum",
        "products": ["convex"]
    }
]

logger = logging.getLogger()
logger.setLevel(logging.INFO) 
logFile = './temp/defi_monitor.log'


# 创建一个FileHandler,并将日志写入指定的日志文件中
fileHandler = logging.FileHandler(logFile, mode='a')
fileHandler.setLevel(logging.INFO) 
 
 # 或者创建一个StreamHandler,将日志输出到控制台
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.INFO)

# 定义Handler的日志输出格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(formatter)
 
# 定义日志滚动条件，这里按日期-天保留日志
timedRotatingFileHandler = handlers.TimedRotatingFileHandler(filename=logFile, when='D')
timedRotatingFileHandler.setLevel(logging.INFO)
timedRotatingFileHandler.setFormatter(formatter)

# 添加Handler
# logger.addHandler(fileHandler)
logger.addHandler(streamHandler)
logger.addHandler(timedRotatingFileHandler)

def Log(*params):

    logging.info(params)


def sql_engine():
    config = configparser.ConfigParser()
    config.read('config.properties')
    db_url=config.get("db", "db_url")


    engine = create_engine(db_url, encoding="utf8", echo=False)

    return engine
    
engine = sql_engine()

DBSessinon = sqlalchemy.orm.sessionmaker(bind=engine)  # 创建会话类
session = DBSessinon()  # 创建会话对象


Base = declarative_base()
metadata = Base.metadata


def check_zapper():
    logging.debug("start to invoke zapper api")

    for config in INVOKER_CONFIG: 
        address = config['address']
        network = config['network']
        #invoke product balance data
        for product in config['products']:
            res_data = invoke_zapper_api(address, config['network'], product)
            process_products(res_data["products"], config['address'])
        
        #invoke wallet balance data
        res_data = invoke_zapper_wallet_balance(address)
        balance_data = parseBalanceResponse(res_data, network)

        assets = balance_data['balances'][address]['products'][0]['assets']
        storeWallet(address, network,assets)
        

#查询apper product:convex数据,network:ethereum
def invoke_zapper_api(address: string, network:string, product: string):
    url = f"https://api.zapper.fi/v1/protocols/{product}/balances?addresses%5B%5D={address}&network={network}&api_key={ZAPPER_API_KEY}"
    logging.info(url)

    zapper_res = requests.get(url).json()
    if zapper_res is None:
        print('无法连接zapper，需要海外托管者')
        exit() 

    return zapper_res[address]

def parseBalanceResponse(zapper_res, network):
    # string = zapper_res.content.decode('utf-8')
    response_data_split_by_line = zapper_res.content.decode('utf-8').splitlines()
    json_line = ""
    for line in response_data_split_by_line:
        if line.find("\"tokens\",\"network\":\"" + network + "\"") != -1:
            json_line = line
            break

    json_response = json_line[5::]
    

    json_data = json.loads(json_response)

    return json_data

# 处理balace data
def invoke_zapper_wallet_balance(address: string):
    url = f"https://api.zapper.fi/v1/balances?addresses%5B%5D={address}&api_key={ZAPPER_API_KEY}"
    logging.info(url)
    zapper_res = requests.get(url)
    if zapper_res is None:
        print('无法连接zapper，需要海外托管者')
        exit() 

    return zapper_res

#保存wallet信息
def storeWallet(address, network, assets):
    try:
        for asset in assets:
            token_record = DefiWalletToken()
            token = asset['tokens'][0]
            token_record.address = address
            token_record.network = network
            token_record.token = token['symbol']
            token_record.usd_value = token['balanceUSD']
            token_record.amount = token['balance']
            token_record.price = token['price']
            token_record.log_time = datetime.now()


            session.add(token_record)
        session.commit()

    except Exception as e:
        logging.error(e)
        session.rollback()

#处理产品信息_convex
def process_products(products, address):
    for product in products:
        if product['label'] == 'Staked':
            assets = product['assets']
            for asset in assets:
                new_record = DefiMonitorBalance()
                new_record.address = address
                new_record.project_name = asset['appName']
                i = 0
                total_claimable_usd_value = 0
                for token_data in asset['tokens']:
                    if token_data["metaType"] == 'claimable': 
                        i +=1
                        total_claimable_usd_value += token_data['balanceUSD']
                        if i==1:
                            new_record.name_claim_reward1= token_data['symbol']
                            new_record.amount_claim_reward1 = token_data['balance']
                        elif i==2:
                            new_record.name_claim_reward2= token_data['symbol']
                            new_record.amount_claim_reward2 = token_data['balance']
                        elif i==3:
                            new_record.name_claim_reward3= token_data['symbol']
                            new_record.amount_claim_reward3 = token_data['balance']
                    elif token_data["metaType"] == 'staked':
    
                        new_record.amount_lp = token_data['balance']
                        new_record.lp_token_name = token_data['label']
                        lp_token_data = token_data['tokens'][0]
                        tokens_in_lp1 = lp_token_data['tokens'][0]
                        new_record.name_token1 = tokens_in_lp1['symbol']
                        new_record.amount_token1 = round(tokens_in_lp1['balance'], 4)
                        new_record.price_lp_token1 = round(tokens_in_lp1['price'], 4)
                        new_record.usd_value_lp_token1 = round(tokens_in_lp1['balanceUSD'],4)


                        tokens_in_lp2 = lp_token_data['tokens'][1]
                        new_record.name_token2 = tokens_in_lp2['symbol']
                        new_record.amount_token2 = round(tokens_in_lp2['balance'],4)
                        new_record.price_lp_token2 = round(tokens_in_lp2['price'],4)
                        new_record.usd_value_lp_token2 = round(tokens_in_lp2['balanceUSD'],4)

                        #TODO 处理eth value，cureve特定
                        new_record.lp_eth_value = tokens_in_lp1['balance'] + tokens_in_lp2['balanceUSD'] / tokens_in_lp1['price']

                new_record.total_claimable_usd_value = total_claimable_usd_value
                new_record.log_datetime = datetime.now()
                session.add(new_record)

    try:

        session.commit()

    except Exception as e:
        session.rollback()
        logging.error(e)

###################################
# main function

###################################
def main():
    #启动运行第一次
    check_zapper()

    scheduler = BackgroundScheduler()
    # scheduler.add_job(check_zapper, 'interval', minutes=30)
    scheduler.add_job(check_zapper, 'cron', hour='*')
    scheduler.start()
    Log('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()

# python cex_monitor.py -f binance_guptalee -p margin_monitor
if __name__ == '__main__':
    main()