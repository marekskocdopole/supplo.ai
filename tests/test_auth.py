import unittest
from app import create_app, db
from app.core.models import User
import os

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        if os.path.exists('test.db'):
            os.remove('test.db')

    def test_login_page(self):
        """Test, že přihlašovací stránka je dostupná"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Přihlášení'.encode('utf-8'), response.data)

    def test_register_page(self):
        """Test, že registrační stránka je dostupná"""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Registrace'.encode('utf-8'), response.data)

    def test_login_redirect(self):
        """Test, že nepřihlášený uživatel je přesměrován na login"""
        response = self.client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Přihlášení'.encode('utf-8'), response.data)

if __name__ == '__main__':
    unittest.main() 