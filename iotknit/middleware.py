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

init("192.168.1.68")
prefix("api")

pub_details = publisher("transaction_details") 
pub_status = publisher("transaction_status")

# Define the network client
JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
client = JsonRpcClient(JSON_RPC_URL)

DB_PATH = "/home/steven/repo/xrpl-iot/database/clients_database.csv"
db_df = pd.read_csv(DB_PATH)


def xrp_transaction(fee, secret):
    
    try:        

        if not secret:
            raise ValueError("Account secret key is missing.")        

        sender_wallet = Wallet.from_seed(seed=secret)
        RECIPIENT_ADDRESS = "rMzQgiefzRfqzKTaZUxD1uYEfNajuFYtwa"  # Service provider's account        

        # Construct the payment transaction
        payment_transaction = Payment(
            account=sender_wallet.classic_address,
            amount=xrp_to_drops(fee),      # 1 XRP is represented as 1,000,000 drops
            destination=RECIPIENT_ADDRESS,
        )

        # Sign and submit the transaction
        tx_response = submit_and_wait(payment_transaction, client, sender_wallet)
        feedback = str(tx_response.status)

        if feedback == "ResponseStatus.SUCCESS":
            screen_msg = "PAYMENT SUCCESSFUL"
        else: 
            screen_msg = "TRANSCTION FAILED, CHECK ACCOUNT DETAILS"

        pub_status.publish(screen_msg)
        print(f"Transaction feedback: {feedback}")

    except Exception as e:
        print(f"Error during XRP transaction: {e}")
        pub_status.publish("TRANSACTION ERROR")

# Dictionary to track active sessions for time-based users
active_sessions = {}


def tempCallback(msg):
    try:
        # Extract the card_id from the received message
        card_id = msg

        # Look up the card in the database
        user_data = db_df[db_df["card_id"] == card_id]

        if user_data.empty:
            pub_status.publish("CARD NOT REGISTERED")
            return
        
        user_id = user_data.iloc[0]["user_id"]
        service_type = user_data.iloc[0]["service_type"]
        tb_fee_rate = user_data.iloc[0].get("tb_fee_rate", 0)
        account_secret = user_data.iloc[0]["account_secret"]
        card_status = user_data.iloc[0]["card_status"]
        service_fee = user_data.iloc[0]["service_fee"]
        subs_date_str = user_data.iloc[0]["subs_date"]

        #Publish user details
        user_details = {
            "user_id": user_id,
            "service_type": service_type,
            "card_status": card_status,
            "subs_date": subs_date_str,
            "service_fee": f"{service_fee} XRP"
        }
        pub_details.publish(str(user_details))

        # Validate the card's status
        if card_status != "active":
            pub_status.publish("CARD INACTIVE")
            return
        
        now = datetime.datetime.now()

        # Parse subs_date for accurate elapsed time calculation
        subs_date = datetime.datetime.strptime(subs_date_str, "%Y-%m-%d %H:%M:%S")
        
        # Handle Subscription-Based (sb)
        if service_type == "sb":
            exp_date_str = user_data.iloc[0]["exp_date"]
            exp_date = datetime.datetime.strptime(exp_date_str, "%Y-%m-%d %H:%M:%S")
            service_fee = user_data.iloc[0]["service_fee"]

            if now > exp_date:
                pub_status.publish("SUBSCRIPTION EXPIRED")
                return

            xrp_transaction(service_fee, account_secret)
        
        ## Handle Time-Based (tb)
        elif service_type == "tb":
            if card_id in active_sessions:
                # This is a check-out event
                start_time = active_sessions.pop(card_id)
                elapsed_time = (now - start_time).total_seconds() / 60  # Duration in minutes
                rounded_elapsed_time = round(elapsed_time, 2)
                service_fee = elapsed_time * tb_fee_rate

                if service_fee <= 0:
                    pub_status.publish("INVALID TIME-BASED FEE")
                    return

                xrp_transaction(service_fee, account_secret)
                session_details = {
                    "user_id": user_id,
                    "elapsed_time": f"{rounded_elapsed_time} min",
                    "service_fee": f"{service_fee} XRP"
                }
                pub_details.publish(str(session_details))

                # Update subs_date with the last check-out time for record-keeping
                db_df.loc[db_df["card_id"] == card_id, "subs_date"] = now.strftime("%Y-%m-%d %H:%M:%S")
                db_df.to_csv("/home/steven/repo/xrpl-iot/database/clients_database.csv", index=False)
            else:
                # This is a check-in event
                active_sessions[card_id] = now
                pub_status.publish("CHECK-IN SUCCESSFUL")
    
    except Exception as e:
        print("Error processing message:", e)


# Subscribe to the MQTT topic "api/used_card"
receiv = subscriber("used_card")                                  
receiv.subscribe(callback=tempCallback, ignore_case=False)

# Start the MQTT service
run()