"""
Backend Tests for Horse Racing Betting Analyzer API
Tests all core endpoints: bankroll, racecards, analyze, bets, statistics, scraper status
"""

import pytest
import requests
import os
import time

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasicEndpoints:
    """Test health check and basic API endpoints"""
    
    def test_api_root(self):
        """Test API root endpoint returns running status"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "Horse Racing" in data["message"]
        print("✓ API root endpoint working")

    def test_scraper_status(self):
        """Test scraper status shows The Racing API as connected"""
        response = requests.get(f"{BASE_URL}/api/scraper/status")
        assert response.status_code == 200
        data = response.json()
        # Check The Racing API status
        assert "the_racing_api" in data
        assert data["the_racing_api"]["configured"] == True
        assert data["the_racing_api"]["status"] == "connected"
        assert data["the_racing_api"]["source"] == "The Racing API (theracingapi.com)"
        print(f"✓ Scraper status: The Racing API is {data['the_racing_api']['status']}")

    def test_tracks_endpoint(self):
        """Test tracks endpoint returns approved tracks"""
        response = requests.get(f"{BASE_URL}/api/tracks")
        assert response.status_code == 200
        data = response.json()
        assert "uk_tracks" in data
        assert "us_tracks" in data
        assert len(data["uk_tracks"]) >= 5
        assert len(data["us_tracks"]) >= 5
        # Check that wolverhampton is in the list
        uk_ids = [t["id"] for t in data["uk_tracks"]]
        assert "wolverhampton" in uk_ids
        print(f"✓ Tracks endpoint: {len(data['uk_tracks'])} UK, {len(data['us_tracks'])} US tracks")


class TestBankrollEndpoints:
    """Test bankroll management endpoints"""

    def test_get_bankroll(self):
        """Test GET /api/bankroll returns bankroll settings"""
        response = requests.get(f"{BASE_URL}/api/bankroll")
        assert response.status_code == 200
        data = response.json()
        # Validate response structure
        assert "current_bankroll" in data
        assert "starting_bankroll" in data
        assert "stop_loss" in data
        assert "max_daily_bets" in data
        assert "today_pl" in data
        assert "cushion" in data
        assert "percent_above_stop_loss" in data
        # Validate values
        assert isinstance(data["current_bankroll"], (int, float))
        assert isinstance(data["stop_loss"], (int, float))
        assert data["current_bankroll"] >= data["stop_loss"]
        print(f"✓ Bankroll: ${data['current_bankroll']:.2f}, Stop-loss: ${data['stop_loss']:.2f}")

    def test_update_bankroll(self):
        """Test PUT /api/bankroll updates settings"""
        # First get current bankroll
        response = requests.get(f"{BASE_URL}/api/bankroll")
        original_data = response.json()
        
        # Update bankroll settings
        new_stop_loss = 70.0
        update_response = requests.put(
            f"{BASE_URL}/api/bankroll",
            json={"stop_loss": new_stop_loss}
        )
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["stop_loss"] == new_stop_loss
        
        # Restore original stop_loss
        requests.put(
            f"{BASE_URL}/api/bankroll",
            json={"stop_loss": original_data["stop_loss"]}
        )
        print(f"✓ Bankroll update works, stop-loss modified and restored")


class TestLiveRacecardsEndpoint:
    """Test live racecards from The Racing API"""

    def test_get_todays_racecards(self):
        """Test GET /api/racecards/today returns live racecards"""
        response = requests.get(f"{BASE_URL}/api/racecards/today")
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "success" in data
        assert data["success"] == True
        assert "data_source" in data
        assert "LIVE" in data["data_source"]
        assert "courses" in data
        assert "races" in data
        assert "total_races" in data
        
        # Validate courses structure
        courses = data["courses"]
        if len(courses) > 0:
            course = courses[0]
            assert "course" in course
            assert "races" in course
            assert "region" in course
            # Check race structure within course
            if len(course["races"]) > 0:
                race = course["races"][0]
                assert "race_id" in race
                assert "off_time" in race
                assert "race_name" in race
        
        print(f"✓ Racecards: {data['total_races']} races across {len(courses)} courses")
        return data


class TestRaceAnalysisEndpoint:
    """Test race analysis endpoint with 8-criteria scoring"""

    def test_analyze_live_race(self):
        """Test POST /api/analyze with a live race_id"""
        # First get today's races
        racecards_response = requests.get(f"{BASE_URL}/api/racecards/today")
        racecards = racecards_response.json()
        
        if racecards["success"] and racecards["total_races"] > 0:
            # Get first available race_id
            first_race = racecards["races"][0]
            race_id = first_race["race_id"]
            
            # Analyze the race
            response = requests.post(
                f"{BASE_URL}/api/analyze",
                json={"race_id": race_id}
            )
            assert response.status_code == 200
            data = response.json()
            
            # Validate response structure
            assert data["success"] == True
            assert "LIVE" in data["data_source"]
            assert "race_info" in data
            assert "recommendations" in data
            assert "all_horses" in data
            assert "bankroll_status" in data
            assert "warnings" in data
            
            # Validate race_info
            race_info = data["race_info"]
            assert "race_id" in race_info
            assert "track" in race_info
            assert "field_size" in race_info
            
            # Validate recommendations structure
            recs = data["recommendations"]
            assert "win" in recs or "place" in recs  # At least one recommendation type
            
            # Validate all_horses have scoring
            if len(data["all_horses"]) > 0:
                horse = data["all_horses"][0]
                assert "name" in horse
                assert "win_score" in horse
                assert "place_score" in horse
                assert horse["win_score"]["score"] >= 0
                assert horse["win_score"]["max_score"] == 8
                assert "criteria_breakdown" in horse["win_score"]
            
            print(f"✓ Analysis: Race {race_id} analyzed, {len(data['all_horses'])} horses scored")
        else:
            pytest.skip("No live races available for testing")

    def test_analyze_mock_race(self):
        """Test POST /api/analyze with track/race_number (mock fallback)"""
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"track": "wolverhampton", "race_number": 1}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "MOCK" in data["data_source"]
        assert "race_info" in data
        assert "recommendations" in data
        assert "all_horses" in data
        assert len(data["all_horses"]) >= 8  # Mock generates 8-12 horses
        print(f"✓ Mock analysis works: {len(data['all_horses'])} horses generated")


class TestBettingEndpoints:
    """Test bet placement and settlement endpoints"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup: store created bet_ids for cleanup"""
        self.created_bet_ids = []
        yield
        # Cleanup: No direct delete endpoint, but bets are tied to test user

    def test_get_bets_empty_or_existing(self):
        """Test GET /api/bets returns bet history"""
        response = requests.get(f"{BASE_URL}/api/bets")
        assert response.status_code == 200
        data = response.json()
        assert "bets" in data
        assert isinstance(data["bets"], list)
        print(f"✓ Bets endpoint: {len(data['bets'])} existing bets")

    def test_place_bet(self):
        """Test POST /api/bets places a new bet"""
        bet_data = {
            "track": "TEST_wolverhampton",
            "race_number": 99,
            "horse_name": "TEST_ThunderBolt",
            "draw_number": 1,
            "bet_type": "PLACE",
            "stake": 5.00,
            "odds": 3.50,
            "score": 6
        }
        
        response = requests.post(f"{BASE_URL}/api/bets", json=bet_data)
        assert response.status_code == 200
        data = response.json()
        
        # Validate response
        assert "bet_id" in data
        assert "message" in data
        assert "new_bankroll" in data
        assert "Bet placed successfully" in data["message"]
        
        self.created_bet_ids.append(data["bet_id"])
        print(f"✓ Bet placed: {data['bet_id']}, new bankroll: ${data['new_bankroll']:.2f}")
        return data["bet_id"]

    def test_place_and_settle_bet_win(self):
        """Test full bet lifecycle: place -> settle as WIN"""
        # Place a bet
        bet_data = {
            "track": "TEST_kempton",
            "race_number": 88,
            "horse_name": "TEST_WinnerHorse",
            "draw_number": 3,
            "bet_type": "WIN",
            "stake": 5.00,
            "odds": 4.00,
            "score": 7
        }
        
        place_response = requests.post(f"{BASE_URL}/api/bets", json=bet_data)
        assert place_response.status_code == 200
        bet_id = place_response.json()["bet_id"]
        
        # Settle as WIN
        settle_response = requests.post(
            f"{BASE_URL}/api/bets/{bet_id}/settle",
            json={"result": "WIN"}
        )
        assert settle_response.status_code == 200
        settle_data = settle_response.json()
        
        assert settle_data["outcome"] == "WIN"
        assert settle_data["profit_loss"] > 0  # Should be positive
        assert "new_bankroll" in settle_data
        assert settle_data["consecutive_losses"] == 0  # Reset on win
        print(f"✓ Bet settled as WIN: profit ${settle_data['profit_loss']:.2f}")

    def test_place_and_settle_bet_loss(self):
        """Test settling a bet as LOSS"""
        # Place a bet
        bet_data = {
            "track": "TEST_lingfield",
            "race_number": 77,
            "horse_name": "TEST_LoserHorse",
            "draw_number": 5,
            "bet_type": "PLACE",
            "stake": 5.00,
            "odds": 2.50,
            "score": 4
        }
        
        place_response = requests.post(f"{BASE_URL}/api/bets", json=bet_data)
        assert place_response.status_code == 200
        bet_id = place_response.json()["bet_id"]
        
        # Settle as LOSS
        settle_response = requests.post(
            f"{BASE_URL}/api/bets/{bet_id}/settle",
            json={"result": "LOSS"}
        )
        assert settle_response.status_code == 200
        settle_data = settle_response.json()
        
        assert settle_data["outcome"] == "LOSS"
        assert settle_data["profit_loss"] < 0  # Should be negative
        print(f"✓ Bet settled as LOSS: loss ${abs(settle_data['profit_loss']):.2f}")

    def test_cannot_settle_already_settled_bet(self):
        """Test that settling an already settled bet returns error"""
        # Place a bet
        bet_data = {
            "track": "TEST_newcastle",
            "race_number": 66,
            "horse_name": "TEST_AlreadySettled",
            "draw_number": 2,
            "bet_type": "PLACE",
            "stake": 5.00,
            "odds": 2.00,
            "score": 5
        }
        
        place_response = requests.post(f"{BASE_URL}/api/bets", json=bet_data)
        bet_id = place_response.json()["bet_id"]
        
        # Settle first time
        requests.post(f"{BASE_URL}/api/bets/{bet_id}/settle", json={"result": "WIN"})
        
        # Try to settle again - should fail
        second_settle = requests.post(
            f"{BASE_URL}/api/bets/{bet_id}/settle",
            json={"result": "LOSS"}
        )
        assert second_settle.status_code == 400
        assert "already settled" in second_settle.json()["detail"].lower()
        print(f"✓ Double settlement correctly prevented")


