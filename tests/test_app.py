"""Tests for the Mergington High School Activities API."""

import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_success(self, client, reset_activities):
        """Test successfully retrieving all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that we have the expected activities
        assert "Tennis Club" in data
        assert "Basketball Team" in data
        assert "Art Club" in data
        
    def test_get_activities_has_required_fields(self, client, reset_activities):
        """Test that each activity has required fields."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, details in data.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            
    def test_get_activities_participants_list(self, client, reset_activities):
        """Test that participants are returned as a list."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, details in data.items():
            assert isinstance(details["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client, reset_activities):
        """Test successfully signing up for an activity."""
        response = client.post(
            "/activities/Tennis Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity."""
        response = client.post(
            "/activities/Tennis Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        # Check that participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Tennis Club"]["participants"]
        
    def test_signup_duplicate_email(self, client, reset_activities):
        """Test that signing up with duplicate email fails."""
        response = client.post(
            "/activities/Tennis Club/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
        
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test that signing up for nonexistent activity fails."""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
        
    def test_signup_multiple_different_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple different activities."""
        student_email = "multi@mergington.edu"
        
        # Sign up for Tennis Club
        response1 = client.post(
            f"/activities/Tennis Club/signup?email={student_email}"
        )
        assert response1.status_code == 200
        
        # Sign up for Basketball Team
        response2 = client.post(
            f"/activities/Basketball Team/signup?email={student_email}"
        )
        assert response2.status_code == 200
        
        # Verify both signups
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert student_email in activities["Tennis Club"]["participants"]
        assert student_email in activities["Basketball Team"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successfully unregistering from an activity."""
        response = client.delete(
            "/activities/Tennis Club/unregister?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant."""
        response = client.delete(
            "/activities/Tennis Club/unregister?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        
        # Check that participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "alex@mergington.edu" not in activities["Tennis Club"]["participants"]
        
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test that unregistering from nonexistent activity fails."""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
        
    def test_unregister_not_registered_student(self, client, reset_activities):
        """Test that unregistering a student who isn't registered fails."""
        response = client.delete(
            "/activities/Tennis Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
        
    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that a student can unregister and then sign up again."""
        email = "alex@mergington.edu"
        
        # Unregister
        response1 = client.delete(
            f"/activities/Tennis Club/unregister?email={email}"
        )
        assert response1.status_code == 200
        
        # Check they're unregistered
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Tennis Club"]["participants"]
        
        # Sign up again
        response2 = client.post(
            f"/activities/Tennis Club/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Check they're registered again
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Tennis Club"]["participants"]


class TestIntegration:
    """Integration tests for the API."""
    
    def test_workflow_signup_and_unregister(self, client, reset_activities):
        """Test complete workflow of signing up and unregistering."""
        activity = "Art Club"
        email = "workflow@mergington.edu"
        
        # Signup
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
        initial_count = len(activities[activity]["participants"])
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        activities = client.get("/activities").json()
        assert email not in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == initial_count - 1
