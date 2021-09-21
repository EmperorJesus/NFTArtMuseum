import os
from web3 import Web3
from dotenv import load_dotenv
from web3.middleware import geth_poa_middleware
from eth_account import Account

from pathlib import Path
from getpass import getpass
import pandas as pd
import getpass

from etherscan import Etherscan
import json

def admin():
    load_dotenv()
    #### Infura API suite provides instant access over HTTPS and WebSockets to the Ethereum network.
    WEB3_INFURA_API_KEY =  os.getenv("WEB3_INFURA_API_KEY")
    WEB3_INFURA_PROJECT_ID = os.getenv("WEB3_INFURA_PROJECT_ID")
    # read contract for NFT musuem
    nft_museum_address = os.getenv("nft_museum_address")
    ### Contract NFT Art Musuem owner private key
    museum_private_key = os.getenv("PRIVATE_KEY1")
    #### project is deployed on Kovan Ethereum testnet
    ETHERSCAN_API = os.getenv("ETHERSCAN_API")
    eth = Etherscan(ETHERSCAN_API, net= "KOVAN")
    #### Connect to infura kovan
    https_str = f'https://kovan.infura.io/v3/{WEB3_INFURA_PROJECT_ID}'
    w1 = Web3(Web3.HTTPProvider(https_str))
    w1.middleware_onion.inject(geth_poa_middleware, layer=0)
    account_contract_owner = Account.from_key(museum_private_key)
    from web3.auto.infura import w3
    return WEB3_INFURA_API_KEY, WEB3_INFURA_PROJECT_ID, nft_museum_address, museum_private_key, eth, w1, account_contract_owner, w3

zero_address = '0x0000000000000000000000000000000000000000'
WEB3_INFURA_API_KEY, WEB3_INFURA_PROJECT_ID, nft_museum_address, museum_private_key, eth, w1, account_contract_owner, w3 = admin()

## read NFTArtMuseum contract ABI
with open("NFTArtMuseumABI.txt") as f:
    nftArtMuseum_json = json.load(f)
    
## Create Contract NFT Art Museum instance
contract_NFTArtMuseuminstance = w1.eth.contract(address=nft_museum_address, abi=nftArtMuseum_json)

## Get contract Functions & Check some Contract attributes --- only for testing
def contract_testing(contract_NFTArtMuseuminstance):
    l_all_funcs = contract_NFTArtMuseuminstance.all_functions()
    #print(l_all_funcs)
    for l_func in l_all_funcs:
        print(l_func)
    l_symbol = contract_NFTArtMuseuminstance.functions.symbol().call()
    print('Symbol: ', l_symbol)
    l_name = contract_NFTArtMuseuminstance.functions.name().call()
    print('Name: , ',l_name)
    l_art_collection = contract_NFTArtMuseuminstance.functions.art_collection(1).call()
    print('Art collection: ', l_art_collection)
    l_total_supply = contract_NFTArtMuseuminstance.functions.totalSupply().call()
    print('Total NFT art in Museum: ', l_total_supply)
    return l_all_funcs, l_symbol, l_name, l_art_collection, l_total_supply

#l_all_funcs, l_symbol, l_name, l_art_collection, l_total_supply =  contract_testing(contract_NFTArtMuseuminstance)

## INPUT Function to Get Artist Registry info and for now maybe write to a file to store it
def get_artist_registry_info():
    error = 0
    error_message = ''
    nft_name = input('Enter your NFT name: ')
    artist_name = input('Enter your name: ')
    l_price = input('Enter your price for this NFT: ')
    try:
        price = int(l_price)
    except Exception as error_message:
        print('ERROR', error_message)
        error = 1    
    token_uri = input('Enter your token URI in IPFS format: ')
    # Get Private key of Artist since we need later for Approval
    try:
        artist_private_key = getpass.getpass('Enter your private key: ')
    except Exception as error_message:
        print('ERROR', error_message)
        error = 1
    try:
        account_artist = Account.from_key(artist_private_key)
    except Exception as error_message:
        print('ERROR', error_message)
        error = 1
    return nft_name, artist_name, price, token_uri, artist_private_key, account_artist, error, error_message


## INPUT Function to Get Artist private key for Approval
def get_artist_private_key():
    error = 0
    error_message = ''
    try:
        artist_private_key_buy = getpass.getpass('Enter Artists private key for the token to buy: ')
    except Exception as error_private_key:
        print('ERROR', error_message)
        error = 1
    if error == 0:
        account_artist_buy = Account.from_key(artist_private_key_buy)
    l_price = input('Enter your price for this NFT: ')
    try:
        price = int(l_price)
    except Exception as error_message:
        print('ERROR', error_message)
        error = 1  
    return price, artist_private_key_buy, account_artist_buy, error, error_message