class TestStatisticsEndpoint:
    """Test statistics endpoint"""

    def test_get_statistics(self):
        """Test GET /api/statistics returns betting statistics"""
        response = requests.get(f"{BASE_URL}/api/statistics")
        assert response.status_code == 200
        data = response.json()
        
        # Validate structure
        assert "overall" in data
        assert "by_score" in data
        assert "recent_form" in data
        
        # Validate overall stats structure
        overall = data["overall"]
        assert "total_bets" in overall
        assert "wins" in overall
        assert "losses" in overall
        assert "win_rate" in overall
        assert "total_staked" in overall
        assert "total_profit" in overall
        assert "roi" in overall
        
        # Validate recent_form
        assert "last_10_bets" in data["recent_form"]
        assert "consecutive_losses" in data["recent_form"]
        
        print(f"✓ Statistics: {overall['total_bets']} total bets, {overall['win_rate']} win rate, {overall['roi']} ROI")


class TestEdgeCases:
    """Test edge cases and validation"""

    def test_analyze_invalid_race_id(self):
        """Test analyze with non-existent race_id returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"race_id": "rac_invalid_nonexistent"}
        )
        assert response.status_code == 404
        print("✓ Invalid race_id correctly returns 404")

    def test_settle_nonexistent_bet(self):
        """Test settling non-existent bet returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/bets/bet_nonexistent123/settle",
            json={"result": "WIN"}
        )
        assert response.status_code == 404
        print("✓ Non-existent bet settle correctly returns 404")

    def test_place_bet_exceeds_max_stake(self):
        """Test placing bet that exceeds max stake returns error"""
        # Get current bankroll
        bankroll_response = requests.get(f"{BASE_URL}/api/bankroll")
        bankroll = bankroll_response.json()["current_bankroll"]
        
        # Try to place bet exceeding max stake (3% of bankroll)
        excessive_stake = bankroll * 0.10  # 10% is way over 3%
        bet_data = {
            "track": "TEST_excessive",
            "race_number": 1,
            "horse_name": "TEST_BigStake",
            "draw_number": 1,
            "bet_type": "WIN",
            "stake": excessive_stake,
            "odds": 2.00,
            "score": 6
        }
        
        response = requests.post(f"{BASE_URL}/api/bets", json=bet_data)
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"].lower() or "max" in response.json()["detail"].lower()
        print("✓ Excessive stake correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
