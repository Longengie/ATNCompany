from math import *

from flask import  (
    Flask,
    render_template,
    request,
    g,
    session,
    redirect,
    url_for
)
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps
from flask import jsonify
import pymongo 
from pymongo import MongoClient 
from datetime import date
### Tạo APP
app = Flask(__name__)
#, static_url_path='', static_folder='/static'
app.secret_key = "Longengie"

client = pymongo.MongoClient("mongodb+srv://longEngie:khanhlong456@longcluster-h1mvy.azure.mongodb.net/test?retryWrites=true&w=majority")
db = client["ATN"]

### CODE Flask - Python Web

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login', methods=['GET','POST'])
def login():
    ###Ch-eck session, if not go to login
    if session.get('logged_in_flag'):
        if session['logged_in_flag'] == True:
            return redirect(url_for('home'))
    query_parameters = request.args
    vusername = query_parameters.get("username")
    vpassword = query_parameters.get("password")
    logcollection = db["account"]
    ### ch-eck Account
    logresults = logcollection.find({"username":vusername, "password": vpassword})
    if  logresults.count() == 1:
        session['logged_in_flag'] = True
        session['ID'] = logresults[0]["StaffID"]
        session['username'] = logresults[0]["Username"]
        ### Search role, name and department
        stacollection = db["staff"]
        staffresults = logcollection.find({"ID": session['ID']})
        session['fullname'] = staffresults[0]["FullName"]
        session['role'] = staffresults[0]["Role"]
        session['department']  = staffresults[0]["Department"]
        return redirect(url_for('index'))
    else:
        session['logged_in_flag'] = False
        session['role'] = None;
        return render_template("login.html", mesg = "")

@app.route('/home')
def home():
    ### Ch-eck role to giving the approviate homepage
    if session.get('logged_in_flag'):
        if session['role'] == "Director":
            return render_template("manager.html")
        elif session['role'] == "Shop":
            return render_template("shop.html")
        else:
            session['logged_in_flag'] = False
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))
    ### Security reason /auto logout because user don't have enough permission

@app.route('/product', methods=['GET', 'POST'])
def product():
    ###Ch-eck role of session, if not the go to home
    if session['role'] == "Shop":
        procollection = db["products"]
        ###Show product database
        lpro = procollection.find()
        return render_template("prolist.html", proList = lpro)
    else:
        return redirect(url_for('home'))

@app.route('/addproduct', methods=['GET', 'POST'])
def addproduct():
    ###Ch-eck role of session, if not the go to home
    if session['role'] == "Shop":
        if ("productID" in request.args and "productName" in request.args and "productPrice" in request.args):
            pID = request.args.get("productID")
            pName = request.args.get("productName")
            pPrice = float(request.args.get("productPrice"))
            procollection = db["product"]
            ### Ch-eck if the product name and product ID available in database
            PIresults = procollection.find({"productID":pID})
            PNresults = procollection.find({"productName": pName})
            ### If the product name and product ID not available in database, count should be zero
            if  PIresults.count() < 1 or PNresults.count() < 1:
                ### Adding data
                newProduct = {"productID": pID,"productName": pName, "productPrice": pPrice}
                procollection.insert_one(newProduct)
                return redirect(url_for('product'))
        return render_template("addProduct.html")
    else:
        return redirect(url_for('home'))

@app.route('/updateproduct', methods=['GET', 'POST'])
def updateproduct():
    ###Ch-eck role of session, if not the go to home
    if session['role'] == "Shop":
        if ("productID" in request.args and "productName" in request.args and "productPrice" in request.args):
            pID = request.args.get("productID")
            pName = request.args.get("productName")
            pPrice = float(request.args.get("productPrice"))
            procollection = db["product"]
            ### Ch-eck if product ID available in database,only allow same department to edit
            PIresults = procollection.find({"productID":pID})
            if  PIresults.count() >= 1:
                ### Adding data in productID's data
                updateProduct = {"productName" : pName, "productPrice" : pPrice}
                procollection.update_one({"productID" : pID}, updateProduct)
                return redirect(url_for('product'))
        return render_template("updateProduct.html")
    else:
        return redirect(url_for('home'))

@app.route('/deleteproduct', methods=['GET', 'POST'])
def deleteproduct():
    ###Ch-eck role of session, if not the go to home
    if session['role'] == "Shop":
        if ("productID" in request.args):
            pID = request.args.get("productID")
            procollection = db["product"]
            ### Ch-eck if product ID available in database,only allow same department to delete
            PIresults = procollection.find({"productID":pID})
            if  PIresults.count() >= 1:
                ### Delete data
                procollection.delete_one({"productID" : pID})
                return redirect(url_for('product'))
        return render_template("deleteProduct.html")
    else:
        return redirect(url_for('home'))

@app.route('/order', methods=['GET', 'POST'])
def order():
    ###Ch-eck role of session, if not the go to home
    if session['role'] == "Shop":
        ordcollection = db["order"]
        ###Show product database
        lord = ordcollection.find()
        return render_template("shoplist.html", orderList = lord)
    else:
        return redirect(url_for('home'))

