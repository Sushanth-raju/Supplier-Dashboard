from bson import decimal128
from flask import Flask,render_template,request,url_for,session
from flask.templating import render_template_string
from reportlab.platypus.flowables import splitLine
from reportlab.platypus.paragraph import split
from werkzeug.utils import redirect
from flask_session import Session
from bson import ObjectId # For ObjectId to work
from bson.objectid import ObjectId
from bson.decimal128 import Decimal128, create_decimal128_context
import decimal
import pymongo
import bcrypt
import pandas as pd
from datetime import datetime
import calendar
import pygal
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
# reading the price and product from grocery sheet
dat=pd.read_csv('Grocery.csv')
dat=dat.values.tolist()
li=[]
mi=[]
st=[]
pr=[]
spl=[]
#treshold = 3
#db connection
mongo = pymongo.MongoClient('mongodb+srv://Salman:salman@cluster0.kjvnu.mongodb.net/chef_at_home_testing?retryWrites=true&w=majority', tls=True, tlsAllowInvalidCertificates=True)

db = pymongo.database.Database(mongo, 'chef_at_home_testing')
col = pymongo.collection.Collection(db, 'supplierlogin')
col1=pymongo.collection.Collection(db, 'companylogin'   )
ind=pymongo.collection.Collection(db, 'items')
ai=pymongo.collection.Collection(db, 'add_item')
inv=pymongo.collection.Collection(db,'inventory')
inv_cred = pymongo.collection.Collection(db, 'inventory_login_cred')
inv_item_ingredients = pymongo.collection.Collection(db, 'inv_item_ingredients')
prod_to_item_map = pymongo.collection.Collection(db, 'prod_to_dish_map')

y=col.find()
for i in y:
    spl.append(i)
    
x=ind.find()
for data in x:
    li.append(data)

#initializing flask
app=Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

#initializing session
Session(app)

#render to homepage
@app.route('/')
def home():
    return render_template('home_final.html')
#validating username and password and redirect to respective dashboard
@app.route('/res' ,methods=['GET', 'POST'])
def res():
    if request.method=="POST":
        details=request.form
        #fectching th data
        print(details)
        details=details.getlist("x")
        print(details)
        domain=str(details[0])
        if domain=="SUPPLIER":
            msg=""
            details=request.form
            #fetching data
            name=str(details.getlist('username')[0])
            password=str(details.getlist('password')[0])
            #fetching data from collection
            login_user=col.find()
            for i in login_user:
                #match case
                if i['name']==name:
                    if i['password']==password:
                        session["s_username"]=name 
                        msg="Successfully Logged In"
                        return render_template('sindex.html',msg=msg)
                    #unmatch case
                    else:
                        msg="Invalid Password!!!"
                        return render_template('home_final.html',msg=msg)
            msg="Invalid Login Credential"
            return render_template('home_final.html',msg=msg)
        elif domain=="INVENTORY":
            credentials = request.form
            print(credentials)

            inv_uname = credentials.getlist("username")
            inv_password = credentials.getlist("password")

            msg=""
            db_cred = inv_cred.find_one({})
            print(db_cred)
            print(inv_uname,inv_password)
            if db_cred["username"] == inv_uname[0]:
                if db_cred["password"] == inv_password[0]:
                    session["i_username"] = inv_uname
                    return render_template("inv_index.html")
                else:
                    return render_template("home_final.html",msg="Invalid Password")
            else:
                return render_template("home_final.html",msg="Invalid Username")
            
        else:
            msg=""
            #fetch the data
            details=request.form
            name=str(details.getlist('username')[0])
            password=str(details.getlist('password')[0])
            #fetch from collection
            login_user=col1.find()
            for i in login_user:
                # match case
                if i["name"] == name:
                    if i["password"] == password:
                        session["c_username"] = name
                        return render_template("cindex.html",spl=spl)
                    # unmatch case
                    else:
                        msg="Invalid Password!!!"
                        return render_template('home_final.html',msg=msg)
            msg="Invalid Login Credential"
            return render_template('home_final.html',msg=msg)
    return redirect(url_for("home"))

#signup button
@app.route('/sgnup')
def ssup():
    return render_template('ssignup.html')

