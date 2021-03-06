import streamlit as st
import requests
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import pandas as pd
from datetime import datetime
from PIL import Image
from streamlit import session_state

image = Image.open('logo.png')
st.set_page_config(
        page_title="TNBC Explorer",
        page_icon=image,
        layout="wide",
    )

VALIDATOR_IP = '52.52.160.149'
BANK_IP = "54.183.16.194"  

if "account_number_for_transaction_history" not in session_state:
    session_state["account_number_for_transaction_history"] = 0

if "isTransactionHistoryEnabled" not in session_state:
    session_state["isTransactionHistoryEnabled"] = False

if "history_offset" not in session_state:
    session_state["history_offset"] = 0

if "offset" not in session_state:
    session_state["offset"] = 0

logo = Image.open('512px.png')
_,logo_col,_ = st.columns([1,2,1])
logo_col.image(logo,use_column_width='always')


# Bank IP and Validator node IP
# This will change in the future
def changeBankIp(IP):
    BANK_IP=IP

def changeValidatorIp(IP):
   VALIDATOR_IP=IP

_, bank_ip = st.columns([10,2])
_, validator_ip = st.columns([10,2])

BANK_IP  = bank_ip.text_input("BANK-IP", value=BANK_IP, on_change=changeBankIp(BANK_IP))
VALIDATOR_IP = validator_ip.text_input("VALIDATOR-IP", value=VALIDATOR_IP,on_change=changeValidatorIp(VALIDATOR_IP))

# Account balance
def balance():
    account_number = st.text_input('Account number', '' ,help='Type your account number here to fetch the account balance')
    if (st.button('Check Balance')):
        if not account_number:
            st.markdown("<h3 style='text-align: center; color: red;'>Please enter a valid TNBC Account number</h3>", unsafe_allow_html=True)
        else:
            session_state["isTransactionHistoryEnabled"] = True
            session_state["account_number_for_transaction_history"] = account_number
            session_state["history_offset"] = 0
            url = "http://{}/accounts/{}/balance".format(VALIDATOR_IP, account_number)
            payload={}
            headers = {}
            try:
                response = requests.request("GET", url, headers=headers, data=payload, timeout=5)
                balance = json.loads(response.text)['balance']
                if balance is not None:
                    balance = "{:,}".format(balance)
                else:
                    balance = 0
                st.markdown("<h3 style='text-align: center; color: green;'>Account balance is : {} TNBC </h3>".format(balance), unsafe_allow_html=True)
            except (ConnectionError, Timeout, TooManyRedirects, Exception) as e:
                st.markdown("<h3 style='text-align: center; color: red;'>Uh oh! Unable to connect to Validator Node!</h3>", unsafe_allow_html=True)

balance()

#  Transaction History for an account
def account_transaction_history(account_number,limit,offset):
    snd =[]
    rcv=[]
    tme=[]
    amt=[]
    # fee=[]
    memo=[]

    url = "http://{}/bank_transactions?account_number={}&block__sender=&fee=&limit={}&offset={}&recipient=".format(BANK_IP,account_number,limit,offset)
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    
    transactions = json.loads(response.text)["results"]
    transaction_count =0

    idx = [ x for x in range(offset+1, offset+1+len(transactions))]
    for transaction in transactions:
        transaction_count+=1
        snd.append(transaction["block"]["sender"])
        rcv.append(transaction["recipient"])
        timestamp = transaction["block"]["modified_date"]
        timestamp = timestamp.rstrip(timestamp[-1])
        date_time = datetime.fromisoformat(timestamp)
        d = date_time.strftime("%d %B %Y, %H:%M:%S")
        tme.append(d+'Z')
        amt.append(transaction["amount"])
        # fee.append(transaction["fee"])
        memo.append(transaction["memo"])
   
    return pd.DataFrame({
        "Index": idx,
        "Sender" :snd,
        "Recipient": rcv,
        "Time" : tme,
        "Memo":memo,
        "Coins" :  amt
        # "Fees" : fee,
        
    })

