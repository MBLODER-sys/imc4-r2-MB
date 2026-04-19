# imc4-r2-MB

########## PRIMARY SECTION 1: Writing an Algorithm in Python  ##########


The explanation below assumes familiarity with the basics of Object-Oriented Programming in Python. To refresh this knowledge you can have a look at the source provided on the ‣.

# The Challenge

For the algorithmic trading challenge, you will be writing and uploading a trading algorithm class in Python, which will then be set loose on Prosperity’s exchange. On this exchange, the algorithm will trade against a number of bots, with the aim of earning as many XIRECs (the currency in Prosperity 4) as possible. The algorithmic trading challenge consists of several rounds, that take place on different days of the challenge. At the beginning of each round, it is disclosed which products will be available for trading on that day. Sample data for these products is provided that players can use to get a better understanding of the price dynamics of these products, and consequently build a better algorithm for trading them. 

The format for the trading algorithm will be a predefined `Trader` class, which has a `run()` method that contains all the trading logic coded up by the trader. For Algorithmic Trading Round 2, the `Trader` class should also define a `bid()` method. It is fine to have a `bid()` method in every submission for every round, it will be ignored for all rounds except Round 2.

Once your algorithm is uploaded it will be run in the simulation environment. The simulation consists of a large number of iterations (1_000 during testing when you develop your algorithm on historical data; 10_000 for the final simulation that determines your PnL for the round). During each iteration the run method will be called and provided with a `TradingState` object. This object contains an overview of all the trades that have happened since the last iteration, both the algorithms own trades as well as trades that happened between other market participants. Even more importantly, the `TradingState` will contain a per product overview of all the outstanding buy and sell orders (also called “quotes”) originating from the bots. Based on the logic in the `run` method the algorithm can then decide to either send orders that will fully or partially match with the existing orders, e.g. sending a buy (sell) order with a price equal to or higher (lower) than one of the outstanding bot quotes, which will result in a trade. If the algorithm sends a buy (sell) order with an associated quantity that is larger than the bot sell (buy) quote that it is matched to, the remaining quantity will be left as an outstanding buy (sell) quote with which the trading bots will then potentially trade. When the next iteration begins, the `TradingState` will then reveal whether any of the bots decided to “trade on” the player’s outstanding quote. If none of the bots trade on an outstanding player quote, the quote is automatically cancelled at the end of the iteration.

Every trade done by the algorithm in a certain product changes the “position” of the algorithm in that product. A position just specifies how much of a product you hold, e.g. “*position=3 in NVIDIA*” could mean holding 3 stocks in NVIDIA.

<aside>
📃

**Example**: if the initial ‘position’ in product X was 2, and the algorithm buys an additional quantity of 3, the position in product X is then 5. If the algorithm then subsequently sells a quantity of 7, the position in product X will be -2, also called being “short 2”.

</aside>

Like in the real world, the algorithms are restricted by per product position limits, which define the absolute position (long or short) that the algorithm is not allowed to exceed. If the aggregated quantity of all the buy (sell) orders an algorithm sends during a certain iteration would, if all fully matched, result in the algorithm obtaining a long (short) position exceeding the position limit, all the orders are cancelled by the exchange.

In the first section, the general outline of the `Trader` class that the player will be creating is outlined.

# Overview of the `Trader` class

Below an abstract representation of what the trader class should look like is shown. The class requires a single method called `run`, which is called by the simulation every time a new `TraderState` is available. The logic within this `run` method is written by the player and determines the behaviour of the algorithm. The output of the method is a dictionary, where the key is a product name and the value is a list that contains all the orders that the algorithm decides to send based on this logic. (Again, for Algo Round 2, the `Trader` class should also define a `bid()` method. It is fine to have a `bid()` method in every submission for every round, it will be ignored for all rounds except Round 2.)

```python
from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string

class Trader:

    def bid(self):
        return 15
    
    def run(self, state: TradingState):
        """Only method required. It takes all buy and sell orders for all
        symbols as an input, and outputs a list of orders to be sent."""

        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        # Orders to be placed on exchange matching engine
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            acceptable_price = 10  # Participant should calculate this value
            print("Acceptable price : " + str(acceptable_price))
            print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
    
            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                if int(best_ask) < acceptable_price:
                    print("BUY", str(-best_ask_amount) + "x", best_ask)
                    orders.append(Order(product, best_ask, -best_ask_amount))
    
            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                if int(best_bid) > acceptable_price:
                    print("SELL", str(best_bid_amount) + "x", best_bid)
                    orders.append(Order(product, best_bid, -best_bid_amount))
            
            result[product] = orders
    
        # String value holding Trader state data required. 
        # It will be delivered as TradingState.traderData on next execution.
        traderData = "SAMPLE" 
        
        # Sample conversion request. Check more details below. 
        conversions = 1
        return result, conversions, traderData
```

Example implementation above presents placing order idea as well.

When you send the Trader implementation there is always submission identifier generated. It’s a *UUID* value of the form `59f81e67-f6c6-4254-b61e-39661eac6141`, and then generates a *runID*, e.g. `"498"`, `"499"`, or `“500”`. Should any questions arise on the results, feel free to reach out to Prosperity staff, e.g. on Discord channels. An identifier is extremely helpful in answering questions (as it allows us to trace your submission), so please do always include it!

