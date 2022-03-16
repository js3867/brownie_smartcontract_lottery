// SPDX-License Identifier: MIT
pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";

// use 'is' to abstract
contract Lottery is VRFConsumerBase, Ownable {
    address payable[] public players; // list of addresses who have entered the contract. Must be payable in order to receive .transfer(wallet)
    address payable public recentWinner; // winner of (This) lottery
    uint256 public randomness;
    uint256 public usdEntryFee;
    AggregatorV3Interface internal ethUsdPriceFeed; // internal > viewable to other files in this collection, but not `public` and not `private` only in this very .sol file
    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }
    // enums are used to list states. Recall {NORTH, SOUTH}, {turn_R, turn_L, do_180}
    // enum states can be called by their reference: if LOTTERY_STATE == 0 (=OPEN) 2 (=CALCULATING_WINNER)
    LOTTERY_STATE public lottery_state;
    uint256 public fee;
    bytes32 public keyhash;
    event RequestedRandomness(bytes32 requestId); // event(?)
    uint256 USD_ENTRY_PRICE = 50;

    // this constructs variables to pull from Chainlink's VRF (Verifiable Randomness ..Fing)
    constructor(
        address _priceFeedAddress, // ?
        address _vrfCoordinator, // ?
        address _link, // address for LINK tokens for fee
        uint256 _fee, // amount of LINK required for fee
        bytes32 _keyhash // ?
    ) public VRFConsumerBase(_vrfCoordinator, _link) {
        usdEntryFee = USD_ENTRY_PRICE * (10**18);
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        lottery_state = LOTTERY_STATE.CLOSED; // sets lottery state to closed in order to... ??
        fee = _fee;
        keyhash = _keyhash;
    }

    function enter() public payable {
        require(lottery_state == LOTTERY_STATE.OPEN); // requires that lottery is OPEN in order to accept new entries
        require(
            msg.value >= getEntranceFee(), // requires min fee has been paid
            "Not enough ETH!"
        );
        players.push(msg.sender); // adds address to list of entrees
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();
        uint256 adjustedPrice = uint256(price) * 10**10; // 8d.p. + 10**10d.p.
        uint256 costToEnter = (usdEntryFee * 10**18) / adjustedPrice;
        // fee_in_USD * 18dp `div` AggV3_ETH_price => fee_in_ETH
        return costToEnter;
    }

    function startLottery() public onlyOwner {
        // require(lottery_state == 2)
        require(
            lottery_state == LOTTERY_STATE.CLOSED, // lottery cannot start while enter() is in progress
            "Can't start a new lottery yet!"
        );
        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public onlyOwner {
        // THIS IS HOW NOT TO DO IT!!!
        //
        // uint256(
        //     keccack256(
        //         abi.encodePacked(
        //             nonce, // nonce is preditable (aka, transaction number)
        //             msg.sender, // msg.sender is predictable
        //             block.difficulty, // can actually be manipulated by the miners!
        //             block.timestamp // timestamp is predictable
        //         )
        //     )
        // ) % players.length;
        //
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER; // set state to CALCULATING WINNER. Prevents OPEN or CLOSE functions/require
        bytes32 requestId = requestRandomness(keyhash, fee); // ?
        emit RequestedRandomness(requestId); // emit ? is it like return except bigger?
    }

    function fulfillRandomness(bytes32 _requestID, uint256 _randomness)
        internal
        override
    {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "You aren't there yet!"
        );
        require(_randomness > 0, "random-not-found");
        uint256 indexOfWinner = _randomness % players.length; // % can return a players index regardless of the size of random number generated
        recentWinner = players[indexOfWinner]; // identify winning player in players[]
        recentWinner.transfer(address(this).balance); // transfer contract balance to Winner
        // Reset
        players = new address payable[](0); // resets the list for new lottery
        lottery_state = LOTTERY_STATE.CLOSED; // resets the state to CLOSED
        randomness = _randomness; // ?
    }
}
