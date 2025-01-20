from app import create_app, socketio
import os

app = create_app()

if __name__ == '__main__':
    # Produkční nastavení
    if os.environ.get('FLASK_ENV') == 'production':
        port = int(os.environ.get('PORT', 80))
        socketio.run(app,
                    host='0.0.0.0',  # Povolí přístup z vnější sítě
                    port=port,
                    debug=False,
                    use_reloader=False,
                    allow_unsafe_werkzeug=True)
    else:
        # Vývojové nastavení - použijeme port 5001 místo 5000
        socketio.run(app, 
                    host='127.0.0.1',
                    port=5001,
                    debug=True,
                    use_reloader=True,
                    reloader_type='stat',
                    allow_unsafe_werkzeug=True) 