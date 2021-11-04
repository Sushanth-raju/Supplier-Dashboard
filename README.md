# SupplierDashboard

- We used flask and pandas libraries and also used flask for making supplier dashboard.
 
- We added the function of adding stock,stock's quantatiy,when stock is registered(Previous Stock) and that things we can see from company side
   - In add stock function company will enter all the stocks they need and also there is option to remove the stocks.. submit button will store the stocks in db 
   - In previous stock function company will see the stock which has been added in db. In that function you have to provide us starting date and ending date and according to that date we retrive data from db and display the stock wich has been added from that time period
   - In view stock function we display the total stock which is saved in our db
- And from supplier side supplier can see the stock and according to it supplier can approved or not-approved stock
   - There is a stock approved function which will help supplier for accepting(approving) or not-accepting(not-approving) order  
   - We show the graph of our top 10 product (Ingrediont) which is sold most
   - In previous stock function supplier will see the stock which has been approved or not-approved in that particular time periods. For that function you have to provide us starting date and ending date and according to that date we retrive data and display the stock wich has been approved or not-approved from that time period


Html Templates:
home.html - home page
slogin.html - supplier login
clogin.html - company login
cpass - company password change password
spass - supplier password change password
sindex - supplier home page
cindex - company home page
view approval - status of stock
stock approve - approve the stock
previous stock - previous stock purchased
price edit - price edit for supplier
visual - data visualization