## INPUT Function to BuyNFT
def get_buy_nft_input():
    error = 0
    error_message = ''
    #nft_name = input('Enter your NFT name: ')
    #artist_name = input('Enter your name: ')
    l_token_id = input('Enter your token_id of NFT: ')
    buy_token_id = int(l_token_id)
    #token_uri = input('Enter your token URI in IPFS format: ')
    # Get Private key of Artist since we need later for Approval
    try:
        buyer_private_key = getpass.getpass('Enter your private key: ')
    except Exception as error_message:
        print('ERROR', error_message)
        error = 1
        #print('Password entered:', artist_private_key)
        # Get Artists Crypto Address they want to use to register and get paid
    try:
        account_buyer = Account.from_key(buyer_private_key)
    except Exception as error_message:
        print('ERROR: ',error_message)
        error = 1
    print('Buyer balance = ', eth.get_eth_balance(address=account_buyer.address))
    return buy_token_id, buyer_private_key, account_buyer, error, error_message


## Prep to Get Nonce, Chain id, Gas estimate 
def prep_transaction(address):
    nonce = w1.eth.get_transaction_count(address)
    chain_id = w1.eth.chain_id
    # For Gas get latest block for better estimation
    w1.eth.getBlock("latest")
    dict1 = w1.eth.getBlock("latest")
    gasEstimate = dict1['gasUsed']
    # we sometimes see that the Latest block could return 0 too
    if gasEstimate < 600000:
        gasEstimate = 600000
    gas_price = w1.eth.gasPrice
    return chain_id, gasEstimate, gas_price, nonce


## Build transaction for Registering Art
def execute_art_registry(museum_private_key, artist_address, nft_name, artist_name, price, token_uri, chain_id, gasEstimate, gas_price, nonce):
    register_nft_txn = contract_NFTArtMuseuminstance.functions.registerArtwork(artist_address,nft_name,artist_name,price,token_uri).buildTransaction({'chainId':chain_id, 'gas': gasEstimate, 'gasPrice': gas_price, 'nonce': nonce})
    ### Register Art Sign transaction w Contract owner credentials
    error_signing_txn = ''
    error_sign = 0
    try:
        register_signed_txn = w1.eth.account.sign_transaction(register_nft_txn, private_key=museum_private_key)
    except Exception as error_signing_txn:
        error_sign = 1
    ### Send transaction for Registering
    error_sending_txn = ''
    error_send = 0
    try:
        register_sent_txn = w1.eth.send_raw_transaction(register_signed_txn.rawTransaction) 
    except Exception as error_sending_txn:
        error_send = 1
    #register_get_txn = w1.eth.getTransaction(register_sent_txn)
    return register_nft_txn, register_signed_txn.hash, register_signed_txn.rawTransaction, register_signed_txn.r, register_signed_txn.s, register_signed_txn.v, register_sent_txn, error_sign, error_signing_txn, error_send, error_sending_txn


## Function to execute approval
def execute_approval(artist_private_key, buyer_address, buy_token_id, chain_id, gasEstimate, gas_price, nonce):
    approve_signed_nft_txn_hash = ''
    approve_signed_nft_txn_rawTransaction = ''
    approve_signed_nft_txn_r = ''
    approve_signed_nft_txn_s = ''
    approve_signed_nft_txn_v = ''
    approve_sent_txn = ''
    approve_nft_txn = contract_NFTArtMuseuminstance.functions.approve(buyer_address,buy_token_id).buildTransaction({'chainId':chain_id, 'gas': gasEstimate, 'gasPrice': gas_price, 'nonce': nonce})
    ### Approval Sign transaction w Artist credentials
    error_signing_txn = ''
    error_sign = 0
    try:
        approve_signed_nft_txn = w1.eth.account.sign_transaction(approve_nft_txn, private_key=artist_private_key)
    except Exception as error_signing_txn:
        error_sign = 1
        print('Error in approval signed transaction: ', error_signing_txn)
    ### Send transaction for Approval
    if error_sign != 1:
        approve_signed_nft_txn_hash = approve_signed_nft_txn.hash
        approve_signed_nft_txn_rawTransaction = approve_signed_nft_txn.rawTransaction
        approve_signed_nft_txn_r = approve_signed_nft_txn.r
        approve_signed_nft_txn_s = approve_signed_nft_txn.s
        approve_signed_nft_txn_v = approve_signed_nft_txn.v
        error_sending_txn = ''
        error_send = 0
        try:
            #register_sent_txn = w1.eth.send_raw_transaction(register_signed_txn.rawTransaction) 
            approve_sent_txn = w1.eth.send_raw_transaction(approve_signed_nft_txn.rawTransaction) 
        except Exception as error_sending_txn:
            error_send = 1
            print('Error in Approval sending: ', error_sending_txn)
    #register_get_txn = w1.eth.getTransaction(register_sent_txn)
    return approve_nft_txn, approve_signed_nft_txn_hash, approve_signed_nft_txn_rawTransaction, approve_signed_nft_txn_r, approve_signed_nft_txn_s, approve_signed_nft_txn_v, approve_sent_txn, error_sign, error_signing_txn, error_send, error_sending_txn