#signup details update in the collection
@app.route('/sgnupdetail',methods=['GET','POST'])
def signdtl():
    if request.method=="POST":
        details=request.form
        #fetch the data
        uname=details['username']
        passsu=details['crpassword']
        passsu1=details['copassword']
        if passsu!=passsu1:
            msg="Password does not match"
            return render_template('ssignup.html',msg=msg)
        else:
            # inserting values to collection
            col.insert_one({"name": uname, "password": passsu})
            msg = "Username succesfully updated"
        return render_template("home_final.html", msg=msg)


#add stock totally
@app.route('/cmain',methods=['GET','POST'])
def cmain():
    # create dictionary
    cost = 0
    if request.method == "POST":
        #push the data into collection
        for i in mi:
            for j in range(len(dat)):
                if dat[j][0] == i[0]:
                    # fetching price of item
                    cost = dat[j][1]
                js = {"product": i[0], "quantity": i[1],"date": datetime.now().isoformat(),"status": "Entered","cost": cost * i[1],'sup_id':i[2]}
                # inserting one by one
                ai.insert_one(js)
                break
        mi.clear()
        return render_template("cindex.html",spl=spl)

@app.route('/cpass')
def cpass():
    if "c_username" not in session:
        return redirect(url_for("home"))
    return render_template('cpass.html')

#change password for company
@app.route('/cpassword',methods=['GET','POST'])
def cpassword():
    if "c_username" not in session:
        return redirect(url_for("home"))
    msg=""
    l=[]
    if request.method=="POST":
        details=request.form
        #fetch the data
        name="chefathome" 
        passw=details['cpassw']
        passw1=details['npassw']
        npass=details['rnpassw']
        if passw1 != npass:
            return render_template('cpass.html')
        #search for password and name if name and password in collection allow them to change password
        login_user=col1.find_one({'name':name})
        upass=login_user['password']
        uname=login_user['name']
        if uname==name and upass==passw:
            #update command
            myquery = { "password": passw }
            newvalues = { "$set": { "password": npass } }
            col1.update_one(myquery, newvalues)
            msg="Password Updated Sucessfully!!!"
            return render_template('home_final.html',msg=msg)
        else:
            msg="Invalid Credentials !! Try Again"
            return render_template('cpass.html',msg=msg)

@app.route('/spass')
def spass():
    if "s_username" not in session:
        return redirect(url_for("home"))
    return render_template('spass.html')


#change password for supplier
@app.route('/spassword',methods=['GET','POST'])
def spassword():
    if "s_username" not in session:
        return redirect(url_for("home"))
    msg=""
    if request.method=="POST":
        details=request.form
        name="Sathya Provision" 
        passw=details['cpassw']
        passw1=details['npassw']
        npass=details['rnpassw']
        if passw1 != npass:
            return render_template('cpass.html')
        login_user=col.find_one({'name':name})
        upass=login_user['password']
        uname=login_user['name']
        #search for password and name if name and password in collection allow them to change password
        if uname==name and upass==passw:
            myquery = { "password": passw }
            newvalues = { "$set": { "password": npass } }
            col.update_one(myquery, newvalues)
            msg="Password Updated Sucessfully!!!"
            return render_template('home_final.html',msg=msg)
        else:
            msg="Invalid Credentials !! Try Again"
            return render_template('spass.html',msg=msg)


#logout part
@app.route('/logout_sess')
def logout_sess():
    if "s_username" in session:
        session.pop('s_username',None)
    elif "c_username" in session:
        session.pop('c_username',None)
    elif "i_username" in session:
        session.pop('i_username',None)
    return redirect(url_for("home"))  



#view stock part
@app.route('/vstock')
def vstock():
    if "c_username" not in session:
        return redirect(url_for("home"))
    return render_template('viewstock.html',tables=ind.find())

#suppliers details in company index
@app.route('/suppliers',methods=["GET","POST"])
def sdisplay():
    if "c_username" not in session:
        return redirect(url_for("home"))
    return render_template("sdisplay.html", spl=spl)


#remove stock part
@app.route('/remove', methods=['GET','POST'] )
def remove():
    if "c_username" not in session:
        return redirect(url_for("home"))
    if request.method=="POST":
        ms=""
        details=request.form
        n=int(details['no'])
        print(n)
        #match case
        if n in range(0,len(mi)):
            mi.pop(n)
            ms="ITEM REMOVED SUCCESSFULLY"
        #unmatch case
        else:
            ms="ITEM NUMBER NOT EXIST, SO CAN'T REMOVE"
        print(mi)
        return render_template("addstock.html", tbl=mi, ms=ms, li=li,spl=spl)