@app.route('/addorder', methods=['GET', 'POST'])
def addorder():
    ###Ch-eck role of session, if not the go to home
    if session['role'] == "Shop":
        if ("productID" in request.args and "orderID" in request.args and "orderAmount" in request.args):
            pID = request.args.get("productID")
            oID = request.args.get("orderID")
            oNum = int(request.args.get("orderAmount"))
            oDept = session['department']
            pStaff = session['ID']
            today = date.today()
            procollection = db["product"]
            ordcollection = db["order"]
            ### Ch-eck if order ID and order ID available in database,only allow same department to edit
            PIresults = procollection.find({"productID":pID})
            ORresults = ordcollection.find({"orderID":oID})
            if  PIresults.count() >= 1 and ORresults.count() < 1:
                pPrice = PIresults[0]["productPrice"]
                oSum = oNum * pPrice
                newOrder = {"orderID" : oID, "productID" : pID, "orderAmount" : oNum, "orderSum" : oSum, "Department" : pDept, "Date": today, "StaffID": oDept}
                procollection.insert_one(updateOrder)
                return redirect(url_for('order'))
        return render_template("addOrder.html")
    else:
        return redirect(url_for('home'))

@app.route('/updateorder', methods=['GET', 'POST'])
def updateorder():
    ###Check role of session, if not the go to home
    if session['role'] == "Shop":
        if ("productID" in request.args and "orderID" in request.args and "orderAmount" in request.args):
            pID = request.args.get("productID")
            oID = request.args.get("orderID")
            oDept = session['department']
            oNum = int(request.args.get("orderAmount"))
            procollection = db["product"]
            ordcollection = db["order"]
            ### Ch-eck if product ID and order ID available in database
            PIresults = procollection.find({"productID":pID})
            ORresults = ordcollection.find({"productID":pID, "Department" : pDept, "StaffID": oDept})
            if  PIresults.count() >= 1 and ORresults.count() >= 1:
                pPrice = PIresults[0]["productPrice"]
                oSum = oNum * pPrice
                updateOrder = {"productID" : pID, "orderAmount" : oNum, "orderSum" : oSum}
                procollection.update_one({"orderID" : oID}, updateOrder)
                return redirect(url_for('order'))
        return render_template("updateOrder.html")
    else:
        return redirect(url_for('home'))

@app.route('/deleteorder', methods=['GET', 'POST'])
def deleteorder():
    ###Check role of session, if not the go to home
    if session['role'] == "Shop":
        if ("productID" in request.args):
            oID = request.args.get("orderID")
            oDept = session['department']
            ordcollection = db["order"]
            ### Ch-eck if product ID available in database
            PIresults = procollection.find({"orderID":oID, "Department" : pDep, "StaffID": oDept})
            if  PIresults.count() >= 1:
                ### Delete data
                procollection.delete_one({"orderID" : oID})
                return redirect(url_for('product'))
        return render_template("deleteOrder.html")
    else:
        return redirect(url_for('home'))

@app.route('/summary', methods=['GET', 'POST'])
def summary():
    ###Check role of session, if not the go to home
    if session['role'] == "Director":
        today = date.today()
        ordcollection = db["order"]
        procollection = db["products"]
        ### Search data product and order for today
        lord = ordcollection.find({"Date": today})
        lpro = procollection.find({"Date": today})
        ### Summary the order in today
        todaytolorder = sum([ row["orderSum"] for row in lord],0)
        ### count order and product today
        sumcollection = lord.count()
        sumproduct = lpro.count()
        return render_template("sum.html", orderCount = sumcollection, todayTolOrder = todayorder, todayProduct = todayproduct)
    else:
        return redirect(url_for('home'))

@app.route('/todayorder', methods=['GET', 'POST'])
def todayorder():
    ###Ch-eck role of session, if not the go to home
    if session['role'] == "Director":
        today = date.today()
        ordcollection = db["order"]
        ###Show product database
        lord = ordcollection.find({"Date": today})
        return render_template("sumlist.html", List = lord)
    else:
        return redirect(url_for('home'))

@app.route('/staff', methods=['GET', 'POST'])
def staff():
    ###Ch-eck role of session, if not the go to home
    if session['role'] == "Director":
        procollection = db["staff"]
        ###Show product database
        lpro = procollection.find()
        return render_template("stafflist.html", List = lpro)
    else:
        return redirect(url_for('home'))
@app.route('/yourprofile')
def yourprofile():
    if session.get('logged_in_flag'):
        staffid = session['ID']
        staffcollection = db["staff"]
        ### ch-eck Account
        staffresults = staffcollection.find({"StaffID": staffid})
        return render_template("list.html",List = staffresults)
    else:
        return redirect(url_for('home'))

    
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    #if session.get('logged_in_flag'):
    if 'logged_in_flag' in session:
        session['username'] = None
        session['fullname'] = None
        session['role'] = None
        session['logged_in_flag'] = False
    return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

@app.errorhandler(500)
def page_not_found(e):
    return render_template("404.html")
