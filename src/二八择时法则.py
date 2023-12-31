from jqdata import *


def initialize(context):
    set_params()  # 1 设置策略参数
    set_backtest()  # 2 设置回测条件


# 设置参数，定义了交易时间和股票
def set_params():
    # 设置基准收益
    set_benchmark('000300.XSHG')
    g.lag = 20    # 回溯期
    g.hour = 14   # 小时（每天交易时间：具体哪个小时bar）
    g.minute = 53  # 分钟（每天交易时间：具体哪个分钟bar）
    g.sz = '000016.XSHG'  # 计算标的——上证50指数（超级大盘股）
    g.hs = '000300.XSHG'  # 计算标的——沪深300指数（价值股）
    g.zz = '000905.XSHG'  # 计算标的——中证500指数（成长股）
    g.ETF50 = '510050.XSHG'  # 交易标的’510050.XSHG'
    g.ETF300 = '510300.XSHG'  # 交易标的’510300.XSHG'
    g.ETF500 = '510500.XSHG'  # 交易标的’510500.XSHG'

# 设置回测条件


def set_backtest():
    set_option('use_real_price', True)  # 用真实价格交易
    # 过滤log日志
    log.set_level('order', 'error')
# 每天开盘前
# 每天开盘前要做的事情
# 输入：context
# 输出：none


def before_trading_start(context):
    # 将滑点设置为交易额的千分之2
    set_slippage(PriceRelatedSlippage(0.002))
    # 设置手续费
    dt = context.current_dt
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003,
                   close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')

# 买入时印花税=0，卖出时印花税=千分之 1，买入佣金=万 3，卖出佣金=万 3，最低佣金 5元
# 定义函数getStockPrice
# 取得股票某个区间内的所有收盘价（用于取前20日和当前收盘价）
# 输入：stock, interval
# 输出：h['close'].values[0] , h['close'].values[-1]
def getStockPrice(stock, interval):  # 输入stock证券名，interval期
    h = attribute_history(stock, interval, unit='1d',
                          fields=('close'), skip_paused=True)
    return (h['close'].values[0], h['close'].values[-1])

# 计算得到信号（这个信号是一个string）
# 输入：context
# 输出：string: sell_the_stocks || ETF50 || ETF300 || ETF500
def get_signal(context):
    # 收盘价，通过getStockPrice获取
    # Yesterday50是昨日收盘价，interval50是interval周期前的收盘价
    # 取出价格
    interval50, Yesterday50 = getStockPrice(g.sz, g.lag)
    interval300, Yesterday300 = getStockPrice(g.hs, g.lag)
    interval500, Yesterday500 = getStockPrice(g.zz, g.lag)
    # 计算前20日动量
    sz50increase = (Yesterday50 - interval50) / interval50
    hs300increase = (Yesterday300 - interval300) / interval300
    zz500increase = (Yesterday500 - interval500) / interval500
    # 对于这3个指数基金的持有金额
    hold50 = context.portfolio.positions[g.ETF50].total_amount
    # positions.total_amount: 上证50ETF持有金额
    hold300 = context.portfolio.positions[g.ETF300].total_amount
    # positions.total_amount: 沪深300ETF持有金额
    hold500 = context.portfolio.positions[g.ETF500].total_amount
    # positions.total_amount: 中证500ETF持有金额
  # 300空头，且300仓位>0 || 500空头，且500仓位>0 || 50空头，且50仓位>0
    if (hs300increase <= 0 and hold300 > 0) \
            or (zz500increase <= 0 and hold500 > 0) \
            or (sz50increase <= 0 and hold50 > 0):
        # 卖出持有的仓位，此条件是针对3个标的的止损条件
        return 'sell_the_stocks'  # 返回string给get_signal函数
    # 如果50增长率大于300和500幅度达到0.01，且 50增长率>0 且 50、300、500仓位=0（目前无仓位）
    elif sz50increase-hs300increase > 0.01 \
            and sz50increase-zz500increase > 0.01 \
            and sz50increase > 0 \
            and (hold300 == 0 and hold500 == 0 and hold50 == 0):
        # 买入50
        return 'ETF50'  # 返回string给get_signal函数
    # 如果300增长率大于500和50幅度达到0.01，且 300增长率>0 且 50、300、500仓位=0（目前无仓位）
    elif hs300increase-zz500increase > 0.01 \
            and hs300increase-sz50increase > 0.01 \
            and hs300increase > 0 \
            and (hold300 == 0 and hold500 == 0 and hold50 == 0):
        # 买入300
        return 'ETF300'  # 返回string给get_signal函数
    # 如果500增长率大于300和50 幅度达到0.01，且 500增长率大于0且 50、300、500仓位=0（目前无仓位）
    elif zz500increase-hs300increase > 0.01\
            and zz500increase-sz50increase > 0.01 \
            and zz500increase > 0 \
            and (hold300 == 0 and hold500 == 0 and hold50 == 0):
        # 买入500
        return 'ETF500'  # 返回string给get_signal函数

# 卖出指令，定义清仓函数：sell_the_stocks
# 输入：context
# 输出：none
def sell_the_stocks(context):
    for i in context.portfolio.positions.keys():
        # context.portfolio.positions是一个dict
        # .keys()函数，以列表返回一个dict所有的键名
        # 将dict的内容（context.portfolio.positions）逐一取出，然后卖出
        return (log.info("Selling %s" % i),
                order_target_value(i, 0))

# 买入股票，定义函数：buy_the_stocks
def buy_the_stocks(context, signal):
    return (log.info("Buying %s" % signal),
            order_value(eval('g.%s' % signal), context.portfolio.available_cash))
# eval把字符串（'%s'% signal）转化为g.ETF50300500的赋值结果（3个指数基金）
# 执行此函数时，signal被传入下单函数order_value的第一个参数security部分，作为标的
# 第二个参数cash = context.portfolio.available cash，现在的账户现金量
# 每日交易，调用自定义函数sell_the_stocks, buy_the_stocks


def handle_data(context, data):
    # 获得当前时间（小时和分钟）
    hour = context.current_dt.hour
    minute = context.current_dt.minute
    # 达到每日时间参数条件（g.hour, g.minute）时，获取get_signal计算得到的信号
    if hour == g.hour and minute == g.minute:
        signal = get_signal(context)
        # 如果信号是sell_the_stocks，就调用函数sell_the_stocks
        if signal == 'sell_the_stocks':
            sell_the_stocks(context)
        # 如果信号是ETF300或者ETF500或者ETF50，就调用函数buy_the_stocks
        elif signal == 'ETF500' or signal == 'ETF50' or signal == 'ETF300':
            buy_the_stocks(context, signal)

# 每日收盘后（输出目前的资金状况）
def after_trading_end(context):
    log.info(context.portfolio.available_cash +
             context.portfolio.positions_value)
    return