Technical implementation for the trading container is based on Amazon Web Services Lambda function. Based on the fact that Lambda is stateless, *AWS can not guarantee any class or global variables will stay in place on subsequent calls*. We provide possibility of defining a traderData string value as an opportunity to keep the state details. Any Python variable could be serialised into string with jsonpickle library and deserialised on the next call based on TradingState.traderData property. Container will not interfere with the content. Please be aware of the content size in this field. External framework will cut the string created to 50 000 characters in order to avoid timing out the call to container. It might become unusable when you try to restore values.

To get a better feel for what this `TradingState` object is exactly and how players can use it, a description of the class is provided below.

# Overview of the `TradingState` class

The `TradingState` class holds all the important market information that an algorithm needs to make decisions about which orders to send. Below the definition is provided for the `TradingState` class:

```python
Time = int
Symbol = str
Product = str
Position = int

class TradingState(object):
   def __init__(self,
                 traderData: str,
                 timestamp: Time,
                 listings: Dict[Symbol, Listing],
                 order_depths: Dict[Symbol, OrderDepth],
                 own_trades: Dict[Symbol, List[Trade]],
                 market_trades: Dict[Symbol, List[Trade]],
                 position: Dict[Product, Position],
                 observations: Observation):
        self.traderData = traderData
        self.timestamp = timestamp
        self.listings = listings
        self.order_depths = order_depths
        self.own_trades = own_trades
        self.market_trades = market_trades
        self.position = position
        self.observations = observations
        
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)
```

The most important properties

- **own_trades**: the trades the algorithm itself has done since the last `TradingState` came in. This property is a dictionary of `Trade` objects with key being a product name. The definition of the `Trade` class is provided in the subsections below.
- **market_trades**: the trades that other market participants have done since the last `TradingState` came in. This property is also a dictionary of `Trade` objects with key being a product name.
- **position**: the long or short position that the player holds in every tradable product. This property is a dictionary with the product as the key for which the value is a signed integer denoting the position, e.g. `{product1: 2, product2: -1}`.
- **order_depths**: all the buy and sell orders per product that other market participants have sent and that the algorithm is able to trade with. This property is a dict where the keys are the products and the corresponding values are instances of the `OrderDepth` class. This `OrderDepth` class then contains all the buy and sell orders. An overview of the `OrderDepth` class is also provided in the subsections below.

## `Trade` class

Both the `own_trades` property and the `market_trades` property provide the traders with a list of trades per products. Every individual trade in each of these lists is an instance of the `Trade` class.

```python
Symbol = str
UserId = str

class Trade:
    def __init__(self, symbol: Symbol, price: int, quantity: int, buyer: UserId = None, seller: UserId = None, timestamp: int = 0) -> None:
        self.symbol = symbol
        self.price: int = price
        self.quantity: int = quantity
        self.buyer = buyer
        self.seller = seller
        self.timestamp = timestamp

    def __str__(self) -> str:
        return "(" + self.symbol + ", " + self.buyer + " << " + self.seller + ", " + str(self.price) + ", " + str(self.quantity) + ", " + str(self.timestamp) + ")"

    def __repr__(self) -> str:
        return "(" + self.symbol + ", " + self.buyer + " << " + self.seller + ", " + str(self.price) + ", " + str(self.quantity) + ", " + str(self.timestamp) + ")" + self.symbol + ", " + self.buyer + " << " + self.seller + ", " + str(self.price) + ", " + str(self.quantity) + ")"
```

These trades have 5 distinct properties (besides the `timestamp` property). On Prosperity’s exchange, like on most real-world exchanges, counterparty information is often not disclosed. Therefore, `self.buyer` and `self.seller` will only be non-empty strings if the algorithm itself is the buyer (`self.buyer = “SUBMISSION”`) or the seller (`self.seller=“SUBMISSION”`).

## `OrderDepth` class

Provided by the `TradingState` class is also the `OrderDepth` per symbol. This object contains the collection of all outstanding buy and sell orders, or “quotes” that were sent by the trading bots, for a certain symbol. 

```python
class OrderDepth:
    def __init__(self):
        self.buy_orders: Dict[int, int] = {}
        self.sell_orders: Dict[int, int] = {}
```

All the orders on a single side (buy or sell) are aggregated in a dict, where the keys indicate the price associated with the order, and the corresponding values indicate the total volume on that price level. 

<aside>
📃

**Example**: if the buy_orders property would look like this for a certain product: `self.buy_orders = {9: 5, 10: 4}`, then there is a total buy order quantity of 5 at the price level of 9, and a total buy order quantity of 4 at a price level of 10. Players should note that in the sell_orders property, the quantities specified will be negative. E.g., `{12: -3, 11: -2}` would mean that the aggregated sell order volume at price level 12 is 3, and 2 at price level 11.

</aside>

Every price level at which there are buy orders should always be strictly lower than all the levels at which there are sell orders. If not, then there is a potential match between buy and sell orders, and a trade between the bots should have happened.

## `Observation` class

<aside>
⚠️

Observation details help to decide on eventual orders or ‘conversion requests’, although we expect you won’t really need to work much with this class (feel free to skip).

</aside>

There are two items delivered inside the TradingState instance:

1. Simple product to value dictionary inside plainValueObservations
2. Dictionary of complex **ConversionObservation** values for respective products. Used to place conversion requests from Trader class. Structure visible below.

