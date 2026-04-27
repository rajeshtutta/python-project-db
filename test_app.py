import pytest
import json
from unittest.mock import patch, MagicMock
from app import app, create_user, fetch_user_by_id, remove_user_by_id
from services.user_service import hash_password, initialize_app_database
from repositories.user_repository import row_to_dict


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'name': 'John Doe',
        'email': 'john@example.com',
        'address': '123 Main St',
        'phonenumber': '555-1234',
        'password': 'securepass123'
    }


class TestUserService:
    """Test cases for the user service layer."""

    def test_hash_password_creates_different_hashes(self):
        """Test that hash_password creates different hashes for the same password."""
        password = 'testpassword123'
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different (due to salt)
        assert hash1 != hash2

    def test_hash_password_is_not_plaintext(self):
        """Test that hashed password is not the same as plaintext."""
        password = 'testpassword123'
        hashed = hash_password(password)
        assert hashed != password

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        password = 'testpassword123'
        hashed = hash_password(password)
        assert isinstance(hashed, str)


class TestUserRepository:
    """Test cases for the repository layer."""

    def test_row_to_dict_converts_correctly(self):
        """Test that row_to_dict correctly converts database row to dictionary."""
        # Simulating a database row (id, name, email, address, phonenumber)
        row = (1, 'John Doe', 'john@example.com', '123 Main St', '555-1234')
        
        result = row_to_dict(row)
        
        assert result['id'] == 1
        assert result['name'] == 'John Doe'
        assert result['email'] == 'john@example.com'
        assert result['address'] == '123 Main St'
        assert result['phonenumber'] == '555-1234'

    def test_row_to_dict_returns_dict(self):
        """Test that row_to_dict returns a dictionary."""
        row = (1, 'John Doe', 'john@example.com', '123 Main St', '555-1234')
        result = row_to_dict(row)
        assert isinstance(result, dict)


class TestFlaskRoutes:
    """Test cases for Flask routes."""

    def test_index_route_returns_success(self, client):
        """Test that index route returns 200 status code."""
        response = client.get('/')
        assert response.status_code == 200

    def test_index_route_returns_html(self, client):
        """Test that index route returns HTML content."""
        response = client.get('/')
        assert response.content_type == 'text/html; charset=utf-8'

    @patch('app.create_user')
    def test_submit_route_with_valid_data(self, mock_create_user, client, sample_user_data):
        """Test submit route with valid user data."""
        mock_create_user.return_value = {
            'id': 1,
            'name': sample_user_data['name'],
            'email': sample_user_data['email'],
            'address': sample_user_data['address'],
            'phonenumber': sample_user_data['phonenumber']
        }
        
        response = client.post('/submit', data=sample_user_data)
        
        assert response.status_code == 200
        mock_create_user.assert_called_once()

    @patch('app.create_user')
    def test_submit_route_missing_name(self, mock_create_user, client, sample_user_data):
        """Test submit route with missing name field."""
        del sample_user_data['name']
        response = client.post('/submit', data=sample_user_data)
        
        assert response.status_code == 302  # Redirect
        mock_create_user.assert_not_called()

    @patch('app.create_user')
    def test_submit_route_missing_email(self, mock_create_user, client, sample_user_data):
        """Test submit route with missing email field."""
        del sample_user_data['email']
        response = client.post('/submit', data=sample_user_data)
        
        assert response.status_code == 302  # Redirect
        mock_create_user.assert_not_called()

    @patch('app.create_user')
    def test_submit_route_missing_address(self, mock_create_user, client, sample_user_data):
        """Test submit route with missing address field."""
        del sample_user_data['address']
        response = client.post('/submit', data=sample_user_data)
        
        assert response.status_code == 302  # Redirect
        mock_create_user.assert_not_called()

    @patch('app.create_user')
    def test_submit_route_missing_phonenumber(self, mock_create_user, client, sample_user_data):
        """Test submit route with missing phonenumber field."""
        del sample_user_data['phonenumber']
        response = client.post('/submit', data=sample_user_data)
        
        assert response.status_code == 302  # Redirect
        mock_create_user.assert_not_called()

    @patch('app.create_user')
    def test_submit_route_missing_password(self, mock_create_user, client, sample_user_data):
        """Test submit route with missing password field."""
        del sample_user_data['password']
        response = client.post('/submit', data=sample_user_data)
        
        assert response.status_code == 302  # Redirect
        mock_create_user.assert_not_called()

    def test_get_data_route_get_request(self, client):
        """Test get_data route returns form for GET request."""
        response = client.get('/get-data')
        assert response.status_code == 200

    @patch('app.fetch_user_by_id')
    def test_get_data_route_post_with_valid_id(self, mock_fetch, client):
        """Test get_data route with valid numeric ID."""
        mock_fetch.return_value = [
            {
                'id': 1,
                'name': 'John Doe',
                'email': 'john@example.com',
                'address': '123 Main St',
                'phonenumber': '555-1234'
            }
        ]
        
        response = client.post('/get-data', data={'input_id': '1'})
        
        assert response.status_code == 200
        mock_fetch.assert_called_once_with(1)

    def test_get_data_route_post_with_invalid_id(self, client):
        """Test get_data route with non-numeric ID."""
        response = client.post('/get-data', data={'input_id': 'abc'})
        
        assert response.status_code == 200
        assert b'Enter a numeric ID' in response.data

    @patch('app.remove_user_by_id')
    def test_delete_route_get_request(self, mock_delete, client):
        """Test delete route returns delete confirmation form."""
        response = client.get('/delete/1')
        assert response.status_code == 200

    @patch('app.remove_user_by_id')
    def test_delete_route_post_request(self, mock_delete, client):
        """Test delete route removes user and redirects."""
        response = client.post('/delete/1', follow_redirects=False)
        
        assert response.status_code == 302  # Redirect
        mock_delete.assert_called_once_with(1)

    def test_submit_route_strips_whitespace(self, client):
        """Test that submit route strips whitespace from inputs."""
        with patch('app.create_user') as mock_create_user:
            mock_create_user.return_value = {'id': 1, 'name': 'John'}
            
            client.post('/submit', data={
                'name': '  John Doe  ',
                'email': '  john@example.com  ',
                'address': '  123 Main St  ',
                'phonenumber': '  555-1234  ',
                'password': 'pass123'
            })
            
            # Verify that the mocked create_user was called with stripped values
            called_args = mock_create_user.call_args[0]
            assert called_args[0] == 'John Doe'  # Name stripped
            assert called_args[1] == 'john@example.com'  # Email stripped


class TestInputValidation:
    """Test input validation across routes."""

    def test_submit_with_empty_strings(self, client):
        """Test submit route rejects empty strings after stripping."""
        with patch('app.create_user') as mock_create_user:
            response = client.post('/submit', data={
                'name': '   ',
                'email': 'john@example.com',
                'address': '123 Main St',
                'phonenumber': '555-1234',
                'password': 'pass123'
            })
            
            assert response.status_code == 302  # Should redirect
            mock_create_user.assert_not_called()

    def test_get_data_with_empty_id(self, client):
        """Test get_data rejects empty ID."""
        response = client.post('/get-data', data={'input_id': ''})
        assert response.status_code == 200
        # Should show error or return empty


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=.', '--cov-report=html'])