#add stock page
@app.route('/stock', methods=['GET','POST'])
def stock():
    if "c_username" not in session:
        return redirect(url_for("home"))
    msg = ""
    if request.method == "POST":
        details = request.form
        # fetch data
        pro = details["name"]
        quan = int(details["pass"])
        supid = details["s_id"]
        mi.append([pro, quan, supid])
        # new=pd.DataFrame(mi,columns=['PRODUCT','QUANTITY'])
        # js={"product":pro,"quantity":quan,"date":datetime.now()}
        # ai.insert_one(js)
        msg = "ITEM ADDED SUCCESSFULLY"
        return render_template("addstock.html", tbl=mi, msg=msg, li=li,spl=spl)


# previously purchased stock
@app.route("/previous", methods=["GET", "POST"])
def previous():
    if "s_username" not in session:
        return redirect(url_for("home"))
    lis = []
    s_name=session["s_username"]
    if request.method == "POST":
        details = request.form
        print(details)
        #getting from date
        d1=details['from']
        date1=datetime.strptime(d1, '%Y-%m-%d')
        #getting two date
        d2=details['to']
        date2=datetime.strptime(d2, '%Y-%m-%d')
        print(date1,date2)
        start = date1.date()
        #from date
        start=str(start)+'T0'
        #end date
        end = date2.date()
        end = str(end) + "T23"
        print(start, end)
        # search in collection
        find = ai.find(
            {"$and": [{"date": {"$gte": start}}, {"date": {"$lte": end}}]},
            {"_id": 0, "product": 1, "quantity": 1, "status": 1,"supp_id":s_name}
        )
        for x in find:
            if x["status"] == "Approved"and x["supp_id"]==s_name:
                pro = [x["product"], x["quantity"], x["status"],x["supp_id"]]
                lis.append(pro)
        print(lis)
        return render_template('previousstock.html',tbl=lis)



#approved stock 
@app.route('/astock')
def astock():
    if "c_username" not in session:
        return redirect(url_for("home"))
    stock=[]
    #todat date
    d=datetime.today().strftime('%Y-%m-%d')
    start = d +'T0'
    #find all the approved stock mand appending in list stock
    find = ai.find({  'date' : { '$gte': start } },{'_id':0,'product':1,'quantity':1,'status':1,'delivery':1,'reason':1})
    for x in find:
        if "delivery" in x:
            s=[x['product'],x['quantity'],x['status'],x['delivery'],x['reason']]
            stock.append(s)
    return render_template('viewapproval.html',tbl=stock)

@app.route('/smain', methods=['GET','POST'])
def smain():
    if "s_username" not in session:
        return redirect(url_for("home"))
    if request.method=="POST":
        details=request.form
        val=int(details.getlist("findItems")[0])
        print(val,type(val))
        if val==1:
            return redirect(url_for("stockapprove"))
        elif val==2:
            x=ind.find()
            for data in x:
                pr.append(data)
            return render_template('priceedit.html',li=pr)
        else:
            return render_template('previousstock.html')
        
#stock approve
@app.route('/stockapprove', methods=['GET','POST'])
def stockapprove():
    if "s_username" not in session:
        return redirect(url_for("home"))
    s_name=session["s_username"]
    # today date
    print("list st is ===>", st)
    while st:
        st.pop()
    d = datetime.today().strftime("%Y-%m-%d")
    start = d + "T0"
    # find the entered stock
    find = ai.find(
        {"date": {"$gte": start}}, {"_id": 1, "product": 1, "quantity": 1, "status": 1,"supp_id":s_name}
    )
    for x in find:
        if x["status"] == "Entered" and x["supp_id"]==s_name:
            st.append(x)
    for i in st:
        print(i["_id"],i["supp_id"])
    return render_template("stockapprove.html", tbl=st)


