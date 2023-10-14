from app import app, serve

if __name__ == '__main__':
    app.run(debug=True, port=9900)

# if __name__ == "__main__":
#     serve(app, host="0.0.0.0", port=8085)
