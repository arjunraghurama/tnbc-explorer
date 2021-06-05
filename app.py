import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from PIL import Image
import SessionState

image = Image.open('logo.png')
st.set_page_config(
        page_title="TNBC Explorer",
        page_icon=image,
        layout="wide",
    )

VALIDATOR_IP = '54.219.183.128' 
BANK_IP = "54.177.121.3"  

st.markdown("<h1 style='text-align: center; color: red;'>TheNewBostonCoin Blockchain Explorer</h1>", unsafe_allow_html=True)

# Account balance
def balance():
    account_number = st.text_input('Account number', '' ,help='Type your account number here to fetch the account balance')
    if (st.button('Check Blance')):
        url = "http://{}/accounts/{}/balance".format(VALIDATOR_IP, account_number)
        payload={}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        balance = json.loads(response.text)['balance']
        st.markdown("<h3 style='text-align: center; color: green;'>Account balance is : {}</h3>".format(balance), unsafe_allow_html=True)

balance()

slot = st.empty()

#  Transactions
st.markdown("<h3 style='text-align: left; color: green;'>Latest Transactions</h3>", unsafe_allow_html=True)

def get_page_count():
    url = "http://{}/bank_transactions?limit={}".format(BANK_IP,5)
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    count = int(json.loads(response.text)["count"])
    page = count // 10
    return page

def get_transaction_df(limit, offset, progress_bar):
    
    snd =[]
    rcv=[]
    tme=[]
    amt=[]

    url = "http://{}/bank_transactions?limit={}&offset={}".format(BANK_IP,limit,offset)
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    
    transactions = json.loads(response.text)["results"]
    itemCount =0

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
        progress_bar.progress( itemCount /len(transactions) )
    
    return pd.DataFrame({
        "Sender" :snd,
        "Recipient": rcv,
        "Time" : tme,
        "Coins" :  amt
    })

transactions_per_page = 10
session_state = SessionState.get(offset = 0)

last_page = get_page_count() 
prev, _ ,nxt = st.beta_columns([1, 10, 1])
if nxt.button("Next"):

    if session_state.offset + 1 > last_page:
        session_state.offset = 0
    else:
        session_state.offset += 1

if prev.button("Previous"):

    if session_state.offset - 1 < 0:
        session_state.offset = last_page
    else:
        session_state.offset -= 1

start_idx = session_state.offset * transactions_per_page 
end_idx = (1 + session_state.offset) * transactions_per_page 

progressbar = st.progress(0.0)
data = get_transaction_df(transactions_per_page,start_idx,progressbar)
st.table(data)

if not hasattr(st, 'already_started_server'):
    # Hack the fact that Python modules (like st) only load once to
    # keep track of whether this file already ran.
    st.already_started_server = True

    st.write('''
        The first time this script executes it will run forever because it's
        running a Flask server.

        Just close this browser tab and open a new one to see your Streamlit
        app.
    ''')

    from flask import Flask

    app = Flask(__name__)

    @app.route('/stats')
    def stats():
        return str(10)

    app.run(port=8888)

footer="""<style>
a:link , a:visited{
color: blue;
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
background-color: white;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p>Made with <a style="text-decoration:none" href="https://streamlit.io/" target="blank"> Streamlit </a>❤  <a> by</a><a style='display: block; text-align: center; text-decoration:none;' href="https://github.com/arjunraghurama" target="blank">Arjun</a></p>
</div>
"""
st.markdown(footer,unsafe_allow_html=True)