def get_history_page_count(account_number):
    url = "http://{}/bank_transactions?account_number={}&block__sender=&fee=&recipient=".format(BANK_IP,account_number)
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    count = int(json.loads(response.text)["count"])
    page = count // 10
    # st.write(count)
    return page

account_transaction_history_per_page =10
 
if(session_state["isTransactionHistoryEnabled"]):
        account_number = session_state["account_number_for_transaction_history"]
        st.markdown("<h3 style='text-align: left; color: #ecedf3;'>Transaction history for the account : {} </h3>".format(account_number), unsafe_allow_html=True)


pv, _ ,nx = st.columns([1, 10, 1])

if(session_state["isTransactionHistoryEnabled"]):
        last_page = get_history_page_count(session_state["account_number_for_transaction_history"]) 
        if nx.button("Next", key="prev_transaction_history_page"):

            if session_state["history_offset"] + 1 > last_page:
                session_state["history_offset"] = 0
            else:
                session_state["history_offset"] += 1

        if pv.button("Previous", key="next_transaction_history_page"):

            if session_state["history_offset"] - 1 < 0:
                session_state["history_offset"] = last_page
            else:
                session_state["history_offset"] -= 1

        history_start_index = session_state["history_offset"] * account_transaction_history_per_page 
        history_data = account_transaction_history(account_number, account_transaction_history_per_page,history_start_index)
        st.table(history_data.set_index('Index'))


#  Transactions
st.markdown("<h3 style='text-align: left; color: #ecedf3;'>Latest transactions on the network : </h3>", unsafe_allow_html=True)

def get_page_count():
    url = "http://{}/bank_transactions?limit={}".format(BANK_IP,5)
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    count = int(json.loads(response.text)["count"])
    page = count // 10
    return page

def get_transaction_df(limit, offset):
    
    snd =[]
    rcv=[]
    tme=[]
    amt=[]
    memo=[]

    url = "http://{}/bank_transactions?limit={}&offset={}".format(BANK_IP,limit,offset)
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    
    transactions = json.loads(response.text)["results"]
    itemCount =0
    idx = [ x for x in range(offset+1, offset+1+len(transactions))]

    for transaction in transactions:
        itemCount+=1
        snd.append(transaction["block"]["sender"])
        rcv.append(transaction["recipient"])
        timestamp = transaction["block"]["modified_date"]
        timestamp = timestamp.rstrip(timestamp[-1])
        date_time = datetime.fromisoformat(timestamp)
        d = date_time.strftime("%d %B %Y, %H:%M:%S")
        tme.append(d+'Z')
        amt.append(transaction["amount"])
        memo.append(transaction["memo"])
    
    return pd.DataFrame({
        "Index" : idx,
        "Sender" :snd,
        "Recipient": rcv,
        "Time" : tme,
        "Memo" : memo,
        "Coins" :  amt
    })

transactions_per_page = 10

last_page = get_page_count() 
prev, _ ,nxt = st.columns([1, 10, 1])
if nxt.button("Next"):

    if session_state["offset"] + 1 > last_page:
        session_state["offset"] = 0
    else:
        session_state["offset"] = session_state["offset"]+1

if prev.button("Previous"):

    if session_state["offset"] - 1 < 0:
        session_state["offset"] = last_page
    else:
        session_state["offset"] = session_state["offset"] - 1

start_idx = session_state["offset"] * transactions_per_page 
end_idx = (1 + session_state["offset"]) * transactions_per_page 

data = get_transaction_df(transactions_per_page,start_idx)
st.table(data.set_index('Index'))


footer="""<style>
a:link , a:visited{
color: #ecedf3;
background-color: transparent;
text-decoration: underline;
}

a:hover,  a:active {
color: red;
background-color: transparent;
text-decoration: underline;
}

.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: black;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p style='color: #ecedf3;'> Made with <a style="text-decoration:none" href="https://streamlit.io/" target="blank"> Streamlit </a>???  <a> by</a><a style='display: block; text-align: center; text-decoration:none;' href="https://github.com/arjunraghurama" target="blank">Arjun</a></p>
</div>
"""
st.markdown(footer,unsafe_allow_html=True)
