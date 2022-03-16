# SPDX-License Identifier: MIT

from scripts.helpful_scripts import get_account, get_contract, fund_with_link
from brownie import Lottery, network, config
import time


def deploy_lottery():
    account = get_account()
    # prepares/pulls in all Constructors required by Lottery.sol
    lottery = Lottery.deploy(
        # pulls only .address trait from Contract object
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
        # publishing sends to...
    )
    print("Deployed lottery!")
    return lottery
    # lottery variable and return value allows function to be imported elsewhere
    # such as in testing


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]  # pulls latest Lottery.sol contract (after deployed)
    starting_tx = lottery.startLottery({"from": account})
    starting_tx.wait(1)  # this is a brownie/local/dev env workaround
    # probably not required if we deploy to a testnet
    print("The lottery is started!")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFee() + 100000000  # +some wei for safety
    # enters the .address who clicked 'enter'
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(1)
    print("You entered the lottery!")


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # fund the contract
    # then end the lottery
    tx = fund_with_link(lottery.address)  # contract needs LINK for randomness service
    tx.wait(1)
    # recall onlyOwner can call endLottery in Lottery.sol
    ending_transaction = lottery.endLottery({"from": account})
    ending_transaction.wait(1)
    time.sleep(180)
    print(f"{lottery.recentWinner()} is the new winner!")


def main():
    # as is, main() simulates a whole process with only one Lottery entrant
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
