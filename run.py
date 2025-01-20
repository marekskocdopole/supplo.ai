from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, 
                host='127.0.0.1',
                port=5001,
                debug=True,
                use_reloader=True,
                reloader_type='stat',
                allow_unsafe_werkzeug=True) 