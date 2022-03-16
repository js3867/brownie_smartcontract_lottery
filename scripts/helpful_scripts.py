# SPDX-License Identifier: MIT

from brownie import (
    accounts,
    network,
    config,
    MockV3Aggregator,
    VRFCoordinatorMock,
    LinkToken,
    Contract,
    interface,
)

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]

# None is default value but can be overridden if params passed
def get_account(index=None, id=None):
    # accounts[0] <- to use ganache accounts
    # accounts.add("env") <- env variables
    # accounts.load("id") <- using our brownie Terminals setup accounts
    if index:
        return accounts[index]  # n/a here
    if id:
        return accounts.load(id)  # n/a here
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]
    return accounts.add(
        config["wallets"]["from_key"]
    )  # default option if all else fail


# return (via mapping) the contract Type from the config file, based on its name
contract_to_mock = {
    # contract_to_mock[contract_name] : Contract Type
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}


def get_contract(contract_name):
    """
    This function will grab the contract addresses from the brownie config
    if defined, otherwise, it will deploy a mock version of that contract, and
    return that mock contract.
        Args:
            contract_name (string)
        Returns:
            brownie.network.contract.ProjectContract: The most recently deployed
            version of this contract.
    """
    contract_type = contract_to_mock[contract_name]  # using mapping
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:  # for development envs
        # we skip in FORKED_BLO... as we don't need to deploy a Mock on a forked environment
        if len(contract_type) <= 0:  # eq. to doing: MockV3Aggregator.length
            # if none have been deployed, then:
            deploy_mocks()
        # else:
        contract = contract_type[-1]
        # eq. to doing: MockV3Aggregator[-1] for 'eth_usd_price_feed'
        # or [other type] for 'vrf_coordinator'
        # this is basically grabbing the latest Mocks contract that has been deployed
    else:  # for testnets etc
        contract_address = config["networks"][network.show_active()][contract_name]
        contract = Contract.from_abi(  # from brownie import Contract
            contract_type._name,
            contract_address,
            contract_type.abi,  # i.e. MockV3Aggregator.abi
        )  # basically serves up a contract with key data to pass
    return contract


DECIMALS = 8
INITIAL_VALUE = 200000000000


def deploy_mocks(decimals=DECIMALS, initial_value=INITIAL_VALUE):
    account = get_account()
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})
    print("Deployed!")


def fund_with_link(
    contract_address, account=None, link_token=None, amount=100000000000000000
):  # 0.1 LINK # these ^ ^ ^ are the params so far (w/ defaults set)
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    # if account == True = account, else = get_account()
    # if LINK == True = LINK, else = get_contract("link_token")
    tx = link_token.transfer(contract_address, amount, {"from": account})
    ### interfaces (e.g. LinkTokenInterface.sol) can be used to help brownie do things more simply
    # link_token_contract = interface.LinkTokenInterface(link_token.address)
    # tx = link_token_contract.transfer(contract_address, amount, {"from": account})
    tx.wait(1)
    print("Fund contract!")
    return tx
