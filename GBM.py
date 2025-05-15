# region imports
from AlgorithmImports import *
# endregion

class SimpleEqualWeightSP500Replicator(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)
        
        self.rebalance_day = -1
        self.last_month = -1
        
        self.AddEquity("SPY", Resolution.Daily)
        self.SetBenchmark("SPY")
        
        self.UniverseSettings.Resolution = Resolution.Daily
        self.UniverseSettings.ExtendedMarketHours = False
        
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        
        self.SetWarmUp(timedelta(days=30))

    def CoarseSelectionFunction(self, coarse):
        if self.Time.month == self.last_month:
            return Universe.Unchanged
        
        self.last_month = self.Time.month
        self.rebalance_day = self.Time.day
        
        filtered = [x for x in coarse if x.HasFundamentalData 
                   and x.Price > 5 
                   and x.DollarVolume > 10000000]
        
        sorted_by_volume = sorted(filtered, key=lambda x: x.DollarVolume, reverse=True)
        
        return [x.Symbol for x in sorted_by_volume[:1000]]
    
    def FineSelectionFunction(self, fine):
        filtered_fine = [x for x in fine if x.MarketCap > 3e9]
        
        sorted_by_market_cap = sorted(filtered_fine, key=lambda x: x.MarketCap, reverse=True)
        
        count = min(500, len(sorted_by_market_cap))
        selected = sorted_by_market_cap[:count]
        
        self.Log(f"Selected {len(selected)} stocks based on market cap")
        
        return [x.Symbol for x in selected]
    
    def OnData(self, data):
        if self.IsWarmingUp: 
            return
        
        if self.Time.day != self.rebalance_day: 
            return
        
        for holding in self.Portfolio.Values:
            if holding.Invested and holding.Symbol not in self.ActiveSecurities:
                self.Liquidate(holding.Symbol)
        
        active_securities = [sec for sec in self.ActiveSecurities.Values 
                           if sec.Symbol.Value != "SPY" and sec.HasData]
        
        if len(active_securities) > 0:
            weight = 1.0 / len(active_securities)
            
            for security in active_securities:
                if security.Price > 0 and security.IsTradable:
                    self.SetHoldings(security.Symbol, weight)
            
            self.Log(f"Rebalanced portfolio: {len(active_securities)} positions at {weight:.4f} weight each")