### Function to Build transaction for Actual buy - Buyer will pay Owner and can tranfer since Buyer has approval now

### later check if Buyer address has enough balance even before the Approval

def execute_buyNFT(buyer_private_key, artist_address, price, buy_token_id, chain_id, gasEstimate, gas_price, nonce):
    #execute_buyNFT(buyer_private_key, account_artist.address, price, buy_token_id, chain_id, gasEstimate, gas_price, nonce)
    buy_nft_txn = contract_NFTArtMuseuminstance.functions.buyNFT(artist_address, price, buy_token_id).buildTransaction({'chainId':chain_id, 'gas': gasEstimate, 'gasPrice': gas_price, 'nonce': nonce, 'value': price})
    ### Sign transaction w Buyer's credentials
    error_signing_txn = ''
    error_sign = 0
    try:
        signed_buy_nft_txn = w1.eth.account.sign_transaction(buy_nft_txn, private_key=buyer_private_key)
    except Exception as error_signing_txn:
        error_sign = 1
    ### Send transaction for Approval
    error_sending_txn = ''
    error_send = 0
    try:
        #register_sent_txn = w1.eth.send_raw_transaction(register_signed_txn.rawTransaction) 
        buy_nft_sent_txn = w1.eth.send_raw_transaction(signed_buy_nft_txn.rawTransaction) 
    except Exception as error_sending_txn:
        error_send = 1
    #register_get_txn = w1.eth.getTransaction(register_sent_txn)
    return buy_nft_txn, signed_buy_nft_txn.hash, signed_buy_nft_txn.rawTransaction, signed_buy_nft_txn.r, signed_buy_nft_txn.s, signed_buy_nft_txn.v, buy_nft_sent_txn, error_sign, error_signing_txn, error_send, error_sending_txn


def approve_buy_nft(account_artist, artist_private_key, account_buyer, buyer_private_key, price, buy_token_id):
    #approve_buy_nft(account_artist_buy, artist_private_key_buy, account_buyer, buyer_private_key, price, buy_token_id)
    #approve_buy_nft(account_artist_buy, artist_private_key_buy, account_buyer, buyer_private_key, price, buy_token_id)
    error_sign = 0
    error_send = 0
    error_signing_txn = ''
    error_sending_txn = ''
    ##### First approve
    # Get Nonce, Chain id, Gas estimate for Approval
    chain_id, gasEstimate, gas_price, nonce = prep_transaction(account_artist.address)
    # call Approval
    approve_nft_txn, approve_signed_nft_txn_hash, approve_signed_nft_txn_rawTransaction, approve_signed_nft_txn_r, approve_signed_nft_txn_s, approve_signed_nft_txn_v, approve_sent_txn, error_sign, error_signing_txn, error_send, error_sending_txn = execute_approval(artist_private_key, account_buyer.address, buy_token_id, chain_id, gasEstimate, gas_price, nonce)
    if error_sign == 1:
        print('Owner approval - Error signing transaction: ', error_signing_txn)
        return error_sign, error_send, error_signing_txn, error_sending_txn
    if error_send == 1:
        print('Owner approval - Error signing transaction: ', error_sending_txn)
        return error_sign, error_send, error_signing_txn, error_sending_txn
    if error_sign != 1 and error_send != 1:
        # Approval Succeeded go forward to buy NFT and transfer funds
        # Get Nonce, Chain id, Gas estimate for Buyer address
        chain_id, gasEstimate, gas_price, nonce = prep_transaction(account_buyer.address)
        # call BuyNFT
        buy_nft_txn, signed_buy_nft_txn_hash, signed_buy_nft_txn_rawTransaction, signed_buy_nft_txn_r, signed_buy_nft_txn_s, signed_buy_nft_txn_v, buy_nft_sent_txn, error_sign, error_signing_txn, error_send, error_sending_txn = execute_buyNFT(buyer_private_key, account_artist.address, price, buy_token_id, chain_id, gasEstimate, gas_price, nonce)
        if error_sign == 1:
            print('BuyNFT - Error signing transaction: ', error_signing_txn)
        if error_send == 1:
            print('BuyNFT - Error signing transaction: ', error_sending_txn)
    return error_sign, error_send, error_signing_txn, error_sending_txn



