from app import create_app


app = create_app()


with app.test_client() as client:
    login_page = client.get('/login')
    assert login_page.status_code == 200

    admin_login = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert admin_login.status_code == 200
    assert admin_login.request.path == '/dashboard'

    client.get('/logout', follow_redirects=True)

    seller_login = client.post('/login', data={'username': 'vendedor', 'password': 'vendedor123'}, follow_redirects=True)
    assert seller_login.status_code == 200
    assert seller_login.request.path == '/dashboard'

    print('AUTH_FLOW_OK')
