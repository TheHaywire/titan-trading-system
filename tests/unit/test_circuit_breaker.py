"""Unit tests for Circuit Breaker."""
import pytest
from titan_system.core.circuit_breaker import CircuitBreaker


class TestCircuitBreakerInitialization:
    """Test circuit breaker initialization."""
    
    def test_default_initialization(self):
        """Test with default parameters."""
        breaker = CircuitBreaker()
        assert breaker.max_daily_loss == 5.0
        assert breaker.max_consecutive_losses == 5
        assert breaker.max_exposure == 50.0
        assert breaker.tripped == False
    
    def test_custom_initialization(self):
        """Test with custom parameters."""
        breaker = CircuitBreaker(
            max_daily_loss_percent=3.0,
            max_consecutive_losses=3,
            max_total_exposure_percent=30.0
        )
        assert breaker.max_daily_loss == 3.0
        assert breaker.max_consecutive_losses == 3
        assert breaker.max_exposure == 30.0


class TestCircuitBreakerDailyLoss:
    """Test daily loss monitoring."""
    
    def test_safe_equity_level(self, mock_account_info):
        """Test that trading is allowed when equity is stable."""
        breaker = CircuitBreaker(max_daily_loss_percent=5.0)
        
        # First check initializes daily equity
        safe, msg = breaker.check_safe_to_trade(mock_account_info)
        assert safe == True
        assert "green" in msg.lower()
    
    def test_approaching_daily_limit(self, mock_account_info):
        """Test warning when approaching but not exceeding limit."""
        breaker = CircuitBreaker(max_daily_loss_percent=5.0)
        
        # Initialize with starting equity
        breaker.check_safe_to_trade(mock_account_info)
        
        # Drop equity by 4% (75% of 5% limit)
        mock_account_info['equity'] = 10050.0 * 0.96
        safe, msg = breaker.check_safe_to_trade(mock_account_info)
        
        # Should still be safe but warn
        assert safe == True
    
    def test_exceeding_daily_limit(self, mock_account_info):
        """Test circuit breaker trips when daily loss exceeds limit."""
        breaker = CircuitBreaker(max_daily_loss_percent=5.0)
        
        # Initialize
        breaker.check_safe_to_trade(mock_account_info)
        
        # Drop equity by 6% (exceeds 5% limit)
        mock_account_info['equity'] = 10050.0 * 0.94
        safe, msg = breaker.check_safe_to_trade(mock_account_info)
        
        # Should be tripped
        assert safe == False
        assert breaker.tripped == True
        assert "Daily loss" in breaker.trip_reason


class TestCircuitBreakerConsecutiveLosses:
    """Test consecutive loss tracking."""
    
    def test_record_single_loss(self):
        """Test recording a single loss."""
        breaker = CircuitBreaker(max_consecutive_losses=3)
        
        breaker.record_trade_result(-50.0, "EURUSD")
        assert breaker.stats.consecutive_losses == 1
    
    def test_record_win_resets_losses(self):
        """Test that a win resets consecutive loss counter."""
        breaker = CircuitBreaker(max_consecutive_losses=3)
        
        # Record losses
        breaker.record_trade_result(-50.0)
        breaker.record_trade_result(-30.0)
        assert breaker.stats.consecutive_losses == 2
        
        # Win resets
        breaker.record_trade_result(100.0)
        assert breaker.stats.consecutive_losses == 0
    
    def test_trip_on_max_consecutive_losses(self, mock_account_info):
        """Test circuit breaker trips on max consecutive losses."""
        breaker = CircuitBreaker(max_consecutive_losses=3)
        
        # Record 3 losses
        breaker.record_trade_result(-50.0)
        breaker.record_trade_result(-75.0)
        breaker.record_trade_result(-100.0)
        
        # Should trip on check
        safe, msg = breaker.check_safe_to_trade(mock_account_info)
        assert safe == False
        assert breaker.tripped == True
        assert "consecutive" in breaker.trip_reason.lower()


class TestCircuitBreakerReset:
    """Test reset functionality."""
    
    def test_manual_reset(self, mock_account_info):
        """Test manual reset after trip."""
        breaker = CircuitBreaker(max_consecutive_losses=2)
        
        # Trip the breaker
        breaker.record_trade_result(-50.0)
        breaker.record_trade_result(-75.0)
        breaker.check_safe_to_trade(mock_account_info)
        
        assert breaker.tripped == True
        
        # Manual reset
        breaker.manual_reset("Testing reset")
        
        assert breaker.tripped == False
        assert breaker.stats.consecutive_losses == 0
        
        # Should be safe now
        safe, msg = breaker.check_safe_to_trade(mock_account_info)
        assert safe == True


class TestCircuitBreakerStatus:
    """Test status reporting."""
    
    def test_get_status(self):
        """Test status dictionary."""
        breaker = CircuitBreaker(max_daily_loss_percent=5.0)
        
        status = breaker.get_status()
        
        assert 'tripped' in status
        assert 'consecutive_losses' in status
        assert 'limits' in status
        assert status['limits']['max_daily_loss_percent'] == 5.0


# Integration test
class TestCircuitBreakerIntegration:
    """Integration tests simulating real trading scenarios."""
    
    def test_full_trading_day_scenario(self, mock_account_info):
        """Simulate a full trading day with various outcomes."""
        breaker = CircuitBreaker(
            max_daily_loss_percent=5.0,
            max_consecutive_losses=3
        )
        
        # Morning: Start trading
        safe, _ = breaker.check_safe_to_trade(mock_account_info)
        assert safe == True
        
        # Trade 1: Win
        breaker.record_trade_result(100.0, "EURUSD")
        mock_account_info['equity'] += 100
        safe, _ = breaker.check_safe_to_trade(mock_account_info)
        assert safe == True
        
        # Trade 2: Small loss
        breaker.record_trade_result(-50.0, "GBPUSD")
        mock_account_info['equity'] -= 50
        safe, _ = breaker.check_safe_to_trade(mock_account_info)
        assert safe == True
        
        # Trade 3: Another loss
        breaker.record_trade_result(-75.0, "USDJPY")
        mock_account_info['equity'] -= 75
        safe, _ = breaker.check_safe_to_trade(mock_account_info)
        assert safe == True
        assert breaker.stats.consecutive_losses == 2
        
        # Trade 4: Win breaks losing streak
        breaker.record_trade_result(150.0, "EURUSD")
        mock_account_info['equity'] += 150
        safe, _ = breaker.check_safe_to_trade(mock_account_info)
        assert safe == True
        assert breaker.stats.consecutive_losses == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