def main_routine():
    # set up admin stuff.
    #WEB3_INFURA_API_KEY, WEB3_INFURA_PROJECT_ID, museum_private_key, eth, w1, account_contract_owner, w3 = admin()
    success = 1
    i=1
    museum_action = 0
    while i == 1:
        l_museum_action = input('Enter 1 to Register Art, 2 to Buy Art, 3 to get ContractInfo, 4 to exit: ')
        try: 
            museum_action = int(l_museum_action)
            break
        except Exception as error_action:
            print('Please only enter 1, 2, 3 or 4 ')
            return error_action
    if museum_action == 1:
        # get Artist NFT info to register
        # Call to execute Art Registry with error handling
        nft_name, artist_name, price, token_uri, artist_private_key, account_artist, error, error_message = get_artist_registry_info()
        if error == 1:
            print(error_message)
            return error_message
        ## Get Nonce, Chain id, Gas estimate for Art Registry
        chain_id, gasEstimate, gas_price, nonce = prep_transaction(account_contract_owner.address)
        register_nft_txn, register_signed_txn_hash, register_signed_txn_rawTransaction, register_signed_txn_r, register_signed_txn_s, register_signed_txn_v, register_sent_txn, error_sign, error_signing_txn, error_send, error_sending_txn = execute_art_registry(museum_private_key, account_artist.address, nft_name, artist_name, price, token_uri, chain_id, gasEstimate, gas_price, nonce)
        if error_sign == 1:
            print('NFT Art Register - Error signing transaction: ', error_signing_txn)
            return error_signing_txn
        if error_send == 1:
            print('NFT Art Register - Error signing transaction: ', error_sending_txn)
            return error_sending_txn
        if error_sign != 1 and error_send != 1:
            print('Art registry successful!! congrats.')
            print('register_nft_txn = ', register_nft_txn)
            print('register_signed_txn_hash = ', register_signed_txn_hash)
            print('register_signed_txn_rawTransaction = ', register_signed_txn_rawTransaction)
            print('register_signed_txn_r = ', register_signed_txn_r)
            print('register_signed_txn_s = ', register_signed_txn_s)
            print('register_signed_txn_v = ', register_signed_txn_v)
            print('register_sent_txn = ', register_sent_txn)
            #register_get_txn = w1.eth.getTransaction(register_sent_txn)
            #print('register_get_txn = ', register_get_txn)
            return success, "Succcess"
    if museum_action == 2:
        # get Buyer info first
        buy_token_id, buyer_private_key, account_buyer, error, error_message = get_buy_nft_input()
        print('Buy Token Id: ', buy_token_id)
        print('Buyer account address', account_buyer.address)
        print('Buyer balance = ', eth.get_eth_balance(address=account_buyer.address))
        if error != 1:
            # go ahead and get Artist's private key needed for Approval
            ## this later need to be Automated to get it automatically.
            price, artist_private_key_buy, account_artist_buy, error, error_message = get_artist_private_key()
            if error != 1:
                # go on to get approval & Buy/transfer now that we have all the info
                ##### First approve
                # Get Nonce, Chain id, Gas estimate for Approval
                error_sign = 0
                error_signing_txn = ''
                error_send = 0
                error_sending_txn = ''
                chain_id, gasEstimate, gas_price, nonce = prep_transaction(account_artist_buy.address)
                print('****************** Approval *************')
                print('Chain id = ', chain_id)
                print('gasEstimate = ', gasEstimate)
                print('gasPrice = ', gas_price)
                print('Nonce = ', nonce)
                # call Approval
                approve_nft_txn, approve_signed_nft_txn_hash, approve_signed_nft_txn_rawTransaction, approve_signed_nft_txn_r, approve_signed_nft_txn_s, approve_signed_nft_txn_v, approve_sent_txn, error_sign, error_signing_txn, error_send, error_sending_txn = execute_approval(artist_private_key_buy, account_buyer.address, buy_token_id, chain_id, gasEstimate, gas_price, nonce)
                if error_sign == 1:
                    print('Owner approval - Error signing transaction: ', error_signing_txn)
                    return error_sign, error_signing_txn
                if error_send == 1:
                    print('Owner approval - Error signing transaction: ', error_sending_txn)
                    return error_send, error_sending_txn
                if error_sign != 1 and error_send != 1:
                    print('Approval successful.')
                    print('approve_nft_txn = ', approve_nft_txn)
                    print('approve_signed_nft_txn_hash = ', approve_signed_nft_txn_hash)
                    print('approve_signed_nft_txn_rawTransaction = ', approve_signed_nft_txn_rawTransaction)
                    print('approve_signed_nft_txn_r = ', approve_signed_nft_txn_r)
                    print('approve_signed_nft_txn_s = ', approve_signed_nft_txn_s)
                    print('approve_signed_nft_txn_v = ', approve_signed_nft_txn_v)
                    print('approve_sent_txn = ', approve_sent_txn)
                    #approve_get_txn = w1.eth.getTransaction(approve_sent_txn)
                    #print('approve_get_txn = ', approve_get_txn)
                    # Approval is success now execute the Buy and Trasnfer function.
                    chain_id, gasEstimate, gas_price, nonce = prep_transaction(account_buyer.address)
                    print('****************** Buy/Transfer *************')
                    print('Chain id = ', chain_id)
                    print('gasEstimate = ', gasEstimate)
                    print('gasPrice = ', gas_price)
                    print('Nonce = ', nonce)
                    # call BuyNFT
                    buy_nft_txn, signed_buy_nft_txn_hash, signed_buy_nft_txn_rawTransaction, signed_buy_nft_txn_r, signed_buy_nft_txn_s, signed_buy_nft_txn_v, buy_nft_sent_txn, error_sign, error_signing_txn, error_send, error_sending_txn = execute_buyNFT(buyer_private_key, account_artist_buy.address, price, buy_token_id, chain_id, gasEstimate, gas_price, nonce)
                    if error_sign == 1:
                        print('BuyNFT - Error signing transaction: ', error_signing_txn)
                        return error_sign, error_signing_txn
                    if error_send == 1:
                        print('BuyNFT - Error signing transaction: ', error_sending_txn)
                        return error_send, error_sending_txn
                    if error_sign != 1 and error_send != 1:
                        print('Buy-Trasnfer successful.')
                        print('buy_nft_txn = ', buy_nft_txn)
                        print('signed_buy_nft_txn_hash = ', signed_buy_nft_txn_hash)
                        print('signed_buy_nft_txn_rawTransaction = ', signed_buy_nft_txn_rawTransaction)
                        print('signed_buy_nft_txn_r = ', signed_buy_nft_txn_r)
                        print('signed_buy_nft_txn_s = ', signed_buy_nft_txn_s)
                        print('signed_buy_nft_txn_v = ', signed_buy_nft_txn_v)
                        print('buy_nft_sent_txn = ', buy_nft_sent_txn)
                        #buy_nft_get_txn = w1.eth.getTransaction(buy_nft_sent_txn)
                        #print('buy_nft_get_txn = ', buy_nft_get_txn)
                        return 1, 'Approve and Buy/Trasfer success'