#supplier change the status approved or not approved
@app.route('/sa', methods=['GET', 'POST'])
def index():
    if "s_username" not in session:
        return redirect(url_for("home"))
    n=[]
    ap=[]
    if request.method == 'POST':
        #if supplier click check box it is approved else not approved
        res=request.form.getlist('mycheckbox')
        day=request.form.getlist('days')
        reason=request.form.getlist('reason')
        print(request.form)
        print(reason)
        print(day)
        j=0
        #approve stock status will be approved else we m,ake it not approved
        for i in st:
            myquery = { "_id": i['_id'] }
            newvalues = { "$set": { "delivery": day[j] } }
            ai.update_one(myquery, newvalues)
            myquery = { "_id": i['_id'] }
            newvalues = { "$set": { "reason": reason[j] } }
            ai.update_one(myquery, newvalues)
            j=j+1
        for i in st:
            print(str(i['_id']))
            if str(i['_id']) not in res:
                n.append(i['_id'])
        print(n)
        for i in res:
            c=0
            myquery = { "_id": ObjectId(i) }
            newvalues = { "$set": { "status": "Approved" } }
            ai.update_one(myquery, newvalues)
            find = ai.find_one({'_id': ObjectId(i)},{'product':1,'quantity':1})
            print(find['product'],find['quantity'])
            #a=inv.find_one({'Item':find['product']},{'Quantity':1})
            #print(a,find)
            c=find['quantity']
            query={"Item":find['product']}
            newval={ "$set": {"Quantity":c}}
            inv.update_one(query,newval)
        for i in n:
            myquery = { "_id": i }
            newvalues = { "$set": { "status": "Not Approved" } }
            ai.update_one(myquery, newvalues)

        return render_template('sindex.html')


@app.route('/commain', methods=['GET','POST'])
def commain():
    if "c_username" not in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        details = request.form
        val = int(details.getlist("findItems")[0])
        print(val, type(val))
        if val == 1:
            spl.clear()
            y=col.find()
            for i in y:
                spl.append(i)
            return render_template("addstock.html", li=li,spl=spl)
        elif val == 2:
            return redirect(url_for("vstock"))
        elif val==3:
            return redirect(url_for("astock"))
        elif val==5:
            return redirect(url_for("view_inventory"))
        elif val==6:
            return render_template("sdisplay.html",spl=spl)
        else:
            return render_template('previousstock.html')
    


@app.route('/dv', methods=['GET','POST'])
def dv():
    if "c_username" not in session:
        return redirect(url_for("home"))
    ab = ai.find({},{"_id":0,"product":1,"quantity":1}).sort([("quantity", -1)]).limit(10)
    data=list(ab)
        #data = pd.DataFrame(list(ab))
    print(data)
        #data.plot.bar(x="product", y="quantity", rot=70, title=" ");
        #plt.show(block=True);
    bar_chart = pygal.Bar(height=300)
    bar_chart.title = 'Top 10 Goods Purchased'
    for x in data:
        bar_chart.add(x['product'],x['quantity'])
    bar_chart = bar_chart.render_data_uri()
    return render_template('visual.html',ch=bar_chart)



 #price edit
@app.route('/price', methods=['GET','POST'])
def priceedit():
    if "s_username" not in session:
        return redirect(url_for("home"))      
    msg=""
    if request.method=="POST":
        details=request.form
        #fetch the data
        pro=details['name']
        price=int(details['price'])
        #changing new price
        myquery = { "ITEM": pro }
        newvalues = { "$set": { "Price": price } }
        ind.update_one(myquery, newvalues)
        msg="Price changed Sucessfully"
        return render_template('priceedit.html',msg=msg,li=pr)


