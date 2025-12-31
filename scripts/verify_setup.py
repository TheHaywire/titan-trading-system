from mt5_interface import MT5Interface
from notification import EmailNotification
import config

def verify():
    print("Verifying setup...")
    
    # 1. Check Config
    print(f"Server: {config.MT5_SERVER}")
    print(f"Login: {config.MT5_LOGIN}")
    
    # 2. MT5 Connection
    mt5 = MT5Interface()
    if mt5.start():
        print("PASS: MT5 Connection Successful")
        info = mt5.get_symbol_info("EURUSD")
        if info:
            print(f"PASS: Symbol Info Retrieved (EURUSD Bid: {info.bid})")
        else:
            print("WARN: Could not get symbol info (Markets might be closed or symbol invalid)")
        mt5.shutdown()
    else:
        print("FAIL: MT5 Connection Failed")

    # 3. Email
    nt = EmailNotification()
    if nt.send_email("Verification Test", "This is a verification email from your Trading Bot."):
        print("PASS: Email Sent")
    else:
        print("FAIL: Email Sending Failed")

if __name__ == "__main__":
    verify()