#                 error_sign, error_send, error_signing_txn, error_sending_txn = approve_buy_nft(account_artist_buy, artist_private_key_buy, account_buyer, buyer_private_key, price, buy_token_id)
#                 if error_sign != 1 and error_send != 1:
#                     print('Successfully executed - Approve/BuyNFY')
#                     # Buy NFT and transfer
#                     #buy_nft_txn, signed_buy_nft_txn_hash, signed_buy_nft_txn_rawTransaction, signed_buy_nft_txn_r, signed_buy_nft_txn_s, signed_buy_nft_txn_v, buy_nft_sent_txn, error_sign, error_signing_txn, error_send, error_sending_txn = execute_buyNFT(buyer_private_key, account_artist_buy.address, price, buy_token_id, chain_id, gasEstimate, gas_price, nonce)
#                     #if error_sign == 1:
#                         # need to later reset Approval with zero address
#                     #    return error_sign, error_signing_txn
#                     #elif error_send == 1:
#                     #    # need to later reset Approval with zero address
#                     #    return error_send, error_sending_txn
#                     #else:
#                     return success, "Success"
                
            else:
                return error, error_message
        else:
            return error, error_message
    if museum_action == 4:
        return success, "no action selected by user"


def main():
    result, result_message = main_routine()
    print('result and message: ', result, result_message)
    
if __name__ == "__main__":
    main()
    