@app.route('/invoice', methods=['GET','POST'])
def invoice():
    if "c_username" not in session:
        return redirect(url_for("home"))
    bill=[]
    msg=""
    d=datetime.today().strftime('%Y-%m-%d')
    start = d +'T0'
    find = ai.find({  'date' : { '$gte': start } },{'date':1,'product':1,'quantity':1,'cost':1,'status':1})
    i=1
    pr=0
    for x in find:
        if x['status']=='Approved':
            bill.append([i,x['date'],x['product'],x['quantity'],x['cost']])
            i=i+1
            pr+=x['cost']
    DATA = [["S.NO","DATE" , "ITEM NAME", "QUANTITY", "PRICE (Rs.)" ]]
    for x in bill:
        DATA.append(x)
    DATA.append(["TOTAL","","","",pr])
    print(DATA)
    # creating a Base Document Template of page size A4
    pdf = SimpleDocTemplate( "receipt.pdf" , pagesize = A4 )

    # standard stylesheet defined within reportlab itself
    styles = getSampleStyleSheet()

    # fetching the style of Top level heading (Heading1)
    title_style = styles[ "Heading1" ]

    # 0: left, 1: center, 2: right
    title_style.alignment = 1

    # creating the paragraph with
    # the heading text and passing the styles of it
    title = Paragraph( "PROVISION BILL" , title_style )

    # creates a Table Style object and in it,
    # defines the styles row wise
    # the tuples which look like coordinates 
    # are nothing but rows and columns
    style = TableStyle(
    [
        ( "BOX" , ( 0, 0 ), ( -1, -1 ), 1 , colors.black ),
        ( "GRID" , ( 0, 0 ), ( 4 , 4 ), 1 , colors.black ),
        ( "BACKGROUND" , ( 0, 0 ), ( 3, 0 ), colors.gray ),
        ( "TEXTCOLOR" , ( 0, 0 ), ( -1, 0 ), colors.whitesmoke ),
        ( "ALIGN" , ( 0, 0 ), ( -1, -1 ), "CENTER" ),
        ( "BACKGROUND" , ( 0 , 1 ) , ( -1 , -1 ), colors.beige ),
    ]
    )

    # creates a table object and passes the style to it
    table = Table( DATA , style = style )

    # final step which builds the
    # actual pdf putting together all the elements
    pdf.build([ title , table ])
    fromaddr = "Zangtechnical3@gmail.com"
    toaddr = "works.suryav@gmail.com"

    msg = MIMEMultipart()

    msg['From'] =fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Invoice Approval"

    body = "Please approve this invoice. To confirm , respond to this mail"

    msg.attach(MIMEText(body, 'plain'))

    filename = "receipt.pdf"
    attachment = open("receipt.pdf", "rb")

    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)

    msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "@Zangers3")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
    return render_template('cindex.html')


#route for view inventory in both inventoy and company dashboard
@app.route('/view_inventory' , methods=['GET','POST'])
def view_inventory():
    if "c_username" not in session and "i_username" not in session:
        return redirect(url_for("home"))
    
    return render_template("view_inventory.html",params=inv.find({}))
    #return redirect(url_for("home"))

#@app.route("/inv_home", methods=['GET','POST'])
#def inv_home():
#    if request.method == 'POST':
#        credentials = request.form
#        print(credentials)
#
#        inv_uname = credentials.getlist("uname")
#        inv_password = credentials.getlist("psw")
#
#        msg=""
#        db_cred = inv_cred.find_one({})
#        print(db_cred)
#        print(inv_uname,inv_password)
#        if db_cred["username"] == inv_uname[0]:
#            if db_cred["password"] == inv_password[0]:
#                return render_template("inv_index.html")
#            else:
#                return render_template("inven_login.html",msg="Invalid Password")
#        else:
#            return render_template("inven_login.html",msg="Invalid Username")
        
        
#route for editing the inventory in inventory dashboard
@app.route("/edit_inventory", methods=['GET','POST'])
def edit_inventory():
    if "i_username" not in session:
        return redirect(url_for("home"))
    return render_template("edit_inventory.html",params=inv.find({}))

#api for editing inventory item values called from edit_inventory.html
@app.route("/edit_inv_items", methods=['GET','POST'])
def edit_inv_items():
    if "i_username" not in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        
        myquery = {"_id": ObjectId(request.json["_id"])}
        newvalues = { "$set": { "Item":request.json["Item"] , "Quantity":float(request.json["Quantity"]),"Unit":request.json["Unit"]}}
        inv.update_one(myquery, newvalues)
        
        return "Succes"

#api for remove inventory items called from remove_inv.html
@app.route("/remove_inv_items" , methods=['GET','POST'])
def remove_inv_items():
    if "i_username" not in session:
            return redirect(url_for("home"))
    if request.method == "POST":
        print(request.json)
        print(request)
        myquery = {"Item": request.json["Item"]}
        inv.delete_one(myquery)
        #inv_treshold.delete_one(myquery)
        print("After request")
        return "hello"

#api for adding items into inventory which is called from add_inv.html
@app.route("/add_inv_items" , methods=['GET','POST'])
def add_inv_items():
    if "i_username" not in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        print(request.json)
        print(request)
        myquery = {"Item": request.json["Item"],"Quantity":float( request.json["Quantity"]),"Treshold":float(request.json["Treshold"]),"Unit":request.json["Unit"]}
        inv.insert_one(myquery)
        #id = inv.find_one(myquery)["_id"]
        #inv_treshold.insert_one({"Item": request.json["Item"],"Treshold":3,"inv_id":id})
        print("After request")
        return "hello"


