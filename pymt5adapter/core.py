import functools
from datetime import datetime

import MetaTrader5 as _mt5
import numpy

from . import const
from . import helpers
from .helpers import _args_to_str
from .helpers import _is_rates_array
from .state import global_state as _state
from .types import *


class MT5Error(Exception):
    pass


def _context_manager_modified(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        result = f(*args, **kwargs)
        if _state.force_namedtuple:
            if _is_rates_array(result):
                result = [Rate(*r) for r in result]
        if _state.global_debugging:  # and not result:
            call_sig = f"{f.__name__}({_args_to_str(args, kwargs)})"
            _state.log(f"[{call_sig}][{last_error()}][{str(result)[:80]}]")
        if _state.raise_on_errors:
            error_code, description = last_error()
            if error_code != const.RES_S_OK:
                raise MT5Error(error_code, description)
        return result

    return wrapper


@_context_manager_modified
def initialize(path: str = None,
               *,
               login: str = None,
               password: str = None,
               server: str = None,
               portable: bool = False,
               timeout: int = None,
               **kwargs
               ) -> bool:
    """Establish a connection with the MetaTrader 5 terminal. Call without parameters. The terminal for connection is found automatically.

    :param path:  Path to the metatrader.exe or metatrader64.exe file. Optional unnamed parameter. It is indicated first without a parameter name. If the path is not specified, the module attempts to find the executable file on its own.
    :param login: Connection timeout in milliseconds. Optional named parameter. If not specified, the value of 60 000 (60 seconds) is applied. If the connection is not established within the specified time, the call is forcibly terminated and the exception is generated.
    :param password: Trading account password. Optional named parameter. If the password is not set, the password saved in the terminal database is applied automatically.
    :param server: Trade server name. Optional named parameter. If no server is set, the last used server is applied automatically.
    :param portable: Launch terminal in portable mode
    :timeout: Number of milliseconds for timeout
    :return: Returns True in case of successful connection to the MetaTrader 5 terminal, otherwise - False.
    """
    cleaned = helpers._clean_args(locals().copy())
    result = _mt5.initialize(**cleaned)
    return result


@_context_manager_modified
def login(login: int, *,
          password: str = None,
          server: str = None,
          timeout: int = None,
          **kwargs,
          ) -> bool:
    """Connect to a trading account using specified parameters.

    :param login: Trading account number. Required unnamed parameter.
    :param password: Trading account password.
    :param server: Trade server name
    :param timeout: Connection timeout in milliseconds.
    :param kwargs:
    :return: True if success.
    """
    args = helpers._clean_args(locals().copy())
    login = args.pop('login')
    return _mt5.login(login, **args)


@_context_manager_modified
def shutdown() -> None:
    """Close the previously established connection to the MetaTrader 5 terminal.

    :return: None
    """
    return _mt5.shutdown()


@_context_manager_modified
def version() -> Tuple[int, int, str]:
    """Return the MetaTrader 5 terminal version.

    :return: Returns the MetaTrader 5 terminal version, build and release date. Return None in case of an error. The info on the error can be obtained using last_error().
    """
    return _mt5.version()


def last_error() -> Tuple[int, str]:
    """last_error() allows obtaining an error code in case of a failed execution of a MetaTrader 5 library function.
    It is similar to GetLastError(). However, it applies its own error codes.

    :return: Return the last error code and description as a tuple.
    """
    return _mt5.last_error()


@_context_manager_modified
def account_info() -> AccountInfo:
    """Get info on the current trading account. The function returns all data that can be obtained using AccountInfoInteger, AccountInfoDouble and AccountInfoString in one call.

    :return: Return info in the form of a named tuple structure (namedtuple). Return None in case of an error. The info on the error can be obtained using last_error().
    """
    return _mt5.account_info()


@_context_manager_modified
def terminal_info() -> TerminalInfo:
    """Get the connected MetaTrader 5 client terminal status and settings. The function returns all data that can be
    obtained using TerminalInfoInteger, TerminalInfoDouble and TerminalInfoDouble in one call.

    :return: Return info in the form of a named tuple structure (namedtuple). Return None in case of an error. The info on the error can be obtained using last_error().
    """
    return _mt5.terminal_info()


@_context_manager_modified
def symbols_total() -> int:
    """Get the number of all financial instruments in the MetaTrader 5 terminal. The function is similar to SymbolsTotal(). However, it returns the number of all symbols including custom ones and the ones disabled in MarketWatch.

    :return: <int>
    """
    return _mt5.symbols_total()


@_context_manager_modified
def symbols_get(group=None,
                function: Callable[[SymbolInfo], bool] = None,
                **kwargs
                ) -> Tuple[SymbolInfo]:
    """Get all financial instruments from the MetaTrader 5 terminal.
        The group parameter allows sorting out symbols by name. '*' can be used at the beginning and the end of a string.
        The group parameter can be used as a named or an unnamed one. Both options work the same way. The named option (group="GROUP") makes the code easier to read.
        The group parameter may contain several comma separated conditions. A condition can be set as a mask using '*'. The logical negation symbol '!' can be used for an exclusion. All conditions are applied sequentially, which means conditions of including to a group should be specified first followed by an exclusion condition. For example, group="*, !EUR" means that all symbols should be selected first and the ones containing "EUR" in their names should be excluded afterwards.
        Unlike symbol_info(), the symbols_get() function returns data on all requested symbols within a single call.

    :param group: The filter for arranging a group of necessary symbols. Optional parameter. If the group is specified, the function returns only symbols meeting a specified criteria.
    :param kwargs:
    :return: A tuple of SymbolInfo objects
    """
    symbols = _mt5.symbols_get(group=group) if group else _mt5.symbols_get()
    if function:
        symbols = tuple(filter(function, symbols))
    return symbols


@_context_manager_modified
def symbol_info(symbol: str) -> SymbolInfo:
    """Get data on the specified financial instrument.

    :param symbol:
    :return: Return info in the form of a named tuple structure (namedtuple). Return None in case of an error. The info on the error can be obtained using last_error().
    """
    return _mt5.symbol_info(symbol)


@_context_manager_modified
def symbol_info_tick(symbol: str) -> Tick:
    """Get the last tick for the specified financial instrument.

    :param symbol:
    :return:
    """
    return _mt5.symbol_info_tick(symbol)


@_context_manager_modified
def symbol_select(symbol: str, enable: bool = True) -> bool:
    """Select a symbol in the MarketWatch window or remove a symbol from the window.

    :param symbol:
    :param enable:
    :return: True if successful, otherwise – False.
    """
    return _mt5.symbol_select(symbol, enable)


@_context_manager_modified
def copy_rates_from(symbol: str,
                    timeframe: int,
                    datetime_from: Union[datetime, int],
                    count: int
                    ) -> Union[numpy.ndarray, None]:
    """Get bars from the MetaTrader 5 terminal starting from the specified date.

    :param symbol: Financial instrument name, for example, "EURUSD".
    :param timeframe: Timeframe the bars are requested for. Set by a value from the TIMEFRAME enumeration.
    :param datetime_from: Date of opening of the first bar from the requested sample. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01.
    :param count: Number of bars to receive.
    :return: Returns bars as the numpy array with the named time, open, high, low, close, tick_volume, spread and real_volume columns. Return None in case of an error. The info on the error can be obtained using last_error().
    """
    try:
        return _mt5.copy_rates_from(symbol, timeframe, datetime_from, count)
    except SystemError:
        return None


@_context_manager_modified
def copy_rates_from_pos(symbol: str,
                        timeframe: int,
                        start_pos: int,
                        count: int
                        ) -> Union[numpy.ndarray, None]:
    """Get bars from the MetaTrader 5 terminal starting from the specified index.

    :param symbol: Financial instrument name, for example, "EURUSD".
    :param timeframe: Timeframe the bars are requested for. Set by a value from the TIMEFRAME enumeration.
    :param start_pos: Initial index of the bar the data are requested from. The numbering of bars goes from present to past. Thus, the zero bar means the current one.
    :param count: Number of bars to receive.
    :return: Returns bars as the numpy array with the named time, open, high, low, close, tick_volume, spread and real_volume columns. Return None in case of an error. The info on the error can be obtained using last_error().
    """
    try:
        return _mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
    except SystemError:
        return None


@_context_manager_modified
def copy_rates_range(symbol: str,
                     timeframe: int,
                     datetime_from: Union[datetime, int],
                     datetime_to: Union[datetime, int]
                     ) -> Union[numpy.ndarray, None]:
    """Get bars from the MetaTrader 5 terminal starting from the specified index.

        :param symbol: Financial instrument name, for example, "EURUSD".
        :param timeframe: Timeframe the bars are requested for. Set by a value from the TIMEFRAME enumeration.
        :param datetime_from: Date of opening of the first bar from the requested sample. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01.
        :param datetime_to: Date, up to which the bars are requested. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01. Bars with the open time <= date_to are returned.
        :return: Returns bars as the numpy array with the named time, open, high, low, close, tick_volume, spread and real_volume columns. Return None in case of an error. The info on the error can be obtained using last_error().
        """
    try:
        return _mt5.copy_rates_range(symbol, timeframe, datetime_from, datetime_to)
    except SystemError:
        return None


@_context_manager_modified
def copy_rates(symbol: str,
               timeframe: int,
               *,
               datetime_from: Union[datetime, int] = None,
               datetime_to: Union[datetime, int] = None,
               start_pos: int = None,
               count: int = None,
               ) -> Union[numpy.ndarray, None]:
    """Generic function to use keywords to automatically call the correct copy rates function depending on the keyword args passed in.

    :param symbol: Financial instrument name, for example, "EURUSD".
    :param timeframe: Timeframe the bars are requested for. Set by a value from the TIMEFRAME enumeration.
    :param datetime_from: Date of opening of the first bar from the requested sample. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01.
    :param datetime_to: Date, up to which the bars are requested. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01. Bars with the open time <= date_to are returned.
    :param start_pos: Initial index of the bar the data are requested from. The numbering of bars goes from present to past. Thus, the zero bar means the current one.
    :param count: Number of bars to receive.
    :return: Returns bars as the numpy array with the named time, open, high, low, close, tick_volume, spread and real_volume columns. Return None in case of an error. The info on the error can be obtained using last_error().
    """
    try:
        if datetime_from is not None:
            if count is not None:
                return _mt5.copy_rates_from(symbol, timeframe, datetime_from, count)
            if datetime_to is not None:
                return _mt5.copy_rates_range(symbol, timeframe, datetime_from, datetime_to)
        if all(x is None for x in [datetime_from, datetime_to, start_pos, count]):
            return _mt5.copy_rates_from_pos(symbol, timeframe, 3000, 0)
        return _mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
    except SystemError:
        return None


@_context_manager_modified
def copy_ticks_from(symbol: str,
                    datetime_from: Union[datetime, int],
                    count: int,
                    flags: int,
                    ) -> Union[numpy.ndarray, None]:
    """Get ticks from the MetaTrader 5 terminal starting from the specified date.

    :param symbol: Financial instrument name, for example, "EURUSD". Required unnamed parameter.
    :param datetime_from: Date the ticks are requested from. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01.
    :param count: Number of ticks to receive.
    :param flags: A flag to define the type of the requested ticks. COPY_TICKS_INFO – ticks with Bid and/or Ask changes, COPY_TICKS_TRADE – ticks with changes in Last and Volume, COPY_TICKS_ALL – all ticks. Flag values are described in the COPY_TICKS enumeration.
    :return: Returns ticks as the numpy array with the named time, bid, ask, last and flags columns. The 'flags' value can be a combination of flags from the TICK_FLAG enumeration. Return None in case of an error. The info on the error can be obtained using last_error().

    Note:
        See the CopyTicks function for more information.

        When creating the 'datetime' object, Python uses the local time zone, while MetaTrader 5 stores tick and bar open time in UTC time zone (without the shift). Therefore, 'datetime' should be created in UTC time for executing functions that use time. Data received from the MetaTrader 5 terminal has UTC time.
    """
    try:
        return _mt5.copy_ticks_from(symbol, datetime_from, count, flags)
    except SystemError:
        return None


@_context_manager_modified
def copy_ticks_range(symbol: str,
                     datetime_from: Union[datetime, int],
                     datetime_to: Union[datetime, int],
                     flags: int,
                     ) -> Union[numpy.ndarray, None]:
    """Get ticks from the MetaTrader 5 terminal starting from the specified date.

        :param symbol: Financial instrument name, for example, "EURUSD". Required unnamed parameter.
        :param datetime_from: Date the ticks are requested from. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01.
        :param datetime_to: Date, up to which the ticks are requested. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01.
        :param flags: A flag to define the type of the requested ticks. COPY_TICKS_INFO – ticks with Bid and/or Ask changes, COPY_TICKS_TRADE – ticks with changes in Last and Volume, COPY_TICKS_ALL – all ticks. Flag values are described in the COPY_TICKS enumeration.
        :return: Returns ticks as the numpy array with the named time, bid, ask, last and flags columns. The 'flags' value can be a combination of flags from the TICK_FLAG enumeration. Return None in case of an error. The info on the error can be obtained using last_error().

        Note:
            See the CopyTicks function for more information.

            When creating the 'datetime' object, Python uses the local time zone, while MetaTrader 5 stores tick and bar open time in UTC time zone (without the shift). Therefore, 'datetime' should be created in UTC time for executing functions that use time. Data received from the MetaTrader 5 terminal has UTC time.
        """
    try:
        return _mt5.copy_ticks_range(symbol, datetime_from, datetime_to, flags)
    except SystemError:
        return None


@_context_manager_modified
def orders_total() -> int:
    """Get the number of active orders.

    :return: Integer value.
    """
    return _mt5.orders_total()


@_context_manager_modified
def orders_get(symbol: str = None,
               *,
               group: str = None,
               ticket: int = None,
               function: Callable[[TradeOrder], bool] = None,
               **kwargs
               ) -> Tuple[TradeOrder]:
    """Get active orders with the ability to filter by symbol or ticket.

    :param symbol: Symbol name. Optional named parameter. If a symbol is specified, the ticket parameter is ignored.
    :param group: The filter for arranging a group of necessary symbols.
    :param ticket: Order ticket (ORDER_TICKET). Optional named parameter.
    :return: tuple of TradeOrder objects

    Note:
        The function allows receiving all active orders within one call similar to the OrdersTotal and OrderSelect tandem.
        The group parameter allows sorting out orders by symbols. '*' can be used at the beginning and the end of a string.
        The group parameter may contain several comma separated conditions. A condition can be set as a mask using '*'. The logical negation symbol '!' can be used for an exclusion. All conditions are applied sequentially, which means conditions of including to a group should be specified first followed by an exclusion condition. For example, group="*, !EUR" means that orders for all symbols should be selected first and the ones containing "EUR" in symbol names should be excluded afterwards.
    """
    return helpers._get_ticket_type_stuff(_mt5.orders_get, symbol=symbol, group=group, ticket=ticket, function=function)


@_context_manager_modified
def order_calc_margin(order_type: int,
                      symbol: str,
                      volume: float,
                      price: float,
                      ) -> float:
    """Return margin in the account currency to perform a specified trading operation.

    :param order_type: Order type taking values from the ORDER_TYPE enumeration
    :param symbol: Financial instrument name.
    :param volume: Trading operation volume.
    :param price: Open price.
    :return: Real value if successful, otherwise None. The error info can be obtained using last_error().
    """
    return _mt5.order_calc_margin(order_type, symbol, volume, price)


@_context_manager_modified
def order_calc_profit(order_type: int,
                      symbol: str,
                      volume: float,
                      price_open: float,
                      price_close: float,
                      ) -> float:
    """Return margin in the account currency to perform a specified trading operation.

    :param order_type: Order type taking values from the ORDER_TYPE enumeration
    :param symbol: Financial instrument name.
    :param volume: Trading operation volume.
    :param price: Open price.
    :return: Real value if successful, otherwise None. The error info can be obtained using last_error().
    """
    return _mt5.order_calc_profit(order_type, symbol, volume, price_open, price_close)


@_context_manager_modified
def order_check(request: dict = None,
                *,
                action: int = None, magic: int = None, order: int = None,
                symbol: str = None, volume: float = None, price: float = None,
                stoplimit: float = None, sl: float = None, tp: float = None,
                deviation: int = None, type: int = None, type_filling: int = None,
                type_time: int = None, expiration: datetime = None,
                comment: str = None, position: int = None, position_by: int = None,
                **kwargs,
                ) -> OrderCheckResult:
    """Check funds sufficiency for performing a required trading operation. Check result are returned as the MqlTradeCheckResult structure.

    :param action: Trade operation type
    :param magic: Expert Advisor ID (magic number)
    :param order: Order ticket
    :param symbol: Trade symbol
    :param volume: Requested volume for a deal in lots
    :param price: Price
    :param stoplimit: Stop-limit level
    :param sl: Stop loss level
    :param tp: Take profit level
    :param deviation: Maximum possible deviation from the requested price
    :param type: Order type
    :param type_filling: Order execution type
    :param type_time: Order expiration type
    :param expiration: Order expiration time (for the orders of ORDER_TIME_SPECIFIED type)
    :param comment: Order comment
    :param position: Position ticket
    :param position_by: The ticket of an opposite position
    :param kwargs:
    :return: OrderSendResult namedtuple
    """
    return helpers._do_trade_action(_mt5.order_check, locals().copy())


@_context_manager_modified
def order_send(request: dict = None,
               *,
               action: int = None, magic: int = None, order: int = None,
               symbol: str = None, volume: float = None, price: float = None,
               stoplimit: float = None, sl: float = None, tp: float = None,
               deviation: int = None, type: int = None, type_filling: int = None,
               type_time: int = None, expiration: datetime = None,
               comment: str = None, position: int = None, position_by: int = None,
               **kwargs,
               ) -> OrderSendResult:
    """Interaction between the client terminal and a trade server for executing the order placing operation is performed
    by using trade requests. The trade request is represented by the special predefined structure of MqlTradeRequest
    type, which contain all the fields necessary to perform trade deals. The request processing result is represented
    by the structure of MqlTradeResult type.

    :param action: Trade operation type
    :param magic: Expert Advisor ID (magic number)
    :param order: Order ticket
    :param symbol: Trade symbol
    :param volume: Requested volume for a deal in lots
    :param price: Price
    :param stoplimit: Stop-limit level
    :param sl: Stop loss level
    :param tp: Take profit level
    :param deviation: Maximum possible deviation from the requested price
    :param type: Order type
    :param type_filling: Order execution type
    :param type_time: Order expiration type
    :param expiration: Order expiration time (for the orders of ORDER_TIME_SPECIFIED type)
    :param comment: Order comment
    :param position: Position ticket
    :param position_by: The ticket of an opposite position
    :param kwargs:
    :return: OrderSendResult namedtuple
    """
    return helpers._do_trade_action(_mt5.order_send, locals().copy())


@_context_manager_modified
def positions_total() -> int:
    """Get the number of open positions.

    :return: Integer value.
    """
    return _mt5.positions_total()


@_context_manager_modified
def positions_get(symbol: str = None,
                  *,
                  group: str = None,
                  ticket: int = None,
                  function: Callable[[TradePosition], bool] = None,
                  **kwargs
                  ) -> Tuple[TradePosition]:
    """Get open positions with the ability to filter by symbol or ticket. There are three call options.

    :param symbol:
    :param group:
    :param ticket:
    :return:
    """
    return helpers._get_ticket_type_stuff(_mt5.positions_get, symbol=symbol, group=group, ticket=ticket,
                                          function=function)


@_context_manager_modified
def history_deals_get(datetime_from: datetime = None,
                      datetime_to: datetime = None,
                      *,
                      group: str = None,
                      ticket: int = None,
                      position: int = None,
                      function: Callable[[TradeDeal], bool] = None,
                      **kwargs
                      ) -> Tuple[TradeDeal]:
    """Get deals from trading history within the specified interval with the ability to filter by ticket or position.

    :param datetime_from: Date the orders are requested from. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01.
    :param datetime_to: Date, up to which the orders are requested. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01.
    :param group: The filter for arranging a group of necessary symbols. Optional named parameter. If the group is specified, the function returns only deals meeting a specified criteria for a symbol name.
    :param ticket: Ticket of an order (stored in DEAL_ORDER) all deals should be received for. Optional parameter.
    :param position: Ticket of a position (stored in DEAL_POSITION_ID) all deals should be received for. Optional parameter.
    :param function: A function that accepts a TradeDeal object and returns True if that object is to be used else False
    :param kwargs:
    :return: a tuple of TradeDeal objects
    """
    d = locals().copy()
    return helpers._get_history_type_stuff(_mt5.history_deals_get, d)


@_context_manager_modified
def history_orders_total(datetime_from: datetime, datetime_to: datetime, **kwargs) -> int:
    """Get the number of orders in trading history within the specified interval.

    :param datetime_from: Date the orders are requested from. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01. Required unnamed parameter.
    :param datetime_to: Date, up to which the orders are requested. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01. Required unnamed parameter.
    :param kwargs:
    :return:
    """
    return _mt5.history_orders_total(datetime_from, datetime_to)


@_context_manager_modified
def history_deals_total(datetime_from: datetime, datetime_to: datetime, **kwargs) -> int:
    """Get the number of ``deals`` in trading history within the specified interval.

    :param datetime_from: Date the orders are requested from. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01. Required unnamed parameter.
    :param datetime_to: Date, up to which the orders are requested. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01. Required unnamed parameter.
    :param kwargs:
    :return:
    """
    return _mt5.history_deals_total(datetime_from, datetime_to)


@_context_manager_modified
def history_orders_get(datetime_from: datetime = None,
                       datetime_to: datetime = None,
                       *,
                       group: str = None,
                       ticket: int = None,
                       position: int = None,
                       function: Callable[[TradeOrder], bool] = None,
                       **kwargs
                       ) -> Tuple[TradeOrder]:
    """Get deals from trading history within the specified interval with the ability to filter by ticket or position.

    :param datetime_from: Date the orders are requested from. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01.
    :param datetime_to: Date, up to which the orders are requested. Set by the 'datetime' object or as a number of seconds elapsed since 1970.01.01.
    :param group: The filter for arranging a group of necessary symbols.
    :param ticket: Ticket of an order (stored in DEAL_ORDER) all deals should be received for. Optional parameter.
    :param position: Ticket of a position (stored in DEAL_POSITION_ID) all deals should be received for. Optional parameter.
    :param function: A function that accepts a TradeOrder object and returns True if that object is to be used else False
    :param kwargs:
    :return: a tuple of TradeOrder objects
    """
    d = locals().copy()
    return helpers._get_history_type_stuff(_mt5.history_orders_get, d)