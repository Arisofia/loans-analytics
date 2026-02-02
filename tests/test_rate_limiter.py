"""Tests for rate limiting middleware."""

import pytest
import time
from python.middleware.rate_limiter import (
    RateLimiter,
    TokenBucketRateLimiter,
    rate_limit,
    api_limiter,
    auth_limiter,
)


class TestRateLimiter:
    """Test simple rate limiter."""
    
    def test_allows_requests_under_limit(self):
        """Test that requests under limit are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # Should allow 5 requests
        for i in range(5):
            assert limiter.is_allowed('user-1'), f"Request {i+1} should be allowed"
    
    def test_blocks_requests_over_limit(self):
        """Test that requests over limit are blocked."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # Allow 3 requests
        for i in range(3):
            assert limiter.is_allowed('user-1')
        
        # Block 4th request
        assert not limiter.is_allowed('user-1'), "4th request should be blocked"
    
    def test_different_users_separate_limits(self):
        """Test that different users have separate rate limits."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # User 1: 2 requests
        assert limiter.is_allowed('user-1')
        assert limiter.is_allowed('user-1')
        assert not limiter.is_allowed('user-1')
        
        # User 2: Should still have 2 requests available
        assert limiter.is_allowed('user-2')
        assert limiter.is_allowed('user-2')
        assert not limiter.is_allowed('user-2')
    
    def test_reset_clears_limit(self):
        """Test that reset clears rate limit for user."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # Use up limit
        limiter.is_allowed('user-1')
        limiter.is_allowed('user-1')
        assert not limiter.is_allowed('user-1')
        
        # Reset
        limiter.reset('user-1')
        
        # Should be allowed again
        assert limiter.is_allowed('user-1')


class TestTokenBucketRateLimiter:
    """Test token bucket rate limiter."""
    
    def test_allows_requests_with_tokens(self):
        """Test that requests are allowed when tokens available."""
        limiter = TokenBucketRateLimiter(rate=10, capacity=10)
        
        # Should allow 10 requests (capacity)
        for i in range(10):
            assert limiter.is_allowed('user-1', tokens=1), f"Request {i+1} should be allowed"
    
    def test_blocks_requests_without_tokens(self):
        """Test that requests are blocked when no tokens."""
        limiter = TokenBucketRateLimiter(rate=1, capacity=2)
        
        # Use up tokens
        assert limiter.is_allowed('user-1', tokens=1)
        assert limiter.is_allowed('user-1', tokens=1)
        
        # No tokens left
        assert not limiter.is_allowed('user-1', tokens=1)
    
    def test_tokens_refill_over_time(self):
        """Test that tokens refill at specified rate."""
        limiter = TokenBucketRateLimiter(rate=10, capacity=10)  # 10 tokens/sec
        
        # Use up tokens
        for i in range(10):
            limiter.is_allowed('user-1', tokens=1)
        
        # No tokens left
        assert not limiter.is_allowed('user-1', tokens=1)
        
        # Wait 0.2 seconds -> should get 2 tokens back
        time.sleep(0.2)
        assert limiter.is_allowed('user-1', tokens=1)
        assert limiter.is_allowed('user-1', tokens=1)
    
    def test_burst_capacity(self):
        """Test that burst capacity allows temporary spikes."""
        limiter = TokenBucketRateLimiter(rate=1, capacity=10)  # 1/sec, burst 10
        
        # Can make 10 requests immediately (burst)
        for i in range(10):
            assert limiter.is_allowed('user-1', tokens=1)
        
        # 11th request blocked
        assert not limiter.is_allowed('user-1', tokens=1)
    
    def test_get_wait_time(self):
        """Test wait time calculation."""
        limiter = TokenBucketRateLimiter(rate=10, capacity=10)  # 10 tokens/sec
        
        # Use all tokens
        for i in range(10):
            limiter.is_allowed('user-1', tokens=1)
        
        # Wait time for 1 token should be ~0.1 seconds
        wait_time = limiter.get_wait_time('user-1', tokens=1)
        assert 0 <= wait_time <= 0.15, f"Wait time {wait_time} not in expected range"
        
        # Wait time for 5 tokens should be ~0.5 seconds
        wait_time = limiter.get_wait_time('user-1', tokens=5)
        assert 0.4 <= wait_time <= 0.6, f"Wait time {wait_time} not in expected range"
    
    def test_different_users_separate_buckets(self):
        """Test that different users have separate token buckets."""
        limiter = TokenBucketRateLimiter(rate=1, capacity=2)
        
        # User 1: use tokens
        assert limiter.is_allowed('user-1', tokens=2)
        assert not limiter.is_allowed('user-1', tokens=1)
        
        # User 2: should have full bucket
        assert limiter.is_allowed('user-2', tokens=2)
    
    def test_reset_refills_bucket(self):
        """Test that reset refills token bucket."""
        limiter = TokenBucketRateLimiter(rate=1, capacity=5)
        
        # Use up tokens
        limiter.is_allowed('user-1', tokens=5)
        assert not limiter.is_allowed('user-1', tokens=1)
        
        # Reset
        limiter.reset('user-1')
        
        # Should have full bucket again
        assert limiter.is_allowed('user-1', tokens=5)