#route for removing stocks form inventory
@app.route("/remove_inventory",methods=["GET","POST"])
def remove_inventory():
    if "i_username" not in session:
        return redirect(url_for("home"))
    return render_template("remove_inv.html",params=inv.find({},{"_id":1,"Item":1,"Quantity":1}))

#route to visit app stocks in inventory
@app.route("/add_inventory",methods=["POST","GET"])
def add_inventory():
    if "i_username" not in session:
        return redirect(url_for("home"))
    return render_template("add_inv.html")

#api for set Threshold called form set_treshold.html
@app.route("/change_set_treshold" , methods=["POST","GET"])
def change_set_treshold():
    if "i_username" not in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        myquery = {"_id":ObjectId(request.json["_id"])} 
        newvalues = {"$set": {"Treshold":int(request.json["Treshold"])}}
        print(myquery,newvalues,request.json)
        inv.update_one(myquery,newvalues)
        return "hello"
#route for set treshold
@app.route("/set_treshold", methods=["POST", "GET"])
def set_treshold():
    if "i_username" not in session:
        return redirect(url_for("home"))
    return render_template("set_treshold.html",params=inv.find({}))

#@app.route("/set_treshold_password", methods=['POST'])
#def set_treshold_password():
#    if request.method == 'POST':
#        cred_details = inv_cred.find_one()
#        print(cred_details)
#        id = cred_details['_id']
#        myquery = {"_id":id}
#        newvalues = { "$set": { "password":request.json["val"]}}
#        inv_cred.update_one(myquery, newvalues)
#        return "successfull"


#route for change password of inventory login
@app.route('/ivcpass' , methods=["POST", "GET"])
def ivcpass():
    if "i_username" not in session:
        return redirect(url_for("home"))
    return render_template('ivcpass.html',params=inv.find({}))

#api for changing password for inventory which is called form ivcpass.html
@app.route('/ivcpassword',methods=['GET','POST'])
def ivcpassword():
    if "i_username" not in session:
        return redirect(url_for("home"))
    msg=""
    if request.method=="POST":
        details=request.form
        name="chefathome" 
        passw=details['icpassw']
        passw1=details['inpassw']
        npass=details['irnpassw']
        if passw1 != npass:
            return render_template('ivcpass.html')
        login_user=inv_cred.find_one()
        print("Hi",login_user)
        upass=login_user['password']
        uname=login_user['username']
        #search for password and name if name and password in collection allow them to change password
        if uname==name and upass==passw:
            myquery = { "password": passw }
            newvalues = { "$set": { "password": npass } }
            inv_cred.update_one(myquery, newvalues)
            msg="Password Updated Sucessfully!!!"
            return render_template('home_final.html',msg=msg)
        else:
            msg="Invalid Credentials !! Try Again"
            return render_template('ivcpass.html',msg=msg)

#api for the products to call when orders are placed
@app.route("/order_placed", methods=['POST'])
def order_placed():
    if request.method=="POST":
        if request.json["api_key"] == "cah_zang":
            items = request.json["items"]

            for item in items:
                dish_name = item["p_name"]
                dish_qty = int(item["quantity"])
                item_arr = prod_to_item_map.find_one({"product_name":dish_name})["items"]
                for i in item_arr:
                    ingred = inv_item_ingredients.find_one({"Recipe":i})["Ingredients&Quantity"]
                
                    for key,val in ingred.items():
                        myquery = {"Item":key}
                        inv_qty_item = inv.find_one(myquery)["Quantity"]
                        newvalues = { "$set": {"Quantity":int(inv_qty_item)-(dish_qty * val)}}
                        inv.update_one(myquery, newvalues)


            
            return "Successfully"


        else:
            return "auth failed"
    return "imporper method(use post)"



if __name__ == '__main__':
    app.run(debug=True)




#n_orders = request.json["n_orders"]
#            item_names = request.json["items"]
#           print(item_names)
#           for dic in item_names:
#              data = inv_item_ingredients.find_one({"Recipe":dic["item"]})
#              print("Data is",data)
#              print("================================")
#                print("next is",data["Ingredients&Quantity"].items())
#              for k,val in data["Ingredients&Quantity"].items():
#                   print("================================")
#                   print(inv)
#                    print("inside lpoop",int(inv.find_one({"Item":k})["Quantity"])-(n_orders*(val)))

#                    inv.update_one({"Item":k},{"$set":{"Quantity":int(inv.find_one({"Item":k})["Quantity"])-(n_orders*(val))}})
                
