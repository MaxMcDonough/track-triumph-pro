#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Horse Racing Betting Analyzer
Tests bankroll, race analysis, betting, and statistics endpoints (NO AUTH MODE)
"""

import requests
import sys
import json
from datetime import datetime
import time

class HorseRacingAPITester:
    def __init__(self, base_url="https://bettingpro-16.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # No auth mode - removed user credentials
        self.test_results = {
            "bankroll": [],
            "tracks": [],
            "analysis": [],
            "bets": [],
            "statistics": [],
            "errors": []
        }

    def log_result(self, category, test_name, success, details="", response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response_data"] = response_data
            
        self.test_results[category].append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {details}")
        
        if not success:
            self.test_results["errors"].append(f"{test_name}: {details}")

    def test_user_registration(self):
        """Test user registration endpoint"""
        print("\n🔍 Testing User Registration...")
        
        try:
            response = self.session.post(f"{self.api_url}/auth/register", json={
                "email": self.test_email,
                "password": self.test_password,
                "name": self.test_name
            })
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user_id" in data:
                    self.user_token = data["token"]
                    self.user_data = data
                    self.session.headers.update({'Authorization': f'Bearer {self.user_token}'})
                    self.log_result("auth", "User Registration", True, 
                                  f"User registered successfully with ID: {data['user_id']}", data)
                    return True
                else:
                    self.log_result("auth", "User Registration", False, 
                                  "Missing token or user_id in response", data)
            else:
                self.log_result("auth", "User Registration", False, 
                              f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("auth", "User Registration", False, f"Exception: {str(e)}")
        
        return False

    def test_user_login(self):
        """Test user login endpoint"""
        print("\n🔍 Testing User Login...")
        
        try:
            response = self.session.post(f"{self.api_url}/auth/login", json={
                "email": self.test_email,
                "password": self.test_password
            })
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data:
                    self.log_result("auth", "User Login", True, 
                                  "Login successful", data)
                    return True
                else:
                    self.log_result("auth", "User Login", False, 
                                  "Missing token in response", data)
            else:
                self.log_result("auth", "User Login", False, 
                              f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("auth", "User Login", False, f"Exception: {str(e)}")
        
        return False

    def test_auth_me(self):
        """Test /auth/me endpoint"""
        print("\n🔍 Testing Auth Me Endpoint...")
        
        try:
            response = self.session.get(f"{self.api_url}/auth/me")
            
            if response.status_code == 200:
                data = response.json()
                if "user_id" in data and "email" in data:
                    self.log_result("auth", "Auth Me", True, 
                                  f"User data retrieved: {data['email']}", data)
                    return True
                else:
                    self.log_result("auth", "Auth Me", False, 
                                  "Missing user_id or email in response", data)
            else:
                self.log_result("auth", "Auth Me", False, 
                              f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("auth", "Auth Me", False, f"Exception: {str(e)}")
        
        return False

    def test_google_oauth_redirect(self):
        """Test Google OAuth button functionality (redirect check)"""
        print("\n🔍 Testing Google OAuth Redirect...")
        
        try:
            # Test that the auth URL is accessible
            auth_url = "https://auth.emergentagent.com/"
            response = requests.get(auth_url, timeout=10, allow_redirects=False)
            
            if response.status_code in [200, 302, 301]:
                self.log_result("auth", "Google OAuth Redirect", True, 
                              f"Auth service accessible (Status: {response.status_code})")
                return True
            else:
                self.log_result("auth", "Google OAuth Redirect", False, 
                              f"Auth service not accessible (Status: {response.status_code})")
                
        except Exception as e:
            self.log_result("auth", "Google OAuth Redirect", False, f"Exception: {str(e)}")
        
        return False

    def test_bankroll_endpoints(self):
        """Test bankroll management endpoints"""
        print("\n🔍 Testing Bankroll Endpoints...")
        
        # Test GET bankroll
        try:
            response = self.session.get(f"{self.api_url}/bankroll")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["current_bankroll", "stop_loss", "starting_bankroll", "max_daily_bets"]
                if all(field in data for field in required_fields):
                    self.log_result("bankroll", "Get Bankroll", True, 
                                  f"Bankroll: ${data['current_bankroll']}, Stop-loss: ${data['stop_loss']}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("bankroll", "Get Bankroll", False, 
                                  f"Missing bankroll fields: {missing}", data)
            else:
                self.log_result("bankroll", "Get Bankroll", False, 
                              f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("bankroll", "Get Bankroll", False, f"Exception: {str(e)}")

        # Test PUT bankroll update
        try:
            update_data = {"current_bankroll": 300.0, "stop_loss": 75.0}
            response = self.session.put(f"{self.api_url}/bankroll", json=update_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("current_bankroll") == 300.0:
                    self.log_result("bankroll", "Update Bankroll", True, 
                                  "Bankroll updated successfully", data)
                else:
                    self.log_result("bankroll", "Update Bankroll", False, 
                                  "Bankroll not updated correctly", data)
            else:
                self.log_result("bankroll", "Update Bankroll", False, 
                              f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("bankroll", "Update Bankroll", False, f"Exception: {str(e)}")

    def test_tracks_endpoint(self):
        """Test tracks endpoint"""
        print("\n🔍 Testing Tracks Endpoint...")
        
        try:
            response = self.session.get(f"{self.api_url}/tracks")
            
            if response.status_code == 200:
                data = response.json()
                if "uk_tracks" in data and "us_tracks" in data:
                    uk_count = len(data["uk_tracks"])
                    us_count = len(data["us_tracks"])
                    
                    # Check if wolverhampton is in the tracks (required for testing)
                    wolverhampton_found = any(track.get("id") == "wolverhampton" for track in data["uk_tracks"])
                    
                    if wolverhampton_found:
                        self.log_result("tracks", "Get Tracks", True, 
                                      f"Retrieved {uk_count} UK tracks and {us_count} US tracks (wolverhampton found)", data)
                    else:
                        self.log_result("tracks", "Get Tracks", False, 
                                      f"Retrieved tracks but wolverhampton not found in UK tracks", data)
                    return data
                else:
                    self.log_result("tracks", "Get Tracks", False, 
                                  "Missing uk_tracks or us_tracks in response", data)
            else:
                self.log_result("tracks", "Get Tracks", False, 
                              f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("tracks", "Get Tracks", False, f"Exception: {str(e)}")
        
        return None

    def test_race_analysis(self):
        """Test race analysis endpoint with 8-criteria scoring"""
        print("\n🔍 Testing Race Analysis Endpoint...")
        
        try:
            analysis_data = {
                "track": "wolverhampton",
                "race_number": 1
            }
            response = self.session.post(f"{self.api_url}/analyze", json=analysis_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "race_info", "recommendations", "all_horses", "bankroll_status"]
                
                if all(field in data for field in required_fields):
                    recommendations = data["recommendations"]
                    horse_count = len(data["all_horses"])
                    
                    # Check if recommendations have proper scoring
                    win_rec = recommendations.get("win")
                    place_rec = recommendations.get("place")
                    
                    scoring_valid = True
                    if win_rec and ("score" not in win_rec or "criteria_breakdown" not in win_rec):
                        scoring_valid = False
                    if place_rec and ("score" not in place_rec or "criteria_breakdown" not in place_rec):
                        scoring_valid = False
                    
                    if scoring_valid:
                        self.log_result("analysis", "Race Analysis", True, 
                                      f"Analysis complete for {horse_count} horses with 8-criteria scoring", 
                                      {"horse_count": horse_count, "has_recommendations": bool(win_rec or place_rec)})
                        return data
                    else:
                        self.log_result("analysis", "Race Analysis", False, 
                                      "Missing scoring or criteria breakdown in recommendations")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("analysis", "Race Analysis", False, 
                                  f"Missing required fields: {missing}", data)
            else:
                self.log_result("analysis", "Race Analysis", False, 
                              f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("analysis", "Race Analysis", False, f"Exception: {str(e)}")
        
        return None

    def test_betting_endpoints(self, analysis_data=None):
        """Test betting endpoints (create, get, settle)"""
        print("\n🔍 Testing Betting Endpoints...")
        
        bet_id = None
        
        # Test POST bet creation
        try:
            bet_data = {
                "track": "wolverhampton",
                "race_number": 1,
                "horse_name": "Test Horse",
                "draw_number": 1,
                "bet_type": "PLACE",
                "stake": 5.0,
                "odds": 3.5,
                "score": 6
            }
            
            # Use data from analysis if available
            if analysis_data and analysis_data.get("recommendations", {}).get("place"):
                place_rec = analysis_data["recommendations"]["place"]
                bet_data.update({
                    "horse_name": place_rec["horse"],
                    "draw_number": place_rec["draw_number"],
                    "stake": place_rec["stake"],
                    "odds": place_rec["odds"],
                    "score": place_rec["score"]
                })
            
            response = self.session.post(f"{self.api_url}/bets", json=bet_data)
            
            if response.status_code == 200:
                data = response.json()
                if "bet_id" in data:
                    bet_id = data["bet_id"]
                    self.log_result("bets", "Create Bet", True, 
                                  f"Bet created with ID: {bet_id}", data)
                else:
                    self.log_result("bets", "Create Bet", False, 
                                  "Missing bet_id in response", data)
            else:
                self.log_result("bets", "Create Bet", False, 
                              f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("bets", "Create Bet", False, f"Exception: {str(e)}")

        # Test GET bet history
        try:
            response = self.session.get(f"{self.api_url}/bets")
            
            if response.status_code == 200:
                data = response.json()
                if "bets" in data:
                    bet_count = len(data["bets"])
                    self.log_result("bets", "Get Bet History", True, 
                                  f"Retrieved {bet_count} bets", {"bet_count": bet_count})
                else:
                    self.log_result("bets", "Get Bet History", False, 
                                  "Missing bets field in response", data)
            else:
                self.log_result("bets", "Get Bet History", False, 
                              f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("bets", "Get Bet History", False, f"Exception: {str(e)}")

        # Test bet settlement if we have a bet_id
        if bet_id:
            try:
                settle_data = {"result": "WIN"}
                response = self.session.post(f"{self.api_url}/bets/{bet_id}/settle", json=settle_data)
                
                if response.status_code == 200:
                    data = response.json()
                    if "outcome" in data and "profit_loss" in data:
                        self.log_result("bets", "Settle Bet", True, 
                                      f"Bet settled as {data['outcome']}, P/L: ${data['profit_loss']}", data)
                    else:
                        self.log_result("bets", "Settle Bet", False, 
                                      "Missing outcome or profit_loss in response", data)
                else:
                    self.log_result("bets", "Settle Bet", False, 
                                  f"Status {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_result("bets", "Settle Bet", False, f"Exception: {str(e)}")

    def test_statistics_endpoint(self):
        """Test statistics endpoint"""
        print("\n🔍 Testing Statistics Endpoint...")
        
        try:
            response = self.session.get(f"{self.api_url}/statistics")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["overall", "by_score", "recent_form"]
                
                if all(field in data for field in required_fields):
                    overall = data["overall"]
                    by_score = data["by_score"]
                    
                    self.log_result("statistics", "Get Statistics", True, 
                                  f"Stats: {overall.get('total_bets', 0)} bets, {overall.get('win_rate', '0%')} win rate, {overall.get('roi', '0%')} ROI", 
                                  {"total_bets": overall.get('total_bets', 0), "score_levels": len(by_score)})
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("statistics", "Get Statistics", False, 
                                  f"Missing required fields: {missing}", data)
            else:
                self.log_result("statistics", "Get Statistics", False, 
                              f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("statistics", "Get Statistics", False, f"Exception: {str(e)}")

    def test_logout(self):
        """Test logout endpoint"""
        print("\n🔍 Testing Logout...")
        
        try:
            response = self.session.post(f"{self.api_url}/auth/logout")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_result("auth", "Logout", True, 
                                  "Logout successful", data)
                    return True
                else:
                    self.log_result("auth", "Logout", False, 
                                  "Missing message in response", data)
            else:
                self.log_result("auth", "Logout", False, 
                              f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("auth", "Logout", False, f"Exception: {str(e)}")
        
        return False

    def run_comprehensive_test(self):
        """Run all backend API tests"""
        print("🚀 Starting Comprehensive Backend API Testing...")
        print(f"🎯 Target API: {self.api_url}")
        print("=" * 60)
        
        # Authentication Tests
        if not self.test_user_registration():
            print("❌ Registration failed - cannot continue with authenticated tests")
            return self.generate_report()
        
        self.test_user_login()
        self.test_auth_me()
        self.test_google_oauth_redirect()
        
        # Core Feature Tests (require authentication)
        self.test_bankroll_endpoints()
        tracks_data = self.test_tracks_endpoint()
        analysis_data = self.test_race_analysis()
        self.test_betting_endpoints(analysis_data)
        self.test_statistics_endpoint()
        
        # Cleanup
        self.test_logout()
        
        return self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 BACKEND API TEST REPORT")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.test_results.items():
            if category == "errors":
                continue
                
            category_passed = sum(1 for test in tests if test["success"])
            category_total = len(tests)
            
            total_tests += category_total
            passed_tests += category_passed
            
            if category_total > 0:
                success_rate = (category_passed / category_total) * 100
                status = "✅" if success_rate == 100 else ("⚠️" if success_rate >= 50 else "❌")
                print(f"{status} {category.upper()}: {category_passed}/{category_total} ({success_rate:.1f}%)")
        
        overall_success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"\n🎯 OVERALL: {passed_tests}/{total_tests} ({overall_success_rate:.1f}%)")
        
        if self.test_results["errors"]:
            print(f"\n❌ CRITICAL ISSUES ({len(self.test_results['errors'])}):")
            for error in self.test_results["errors"]:
                print(f"   • {error}")
        
        # Determine if backend is functional
        auth_working = any(test["success"] for test in self.test_results["auth"] if "Registration" in test["test"] or "Login" in test["test"])
        core_working = any(test["success"] for test in self.test_results["analysis"])
        
        if auth_working and core_working:
            print(f"\n✅ BACKEND STATUS: FUNCTIONAL - Ready for frontend testing")
            return True
        else:
            print(f"\n❌ BACKEND STATUS: CRITICAL ISSUES - Fix backend before frontend testing")
            return False

def main():
    """Main test execution"""
    tester = HorseRacingAPITester()
    
    try:
        backend_functional = tester.run_comprehensive_test()
        
        # Save detailed results
        with open('/app/backend_test_results.json', 'w') as f:
            json.dump(tester.test_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")
        
        return 0 if backend_functional else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())