class TestRateLimitDecorator:
    """Test rate_limit decorator."""
    
    def test_decorator_allows_under_limit(self):
        """Test that decorated function works under limit."""
        limiter = TokenBucketRateLimiter(rate=10, capacity=5)
        
        @rate_limit(limiter, tokens=1)
        def test_func(user_id: str):
            return "success"
        
        # Should work 5 times
        for i in range(5):
            result = test_func(user_id='test-user')
            assert result == "success"
    
    def test_decorator_blocks_over_limit(self):
        """Test that decorated function raises exception over limit."""
        limiter = TokenBucketRateLimiter(rate=1, capacity=2)
        
        @rate_limit(limiter, tokens=1)
        def test_func(user_id: str):
            return "success"
        
        # Use up tokens
        test_func(user_id='test-user')
        test_func(user_id='test-user')
        
        # Should raise exception
        with pytest.raises(Exception) as exc_info:
            test_func(user_id='test-user')
        
        assert "Rate limit exceeded" in str(exc_info.value)
    
    def test_decorator_custom_error_message(self):
        """Test custom error message in decorator."""
        limiter = TokenBucketRateLimiter(rate=1, capacity=1)
        
        @rate_limit(limiter, error_message="Too many requests!")
        def test_func(user_id: str):
            return "success"
        
        # Use up tokens
        test_func(user_id='test-user')
        
        # Should raise with custom message
        with pytest.raises(Exception) as exc_info:
            test_func(user_id='test-user')
        
        assert "Too many requests!" in str(exc_info.value)


class TestGlobalLimiters:
    """Test global rate limiter instances."""
    
    def test_api_limiter_exists(self):
        """Test that api_limiter is configured."""
        assert api_limiter is not None
        assert isinstance(api_limiter, TokenBucketRateLimiter)
        assert api_limiter.rate == 10
        assert api_limiter.capacity == 20
    
    def test_auth_limiter_exists(self):
        """Test that auth_limiter is configured."""
        assert auth_limiter is not None
        assert isinstance(auth_limiter, TokenBucketRateLimiter)
        # Should be very restrictive (~5 per minute)
        assert auth_limiter.capacity == 5
    
    def test_api_limiter_functional(self):
        """Test that api_limiter works correctly."""
        # Reset to ensure clean state
        api_limiter.reset('test-api-user')
        
        # Should allow several requests
        assert api_limiter.is_allowed('test-api-user', tokens=1)
        assert api_limiter.is_allowed('test-api-user', tokens=1)
    
    def test_auth_limiter_restrictive(self):
        """Test that auth_limiter is more restrictive."""
        # Reset to ensure clean state
        auth_limiter.reset('test-auth-user')
        
        # Can make 5 requests (capacity)
        for i in range(5):
            assert auth_limiter.is_allowed('test-auth-user', tokens=1)
        
        # 6th request should be blocked
        assert not auth_limiter.is_allowed('test-auth-user', tokens=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