```python
class ConversionObservation:

    def __init__(self, bidPrice: float, askPrice: float, transportFees: float, exportTariff: float, importTariff: float, sunlight: float, humidity: float):
        self.bidPrice = bidPrice
        self.askPrice = askPrice
        self.transportFees = transportFees
        self.exportTariff = exportTariff
        self.importTariff = importTariff
        self.sugarPrice = sugarPrice
        self.sunlightIndex = sunlightIndex
```

In case you decide to place a conversion request on a product, then the listed integer number should be returned as a “conversions” value from the `run()` method. Based on logic defined inside Prosperity container it will convert positions acquired by submitted code. There is a number of conditions for conversion to happen:

- You need to obtain either long or short position earlier.
- Conversion request cannot exceed possessed items count.
- In case you have 10 items short (-10) you can only request from 1 to 10. Request for 11 or more will be fully ignored.
- While conversion happens you will need to cover transportation and import/export tariff.
- Conversion request is not mandatory. You can send 0 or None as value.

# How to send orders using the `Order` class

After performing logic on the incoming order state, the `run` method defined by the player should output a dictionary containing the orders that the algorithm wants to send. The keys of this dictionary should be all the products that the algorithm wishes to send orders for. These orders should be instances of the `Order` class. Each order has three important properties. These are:

1. The symbol of the product for which the order is sent.
2. The price of the order: the maximum price at which the algorithm wants to buy in case of a BUY order, or the minimum price at which the algorithm wants to sell in case of a SELL order.
3. The quantity of the order: the maximum quantity that the algorithm wishes to buy or sell. If the sign of the quantity is positive, the order is a buy order, if the sign of the quantity is negative it is a sell order.

```python
Symbol = str

class Order:
    def __init__(self, symbol: Symbol, price: int, quantity: int) -> None:
        self.symbol = symbol
        self.price = price
        self.quantity = quantity

    def __str__(self) -> str:
        return "(" + self.symbol + ", " + str(self.price) + ", " + str(self.quantity) + ")"

    def __repr__(self) -> str:
        return "(" + self.symbol + ", " + str(self.price) + ", " + str(self.quantity) + ")"
```

If there are active orders from counterparties for the same product against which the algorithms’ orders can be matched, the algorithms’ order will be (partially) executed right away. If no immediate or partial execution is possible, the remaining order quantity will be visible for the bots in the market, and it might be that one of them sees it as a good trading opportunity and will trade against it. If none of the bots decides to trade against the remaining order quantity, it is cancelled. Note that after cancellation of the algorithm’s orders, but before the next `Tradingstate` comes in, bots might also trade with each other.

Note that on Prosperity’s exchange, execution of orders is instantaneous, which means that all their orders arrive in the exchange matching engine without any delay. Therefore, all the orders that a player sends that could be immediately matched with an order from one of the bots, and result in a trade if matched. In other words, none of the bots can send an order that is faster than the player’s order and get the opportunity instead.

See ‣ for a more elaborate explanation of order execution in financial markets.

## Position Limits

Just like in the real world of trading, there are position limits, i.e. limits to the size of the position that the algorithm can trade into in a single product. These position limits are defined on a per-product basis, and refer to the absolute allowable position size. So for a hypothetical position limit of 10, the position can neither be greater than 10 (long) nor less than -10 (short). On the Prosperity exchange, this position limit is enforced by the exchange. If at any iteration, the player’s algorithm tries to send buy (sell) orders for a product with an aggregated quantity that would cause the player to go over long (short) position limits if all orders would be fully executed, all orders will be rejected automatically. 

<aside>
📃

**Example**: say the position limit in product X is 30 and the current position is -5, then any aggregated buy order volume exceeding 30 - (-5) = 35 would result in an order rejection. However, an order with volume/quantity 35 itself is perfectly legal!

</aside>

For an overview of the per-product position limits, please refer to the ‘Rounds’ section on Wiki. The position limits are listed per round.

# Example of Trading

Two example iterations are provided below to give an idea what the simulation behaviour looks like.

For the following example we assume a situation with two products:

- PRODUCT1 with position limit 10
- PRODUCT2 with position limit 20

