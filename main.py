#region Imports
from extensions import login_manager
from app_factory import create_app
from flask import render_template,request
from flask_login import current_user
from models import User
from dotenv import load_dotenv



# endregion

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Server Error: {error}, User: {current_user.get_id()}, Route: {request.url}, "
                     f"Method: {request.method}, Data: {request.data}")
    return render_template('500.html',sida='Server Fel',header='Server Fel'), 500

# Exempelrutt som kan orsaka ett fel
@app.route('/cause_error')
def cause_error():
    raise Exception("This is a test exception")

#region Userless
@app.route('/')
def home():
    sida = "Hem"
    #info = read_info("texts/unikOrg.txt")
    info = "info"
    unik = info.split("*")
    content_header = [unik[i] for i in range(len(unik)) if i % 2 == 0]
    content_text = [unik[i] for i in range(len(unik)) if i % 2 != 0]
    start_info = zip(content_header, content_text)
    return render_template('base/home.html',sida=sida,header="Tyler O'Brien",sideOptions=None, start_info=start_info)

@app.route('/blog')
def blog():
    sida="Blogg"
    render_template('blog.html',sida=sida,header=sida)
    
# endregion

#region Login/Out


#endregion

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5001, debug=True)