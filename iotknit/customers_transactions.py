from iotknit import *
from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrp_to_drops
import json
import csv
import pandas as pd
import datetime

# Initialize MQTT with a localhost broker
init("192.168.1.68")

# Set the prefix for actors
prefix("api")


pub = publisher("user_details") 
pub_status = publisher("transaction_status")


# Define the network client
JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
client = JsonRpcClient(JSON_RPC_URL)

# load db in runtime
db_df = pd.read_csv("/home/steven/repo/xrpl-iot/database/db_customersMQTT.csv", delimiter=",")
# print(db_df)

cuccrent_results = []

def search_card(db_df, used_card):  
    # search card in db  
    card_list = db_df['card_id']
    card_found = False
    results = [None, None, None, None]
    global cuccrent_results
    for card in card_list:
        if(card == used_card):        
            card_index = db_df.index.get_loc(db_df[db_df['card_id'] == used_card].index[0])
            card_found = True            
            
            has_account = db_df['account_holder'].loc[card_index]  # is it an account holder?           
            billing_system = db_df['service_type'].loc[card_index] # What is the billing type
            service_cost = db_df['service_fee'].loc[card_index] # fee for the service
            key_needed = db_df['pay_with_passkey'].loc[card_index] # user approval for 4 digits passkey usage
            account_secret = db_df['account_secret'].loc[card_index]


            results = [has_account, billing_system, card_found, service_cost, key_needed, used_card, account_secret]
            cuccrent_results = [service_cost, account_secret]

    return results
            

# transaction vars
 
def get_credentials(pass_key):  
    # get pass_key index from db  
    key_index = db_df.index.get_loc(db_df[db_df['pass_key'] == int(pass_key)].index[0])
    # extract secret key from db
    finger_Print_Key = str(db_df['account_secret'].loc[key_index])
    return finger_Print_Key

def get_credentials_byCard(card):  
    # get pass_key index from db  
    key_index = db_df.index.get_loc(db_df[db_df['card_id'] == int(card)].index[0])
    # extract secret key from db
    finger_Print_Key = str(db_df['account_secret'].loc[key_index])
    return finger_Print_Key


# Transaction
def xrp_transaction(fee, secret):
    
    try:        

        if secret is not None:        

            amount = str(fee)
            sender_secret = secret
            RECIPIENT_ADDRESS = "rMzQgiefzRfqzKTaZUxD1uYEfNajuFYtwa"  # Service provider's account

            print('Transaction is progress ...')

            # Generate a wallet object for the sender
            sender_wallet = Wallet.from_seed(seed=sender_secret)

            # Construct the payment transaction
            payment_transaction = Payment(
                account=sender_wallet.classic_address,
                amount=xrp_to_drops(amount),            # 1 XRP is represented as 1,000,000 drops
                destination=RECIPIENT_ADDRESS,
            )

            # Sign and submit the transaction
            tx_response = submit_and_wait(payment_transaction, client, sender_wallet)
            # print(tx_response)

            client_feedback = str(tx_response.status)

            if(client_feedback == "ResponseStatus.SUCCESS"):
                screen_msg = "PAYMENT SUCCESSFUL"
            else: 
                screen_msg = "TRANSCTION FAIL PLEASE CHECK ACCOUNT DETAILS"

            pub_status.publish(screen_msg)

            print('client_feedback--------------------', client_feedback)

    except Exception as e:
        print("Error processing message:", e)


# Callback function for MQTT message
def tempCallback(msg):
    global db_df
   
    try:
        # print("received:", msg)
        results = search_card(db_df, msg)
        # print(results)

        pub.publish(results)
        # results ############ [has_account, billing_system, card_found, service_cost, key_needed, used_card, account_secret]
        amount = results[3]
        secret = results[6]
        xrp_transaction(amount, secret)

    except Exception as e:
        print("Error processing message:", e)


# Subscribe to the MQTT topic "api/used_card"
receiv = subscriber("used_card")                                  
receiv.subscribe(callback=tempCallback, ignore_case=False)

# Run indefinitely
run()




