At the start of the first iteration the run method is called with the `TradingState` generated by the below code. Note: the [datamodel.py](http://datamodel.py) file from which the classes are imported is provided in Appendix B. The code can also be used to test algorithms locally.

```python
from datamodel import Listing, OrderDepth, Trade, TradingState

timestamp = 1000

listings = {
	"PRODUCT1": Listing(
		symbol="PRODUCT1", 
		product="PRODUCT1", 
		denomination= "XIRECS"
	),
	"PRODUCT2": Listing(
		symbol="PRODUCT2", 
		product="PRODUCT2", 
		denomination= "XIRECS"
	),
}

order_depths = {
	"PRODUCT1": OrderDepth(
		buy_orders={10: 7, 9: 5},
		sell_orders={11: -4, 12: -8}
	),
	"PRODUCT2": OrderDepth(
		buy_orders={142: 3, 141: 5},
		sell_orders={144: -5, 145: -8}
	),	
}

own_trades = {
	"PRODUCT1": [],
	"PRODUCT2": []
}

market_trades = {
	"PRODUCT1": [
		Trade(
			symbol="PRODUCT1",
			price=11,
			quantity=4,
			buyer="",
			seller="",
			timestamp=900
		)
	],
	"PRODUCT2": []
}

position = {
	"PRODUCT1": 3,
	"PRODUCT2": -5
}

observations = {}
traderData = ""

state = TradingState(
	traderData,
	timestamp,
  listings,
	order_depths,
	own_trades,
	market_trades,
	position,
	observations
)
```

Let’s say that at this point in the simulation, the algorithm has the following convictions:

1. PRODUCT1 is worth 13
2. PRODUCT2 is worth 142

It could then potentially decide on the following

1. Since the sell orders in PRODUCT1 at price 11 (qty 4) and price 12 (qty 8) are both below the algorithms calculated fair value, it would like to send a buy order to trade with these sell orders. Given that the position in PRODUCT1 is already 3 long and the position limit is set at 10, sending one or more buy orders with an aggregated quantity of >7 would result in rejection of all buy orders, the algorithm sends a buy order with quantity 7 and a price of 12.
2. Versus the fair value of 142 neither the sell orders nor the buy orders look profitable. The algorithm therefore decides to see if any of the bots is willing to buy at 143, and sends a sell order of quantity 5 at that price level.

Based on the above the `run` method output would then be generated as shown below:

```python
result["PRODUCT1"] = [Order("PRODUCT1", 12, 7)]
result["PRODUCT2"] = [Order("PRODUCT2", 143, -5)]
```

An example of what the next `TradingState` will look like is generated by the code below.

```python
from datamodel import Listing, OrderDepth, Trade, TradingState

timestamp = 1100

listings = {
	"PRODUCT1": Listing(
		symbol="PRODUCT1", 
		product="PRODUCT1", 
		denomination: "XIRECS"
	),
	"PRODUCT2": Listing(
		symbol="PRODUCT2", 
		product="PRODUCT2", 
		denomination: "XIRECS"
	),
}

order_depths = {
	"PRODUCT1": OrderDepth(
		buy_orders={10: 7, 9: 5},
		sell_orders={12: -5, 13: -3}
	),
	"PRODUCT2": OrderDepth(
		buy_orders={142: 3, 141: 5},
		sell_orders={144: -5, 145: -8}
	),	
}

own_trades = {
	"PRODUCT1": [
		Trade(
			symbol="PRODUCT1",
			price=11,
			quantity=4,
			buyer="SUBMISSION",
			seller="",
			timestamp=1000
		),
		Trade(
			symbol="PRODUCT1",
			price=12,
			quantity=3,
			buyer="SUBMISSION",
			seller="",
			timestamp=1000
		)
	],
	"PRODUCT2": [
		Trade(
			symbol="PRODUCT2",
			price=143,
			quantity=2,
			buyer="",
			seller="SUBMISSION",
			timestamp=1000
		),
	]
}

market_trades = {
	"PRODUCT1": [],
	"PRODUCT2": []
}

position = {
	"PRODUCT1": 10,
	"PRODUCT2": -7
}

observations = {}
traderData = ""

state = TradingState(
	traderData,
	timestamp,
  listings,
	order_depths,
	own_trades,
	market_trades,
	position,
	observations
)
```

A few observations can be made from this `TradingState`'s properties:

1. The algorithm’s buy orders for `“PRODUCT1"` matched first with the full quantity of the sell order at price 11. As a result the order is now gone from the order_depths and a corresponding own_trade is created.
2. The remaining order quantity of 3 then matched with part of the order at price 12, resulting in a second trade at price 12. As can be seen in the order_depths the quantity of the corresponding sell order is now reduced by 3 as well.
3. For “PRODUCT2” a trade at price 143 with a quantity 2 can be observed, which indicates that one of the bots decided to send a buy order of quantity 2 as a reaction to the player’s sell order at that price level. For the player’s initial order this means that a quantity of 3 of the 5 total remains unexecuted. None of the bots decides to trade against this order, and the full order quantity is automatically cancelled.

# Technical Notes

There are a few technicalities that players should take into account when writing an algorithms:

1. Only the libraries noted at the bottom of this page under “Supported Libraries” are allowed to be used by the algorithm. These are listed in Appendix C.
2. Each time the “run” method is called, it should generate a response in 900ms, which should be reasonable as the average is ≤ 100ms; otherwise, the function call will time out. Players should make sure that their algorithms are sufficiently lightweight to make sure this requirement is met. 

# Available Resources to Help Build the Algorithm

To aid players in building the algorithm several resources are made available:

1. For every new product introduced several days of sample data are provided. For each of these days two .csv’s are available, one containing a list of all the trades done on that day, and one showing the market orders at every time step. Examples of the file formats:
    1. .csv file with trade example
    2. .csv file with market orders example
2. When players upload their algorithms on the Prosperity platform, the algorithm is tested for 1000 iterations using data from a sample day (different than the actual day that will be used for the challenge). After the run a log file is provided which can aid players in debugging their algorithms. To aid debugging, the log file also contains the output of any print statements that players put within the `run` method of their trading class.

# Appendix A: `Trader` Class Example

Below an example of an implementation of the `Trader` class is provided. While very simple and likely not profitable, this example algorithm does include all the necessary logic to send orders. 

 ⬇️ Download

[example.py](example.py)

```python
from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string

class Trader:

    def bid(self):
        return 15
    
    def run(self, state: TradingState):
        """Only method required. It takes all buy and sell orders for all
        symbols as an input, and outputs a list of orders to be sent."""

        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        # Orders to be placed on exchange matching engine
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            acceptable_price = 10  # Participant should calculate this value
            print("Acceptable price : " + str(acceptable_price))
            print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
    
            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                if int(best_ask) < acceptable_price:
                    print("BUY", str(-best_ask_amount) + "x", best_ask)
                    orders.append(Order(product, best_ask, -best_ask_amount))
    
            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                if int(best_bid) > acceptable_price:
                    print("SELL", str(best_bid_amount) + "x", best_bid)
                    orders.append(Order(product, best_bid, -best_bid_amount))
            
            result[product] = orders
    
        traderData = ""  # No state needed - we check position directly
        conversions = 0
        return result, conversions, traderData
```

# Appendix B: [datamodel.py](http://datamodel.py) file

Observation details help to decide on eventual orders or ‘conversion requests’, although we expect you won’t really need to work much with this class (feel free to skip).

```python
import json
from typing import Dict, List
from json import JSONEncoder
import jsonpickle

Time = int
Symbol = str
Product = str
Position = int
UserId = str
ObservationValue = int

class Listing:

    def __init__(self, symbol: Symbol, product: Product, denomination: Product):
        self.symbol = symbol
        self.product = product
        self.denomination = denomination
        
                 
class ConversionObservation:

    def __init__(self, bidPrice: float, askPrice: float, transportFees: float, exportTariff: float, importTariff: float, sunlight: float, humidity: float):
        self.bidPrice = bidPrice
        self.askPrice = askPrice
        self.transportFees = transportFees
        self.exportTariff = exportTariff
        self.importTariff = importTariff
        self.sugarPrice = sugarPrice
        self.sunlightIndex = sunlightIndex
        

class Observation:

    def __init__(self, plainValueObservations: Dict[Product, ObservationValue], conversionObservations: Dict[Product, ConversionObservation]) -> None:
        self.plainValueObservations = plainValueObservations
        self.conversionObservations = conversionObservations
        
    def __str__(self) -> str:
        return "(plainValueObservations: " + jsonpickle.encode(self.plainValueObservations) + ", conversionObservations: " + jsonpickle.encode(self.conversionObservations) + ")"
     

class Order:

    def __init__(self, symbol: Symbol, price: int, quantity: int) -> None:
        self.symbol = symbol
        self.price = price
        self.quantity = quantity

    def __str__(self) -> str:
        return "(" + self.symbol + ", " + str(self.price) + ", " + str(self.quantity) + ")"

    def __repr__(self) -> str:
        return "(" + self.symbol + ", " + str(self.price) + ", " + str(self.quantity) + ")"
    

class OrderDepth:

    def __init__(self):
        self.buy_orders: Dict[int, int] = {}
        self.sell_orders: Dict[int, int] = {}

class Trade:

    def __init__(self, symbol: Symbol, price: int, quantity: int, buyer: UserId=None, seller: UserId=None, timestamp: int=0) -> None:
        self.symbol = symbol
        self.price: int = price
        self.quantity: int = quantity
        self.buyer = buyer
        self.seller = seller
        self.timestamp = timestamp

    def __str__(self) -> str:
        return "(" + self.symbol + ", " + self.buyer + " << " + self.seller + ", " + str(self.price) + ", " + str(self.quantity) + ", " + str(self.timestamp) + ")"

    def __repr__(self) -> str:
        return "(" + self.symbol + ", " + self.buyer + " << " + self.seller + ", " + str(self.price) + ", " + str(self.quantity) + ", " + str(self.timestamp) + ")"

class TradingState(object):

    def __init__(self,
                 traderData: str,
                 timestamp: Time,
                 listings: Dict[Symbol, Listing],
                 order_depths: Dict[Symbol, OrderDepth],
                 own_trades: Dict[Symbol, List[Trade]],
                 market_trades: Dict[Symbol, List[Trade]],
                 position: Dict[Product, Position],
                 observations: Observation):
        self.traderData = traderData
        self.timestamp = timestamp
        self.listings = listings
        self.order_depths = order_depths
        self.own_trades = own_trades
        self.market_trades = market_trades
        self.position = position
        self.observations = observations
        
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    
class ProsperityEncoder(JSONEncoder):

        def default(self, o):
            return o.__dict__
```

# Appendix C: Supported libraries

All the standard python libraries included in Python 3.12 are fully supported, including the libraries below that might be of interest to you to run during the simulation. Importing other, external libraries is not supported.

[pandas](https://pandas.pydata.org/)

[NumPy](https://numpy.org/)

[statistics](https://docs.python.org/3.9/library/statistics.html)

[math](https://docs.python.org/3.9/library/math.html)

[typing](https://docs.python.org/3.9/library/typing.html)

[Round 1 - “Trading groundwork” d4e4b7f3146d83869f7c0117d7f7ca4f.md](https://github.com/user-attachments/files/26864263/Round.1.-.Trading.groundwork.d4e4b7f3146d83869f7c0117d7f7ca4f.md)


##########  PRIMARY SECTION 2: Round 1 - “Trading groundwork”  ##########


You have reached Intara.

You establish a Trade Outpost on the dry and arid landscape, overlooking endless dusty plateaus, jagged rock formations, and ancient impact craters. This outpost will serve as your trading hub for the duration of your mission on Intara.

Your goal is clear: **earn a net profit of 200,000 XIRECs or more** before the beginning of the third trading day. Only then will the Intarians be able to build upon your foundation, and only then will your outpost be acknowledged by the *eXtended Interplanetary Resource Exchange Network* (XIREN) as an official trading node.

The first goods available for trade are ***Ash-Coated Osmium*** (`ASH_COATED_OSMIUM`) and ***Intarian Pepper Root*** (`INTARIAN_PEPPER_ROOT`). Devising a strategy to turn these products into profit should be your primary focus.

However, the Intarian people are also organizing a celebratory **Exchange Auction** to welcome you to their planet. This auction provides an opportunity to generate additional profit alongside your algorithmic earnings and to kickstart your mission in strong form.

Trading days on Intara last 72 hours, giving you ample time to develop a solid strategy for both algorithmic and manual trading challenges.

## **Round Objective**

Translate your first trading strategy into a Python program that trades `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT` on your behalf. In addition to deploying your first official trading algorithm, participate in the Exchange Auction to generate additional profit.

## Algorithmic trading challenge: “First Intarian Goods”

Similar to the `EMERALDS` products in the Tutorial round, the value of `INTARIAN_PEPPER_ROOT` is quite steady, but keep in mind that it’s a hardy, slow-growing root. On the other hand, `ASH_COATED_OSMIUM` is rumored to be a bit more volatile, although one may speculate that its apparent unpredictability may follow a hidden pattern. The product limits ([see the Position Limits page for extra context and troubleshooting](https://imc-prosperity.notion.site/writing-an-algorithm-in-python#328e8453a09380cfb53edaa112e960a9)) are:

- `ASH_COATED_OSMIUM`: 80
- `INTARIAN_PEPPER_ROOT`: 80

## Manual trading challenge: “An Intarian Welcome”

The Intarian people are kicking off your visit to Intara with two opening auctions for ***Dryland Flax*** (`DRYLAND_FLAX`) and ***Ember Mushrooms*** (`EMBER_MUSHROOM`).

You will submit your orders last. No other bids/asks will arrive and no volumes will change after you place your order.

### **Auction rules**

You have to submit a single limit order (price, quantity). When the auction ends, the exchange selects a single clearing price that:

1. maximizes total traded volume, then
2. breaks ties by choosing the higher price.

All bids with price ≥ clearing price and asks with price ≤ clearing price execute at the clearing price. Allocation is price priority, then time priority. Since you are last to submit, you are last in line at any price level you join.

### Guaranteed buyback after the auction

You will not trade these products in continuous trading. Instead, right after the auction the Merchant Guild will buy any inventory you trade at a fixed price:

- `DRYLAND_FLAX`: 30 per unit (no fees)
- `EMBER_MUSHROOM`: 20 per unit (fee: 0.10 per unit traded)

### Submit your orders

Choose a bid price and quantity for each product to maximize your profit. Enter your orders directly in the Manual Challenge Overview window and click the “Submit” button. You can re-submit new orders until the end of the trading round. When the round ends, the last submitted orders will be executed.

[jsonpickle](https://jsonpickle.github.io/)

[Round 2 - “Growing Your Outpost” .md](https://github.com/user-attachments/files/26864283/Round.2.-.Growing.Your.Outpost.md)


##########  PRIMARY SECTION 3: Round 2 - “Growing Your Outpost”  ##########


It is the second trading round, and your final opportunity to reach the threshold goal of a net PnL of 200,000 XIRECs or more before the leaderboard resets for Phase 2. These first 2 rounds act as qualifiers for the final mission. Trading activity has accelerated significantly since your arrival. With you and the other outposts actively trading ***Ash-Coated Osmium*** and ***Intarian Pepper Root***, the market has become increasingly competitive and dynamic.

In this second and final trading round on Intara, you will continue trading `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`. This time, however, you have the opportunity to gain access to additional market volume. To compete for this increased capacity, you must incorporate a ***Market Access Fee*** bid into your Python program.

Of course, you should also analyze your previous round’s performance and refine your algorithm accordingly.

Additionally, XIREN has provided a ***50*,*000 XIRECs investment budget*** for you to allocate across three growth pillars in order to accelerate the development of your outpost. You must decide how to distribute this budget strategically to maximize your profit once the trading round closes.

# **Round Objective**

Optimize your Python program to trade `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`, and incorporate a ***Market Access Fee*** to potentially gain access to additional market volume.

In addition to refining your trading algorithm, ***allocate your 50,000 XIRECs investment budget*** across the three growth pillars to strengthen your outpost’s performance.

# **Algorithmic trading challenge: “limited Market Access”**

[Wiki_ROUND_2_data.zip](Wiki_ROUND_2_data.zip)

The products `INTARIAN_PEPPER_ROOT` and `ASH_COATED_OSMIUM` are the same, but the challenge now primarily lies in deciding how much to bid for extra market access, as well as refining your algorithm. The position limits ([see the Position Limits page for extra context and troubleshooting](https://imc-prosperity.notion.site/writing-an-algorithm-in-python#328e8453a09380cfb53edaa112e960a9)) are again

- `ASH_COATED_OSMIUM`: 80
- `INTARIAN_PEPPER_ROOT`: 80

In this round, you can bid for 25% more quotes in the order book. The volumes and prices of these quotes fit perfectly in the distribution of the already available quotes. A simple example:

<aside>
📖

**Example Extra Market Access**

Order book for participants with no extra market access:
(ask, 10 volume, $9)
(ask, 10 volume, $7)
(bid, 10 volume, $5)
(bid, 5 volume, $4)

Order book for participants with *extra* market access:
(ask, 10 volume, $9)
(ask, 5 volume, $8)          <--- extra flow to trade against
(ask, 10 volume, $7)
(bid, 10 volume, $5)
(bid, 5 volume, $4)

</aside>

You bid for extra market access by incorporating a `bid()` function inside your `class Trader` implementation:

```python
class Trader:
    def bid(self):
        return 15

    def run(self, state: TradingState):
        (Implementation)
```

The Market Access Fee (MAF) is a *one-time fee* at the start of Round 2 paid *only* if your bid is accepted. It only determines who gets extra market access, and is not used in the simulation dynamics whatsoever. The top 50% of bids across all participants are accepted.

<aside>
🔨

**Example Bidding Mechanism**

Bids:           [10,   20,  15,   19,   21,   34]
Accepted:  [No, Yes, No, No, Yes, Yes]
Explanation: the median of the bids is 19.5, so all bids higher (20, 21, 34) are accepted → these participants get extra market access flow while paying the price they bid, and all bids below 19.5 are rejected (and these participants do *not* pay the fee).

</aside>

The accepted bids are subtracted from Round 2 profits to compute the final PnL. To be explicit,

<aside>
ℹ️

For those with full market access (i.e. those in the top 50% of bids),
`profit = profit from round 2 - bid for getting full market access`.

For those with no full market access,
`profit = profit from round 2`.

</aside>

The MAF is unique to Round 2, and does not apply to any other round; any `bid()` function in Rounds 1,3,4,5 is ignored. It is also ignored during testing of round 2, since bids are only compared on our end when the final simulation of Round 2 starts. In that sense, it’s a “blind auction” for extra flow.

During testing of round 2, the default set of quotes you interact with is 80% of all quotes we generated (i.e., no extra market access). This 80% has been slightly randomized for every submission to reflect real-world conditions where not all patterns in trading behavior are up 100% of the time. While you could optimize the PnL by submitting the same file many times, this has very limited payoff and your effort is much better put into improving your algorithm ;).

### **Game theory**

To get extra market access, you just need to be in the top 50% of bidders, not necessarily the highest bidder. Placing an extremely high bid will almost certainly yield full market access, but perhaps you could save (a lot of) XIRECs by bidding less while staying in the top 50% of bidders.

# **Manual trading challenge: “Invest & Expand”**

You are expanding your outpost into a true market making firm with a budget of `50 000` XIRECs. You need to allocate this budget across three pillars:

- **Research**
- **Scale**
- **Speed**

You choose percentages for each pillar between 0–100%. Total allocation cannot exceed 100%. Your final PnL (Profit and Loss) score is:

<aside>
ℹ️

PnL = (Research × Scale × Speed) − Budget_Used

</aside>

### **The pillars**

**Research** determines how strong your trading edge is. It grows **logarithmically** from `0` (for `0` invested) to `200 000`  (for `100` invested). The exact formula is `research(x) = 200_000 * np.log(1 + x) / np.log(1 + 100)`. Here, `np.log` is a python function from NumPy package for natural logarithm.

**Scale** determines how broadly you deploy your strategy across markets. It grows **linearly** from `0` (for `0` invested) to `7` (for `100` invested).

**Speed** determines how often you win the trades you target. It is **rank-based** across all players:

- Highest speed investment receives a `0.9` multiplier.
- Lowest receives `0.1`.
- Everyone in between is scaled linearly by rank, equal investments share the same rank.
- For example, if people invested `70, 70, 70, 50, 40, 40, 30`, they get the following ranks: `1, 1, 1, 4, 5, 5, 7`. First three players get `0.9` for hit rate multiplier, last player gets `0.1`, and everybody in between gets linearly scaled between top and bottom rank. Another example, if you have three players investing `95, 20, 10`, their ranks are `1, 2, 3`, and their hit rates are `0.9, 0.5, 0.1`.

Your Research, Scale, and Speed outcomes are multiplied together to form your gross PnL, after which the used part of your budget is deducted.

Every decision you make reflects a real trade-off faced by modern market makers: capital is finite, competition is relentless, and edge alone is never enough. Good luck!

### **Submit your orders**

Choose the distribution of your budget by assigning percentages to the three pillars directly in the Manual Challenge Overview window and click the “Submit” button. You can re-submit new distributions until the end of the trading round. When the round ends, the last submitted distribution will be locked in and processed.

##########  PRIMARY SECTION 4: Trading Glossary  ##########

# Trading glossary

The aim of this page is to introduce players to real world trading concepts and jargon which they will also encounter in the world of prosperity.

### Exchange

A central marketplace where buyers and sellers meet to arrange trades in certain products. These products can be a wide range of things. Commodities, Stocks, Bonds, ETFs, Derivatives, Currencies, Cryptocurrencies. Modern exchanges are often heavily relying on digital infrastructure, and to a large extent match buyers and sellers using automated matching of BUY and SELL orders.

### Order

An order is a binding message sent by a market participant to indicate a willingness to buy or sell a certain amount (e.g. 1 stock) of a specified product (e.g., NVIDIA) on an exchange (e.g., NASDAQ). There are essentially 3 types of orders:

<aside>

**Market order**
An order to buy or sell immediately at the best available prices in the market.

</aside>

<aside>

**Limit order**
An order to buy or sell at a specified price or better (buy at that price or lower, sell at that price or higher).

</aside>

<aside>

**Stop order**
An order that becomes active only when the market price reaches a specified trigger level, after which it is typically sent as a market order.

</aside>

Some general properties of an order:

- **Participant / Account (Owner)**: who sent the order.
    - This information is visible to the exchange, but typically *not* to other market participants.
- **Product**: the product the participant wants to trade.
- **Quantity**: how much of the product the participant wants to trade.
- **Side**: whether the order is a BUY or a SELL order.
    - The `Side` field could be skipped if quantity is allowed to be negative, e.g. `quantity=1` for a BUY order, and `quantity=-1` for a SELL order.
- **Price**: the price associated with the order.
    - This is required for limit orders. Market orders do not specify a price.
- **Validity**: how long the order remains active in the market.

Depending on the context, orders may have additional properties, but the ones above are the most fundamental. If a BUY order and a SELL order are compatible — meaning that a trade can be arranged where both the conditions of the SELL as well as the BUY order are met (e.g., price) — they are **matched**, and a trade is **executed**. (More about order matching below.)

In Prosperity, we focus on limit orders sent to Prosperity’s own exchange. 

### Bid Order

A bid order, is financial jargon for a BUY order. The price of such a bid order is typically referred to as the “bid” or the “bid price”. If traders refer to the “best bid”, they typically refer to the price corresponding to the highest active buy order for a certain product, which is the highest price another market participant can decide to sell the product at.

### Ask Order / Offer

Similar to “Bid Orders”, but referring to SELL orders.

### Order Matching

How order execution works on Prosperity’s exchange (and on most real-world exchanges):

A BUY order will be immediately executed if there is an active SELL order in the market with an associated price equal to or lower than the price associated with the BUY order (the lower the sell price the better it is for the buyer). In that case the buyer will buy an amount equal to the minimum of the two order quantities, at the price of the SELL order. If the SELL order quantity was lower than the BUY order, that means only part of the BUY order gets executed, and a resting order (equal to the BUY order quantity minus the SELL order quantity) remains in the market. If there is no SELL order with a price equal or lower than the price of the BUY order, the full order remains in the market. If an order remains in the market, the bots might decide to send crossing sell orders at a later point, which would then mean that at that point the order still trades.

By symmetry, SELL orders will trade immediately against any BUY orders with a price equal or higher than the price associated with the SELL order (the higher the buy price the better it is for the seller). Beside from that SELL orders behave in the exact same way as BUY orders.

### Order Book

Orders for a certain product are collected in something called an Order Book. While there are multiple ways to visualize an Order Book, a common representation is shown below. The middle of the book shows the different price levels. The left side, or bid side, shows the combined quantity of all the BUY orders which have the same price associated with them. On the right side, or ask side, the combined quantity of all the sell orders per price level is represented. As described above, once there are buy and sell orders at the same price level, or even buy orders at a price level above the price level of the lowest sell order, orders are matched and trading takes place. We would call an order book with no bid orders at or above the level of the lowest ask order “uncrossed”. No trading is then possible. If there are buy orders above the lowest price level with ask orders, we would call the book “crossed” and trading is possible.

![Order Book.png](Order_Book.png)

### Priority

Sometimes an incoming order could be matched to several existing orders. In that case the priority rules of the exchange determine at which the order will be executed. The most common priority rule, also enforced on Prosperity’s exchange, is “price-time priority”. This means that the incoming order is first matched against the existing order with the most attractive price (from the perspective of the incoming order) at the price level of the existing order. If there are multiple orders at that price level, the oldest order is executed first. If we take the right most order book in the figure above as an example and assume that the sell order with a quantity of 2 at price level 4 was the last order to be entered in the book, we see that this order could be matched either against the buy orders at price level 4 or the buy orders at price level 5. Selling at a price of 5 is more attractive from the perspective of the incoming order so the order will match with buy orders on that level. If the aggregate quantity of 3 on the bid side at price level 5 consists of multiple orders, the ask order will first be executed against the oldest order at that level. If any quantity of the incoming order remains after that trade it is executed against the second oldest order at that price level.

### Market Making

A trading strategy where the trader does not necessarily have a strong opinion on the direction in which they expect the price to move, but conduct business through the (attempt of) simultaneous buying and selling of certain products. An example is a currency exchange shop at the airport where at any point in time they are willing to buy people’s dollars at 0.95 Euro, and sell dollars to people at 1.05. Even if the relative value of euros and dollars doesn’t change, the currency shop will make a living as long as they sell approximately as many dollars as they buy, making a 10ct profit on every buy-sell pair while they provide liquidity to travellers. These travellers are happy as well, as even though they had to make a small financial investment, they now have the right currency required to go about their business. IMC does the same thing in financial derivatives, just as you’d be wise to consider doing a bit of market making yourself in the exciting world of Prosperity!

The aim of this page is to introduce players to real world trading concepts and jargon which they will also encounter in the world of prosperity.

########### END ##########
