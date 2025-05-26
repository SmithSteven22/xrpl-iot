from iotknit import *
from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrp_to_drops
import pandas as pd
import datetime

init("192.168.1.67")
prefix("api")

pub_details = publisher("transaction_details") 
pub_status = publisher("transaction_status")

# Define the network client
JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
client = JsonRpcClient(JSON_RPC_URL)

DB_PATH = "/home/steven/repo/xrpl-iot/database/clients_database.csv"
db_df = pd.read_csv(DB_PATH)

# Dictionary to track active sessions for time-based users
active_sessions = {}


def xrp_transaction(fee, secret):
    
    try:        

        if not secret:
            raise ValueError("Account secret key is missing.")        

        sender_wallet = Wallet.from_seed(seed=secret)
        RECIPIENT_ADDRESS = "rMzQgiefzRfqzKTaZUxD1uYEfNajuFYtwa"  # Service provider's account secret key       

        # Construct the payment transaction
        payment_transaction = Payment(
            account=sender_wallet.classic_address,
            amount=xrp_to_drops(fee),      # 1 XRP is represented as 1,000,000 drops
            destination=RECIPIENT_ADDRESS,
        )

        # Sign and submit the transaction
        tx_response = submit_and_wait(payment_transaction, client, sender_wallet)
        status = str(tx_response.status)

        drops_received = int(tx_response.result["meta"]["delivered_amount"])
        xrp_received   = drops_received / 1_000_000

        if status == "ResponseStatus.SUCCESS":
            pub_status.publish("PAYMENT SUCCESSFUL")
        else: 
            pub_status.publish("TRANSACTION FAILED")

        print(f"Transaction feedback: {status}, received: {xrp_received} XRP")
        return status, xrp_received

    except Exception as e:
        pub_status.publish("TRANSACTION ERROR")
        print(f"Error during XRP transaction: {e}")
        return "ERROR", 0.0



def tempCallback(msg):
    
    card_id = msg

    # Look up the card in the database
    user_data = db_df[db_df["card_id"] == card_id]

    if user_data.empty:
        pub_status.publish("CARD NOT REGISTERED")
        return
    
    info = user_data.iloc[0]
    now = datetime.datetime.now()
    service_type = info["service_type"]
    account_secret = info["account_secret"]
    user_id = info["user_id"]
    card_status = info["card_status"]
    subs_date_str = info["subs_date"]

    if card_status != "active":
        return pub_status.publish("CARD INACTIVE")

    # Publish user details
    user_details = {
        "user_id": user_id,
        "service_type": service_type,
        "card_status": card_status,
        "subs_date": subs_date_str,
    }
    pub_details.publish(str(user_details))


    # -------Time-based------------
    # Check-in
    if service_type == "tb":
        if card_id not in active_sessions:
            active_sessions[card_id] = now
            return pub_status.publish("CHECK-IN SUCCESSFUL")
        
        # Check-out
        start = active_sessions.pop(card_id)
        minutes =(now - start).total_seconds() / 60
        fee = minutes * info.get("tb_fee_rate", 0)
        # xrp_transaction(fee, account_secret)

    else:
        # Subscription-based
        exp = datetime.datetime.strptime(info["exp_date"], "%Y-%m-%d %H:%M:%S")
        if now > exp:
            return pub_status.publish("SUBSCRIPTION EXIRED")
        # xrp_transaction(info["service_fee"], account_secret)
        fee = info["service_fee"]
    
    tx_status, xrp_received = xrp_transaction(fee, account_secret)

    user_details = {
        "user_id":      user_id,
        "service_type": service_type,
        "card_status":  card_status,
        "subs_date":    subs_date_str,
        "service_fee":  f"{fee} XRP",
        "tx_status":    tx_status,
        "xrp_received": f"{xrp_received:,.6f} XRP"
    }
    pub_details.publish(str(user_details))


receiv = subscriber("used_card")                                  
receiv.subscribe(callback=tempCallback, ignore_case=False)

# Start the MQTT service
run()